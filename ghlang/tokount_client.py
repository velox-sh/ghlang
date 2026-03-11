import json
from pathlib import Path
import shutil
import subprocess

from .exceptions import TokountArgumentError
from .exceptions import TokountError
from .exceptions import TokountIoError
from .exceptions import TokountNotFoundError
from .logging import logger


def _find_tokount() -> Path:
    """Find tokount binary in PATH"""
    tokount_path = shutil.which("tokount")
    if tokount_path is None:
        raise TokountNotFoundError()
    return Path(tokount_path)


class TokountClient:
    """Client for running tokount on local files/directories"""

    def __init__(self, ignored_dirs: list[str]):
        self._ignored_dirs = ignored_dirs
        self._tokount_path = _find_tokount()

    def _build_tokount_command(self, tokount_path: Path, path: Path) -> list[str]:
        """Build tokount command with optional excluded dirs"""
        cmd = [str(tokount_path), str(path.resolve())]

        if self._ignored_dirs:
            cmd.append(",".join(self._ignored_dirs))

        return cmd

    def _parse_tokount_error(self, stderr: str) -> TokountError | None:
        """Parse tokount's structured JSON error output"""
        try:
            data = json.loads(stderr)

        except json.JSONDecodeError:
            return None

        error = data.get("error")
        if not isinstance(error, dict):
            return None

        message = error.get("message")
        if not isinstance(message, str) or not message:
            return None

        kind = error.get("kind") if isinstance(error.get("kind"), str) else None
        details = error.get("details") if isinstance(error.get("details"), dict) else None

        error_map: dict[str, type[TokountError]] = {
            "InvalidArgs": TokountArgumentError,
            "NotFound": TokountNotFoundError,
            "IoError": TokountIoError,
        }

        if kind is None:
            exc_type: type[TokountError] = TokountError
        else:
            exc_type = error_map.get(kind, TokountError)

        return exc_type(message, kind=kind, details=details)

    def _analyze_path(self, path: Path) -> dict:
        """Run tokount on a file or directory and return raw JSON output"""
        cmd = self._build_tokount_command(self._tokount_path, path)
        logger.debug(f"Running: {' '.join(cmd)}")

        with logger.console.status(f"[bold]Analyzing {path}..."):
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                cwd=path if path.is_dir() else path.parent,
            )

        if result.returncode != 0:
            logger.debug(f"tokount stderr: {result.stderr}")
            parsed_error = self._parse_tokount_error(result.stderr)

            if parsed_error:
                raise parsed_error
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        try:
            return dict(json.loads(result.stdout))

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse tokount output: {result.stdout[:500]}")
            raise ValueError(f"Invalid JSON from tokount: {e}") from e

    def get_language_stats(
        self,
        path: Path,
        stats_output: Path | None = None,
    ) -> dict[str, dict]:
        """Get language statistics for a path"""
        logger.info(f"Analyzing {path}")

        raw_output = self._analyze_path(path)

        if stats_output:
            stats_output.parent.mkdir(parents=True, exist_ok=True)

            with stats_output.open("w") as f:
                json.dump(raw_output, f, indent=2)

            logger.debug(f"Saved raw tokount output to {stats_output}")

        stats = {}
        for key, value in raw_output.items():
            if not isinstance(value, dict):
                continue

            if key == "SUM":
                stats["_summary"] = {
                    "files": value.get("nFiles", 0),
                    "blank": value.get("blank", 0),
                    "comment": value.get("comment", 0),
                    "code": value.get("code", 0),
                }
            else:
                stats[key] = {
                    "files": value.get("nFiles", 0),
                    "blank": value.get("blank", 0),
                    "comment": value.get("comment", 0),
                    "code": value.get("code", 0),
                }

        total_code = stats.get("_summary", {}).get("code", 0)
        total_files = stats.get("_summary", {}).get("files", 0)
        logger.success(f"Analyzed {total_files} files, {total_code} lines of code")

        return stats
