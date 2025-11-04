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

console = Console()
kmpkg_app = typer.Typer(help="Manage kmup components or dependencies (kmpkg).")

@kmpkg_app.callback(invoke_without_command=True)
def kmpkg(ctx: typer.Context):
    """
    kmpkg command group — show available subcommands when none is given.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    

@kmpkg_app.command("uri", help="Show remote URI for KMPKG.")
def kmpkg_uri():
    uri = "https://gitee.com/kumo-pub/kmpkg"
    console.print(f"[cyan]URI for KMPKG:[/cyan] {uri}")

@kmpkg_app.command("location", help="Show local installation location.")
def kmpkg_location():
    path = os.getenv("KMPKG_ROOT", "/home/jeff/pkg/kmpkg")
    console.print(f"[cyan]LOCATION for KMPKG:[/cyan] {path}")



@kmpkg_app.command("log", help="kmpkg last commit log id")
def kmpkg_log():
    """Show local installation location."""
    path = os.getenv("KMPKG_ROOT", "no")
    if path == "no":
        console.print(f"[red]KMPKG not installed[/red]")
        return
    
    try:
        commit_id = subprocess.check_output(
            ["git",  "-C", path, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        console.print(f"[cyan]LOGID for KMPKG:[/cyan] {commit_id}")
    except Exception:
        console.print(f"[cyan]LOGID for KMPKG:[/cyan] unknown")
