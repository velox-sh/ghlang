import json
from pathlib import Path
from sys import platform

import typer

from ghlang.exceptions import ConfigError
from ghlang.exceptions import TokountNotFoundError
from ghlang.logging import logger
from ghlang.tokount_client import TokountClient

from .utils import generate_charts
from .utils import get_chart_title
from .utils import get_output_path
from .utils import handle_cli_errors
from .utils import save_json_stats
from .utils import setup_cli_environment
from .utils import styles_autocomplete
from .utils import themes_autocomplete


def _merge_stats(all_stats: list[dict[str, dict]]) -> dict[str, dict]:
    """Merge multiple stats dictionaries into one"""
    merged: dict[str, dict] = {}

    for stats in all_stats:
        for lang, data in stats.items():
            if lang == "_summary":
                continue

            if lang not in merged:
                merged[lang] = {"files": 0, "blank": 0, "comment": 0, "code": 0}

            merged[lang]["files"] += data.get("files", 0)
            merged[lang]["blank"] += data.get("blank", 0)
            merged[lang]["comment"] += data.get("comment", 0)
            merged[lang]["code"] += data.get("code", 0)

    return merged


def local(
    paths: list[Path] | None = typer.Argument(
        None,
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        help="Paths to analyze (defaults to current directory)",
    ),
    config_path: Path | None = typer.Option(
        None,
        "--config",
        help="Use a different config file",
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        help="Where to save the charts",
        file_okay=False,
        dir_okay=True,
        writable=True,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Custom output path/filename",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        "-t",
        help="Custom chart title",
    ),
    top_n: int = typer.Option(
        5,
        "--top-n",
        help="How many languages to show in the bar chart",
    ),
    save_json: bool = typer.Option(
        False,
        "--save-json",
        help="Save raw stats as JSON files",
    ),
    json_only: bool = typer.Option(
        False,
        "--json-only",
        help="Output JSON only, skip chart generation",
    ),
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Output stats to stdout instead of files (implies --json-only --quiet)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress log output (only show errors)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show more details",
    ),
    follow_links: bool = typer.Option(
        False,
        "--follow-links",
        "-L",
        help="Follow symlinks when analyzing",
    ),
    theme: str | None = typer.Option(
        None,
        "--theme",
        help="Chart theme (default: light)",
        autocompletion=themes_autocomplete,
    ),
    style: str = typer.Option(
        "pixel",
        "--style",
        "-s",
        help="Chart style (default: pixel)",
        autocompletion=styles_autocomplete,
    ),
) -> None:
    """Analyze local files with tokount"""
    from ghlang.display.utils import normalize_language_stats  # noqa: PLC0415

    if paths is None:
        paths = [Path()]

    try:
        cfg, quiet, json_only = setup_cli_environment(
            config_path=config_path,
            output_dir=output_dir,
            verbose=verbose,
            theme=theme,
            stdout=stdout,
            quiet=quiet,
            require_token=False,
        )

    except ConfigError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    if follow_links and platform == "win32":
        logger.error("--follow-links is not supported on Windows")
        raise typer.Exit(1)

    try:
        tokount = TokountClient(ignored_dirs=cfg.ignored_dirs, follow_symlinks=follow_links)

    except TokountNotFoundError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    with handle_cli_errors():
        all_stats: list[dict[str, dict]] = []

        for i, path in enumerate(paths, start=1):
            path_name = path.name or path.expanduser().resolve().name or "current"
            stats_output = None
            if len(paths) > 1:
                stats_output = get_output_path(
                    cfg.output_dir,
                    f"tokount_stats_{i:02d}_{path_name}.json",
                    save_json,
                    stdout,
                )
            else:
                stats_output = get_output_path(
                    cfg.output_dir, "tokount_stats.json", save_json, stdout
                )

            detailed_stats = tokount.get_language_stats(path, stats_output=stats_output)
            all_stats.append(detailed_stats)

        merged_stats = _merge_stats(all_stats) if len(paths) > 1 else all_stats[0]

        raw_stats = {
            lang: data["code"]
            for lang, data in merged_stats.items()
            if lang != "_summary" and data["code"] > 0
        }
        language_stats = normalize_language_stats(raw_stats)

        if not language_stats:
            logger.error("No code found to analyze, nothing to visualize")
            raise typer.Exit(1)

        if stdout:
            print(json.dumps(language_stats, indent=2))
        elif json_only:
            save_json_stats(language_stats, cfg.output_dir)
        else:
            generate_charts(
                language_stats,
                cfg,
                title=get_chart_title(paths, title, "Local"),
                output=output,
                style=style,
                top_n=top_n,
                save_json=save_json,
            )
