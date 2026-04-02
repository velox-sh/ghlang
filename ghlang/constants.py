from datetime import timedelta
from typing import Final


# config defaults
DEFAULT_IGNORED_DIRS: list[str] = [
    "node_modules",
    "vendor",
    ".git",
    "dist",
    "build",
    "__pycache__",
]
DEFAULT_OUTPUT_DIR: Final = "~/Documents/ghlang-stats"

# GitHub API
API_URL: Final = "https://api.github.com"
API_VERSION: Final = "2022-11-28"
API_PER_PAGE: Final = 100
API_MAX_RETRIES: Final = 5
API_BASE_DELAY: Final = 1
API_MAX_WORKERS: Final = 10
REQUEST_TIMEOUT: Final = 10

# remote URLs
LINGUIST_URL: Final = (
    "https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml"
)
MANIFEST_URL: Final = (
    "https://raw.githubusercontent.com/velox-sh/ghlang/master/themes/manifest.json"
)

# themes
THEME_CACHE_TTL: Final = timedelta(days=1)
