use std::collections::HashMap;

use chrono::DateTime;
use chrono::TimeZone;
use chrono::Utc;
use reqwest::StatusCode;
use serde::Deserialize;
use serde::Serialize;
use thiserror::Error;

use crate::fetch::types::LanguageStat;
use crate::fetch::types::Stats;
use crate::fetch::types::Target;

const GITHUB_GRAPHQL: &str = "https://api.github.com/graphql";

// query lifted from insp/github-stats/src/statistics.zig:252-283
const QUERY: &str = r"
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(
      first: 100,
      after: $after,
      ownerAffiliations: [OWNER],
      isFork: false
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        nameWithOwner
        languages(
          first: 100,
          orderBy: { direction: DESC, field: SIZE }
        ) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
  }
}
";

#[derive(Debug, Serialize)]
struct GraphQLRequest<'a> {
    query: &'a str,
    variables: Variables<'a>,
}

#[derive(Debug, Serialize)]
struct Variables<'a> {
    login: &'a str,
    after: Option<&'a str>,
}

#[derive(Debug, Deserialize)]
struct GraphQLResponse<T> {
    data: Option<T>,
    errors: Option<Vec<GraphQLError>>,
}

#[derive(Debug, Deserialize)]
struct GraphQLError {
    message: String,
}

#[derive(Debug, Deserialize)]
struct UserData {
    user: Option<UserNode>,
}

#[derive(Debug, Deserialize)]
struct UserNode {
    repositories: RepoConnection,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RepoConnection {
    page_info: PageInfo,
    nodes: Vec<RepoNode>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PageInfo {
    has_next_page: bool,
    end_cursor: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RepoNode {
    // kept in the deserialised shape for debugging diffs; not consumed by aggregation
    #[allow(dead_code)]
    name_with_owner: String,
    languages: LanguageConnection,
}

#[derive(Debug, Deserialize)]
struct LanguageConnection {
    edges: Vec<LanguageEdge>,
}

#[derive(Debug, Deserialize)]
struct LanguageEdge {
    size: u64,
    node: LanguageNode,
}

#[derive(Debug, Deserialize)]
struct LanguageNode {
    name: String,
    color: Option<String>,
}

#[derive(Debug, Error)]
pub enum FetchError {
    #[error("http error: {0}")]
    Http(#[from] reqwest::Error),
    #[error("rate limited (remaining {remaining}, reset at {reset_at})")]
    RateLimited {
        reset_at: DateTime<Utc>,
        remaining: u32,
    },
    #[error("unauthorized: token missing or invalid")]
    Unauthorized,
    #[error("graphql error(s): {0:?}")]
    GraphQL(Vec<String>),
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
}

pub struct Client {
    http: reqwest::Client,
    endpoint: String,
    token: String,
}

impl Client {
    /// Create a client targeting the production GitHub GraphQL endpoint.
    pub fn new(token: impl Into<String>) -> Result<Self, FetchError> {
        Self::with_endpoint(GITHUB_GRAPHQL, token)
    }

    /// Create a client pointing at a custom endpoint, used by tests.
    pub fn with_endpoint(
        endpoint: impl Into<String>,
        token: impl Into<String>,
    ) -> Result<Self, FetchError> {
        let http = reqwest::Client::builder()
            .user_agent(concat!("ghlang/", env!("CARGO_PKG_VERSION")))
            .build()?;
        Ok(Self {
            http,
            endpoint: endpoint.into(),
            token: token.into(),
        })
    }

    /// Fetch a user's aggregated language stats across all owned non-fork repos.
    pub async fn fetch_user(&self, login: &str) -> Result<Stats, FetchError> {
        let mut after: Option<String> = None;
        let mut totals: HashMap<String, (u64, Option<String>)> = HashMap::new();
        let mut repo_count: u32 = 0;

        loop {
            let body = GraphQLRequest {
                query: QUERY,
                variables: Variables {
                    login,
                    after: after.as_deref(),
                },
            };

            let resp = self
                .http
                .post(&self.endpoint)
                .bearer_auth(&self.token)
                .json(&body)
                .send()
                .await?;

            let status = resp.status();
            if status == StatusCode::UNAUTHORIZED {
                return Err(FetchError::Unauthorized);
            }
            if status == StatusCode::FORBIDDEN
                && let Some(rate) = parse_rate_limit(&resp)
                && rate.0 == 0
            {
                return Err(FetchError::RateLimited {
                    reset_at: rate.1,
                    remaining: rate.0,
                });
            }
            let resp = resp.error_for_status()?;
            let parsed: GraphQLResponse<UserData> = resp.json().await?;

            if let Some(errs) = parsed.errors
                && !errs.is_empty()
            {
                return Err(FetchError::GraphQL(
                    errs.into_iter().map(|e| e.message).collect(),
                ));
            }

            let Some(data) = parsed.data else {
                return Err(FetchError::GraphQL(vec!["no data field".into()]));
            };
            let Some(user) = data.user else {
                return Err(FetchError::GraphQL(vec![format!("user {login} not found")]));
            };

            for repo in user.repositories.nodes {
                repo_count += 1;
                for edge in repo.languages.edges {
                    let entry = totals
                        .entry(edge.node.name)
                        .or_insert((0, edge.node.color.clone()));
                    entry.0 += edge.size;
                    if entry.1.is_none() {
                        entry.1 = edge.node.color;
                    }
                }
            }

            if !user.repositories.page_info.has_next_page {
                break;
            }
            after = user.repositories.page_info.end_cursor;
            if after.is_none() {
                break;
            }
        }

        let languages: Vec<LanguageStat> = totals
            .into_iter()
            .map(|(name, (bytes, colour))| LanguageStat {
                name,
                bytes,
                fraction: 0.0,
                colour,
            })
            .collect();

        Ok(Stats::new(
            Target::User(login.to_string()),
            Utc::now(),
            repo_count,
            languages,
        ))
    }
}

fn parse_rate_limit(resp: &reqwest::Response) -> Option<(u32, DateTime<Utc>)> {
    let headers = resp.headers();
    let remaining: u32 = headers
        .get("x-ratelimit-remaining")?
        .to_str()
        .ok()?
        .parse()
        .ok()?;
    let reset_epoch: i64 = headers
        .get("x-ratelimit-reset")?
        .to_str()
        .ok()?
        .parse()
        .ok()?;
    let reset_at = Utc.timestamp_opt(reset_epoch, 0).single()?;
    Some((remaining, reset_at))
}

#[cfg(test)]
mod tests {
    use serde_json::json;
    use wiremock::Mock;
    use wiremock::MockServer;
    use wiremock::ResponseTemplate;
    use wiremock::matchers::method;
    use wiremock::matchers::path;

    use super::*;

    fn single_page_response() -> serde_json::Value {
        json!({
            "data": {
                "user": {
                    "repositories": {
                        "pageInfo": { "hasNextPage": false, "endCursor": null },
                        "nodes": [
                            {
                                "nameWithOwner": "u/r1",
                                "languages": {
                                    "edges": [
                                        { "size": 700, "node": { "name": "Rust",   "color": "#dea584" } },
                                        { "size": 300, "node": { "name": "Python", "color": "#3572A5" } }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        })
    }

    #[tokio::test]
    async fn fetch_user_single_page_aggregates() {
        let server = MockServer::start().await;
        Mock::given(method("POST"))
            .and(path("/"))
            .respond_with(ResponseTemplate::new(200).set_body_json(single_page_response()))
            .mount(&server)
            .await;

        let client = Client::with_endpoint(server.uri(), "tok").unwrap();
        let stats = client.fetch_user("u").await.unwrap();

        assert_eq!(stats.total_bytes, 1000);
        assert_eq!(stats.repo_count, 1);
        assert_eq!(stats.languages.len(), 2);
        assert_eq!(stats.languages[0].name, "Rust");
        assert_eq!(stats.languages[0].bytes, 700);
        assert_eq!(stats.languages[1].name, "Python");
    }
}
