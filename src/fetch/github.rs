// fields and shapes are wired up in the fetch_user impl in the next commit
#![allow(dead_code)]

use chrono::DateTime;
use chrono::Utc;
use serde::Deserialize;
use serde::Serialize;
use thiserror::Error;

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
}
