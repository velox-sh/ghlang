use std::env;
use std::fs;
use std::io;
use std::path::PathBuf;
use std::time::Duration as StdDuration;

use chrono::DateTime;
use chrono::Duration;
use chrono::Utc;
use thiserror::Error;

use crate::fetch::types::SCHEMA_VERSION;
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

    /// Read stats for `key`. Returns `Ok(None)` when:
    /// - the file is missing
    /// - the JSON is corrupted
    /// - the `schema_version` differs from the current build
    /// - the entry is older than `ttl_hours`
    pub fn read(&self, key: &str, ttl_hours: u32) -> Result<Option<Stats>, CacheError> {
        let path = self.user_path(key);
        let bytes = match fs::read(&path) {
            Ok(b) => b,
            Err(e) if e.kind() == io::ErrorKind::NotFound => return Ok(None),
            Err(e) => return Err(e.into()),
        };

        let stats: Stats = match serde_json::from_slice(&bytes) {
            Ok(s) => s,
            Err(_) => return Ok(None),
        };

        if stats.schema_version != SCHEMA_VERSION {
            return Ok(None);
        }
        if is_expired(stats.fetched_at, ttl_hours) {
            return Ok(None);
        }

        Ok(Some(stats))
    }

    /// Remove cache entries older than `older_than`. Corrupted JSON is also removed.
    /// A missing users/ directory is not an error - returns 0.
    pub fn prune(&self, older_than: StdDuration) -> Result<u32, CacheError> {
        let users_dir = self.root.join("users");
        let entries = match fs::read_dir(&users_dir) {
            Ok(e) => e,
            Err(e) if e.kind() == io::ErrorKind::NotFound => return Ok(0),
            Err(e) => return Err(e.into()),
        };

        let cutoff = Utc::now() - Duration::from_std(older_than).unwrap_or_default();
        let mut removed = 0u32;

        for entry in entries {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }

            let Ok(bytes) = fs::read(&path) else {
                continue;
            };

            let stale = match serde_json::from_slice::<Stats>(&bytes) {
                Ok(stats) => stats.fetched_at < cutoff,
                Err(_) => true,
            };
            if stale {
                fs::remove_file(&path)?;
                removed += 1;
            }
        }

        Ok(removed)
    }
}

fn is_expired(fetched_at: DateTime<Utc>, ttl_hours: u32) -> bool {
    let ttl = Duration::hours(i64::from(ttl_hours));
    Utc::now() - fetched_at > ttl
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

    #[test]
    fn read_missing_returns_none() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        assert!(cache.read("nobody", 24).unwrap().is_none());
    }

    #[test]
    fn write_then_read_roundtrip() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        let stats = sample_stats();

        cache.write("u", &stats).unwrap();
        let back = cache.read("u", 24).unwrap().expect("hit");
        assert_eq!(stats, back);
    }

    #[test]
    fn read_expired_returns_none() {
        use chrono::TimeZone;

        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        let mut stats = sample_stats();
        stats.fetched_at = Utc.with_ymd_and_hms(2020, 1, 1, 0, 0, 0).unwrap();

        cache.write("u", &stats).unwrap();
        assert!(cache.read("u", 24).unwrap().is_none());
    }

    #[test]
    fn read_schema_mismatch_returns_none() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        let mut stats = sample_stats();
        stats.schema_version = SCHEMA_VERSION + 99;

        cache.write("u", &stats).unwrap();
        assert!(cache.read("u", 24).unwrap().is_none());
    }

    #[test]
    fn read_corrupted_json_returns_none() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        let users = dir.path().join("users");
        fs::create_dir_all(&users).unwrap();
        fs::write(users.join("bad.json"), b"not json").unwrap();

        assert!(cache.read("bad", 24).unwrap().is_none());
    }

    #[test]
    fn prune_removes_stale_keeps_fresh() {
        use chrono::TimeZone;

        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());

        let fresh = sample_stats();
        cache.write("fresh", &fresh).unwrap();

        let mut stale = sample_stats();
        stale.fetched_at = Utc.with_ymd_and_hms(2020, 1, 1, 0, 0, 0).unwrap();
        cache.write("stale", &stale).unwrap();

        let removed = cache
            .prune(StdDuration::from_secs(60 * 60 * 24 * 30))
            .unwrap();
        assert_eq!(removed, 1);

        assert!(cache.read("fresh", 9999).unwrap().is_some());
        assert!(!dir.path().join("users").join("stale.json").exists());
    }

    #[test]
    fn prune_on_missing_dir_returns_zero() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().join("does-not-exist"));
        assert_eq!(cache.prune(StdDuration::from_secs(60)).unwrap(), 0);
    }

    #[test]
    fn prune_removes_corrupted_json() {
        let dir = tempdir().unwrap();
        let cache = Cache::new(dir.path().to_path_buf());
        let users = dir.path().join("users");
        fs::create_dir_all(&users).unwrap();
        fs::write(users.join("bad.json"), b"not json").unwrap();

        let removed = cache.prune(StdDuration::from_secs(60)).unwrap();
        assert_eq!(removed, 1);
        assert!(!users.join("bad.json").exists());
    }
}
