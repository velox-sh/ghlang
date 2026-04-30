use std::collections::HashMap;
use std::hash::BuildHasher;

use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum TemplateError {
    #[error("missing template key: {0}")]
    MissingKey(String),
}

/// Replace `{{ key }}` markers in `template` with values from `vars`.
/// Values are XML-escaped except for keys ending in `_raw`, which are inserted verbatim.
pub fn fill<S: BuildHasher>(
    template: &str,
    vars: &HashMap<&str, String, S>,
) -> Result<String, TemplateError> {
    let bytes = template.as_bytes();
    let mut out = String::with_capacity(template.len());
    let mut i = 0;

    while i < bytes.len() {
        if i + 1 < bytes.len() && bytes[i] == b'{' && bytes[i + 1] == b'{' {
            // Look for the closing `}}` after the opening pair. We search the
            // tail directly so that any `{{`/`}}` inside the key region is
            // treated as plain bytes (the scanner is non-recursive on purpose).
            if let Some(rel_close) = find_close(&bytes[i + 2..]) {
                let raw_key = &template[i + 2..i + 2 + rel_close];
                let key = raw_key.trim();
                let value = vars
                    .get(key)
                    .ok_or_else(|| TemplateError::MissingKey(key.to_string()))?;
                if key.ends_with("_raw") {
                    out.push_str(value);
                } else {
                    push_escaped(&mut out, value);
                }
                i += 2 + rel_close + 2;
                continue;
            }
        }
        out.push(bytes[i] as char);
        i += 1;
    }

    Ok(out)
}

fn find_close(haystack: &[u8]) -> Option<usize> {
    let mut j = 0;
    while j + 1 < haystack.len() {
        if haystack[j] == b'}' && haystack[j + 1] == b'}' {
            return Some(j);
        }
        j += 1;
    }
    None
}

fn push_escaped(out: &mut String, value: &str) {
    for ch in value.chars() {
        match ch {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            '"' => out.push_str("&quot;"),
            '\'' => out.push_str("&apos;"),
            _ => out.push(ch),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn vars(pairs: &[(&'static str, &str)]) -> HashMap<&'static str, String> {
        pairs.iter().map(|(k, v)| (*k, (*v).to_string())).collect()
    }

    #[test]
    fn substitutes_a_single_marker() {
        let v = vars(&[("a", "hello")]);
        assert_eq!(fill("{{ a }}", &v).unwrap(), "hello");
    }

    #[test]
    fn whitespace_tolerant() {
        let v = vars(&[("a", "x")]);
        assert_eq!(fill("{{a}}", &v).unwrap(), "x");
        assert_eq!(fill("{{   a   }}", &v).unwrap(), "x");
    }

    #[test]
    fn escapes_all_five_xml_specials() {
        let v = vars(&[("a", "<&>\"'")]);
        assert_eq!(fill("{{ a }}", &v).unwrap(), "&lt;&amp;&gt;&quot;&apos;");
    }

    #[test]
    fn raw_suffix_skips_escaping() {
        let v = vars(&[("html_raw", "<rect x=\"0\"/>")]);
        assert_eq!(fill("{{ html_raw }}", &v).unwrap(), "<rect x=\"0\"/>");
    }

    #[test]
    fn missing_key_returns_error() {
        let v = vars(&[]);
        let err = fill("{{ ghost }}", &v).unwrap_err();
        assert_eq!(err, TemplateError::MissingKey("ghost".into()));
    }

    #[test]
    fn nested_braces_do_not_break_scanner() {
        // Outer `{{ {{ x }}` parses as a key whose name happens to contain
        // an extra `{{`; that key is missing, so we get a clear error.
        let v = vars(&[("x", "X")]);
        let err = fill("{{ {{ x }} }}", &v).unwrap_err();
        match err {
            TemplateError::MissingKey(name) => assert_eq!(name, "{{ x"),
        }
    }

    #[test]
    fn zero_markers_pass_through() {
        let v = vars(&[]);
        let s = "<svg>plain text & no markers</svg>";
        assert_eq!(fill(s, &v).unwrap(), s);
    }

    #[test]
    fn multiple_markers_in_one_template() {
        let v = vars(&[("title", "Hi"), ("body_raw", "<rect/>")]);
        let out = fill("<h>{{ title }}</h><b>{{ body_raw }}</b>", &v).unwrap();
        assert_eq!(out, "<h>Hi</h><b><rect/></b>");
    }
}
