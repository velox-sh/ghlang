// fields are wired up in the fetch_user impl in the next commit
#![allow(dead_code)]

use chrono::DateTime;
use chrono::Utc;
use thiserror::Error;

const GITHUB_GRAPHQL: &str = "https://api.github.com/graphql";

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
