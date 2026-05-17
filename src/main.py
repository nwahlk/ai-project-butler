import typer
from rich import print as rprint
import logging

app = typer.Typer()

# 基础 logger 配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.command()
def hello(name: str):
    """Say hello to NAME."""
    rprint(f"[bold green]Hello {name}![/bold green]")
    logger.info(f"User greeted: {name}")

def scan_project(path: str):
    """Scan a project at the given path."""
    rprint(f"[bold blue]Scanning project at {path}...[/bold blue]")
    logger.info(f"Scanning project at {path}")
    # 这里可以添加实际的扫描逻辑

if __name__ == "__main__":
    app()
