# Copyright (C) Kumo inc. and its affiliates.
# Author: Jeff.li lijippy@163.com
# All rights reserved.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import os
import subprocess
import typer
from rich.console import Console
from loguru import logger
from kmup.kmpkg.commands import kmpkg_app

app = typer.Typer(help="Kumo Unified Platform CLI (kmup)")

console = Console()

@app.callback(invoke_without_command=True)
def app_run(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

@app.command()
def install():
    """
    Install kmup components or dependencies.
    """
    logger.info("Starting installation...")
    console.print("[bold green]✅ kmup installation completed successfully![/bold green]")

@app.command()
def mirror():
    """
    Manage or switch mirrors.
    """
    logger.info("Updating mirrors...")
    console.print("[bold cyan]🌐 Mirror updated successfully![/bold cyan]")

@app.command()
def gen(name: str):
    """
    Generate a new command template: kmup gen <name>
    """
    import os, textwrap

    path = f"kmup/commands/{name}.py"
    os.makedirs("kmup/commands", exist_ok=True)

    if os.path.exists(path):
        console.print(f"[bold yellow]⚠️ Command {name} already exists.[/bold yellow]")
        raise typer.Exit(1)

    code = textwrap.dedent(f"""
    import typer
    from rich.console import Console
    from loguru import logger

    console = Console()

    def register(app: typer.Typer):
        @app.command()
        def {name}():
            logger.info("Running command: {name}")
            console.print("[bold magenta]{name} executed successfully.[/bold magenta]")
    """)

    with open(path, "w") as f:
        f.write(code.strip() + "\n")

    console.print(f"[bold green]✅ Command '{name}' created at {path}![/bold green]")

app.add_typer(kmpkg_app, name="kmpkg")

def run():
    app()
