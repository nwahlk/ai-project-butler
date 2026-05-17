import pytest

# 将项目根目录添加到 Python 路径
import sys
sys.path.insert(0, '..')

from src.main import hello, scan_project

def test_hello():
    """Test the hello command."""
    result = hello("Alice")
    assert "Hello Alice!" in result

def test_scan_project(mocker):
    """Test the scan_project function."""
    mock_print = mocker.patch('src.main.rprint')
    scan_project("/path/to/project")
    mock_print.assert_called_once_with("[bold blue]Scanning project at /path/to/project...[/bold blue]")
