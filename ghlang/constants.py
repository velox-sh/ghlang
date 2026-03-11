from datetime import timedelta


# config defaults
DEFAULT_IGNORED_DIRS: list[str] = [
    "node_modules",
    "vendor",
    ".git",
    "dist",
    "build",
    "__pycache__",
]
DEFAULT_OUTPUT_DIR = "~/Documents/ghlang-stats"

# GitHub API
API_BASE_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
API_PER_PAGE = 100
API_MAX_RETRIES = 5
API_BASE_DELAY = 1.0
API_MAX_WORKERS = 10
REQUEST_TIMEOUT = 10

# remote URLs
LINGUIST_LANGUAGES_URL = (
    "https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml"
)
THEME_MANIFEST_URL = (
    "https://raw.githubusercontent.com/MihaiStreames/ghlang/master/themes/manifest.json"
)

# themes
THEME_CACHE_TTL = timedelta(days=1)

# visualizer - general
ROUNDED_CORNER_RADIUS = 40
PNG_DPI = 200

# visualizer - pie chart
PIE_FIGSIZE: tuple[int, int] = (14, 10)
PIE_TITLE_FONTSIZE = 24
PIE_TITLE_PAD = 20
PIE_MIN_PERCENTAGE = 1.5
PIE_PCT_FONTSIZE = 9
PIE_LEGEND_FONTSIZE = 9
PIE_LEGEND_TITLE_FONTSIZE = 11

# visualizer - bar chart
BAR_FIGSIZE: tuple[int, int] = (12, 3)
BAR_HEIGHT = 0.5
BAR_TITLE_FONTSIZE = 20
BAR_TITLE_PAD = 10
BAR_MIN_LABEL_WIDTH = 0.05
BAR_LABEL_FONTSIZE = 11
BAR_LEGEND_FONTSIZE = 10
BAR_LEGEND_NCOL = 3
