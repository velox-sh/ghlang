use chrono::DateTime;
use chrono::Utc;
use serde::Deserialize;
use serde::Serialize;

pub const SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "scope", content = "value")]
pub enum Target {
    User(String),
    Repo { owner: String, name: String },
    Org(String),
    Multi(Vec<(String, String)>),
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LanguageStat {
    pub name: String,
    pub bytes: u64,
    pub fraction: f32,
    pub colour: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Stats {
    pub schema_version: u32,
    pub target: Target,
    pub fetched_at: DateTime<Utc>,
    pub total_bytes: u64,
    pub languages: Vec<LanguageStat>,
    pub repo_count: u32,
}

impl Stats {
    /// Build a `Stats` and enforce invariants:
    /// - languages sorted by bytes desc, fractions
    /// - recomputed from `total_bytes`.
    #[must_use]
    pub fn new(
        target: Target,
        fetched_at: DateTime<Utc>,
        repo_count: u32,
        mut languages: Vec<LanguageStat>,
    ) -> Self {
        let total_bytes: u64 = languages.iter().map(|l| l.bytes).sum();
        languages.sort_by(|a, b| b.bytes.cmp(&a.bytes).then_with(|| a.name.cmp(&b.name)));

        #[allow(clippy::cast_precision_loss)]
        if total_bytes > 0 {
            let total = total_bytes as f64;
            for lang in &mut languages {
                lang.fraction = (lang.bytes as f64 / total) as f32;
            }
        } else {
            for lang in &mut languages {
                lang.fraction = 0.0;
            }
        }

        Self {
            schema_version: SCHEMA_VERSION,
            target,
            fetched_at,
            total_bytes,
            languages,
            repo_count,
        }
    }
}

#[cfg(test)]
mod tests {
    use chrono::TimeZone;
    use proptest::prelude::*;

    use super::*;

    fn sample_stats() -> Stats {
        Stats::new(
            Target::User("torvalds".into()),
            Utc.with_ymd_and_hms(2026, 4, 29, 12, 0, 0).unwrap(),
            3,
            vec![
                LanguageStat {
                    name: "C".into(),
                    bytes: 700,
                    fraction: 0.0,
                    colour: Some("#555555".into()),
                },
                LanguageStat {
                    name: "Rust".into(),
                    bytes: 200,
                    fraction: 0.0,
                    colour: Some("#dea584".into()),
                },
                LanguageStat {
                    name: "Python".into(),
                    bytes: 100,
                    fraction: 0.0,
                    colour: Some("#3572A5".into()),
                },
            ],
        )
    }

    #[test]
    fn json_round_trip_byte_equal() {
        let stats = sample_stats();
        let json = serde_json::to_string(&stats).expect("serialise");
        let back: Stats = serde_json::from_str(&json).expect("deserialise");
        assert_eq!(stats, back);
    }

    #[test]
    fn languages_sorted_desc_by_bytes() {
        let stats = sample_stats();
        let bytes: Vec<u64> = stats.languages.iter().map(|l| l.bytes).collect();
        let mut sorted = bytes.clone();
        sorted.sort_unstable_by(|a, b| b.cmp(a));
        assert_eq!(bytes, sorted);
        assert_eq!(stats.languages[0].name, "C");
    }

    #[test]
    fn fractions_sum_to_one() {
        let stats = sample_stats();
        let sum: f32 = stats.languages.iter().map(|l| l.fraction).sum();
        assert!((sum - 1.0).abs() < 1e-5, "fractions sum to {sum}");
    }

    #[test]
    fn empty_stats_does_not_panic() {
        let stats = Stats::new(Target::User("ghost".into()), Utc::now(), 0, Vec::new());
        assert_eq!(stats.total_bytes, 0);
        assert!(stats.languages.is_empty());
        let _ = serde_json::to_string(&stats).expect("serialise empty");
    }

    #[test]
    fn target_variants_round_trip() {
        for t in [
            Target::User("a".into()),
            Target::Repo {
                owner: "o".into(),
                name: "r".into(),
            },
            Target::Org("o".into()),
            Target::Multi(vec![("o".into(), "r".into())]),
        ] {
            let json = serde_json::to_string(&t).unwrap();
            let back: Target = serde_json::from_str(&json).unwrap();
            assert_eq!(t, back);
        }
    }

    fn arb_lang() -> impl Strategy<Value = LanguageStat> {
        ("[A-Za-z][A-Za-z0-9 _-]{0,15}", 0u64..1_000_000u64).prop_map(|(name, bytes)| {
            LanguageStat {
                name,
                bytes,
                fraction: 0.0,
                colour: None,
            }
        })
    }

    proptest! {
        #![proptest_config(ProptestConfig { cases: 64, ..ProptestConfig::default() })]

        #[test]
        fn prop_json_round_trip(langs in prop::collection::vec(arb_lang(), 0..20)) {
            let stats = Stats::new(
                Target::User("u".into()),
                Utc.with_ymd_and_hms(2026, 1, 1, 0, 0, 0).unwrap(),
                1,
                langs,
            );
            let json = serde_json::to_string(&stats).unwrap();
            let back: Stats = serde_json::from_str(&json).unwrap();
            prop_assert_eq!(stats, back);
        }

        #[test]
        #[allow(clippy::float_cmp)]
        fn prop_fractions_sum_or_zero(langs in prop::collection::vec(arb_lang(), 0..20)) {
            let stats = Stats::new(
                Target::User("u".into()),
                Utc.with_ymd_and_hms(2026, 1, 1, 0, 0, 0).unwrap(),
                1,
                langs,
            );
            let sum: f32 = stats.languages.iter().map(|l| l.fraction).sum();
            if stats.total_bytes == 0 {
                prop_assert!(sum == 0.0, "sum {sum} should be 0 when total_bytes is 0");
            } else {
                prop_assert!((sum - 1.0).abs() < 1e-3, "sum {} not near 1.0", sum);
            }
        }

        #[test]
        fn prop_languages_sorted_desc(langs in prop::collection::vec(arb_lang(), 0..20)) {
            let stats = Stats::new(
                Target::User("u".into()),
                Utc.with_ymd_and_hms(2026, 1, 1, 0, 0, 0).unwrap(),
                1,
                langs,
            );
            for window in stats.languages.windows(2) {
                prop_assert!(window[0].bytes >= window[1].bytes);
            }
        }

        #[test]
        fn prop_no_panic_extreme_sizes(n in 0usize..100) {
            let langs: Vec<LanguageStat> = (0..n)
                .map(|i| LanguageStat {
                    name: format!("L{i}"),
                    bytes: u64::from(i as u32) * 1_000_000,
                    fraction: 0.0,
                    colour: None,
                })
                .collect();
            let stats = Stats::new(
                Target::User("u".into()),
                Utc.with_ymd_and_hms(2026, 1, 1, 0, 0, 0).unwrap(),
                1,
                langs,
            );
            let _ = serde_json::to_string(&stats).unwrap();
        }
    }
}
