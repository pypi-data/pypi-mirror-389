import typer
import yaml
from pathlib import Path
from pydantic import ValidationError
from typing_extensions import Annotated
import importlib.metadata
import subprocess
import shlex

from .config import find_config, load_config, validate_config

app = typer.Typer(
    help="wandler: A smart, fast task orchestrator for Python projects.",
    add_completion=False,
    no_args_is_help=True,
    epilog="""For more info, run any command with the --help flag:
    
  $ wandler run --help
  $ wandler list --help
"""
)

@app.callback(invoke_without_command=True)
def callback(
        ctx: typer.Context,
        version: Annotated[
            bool, typer.Option(
                "--version",
                "-v",
                help="Show the version and exit.")
        ] = False,
):
    """
    For more info, run any command with the --help flag:
      $ wandler run --help
      $ wandler list --help
    """
    if version:
        try:
            # This reads the version from your pyproject.toml
            __version__ = importlib.metadata.version("wandler")
            typer.echo(__version__)
        except importlib.metadata.PackageNotFoundError:
            # Fallback if the package isn't installed
            typer.echo("wandler version (unknown: package not installed)")
        raise typer.Exit()

    # This prevents the callback from running when a subcommand is used
    if ctx.invoked_subcommand is not None:
        return


@app.command()
def run(task_name: str):
    """Run the specified task by name."""
    config_file_path: Path = find_config()

    if not config_file_path:
        typer.secho("Error: No wandler.yaml configuration file found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        raw_config_data = load_config(config_file_path)
        validated_config = validate_config(raw_config_data)
        task_to_run = validated_config.tasks.get(task_name, '')

        if not task_to_run:
            typer.echo(f"Error: Task '{task_name}' not found in the configuration.")
            raise typer.Exit(code=1)

        typer.echo(f"Running task '{task_name}': {task_to_run.command}")
        command_list = shlex.split(task_to_run.command)
        subprocess.run(
            command_list,
            cwd=config_file_path.parent,
            check=True
        )
        typer.secho(f"Task '{task_name}' completed successfully.", fg=typer.colors.GREEN)

    except subprocess.CalledProcessError as e:
        # This catches when the task (e.g., ruff, pytest) fails
        typer.secho(f"\nError: Task '{task_name}' failed!", fg=typer.colors.RED, bold=True)
        typer.echo(f"The command '{task_to_run.command}' returned a non-zero exit code.")
        raise typer.Exit(code=1)

    except ValidationError as e:
        typer.secho("Error: Your 'wandler.yaml' file has invalid content.", fg=typer.colors.RED, bold=True)
        typer.echo("Please fix the following validation errors:")
        typer.echo(str(e))
        raise typer.Exit(code=1)

    except yaml.YAMLError as e:
        typer.secho("Error: Your 'wandler.yaml' file is not valid YAML.", fg=typer.colors.RED, bold=True)
        typer.echo("It seems to have a syntax error. Please check for typos like missing colons or bad indentation.")
        typer.echo(f"\nYAML Parser Details:\n{e}")
        raise typer.Exit(code=1)

    except OSError as e:
        typer.secho(f"Error: Could not read the file at {config_file_path}.", fg=typer.colors.RED, bold=True)
        typer.echo("Please check that the file exists and you have permission to read it.")
        typer.echo(f"\nOS Error Details: {e}")
        raise typer.Exit(code=1)

@app.command(name="list")
def list_tasks():
    """Lists all available tasks defined in the configuration file.

    Reads the configuration, validates it, and prints a formatted list
    of all task names along with their descriptions.
    """
    config_file_path: Path = find_config()

    if not config_file_path:
        typer.secho("Error: No wandler.yaml configuration file found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        raw_config_data = load_config(config_file_path)
        validated_config = validate_config(raw_config_data)

        if not validated_config.tasks:
            typer.secho("No tasks found in the configuration file.", fg=typer.colors.YELLOW)
            return

        typer.secho("Available tasks:", bold=True)
        for task_name, task_details in validated_config.tasks.items():
            # Use f-string alignment for clean, table-like output
            # This pads the task name to 20 characters
            description = task_details.description or "No description"
            typer.echo(f"{task_name:<20} - {description}")

    except ValidationError as e:
        typer.secho("Error: Your 'wandler.yaml' file has invalid content.", fg=typer.colors.RED, bold=True)
        typer.echo("Please fix the following validation errors:")
        typer.echo(str(e))
        raise typer.Exit(code=1)

    except yaml.YAMLError as e:
        typer.secho("Error: Your 'wandler.yaml' file is not valid YAML.", fg=typer.colors.RED, bold=True)
        typer.echo("It seems to have a syntax error. Please check for typos like missing colons or bad indentation.")
        typer.echo(f"\nYAML Parser Details:\n{e}")
        raise typer.Exit(code=1)

    except OSError as e:
        typer.secho(f"Error: Could not read the file at {config_file_path}.", fg=typer.colors.RED, bold=True)
        typer.echo("Please check that the file exists and you have permission to read it.")
        typer.echo(f"\nOS Error Details: {e}")
        raise typer.Exit(code=1)

def main():
    app()