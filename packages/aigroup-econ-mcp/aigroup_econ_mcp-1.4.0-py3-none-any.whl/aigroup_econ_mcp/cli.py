"""
AIGroup  MCP 
"""

import sys
import click
import uvicorn
from .server import create_mcp_server


@click.command()
@click.option('--port', default=8000, help='')
@click.option('--host', default='127.0.0.1', help='')
@click.option('--transport', default='stdio',
              type=click.Choice(['stdio', 'streamable-http', 'sse']),
              help=' (: stdio)')
@click.option('--debug', is_flag=True, help='')
@click.option('--mount-path', default=None, help='')
@click.option('--version', is_flag=True, help='')
def cli(port: int, host: str, transport: str, debug: bool, mount_path: str, version: bool):
    """AIGroup  MCP 
    
    stdioMCPMCP
    """
    
    # 
    if version:
        from . import __version__
        click.echo(f"aigroup-econ-mcp v{__version__}", err=True)
        click.echo("Professional econometrics MCP tool", err=True)
        click.echo("Author: AIGroup", err=True)
        sys.exit(0)

    # MCP
    mcp_server = create_mcp_server()

    # 
    if debug:
        mcp_server.settings.debug = True
        click.echo(f"[DEBUG] ", err=True)

    # 
    if transport == 'stdio':
        # stdiostdoutMCP
        # stderr
        from . import __version__
        click.echo(f"[INFO] aigroup-econ-mcp v{__version__} starting...", err=True)
        click.echo(f"[INFO] Transport: stdio (MCP protocol)", err=True)
        if debug:
            click.echo(f"[DEBUG] Debug mode enabled", err=True)
        click.echo(f"[INFO] Server ready. Waiting for MCP client connection...", err=True)
        mcp_server.run(transport='stdio')
        
    elif transport == 'streamable-http':
        # Streamable HTTP - uvicorn
        click.echo(f"[INFO] Starting aigroup-econ-mcp server", err=True)
        click.echo(f"[INFO] Professional econometrics MCP tool for AI data analysis", err=True)
        click.echo(f"[INFO] Transport protocol: {transport}", err=True)
        click.echo(f"[INFO] Service address: http://{host}:{port}", err=True)
        if mount_path:
            click.echo(f"[INFO] Mount path: {mount_path}", err=True)
        
        # Starletteuvicorn
        app = mcp_server.streamable_http_app()
        uvicorn.run(app, host=host, port=port, log_level="info")
        
    elif transport == 'sse':
        # SSE - uvicorn
        click.echo(f"[INFO] Starting aigroup-econ-mcp server", err=True)
        click.echo(f"[INFO] Professional econometrics MCP tool for AI data analysis", err=True)
        click.echo(f"[INFO] Transport protocol: {transport}", err=True)
        click.echo(f"[INFO] Service address: http://{host}:{port}", err=True)
        if mount_path:
            click.echo(f"[INFO] Mount path: {mount_path}", err=True)
        
        # Starletteuvicorn
        app = mcp_server.sse_app()
        uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    cli()