"""Tokount-to-linguist language mapping and normalization."""

# explicit mapping table
# - string value: map tokount name to linguist name
# - None: no linguist equivalent, force theme fallback color
TOKOUNT_TO_LINGUIST: dict[str, str | None] = {
    ".NET Resource": None,
    "8th": None,
    # "Alex": None,
    "Apache Velocity": None,
    "Arduino C++": None,
    # "Ark TypeScript": "ArkTS",
    "Arturo": None,
    # "ASP": "Classic ASP",
    "Autoconf": None,
    "AutoHotKey": "AutoHotkey",
    # "Autoit": "AutoIt",
    # "Automake": None,
    "AWK": "Awk",
    # "AXAML": None,
    # B
    "Bash": "Shell",
    # "Batch": "Batchfile",
    "Bazel": None,
    "Bean": None,
    "Bitbake": "BitBake",
    "BrightScript": "Brightscript",
    # C
    "C Header": "C",
    "C Shell": "Tcsh",
    "C++ Header": "C++",
    "C++ Module": None,
    # "Cabal": None,
    # "Cassius": None,
    "CIL (SELinux)": None,
    "ClojureC": "Clojure",
    "ClojureScript": "Clojure",
    "Cogent": None,
    # "ColdFusion CFScript": "ColdFusion CFC",
    # "Coq": "Rocq Prover",
    # D
    "DAML": None,
    # "Device Tree": None,
    "Dream Maker": None,
    "Dust.js": None,
    # E
    "Ebuild": None,
    "EdgeDB Schema Definition": None,
    "Edn": None,
    "Emacs Dev Env": None,
    "Emojicode": None,
    # F
    # "FEN": None,
    "Fish": "fish",
    "FlatBuffers Schema": None,
    "Forge Config": None,
    # "FORTRAN Legacy": "Fortran",
    # "FORTRAN Modern": "Fortran",
    # G
    "GDB Script": None,
    "Gherkin (Cucumber)": None,
    "Gml": None,  # huh
    "GNU Style Assembly": "Unix Assembly",
    "Go HTML": "HTML",
    "Gwion": None,
    # H
    "HAML": "Haml",
    # "Happy": None,
    "Headache": None,
    "Hex0": None,
    "Hex1": None,
    "Hex2": None,
    "HICAD": None,
    "hledger": None,
    # I
    # "Intel HEX": None,
    # J
    # "JAI": "Jai",
    "Jinja2": "Jinja",
    "JSLT": None,
    "JSX": "JavaScript",
    # "Julius": None,
    "Jupyter Notebooks": "Jupyter Notebook",
    # K
    "K": None,
    "Kaem": None,
    "Korn Shell": "Shell",
    "KV Language": None,
    # L
    "LALRPOP": None,
    # "Lauterbach PRACTICE Script": None,
    # "LD Script": "Linker Script",
    "LESS": "Less",
    "Lingua Franca": None,
    # "Lucius": None,
    # M
    "M1 Assembly": "Unix Assembly",
    # "Madlang": None,
    "Menhir": None,
    "Metal Shading Language": None,
    "Mlatu": None,
    "Module-Definition": None,
    "MSBuild": "XML",
    # N
    "Not Quite Perl": None,
    "NuGet Config": None,
    # P
    "Pacman's makepkg": None,
    "Pest": None,
    "Phix": None,
    "Plain Text": "Text",
    "PO File": None,
    "Poke": None,
    # "Polly": None,
    "Protocol Buffers": "Protocol Buffer",
    # "PRQL": None,
    # "PSL Assertion": None,
    # Q
    "Q": "q",
    # "QCL": None,
    # R
    "Rakefile": None,
    "Razor": "HTML+Razor",
    "Redscript": None,
    "ReStructuredText": "reStructuredText",
    "RPM Specfile": None,
    "Ruby HTML": "HTML+ERB",
    "Rusty Object Notation": "RON",
    # S
    "Scons": None,
    # "SIL": None,
    "Specman e": "E",
    # "Spice Netlist": None,
    "Standard ML (SML)": "Standard ML",
    "Stratego/XT": None,
    # T
    "TCL": "Tcl",
    "Templ": "templ",
    "Tera": "Terra",
    "The WenYan Programming Language": None,
    "TTCN-3": None,
    # U
    "Uiua": None,
    "UMPL": None,
    "Unison": None,
    "Unreal Markdown": "Markdown",
    "Unreal Plugin": None,
    "Unreal Project": None,
    "Unreal Script": "UnrealScript",
    "Unreal Shader": None,
    "Unreal Shader Header": None,
    "Ur/Web": "UrWeb",
    "Ur/Web Project": "UrWeb",
    # V
    "VB6/VBA": "VBA",
    "Verilog Args File": None,
    "Virgil": None,
    "Visual Basic": "Visual Basic .NET",
    "Visual Studio Project": "Microsoft Developer Studio Project",
    "Visual Studio Solution": "Microsoft Visual Studio Solution",
    "WebGPU Shader Language": None,
    "Wolfram": "Wolfram Language",
    # X
    "XAML": "XML",
    "Xcode Config": None,
    "XSL": None,
    # Z
    "ZenCode": None,
    "ZoKrates": None,
    "Zsh": "Shell",
}


def _normalize_language(lang: str) -> str:
    if lang in TOKOUNT_TO_LINGUIST:
        mapped = TOKOUNT_TO_LINGUIST[lang]
        return mapped if mapped is not None else lang
    return lang


def normalize_language_stats(stats: dict[str, int]) -> dict[str, int]:
    """Normalize language names and merge duplicates.

    Map tokount language names to their GitHub Linguist equivalents and
    sum counts for names that collapse into the same canonical form.

    Parameters
    ----------
    stats : dict[str, int]
        Raw language name to count mapping.

    Returns
    -------
    dict[str, int]
        Normalized language name to merged count.
    """
    normalized: dict[str, int] = {}
    for lang, count in stats.items():
        norm_lang = _normalize_language(lang)
        normalized[norm_lang] = normalized.get(norm_lang, 0) + count
    return normalized
