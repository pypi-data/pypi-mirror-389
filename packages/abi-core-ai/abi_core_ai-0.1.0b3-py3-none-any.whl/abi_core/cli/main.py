#!/usr/bin/env python3
"""
ABI Core CLI - Command Line Interface for ABI-Core
"""

import click
import io
from rich.console import Console

from .banner import ABI_BANNER
from .commands import create, add, run, status, info

console = Console()

class RichGroup(click.Group):
    def format_help(self, ctx, formatter):
        sio = io.StringIO()
        rich_console = Console(file=sio, force_terminal=True)
        rich_console.print(ABI_BANNER, style="cyan")
        rich_console.print()
        
        formatter.write(sio.getvalue())
        super().format_help(ctx, formatter)

@click.group(cls=RichGroup)
@click.version_option(version="1.0.0", prog_name="abi-core")
def cli():
    """ABI Core - Agent-Based Infrastructure CLI
    
    Create, manage and deploy ABI-powered projects with agents,
    semantic layers, and security policies.
    """
    pass

# Register command groups and commands
cli.add_command(create)
cli.add_command(add)
cli.add_command(run)
cli.add_command(status)
cli.add_command(info)

if __name__ == "__main__":
    cli()