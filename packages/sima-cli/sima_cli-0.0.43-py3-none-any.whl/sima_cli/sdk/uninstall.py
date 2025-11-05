#!/usr/bin/env python3
"""
remove.py — interactive utility to stop and remove one or more SiMa SDK containers (and their images).

Usage:
    python remove.py ctx keyword
"""

import subprocess
import sys
import json
from rich.console import Console
from InquirerPy import inquirer
from sima_cli.sdk.utils import select_containers, get_all_containers

console = Console()

# ─────────────────────────────────────────────
# Core removal logic (with version filter)
# ─────────────────────────────────────────────
def remove_containers(ctx, keyword=None):
    """Stop and remove containers matching keyword (and optional version filter)."""
    version_filter = None
    if ctx and getattr(ctx, "obj", None):
        version_filter = ctx.obj.get("version_filter")

    containers = get_all_containers(running_containers_only=False)
    if not containers:
        console.print("[yellow]⚠️  No containers found.[/yellow]")
        return

    # 🔹 Filter by keyword
    if keyword:
        containers = [
            c for c in containers
            if keyword.lower() in c["Names"].lower() or keyword.lower() in c["Image"].lower()
        ]

    # 🔹 Apply version filter if provided
    if version_filter:
        containers = [
            c for c in containers
            if version_filter.lower() in c["Names"].lower() or version_filter.lower() in c["Image"].lower()
        ]
        console.print(f"[dim]🔍 Version filter applied:[/dim] [bold cyan]{version_filter}[/bold cyan]")

    if not containers:
        console.print(
            f"[red]❌ No containers found matching '{keyword or '*'}'"
            + (f" with version '{version_filter}'" if version_filter else "")
            + ".[/red]"
        )
        return

    selected = select_containers(containers)
    if not selected:
        console.print("[yellow]No containers selected. Exiting.[/yellow]")
        return

    for name in selected:
        console.print(f"[cyan]🛑 Stopping (if running):[/cyan] [bold]{name}[/bold]")
        subprocess.run(["docker", "stop", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        console.print(f"[red]🧹 Removing container:[/red] [bold]{name}[/bold]")
        subprocess.run(["docker", "rm", "-f", name])

    console.print("[green]✅ Done removing selected containers.[/green]")

    # Ask user if they want to remove associated images
    if inquirer.confirm(
        message="Also remove associated images?",
        default=False,
        qmark="🧩",
    ).execute():
        images = set(c["Image"] for c in containers if c["Names"] in selected)
        for img in images:
            console.print(f"[red]🧨 Removing image:[/red] [bold]{img}[/bold]")
            subprocess.run(["docker", "rmi", "-f", img])
        console.print("[green]✅ Done removing images.[/green]")
