use std::env;
use std::path::PathBuf;

use thiserror::Error;

#[derive(Debug, Error)]
pub enum CacheError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
}

#[derive(Debug, Clone)]
pub struct Cache {
    root: PathBuf,
}

impl Cache {
    #[must_use]
    pub fn new(root: PathBuf) -> Self {
        Self { root }
    }

    #[must_use]
    pub fn root(&self) -> &PathBuf {
        &self.root
    }
}

/// Resolve the default cache root.
/// `$XDG_CACHE_HOME/ghlang` if the env var is set and non-empty,
/// else `dirs::cache_dir()/ghlang`,
/// else `.ghlang-cache` in the current directory as a last-resort fallback.
#[must_use]
pub fn default_cache_root() -> PathBuf {
    if let Ok(xdg) = env::var("XDG_CACHE_HOME")
        && !xdg.is_empty()
    {
        return PathBuf::from(xdg).join("ghlang");
    }

    if let Some(cache) = dirs::cache_dir() {
        return cache.join("ghlang");
    }

    PathBuf::from(".ghlang-cache")
}

#[cfg(test)]
#[allow(
    unsafe_code,
    reason = "env::set_var is unsafe in 2024 edition; only tests touch env"
)]
mod tests {
    use super::*;

    #[test]
    fn default_root_respects_xdg_env() {
        // SAFETY: single-threaded test, env mutation scoped to this case
        unsafe {
            env::set_var("XDG_CACHE_HOME", "/tmp/xdg-ghlang-test");
        }

        let root = default_cache_root();
        unsafe {
            env::remove_var("XDG_CACHE_HOME");
        }

        assert_eq!(root, PathBuf::from("/tmp/xdg-ghlang-test/ghlang"));
    }
}
