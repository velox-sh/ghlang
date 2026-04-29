import fnmatch
import re

from ghlang import constants
from ghlang import exceptions
from ghlang import log

from . import client


class GitHubClient:
    """Client for interacting with the GitHub REST API.

    Attributes
    ----------
    _session : client.Session
        Authenticated HTTP session with connection reuse.
    _affiliation : str
        Repo affiliation filter.
    _visibility : str
        Repo visibility filter.
    _ignored_repos : list[str]
        Glob patterns for repos to skip.
    """

    def __init__(
        self,
        token: str,
        affiliation: str,
        visibility: str,
        ignored_repos: list[str],
    ) -> None:
        self._api = constants.API_URL
        self._session = client.Session()
        self._session.update_headers(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": constants.API_VERSION,
            }
        )
        self._affiliation = affiliation
        self._visibility = visibility
        self._ignored_repos = ignored_repos
        self._per_page = constants.API_PER_PAGE

    def _normalize_repo_pattern(self, pattern: str) -> str:
        prefixes = ["https://github.com/", "http://github.com/", "github.com/"]

        for prefix in prefixes:
            if pattern.startswith(prefix):
                return pattern[len(prefix) :].rstrip("/")

        return pattern

    def _validate_repo_name(self, repo_name: str) -> bool:
        pattern = r"^[\w\-\.]+/[\w\-\.]+$"
        return bool(re.match(pattern, repo_name)) and len(repo_name) <= 100

    def _should_ignore_repo(self, full_name: str) -> bool:
        for pattern in self._ignored_repos:
            normalized = self._normalize_repo_pattern(pattern)

            if fnmatch.fnmatch(full_name, normalized):
                return True
            if fnmatch.fnmatch(full_name.lower(), normalized.lower()):
                return True

        return False

    def get_repo_info(self, full_name: str) -> dict[str, object]:
        """Fetch metadata for a single repo.

        Parameters
        ----------
        full_name : str
            Repository in ``owner/repo`` format.

        Returns
        -------
        dict
            Repository metadata from the GitHub API.

        Raises
        ------
        ValueError
            If the repo name format is invalid.
        """
        if not self._validate_repo_name(full_name):
            raise ValueError(f"Invalid repository name format: {full_name}")
        r = self._session.get(f"{self._api}/repos/{full_name}")
        return dict(r.json())

    def list_repos(self) -> list[dict[str, object]]:
        """Paginate all repos matching affiliation/visibility filters.

        Returns
        -------
        list[dict]
            Deduplicated, filtered repo dicts.
        """
        repos = []
        page = 1

        while True:
            r = self._session.get(
                f"{self._api}/user/repos",
                params={
                    "per_page": self._per_page,
                    "page": page,
                    "affiliation": self._affiliation,
                    "visibility": self._visibility,
                    "sort": "pushed",
                    "direction": "desc",
                },
            )

            batch = r.json()
            if not batch:
                break

            repos.extend(batch)
            page += 1

        seen = set()
        unique_repos = []

        for repo in repos:
            full_name = repo["full_name"]

            if full_name in seen:
                continue

            seen.add(full_name)

            if self._should_ignore_repo(full_name):
                log.logger.debug(f"Ignoring repo: {full_name}")
                continue

            unique_repos.append(repo)

        return unique_repos

    def get_repo_languages(self, full_name: str) -> dict[str, int]:
        """Fetch byte-count language breakdown for a single repo.

        Parameters
        ----------
        full_name : str
            Repository in ``owner/repo`` format.

        Returns
        -------
        dict[str, int]
            Language name to byte count mapping.
        """
        r = self._session.get(f"{self._api}/repos/{full_name}/languages")
        return dict(r.json())

    def fetch_specific_repos(self, specific_repos: list[str]) -> list[dict[str, object]]:
        """Resolve a list of owner/repo strings to repo dicts.

        Parameters
        ----------
        specific_repos : list[str]
            Repository names or GitHub URLs.

        Returns
        -------
        list[dict]
            Successfully fetched repo dicts. Failed repos are logged and skipped.
        """
        repos = []
        for repo_name in specific_repos:
            normalized = self._normalize_repo_pattern(repo_name)

            try:
                repo = self.get_repo_info(normalized)
                repos.append(repo)
                log.logger.debug(f"Found repo: {normalized}")

            except ValueError as e:
                log.logger.warning(str(e))
            except exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None

                if status_code == 404:
                    log.logger.warning(f"Repository not found: {normalized}")
                elif status_code == 403:
                    log.logger.warning(f"Access denied to {normalized} (check permissions)")
                else:
                    log.logger.warning(f"Failed to fetch {normalized}: {e}")

            except exceptions.RequestError as e:
                log.logger.warning(f"Network error fetching {normalized}: {e}")

        return repos
