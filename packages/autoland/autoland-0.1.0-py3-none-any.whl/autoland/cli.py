import subprocess

import click

from .i18n import _
from .service import AutolandService, AutolandError

from importlib.metadata import version

__version__ = version("autoland")


def run_autoland(**kwargs):
    try:
        service = AutolandService(**kwargs)
        service.execute()
    except subprocess.CalledProcessError as error:
        click.echo(f"Command failed: {' '.join(error.cmd)}", err=True)
        if error.stderr:
            click.echo(f"Error: {error.stderr}", err=True)
        raise click.Abort()
    except AutolandError as error:
        click.echo(f"Error: {error}", err=True)
        raise click.Abort()
    except Exception as error:
        click.echo(f"Unexpected error: {error}", err=True)
        raise click.Abort()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help=_("Enable verbose logging."),
)
@click.option(
    "--locale",
    type=str,
    help=_("Language used by coding agents (e.g., ja_JP, en_GB). Defaults to OS settings if omitted."),
)
@click.option(
    "--polling-interval",
    type=int,
    default=30,
    show_default=True,
    help=_("Polling interval in seconds to check GitHub Actions completion."),
)
@click.option(
    "--agent",
    type=click.Choice(["codex", "claude"]),
    default="codex",
    show_default=True,
    help=_("Coding agent to use."),
)
@click.pass_context
def cli(ctx, verbose: bool, locale: str, polling_interval: int, agent: str):
    """
    Automatically land pull requests after GitHub Actions checks pass.

    This command monitors pull requests in the current repository,
    waits for all required checks to complete successfully,
    and then merges the pull request automatically.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['locale'] = locale
    ctx.obj['polling_interval'] = polling_interval
    ctx.obj['agent'] = agent

    if ctx.invoked_subcommand is None:
        run_autoland(**ctx.obj)


@cli.command()
@click.argument("pr_number", type=int)
@click.option(
    "--repo",
    type=str,
    help=_("Specify target repository (e.g., owner/repo)."),
)
@click.pass_context
def debug(ctx, pr_number: int, repo: str) -> None:
    """
    Output debug information for the specified PR.
    """
    click.echo(f"Debug command started for PR #{pr_number}")

    service_kwargs = ctx.obj.copy()

    if repo:
        service_kwargs['repo'] = repo

    service = AutolandService(**service_kwargs)

    click.echo(f"{'=' * 60}")
    click.echo(f"PR #{pr_number} Debug Information")
    click.echo(f"{'=' * 60}")
    click.echo()

    try:
        pr_data = service.fetch_pr_data(pr_number)
        timeline = service.format_pr_timeline(pr_data)

        click.echo(f"{'#' * 60}")
        click.echo("PR Timeline Data")
        click.echo(f"{'#' * 60}")
        if timeline:
            click.echo(timeline)
        else:
            click.echo("(No data could be retrieved)")

    except subprocess.CalledProcessError as error:
        click.echo(f"Command failed: {' '.join(error.cmd)}", err=True)
        if error.stderr:
            click.echo(f"Error: {error.stderr}", err=True)
        raise click.Abort()
    except AutolandError as error:
        click.echo(f"Error: {error}", err=True)
        raise click.Abort()
    except Exception as error:
        click.echo(f"Unexpected error: {error}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
