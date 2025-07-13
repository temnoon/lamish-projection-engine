"""Basic tests to verify project setup."""
import pytest
import sys
from pathlib import Path


def test_imports():
    """Test that main modules can be imported."""
    import lamish_projection_engine
    from lamish_projection_engine.cli.main import cli
    from lamish_projection_engine.transformers.base import BaseTransformer
    from lamish_projection_engine.utils.config import Settings
    
    assert lamish_projection_engine.__version__ == "0.1.0"


def test_cli_entry_point():
    """Test that CLI entry point exists."""
    from lamish_projection_engine.cli.main import cli
    from click.testing import CliRunner
    
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Lamish Projection Engine" in result.output


def test_project_structure():
    """Test that project structure is correct."""
    project_root = Path(__file__).parent.parent.parent
    
    # Check main directories exist
    assert (project_root / "lamish_projection_engine").is_dir()
    assert (project_root / "lamish_projection_engine" / "core").is_dir()
    assert (project_root / "lamish_projection_engine" / "cli").is_dir()
    assert (project_root / "lamish_projection_engine" / "transformers").is_dir()
    assert (project_root / "lamish_projection_engine" / "utils").is_dir()
    assert (project_root / "lamish_projection_engine" / "tests").is_dir()
    
    # Check key files exist
    assert (project_root / "setup.py").is_file()
    assert (project_root / "requirements.txt").is_file()
    assert (project_root / "pyproject.toml").is_file()
    assert (project_root / "docker-compose.yml").is_file()
    assert (project_root / ".env.example").is_file()
    assert (project_root / ".gitignore").is_file()