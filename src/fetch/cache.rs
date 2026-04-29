use std::env;
use std::fs;
use std::path::PathBuf;

use thiserror::Error;

use crate::fetch::types::Stats;

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

    fn user_path(&self, key: &str) -> PathBuf {
        self.root.join("users").join(format!("{key}.json"))
    }

    /// Write stats for `key` as pretty JSON. Creates parent directories as needed.
    pub fn write(&self, key: &str, stats: &Stats) -> Result<(), CacheError> {
        let path = self.user_path(key);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        let json = serde_json::to_vec_pretty(stats)?;
        fs::write(path, json)?;
        Ok(())
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
    use chrono::Utc;
    use tempfile::tempdir;

    use super::*;
    use crate::fetch::types::LanguageStat;
    use crate::fetch::types::Target;

    fn sample_stats() -> Stats {
        Stats::new(
            Target::User("u".into()),
            Utc::now(),
            1,
            vec![LanguageStat {
                name: "Rust".into(),
                bytes: 100,
                fraction: 0.0,
                colour: None,
            }],
        )
    }

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

    #[test]
    fn write_creates_users_dir_and_pretty_json() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        let stats = sample_stats();

        cache.write("torvalds", &stats).unwrap();

        let path = dir.path().join("users").join("torvalds.json");
        assert!(path.exists());
        let bytes = fs::read(&path).unwrap();
        let back: Stats = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(stats, back);
    }
}
