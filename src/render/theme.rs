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
