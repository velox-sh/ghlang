from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import json
from pathlib import Path

import typer

from ghlang import constants
from ghlang import exceptions
from ghlang import log
from ghlang import utils
from ghlang.net import github as github_client

from . import charts
from . import utils as cli_utils


def _fetch_repos(
    client: github_client.GitHubClient,
    specific_repos: list[str] | None,
    repos_output: Path | None,
) -> list[dict]:
    if specific_repos:
        log.logger.info(f"Fetching {len(specific_repos)} specific repos")
        repos = client.fetch_specific_repos(specific_repos)
    else:
        log.logger.info("Fetching repos")

        with log.logger.spinner() as progress:
            progress.add_task("Fetching repos...", total=None)
            repos = client.list_repos()

        log.logger.info(f"Found {len(repos)} repos")

    if repos_output and repos:
        utils.save_json(repos, repos_output)

    return repos


def _aggregate_languages(
    client: github_client.GitHubClient,
    repos: list[dict],
    stats_output: Path | None,
) -> dict[str, int]:
    totals: defaultdict[str, int] = defaultdict(int)
    processed = 0
    skipped = 0

    num_workers = min(constants.API_MAX_WORKERS, len(repos))
    log.logger.debug(f"Using {num_workers} concurrent workers for {len(repos)} repos")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_repo = {
            executor.submit(client.get_repo_languages, repo["full_name"]): repo for repo in repos
        }

        with log.logger.progress() as progress:
            task = progress.add_task("Processing repos", total=len(repos))

            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                full_name = repo["full_name"]

                try:
                    langs = future.result()

                    for lang, bytes_count in langs.items():
                        totals[lang] += int(bytes_count)

                    processed += 1
                    log.logger.debug(f"Processed {full_name}")

                except exceptions.HTTPError as e:
                    skipped += 1
                    log.logger.warning(f"Skipped {full_name}: {e}")
                except (exceptions.RequestError, KeyError, ValueError) as e:
                    skipped += 1
                    log.logger.warning(f"Skipped {full_name}: {e}")

                progress.advance(task)

    log.logger.success(f"Processed {processed} repositories ({skipped} skipped)")

    result = dict(totals)
    if stats_output:
        utils.save_json(result, stats_output)

    return result


def github(
    repos: list[str] | None = typer.Argument(
        None,
        help="Specific repos to analyze (owner/repo format, defaults to all your repos)",
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
    """Analyze your GitHub repos"""
    try:
        cfg, quiet, json_only = cli_utils.setup_cli_environment(
            config_path=config_path,
            output_dir=output_dir,
            verbose=verbose,
            theme=theme,
            stdout=stdout,
            quiet=quiet,
            require_token=True,
        )

    except exceptions.ConfigError as e:
        log.logger.error(str(e))
        raise typer.Exit(1)

    with cli_utils.handle_cli_errors():
        client = github_client.GitHubClient(
            token=cfg.token,
            affiliation=cfg.affiliation,
            visibility=cfg.visibility,
            ignored_repos=cfg.ignored_repos,
        )

        repo_list = _fetch_repos(
            client,
            specific_repos=repos,
            repos_output=charts.get_output_path(
                cfg.output_dir, "repositories.json", save_json, stdout
            ),
        )

        if not repo_list:
            log.logger.error("No repositories found, nothing to visualize")
            raise typer.Exit(1)

        language_stats = _aggregate_languages(
            client,
            repo_list,
            stats_output=charts.get_output_path(
                cfg.output_dir, "language_stats.json", save_json, stdout
            ),
        )

        if not language_stats:
            log.logger.error("No language statistics found, nothing to visualize")
            raise typer.Exit(1)

        if stdout:
            print(json.dumps(language_stats, indent=2))
        elif json_only:
            utils.save_json(language_stats, cfg.output_dir / "language_stats.json")
        else:
            charts.generate_charts(
                language_stats,
                cfg,
                title=charts.get_chart_title(repos, title, "GitHub"),
                output=output,
                style=style,
                top_n=top_n,
                save_json=save_json,
            )
