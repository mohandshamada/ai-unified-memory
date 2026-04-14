"""Agent Status - Dashboard for checking all agents."""

__version__ = "0.1.0"

from .checks import CheckResult, run_all_checks
from .cli import main, render_dashboard

__all__ = ["CheckResult", "run_all_checks", "main", "render_dashboard"]
