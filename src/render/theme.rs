use std::collections::HashMap;
use std::fs;
use std::io;
use std::path::Path;

use thiserror::Error;

#[derive(Debug, Error)]
pub enum ThemeError {
    #[error("io error: {0}")]
    Io(#[from] io::Error),
    #[error("parse error: {0}")]
    Parse(#[from] toml::de::Error),
    #[error("theme not found: {0}")]
    NotFound(String),
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct Theme {
    pub name: String,
    pub description: String,
    pub colors: Colors,
    pub fonts: Fonts,
    #[serde(default)]
    pub language_colors: HashMap<String, String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct Colors {
    pub background: String,
    pub text: String,
    pub muted: String,
    pub fallback: String,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct Fonts {
    pub family: String,
    pub size: u32,
}

impl Theme {
    /// Load a theme by builtin name (`default`, `dark`, `monokai`) or by filesystem path.
    pub fn load(name_or_path: &str) -> Result<Self, ThemeError> {
        if let Some(builtin) = builtin(name_or_path) {
            return parse_toml(builtin);
        }

        let path = Path::new(name_or_path);
        if path.exists() {
            let text = fs::read_to_string(path)?;
            return parse_toml(&text);
        }

        Err(ThemeError::NotFound(name_or_path.to_string()))
    }
}

fn parse_toml(text: &str) -> Result<Theme, ThemeError> {
    toml::from_str(text).map_err(ThemeError::Parse)
}

fn builtin(name: &str) -> Option<&'static str> {
    match name {
        "default" => Some(DEFAULT_TOML),
        "dark" => Some(DARK_TOML),
        "monokai" => Some(MONOKAI_TOML),
        _ => None,
    }
}

const DEFAULT_TOML: &str = include_str!("../../themes/default.toml");
const DARK_TOML: &str = include_str!("../../themes/dark.toml");
const MONOKAI_TOML: &str = include_str!("../../themes/monokai.toml");
const LINGUIST_COLORS_TOML: &str = include_str!("../static/languages.toml");

impl Theme {
    /// Resolve the colour for a language name.
    /// Theme override wins, then the builtin linguist map, then `colors.fallback`.
    #[must_use]
    pub fn language_colour(&self, name: &str) -> &str {
        if let Some(c) = self.language_colors.get(name) {
            return c;
        }
        if let Some(c) = LINGUIST_COLOURS.get(name) {
            return c;
        }
        &self.colors.fallback
    }
}

static LINGUIST_COLOURS: std::sync::LazyLock<HashMap<String, String>> =
    std::sync::LazyLock::new(|| {
        toml::from_str::<HashMap<String, String>>(LINGUIST_COLORS_TOML).unwrap_or_default()
    });

#[cfg(test)]
mod tests {
    use std::io::Write;

    use tempfile::NamedTempFile;

    use super::*;

    #[test]
    fn loads_default_builtin() {
        let theme = Theme::load("default").unwrap();
        assert_eq!(theme.name, "default");
        assert_eq!(theme.colors.background, "#ffffff");
    }

    #[test]
    fn loads_dark_builtin() {
        let theme = Theme::load("dark").unwrap();
        assert_eq!(theme.name, "dark");
    }

    #[test]
    fn loads_monokai_builtin() {
        let theme = Theme::load("monokai").unwrap();
        assert_eq!(theme.name, "monokai");
    }

    #[test]
    fn loads_from_path() {
        let mut f = NamedTempFile::new().unwrap();
        writeln!(
            f,
            r##"
name = "custom"
description = "test"
[colors]
background = "#000"
text = "#fff"
muted = "#888"
fallback = "#444"
[fonts]
family = "monospace"
size = 12
"##,
        )
        .unwrap();

        let theme = Theme::load(f.path().to_str().unwrap()).unwrap();
        assert_eq!(theme.name, "custom");
    }

    #[test]
    fn invalid_toml_returns_parse_error() {
        let mut f = NamedTempFile::new().unwrap();
        writeln!(f, "not a toml file at all !!! [invalid").unwrap();

        let err = Theme::load(f.path().to_str().unwrap()).unwrap_err();
        assert!(matches!(err, ThemeError::Parse(_)), "got {err:?}");
    }

    #[test]
    fn unknown_name_returns_not_found() {
        let err = Theme::load("nonexistent-theme-xyz").unwrap_err();
        assert!(matches!(err, ThemeError::NotFound(_)), "got {err:?}");
    }

    #[test]
    fn theme_override_wins_over_linguist() {
        let mut theme = Theme::load("default").unwrap();
        theme
            .language_colors
            .insert("Rust".into(), "#000000".into());
        assert_eq!(theme.language_colour("Rust"), "#000000");
    }

    #[test]
    fn linguist_used_when_no_override() {
        let theme = Theme::load("default").unwrap();
        assert_eq!(theme.language_colour("Rust"), "#dea584");
    }

    #[test]
    fn unknown_language_falls_back() {
        let theme = Theme::load("default").unwrap();
        assert_eq!(theme.language_colour("Made-Up"), &theme.colors.fallback);
    }
}
