import os
import typer
from .server import run_sse, run_stdio, run_streamable_http
from bonuspay import __version__

app = typer.Typer(help=f"BonusPay API MCP Server {__version__}")


@app.command()
def sse(
    host: str = typer.Option("0.0.0.0", help="Host to bind the MCP server to."),
    port: int = typer.Option(9998, help="Port to run the MCP server on."),
    network: str = typer.Option("test", help="network of use BonusPay API"),
    private_key_path: str = typer.Option(os.getenv("BONUSPAY_PRIVATE_KEY_PATH", ""), help="Path to the RSA private key .pem file. (Overrides BONUSPAY_PRIVATE_KEY_PATH env var)"),
    public_key_path: str = typer.Option(os.getenv("BONUSPAY_PUBLIC_KEY_PATH", ""), help="Path to the RSA public key .pem file. (Overrides BONUSPAY_PUBLIC_KEY_PATH env var)"),
    partner_id: str = typer.Option(os.getenv("BONUSPAY_PARTNER_ID", ""), help="the partner id of bonuspay. (Overrides BONUSPAY_PARTNER_ID env var)"),
):
    """Start BonusPay API MCP Server in SSE mode"""
    try:
        run_sse(host=host, port=port, network=network, private_key_path=private_key_path, public_key_path=public_key_path, partner_id=partner_id)
    except Exception as e:
        typer.echo(f"\nError: {e}", err=True)
        import traceback
        traceback.print_exc()
    finally:
        typer.echo("Service stopped.")

@app.command()
def streamable_http(
    host: str = typer.Option("0.0.0.0", help="Host to bind the MCP server to."),
    port: int = typer.Option(9998, help="Port to run the MCP server on."),
    network: str = typer.Option("test", help="network of use BonusPay API"),
    private_key_path: str = typer.Option(os.getenv("BONUSPAY_PRIVATE_KEY_PATH", ""), help="Path to the RSA private key .pem file. (Overrides BONUSPAY_PRIVATE_KEY_PATH env var)"),
    public_key_path: str = typer.Option(os.getenv("BONUSPAY_PUBLIC_KEY_PATH", ""), help="Path to the RSA public key .pem file. (Overrides BONUSPAY_PUBLIC_KEY_PATH env var)"),
    partner_id: str = typer.Option(os.getenv("BONUSPAY_PARTNER_ID", ""), help="the partner id of bonuspay. (Overrides BONUSPAY_PARTNER_ID env var)"),
):
    """Start BonusPay API MCP Server in streamable HTTP mode"""
    try:
        run_streamable_http(host=host, port=port, network=network, private_key_path=private_key_path, public_key_path=public_key_path, partner_id=partner_id)
    except Exception as e:
        typer.echo(f"\nError: {e}", err=True)
        import traceback
        traceback.print_exc()
    finally:
        typer.echo("Service stopped.")

@app.command()
def stdio(
    network: str = typer.Option("test", help="network of use BonusPay API"),
    private_key_path: str = typer.Option(os.getenv("BONUSPAY_PRIVATE_KEY_PATH", ""), help="Path to the RSA private key .pem file. (Overrides BONUSPAY_PRIVATE_KEY_PATH env var)"),
    public_key_path: str = typer.Option(os.getenv("BONUSPAY_PUBLIC_KEY_PATH", ""), help="Path to the RSA public key .pem file. (Overrides BONUSPAY_PUBLIC_KEY_PATH env var)"),
    partner_id: str = typer.Option(os.getenv("BONUSPAY_PARTNER_ID", ""), help="the partner id of bonuspay. (Overrides BONUSPAY_PARTNER_ID env var)"),
):
    """Start BonusPay API MCP Server in stdio mode"""
    try:
        run_stdio(network=network, private_key_path=private_key_path, public_key_path=public_key_path, partner_id=partner_id)
    except Exception as e:
        typer.echo(f"\nError: {e}", err=True)
        import traceback
        traceback.print_exc()
    finally:
        typer.echo("Service stopped.")

if __name__ == "__main__":
    app()