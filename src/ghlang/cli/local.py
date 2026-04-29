import json
from pathlib import Path
from sys import platform

import typer

from ghlang import exceptions
from ghlang import log
from ghlang import tokount_client
from ghlang import utils
from ghlang.static import languages

from . import charts
from . import utils as cli_utils


def _merge_stats(all_stats: list[dict[str, dict]]) -> dict[str, dict]:
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
        autocompletion=cli_utils.themes_autocomplete,
    ),
    style: str = typer.Option(
        "pixel",
        "--style",
        "-s",
        help="Chart style (default: pixel)",
        autocompletion=cli_utils.styles_autocomplete,
    ),
) -> None:
    """Analyze local files with tokount"""
    if paths is None:
        paths = [Path()]

    try:
        cfg, quiet, json_only = cli_utils.setup_cli_environment(
            config_path=config_path,
            output_dir=output_dir,
            verbose=verbose,
            theme=theme,
            stdout=stdout,
            quiet=quiet,
            require_token=False,
        )

    except exceptions.ConfigError as e:
        log.logger.error(str(e))
        raise typer.Exit(1)

    if follow_links and platform == "win32":
        log.logger.error("--follow-links is not supported on Windows")
        raise typer.Exit(1)

    try:
        tokount = tokount_client.TokountClient(
            ignored_dirs=cfg.ignored_dirs, follow_symlinks=follow_links
        )
    except exceptions.TokountNotFoundError as e:
        log.logger.error(str(e))
        raise typer.Exit(1)

    with cli_utils.handle_cli_errors():
        all_stats: list[dict[str, dict]] = []

        for i, path in enumerate(paths, start=1):
            path_name = path.name or path.expanduser().resolve().name or "current"
            stats_output = None
            if len(paths) > 1:
                stats_output = charts.get_output_path(
                    cfg.output_dir,
                    f"tokount_stats_{i:02d}_{path_name}.json",
                    save_json,
                    stdout,
                )
            else:
                stats_output = charts.get_output_path(
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
        language_stats = languages.normalize_language_stats(raw_stats)

        if not language_stats:
            log.logger.error("No code found to analyze, nothing to visualize")
            raise typer.Exit(1)

        if stdout:
            print(json.dumps(language_stats, indent=2))
        elif json_only:
            utils.save_json(language_stats, cfg.output_dir / "language_stats.json")
        else:
            charts.generate_charts(
                language_stats,
                cfg,
                title=charts.get_chart_title(paths, title, "Local"),
                output=output,
                style=style,
                top_n=top_n,
                save_json=save_json,
            )
