from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any

@dataclass
class ProjectSetupContext:
    """Context object holding parameters for project setup."""
    name: str
    technologies: List[str]
    db_type: str
    db_name: Optional[str]
    use_yandex_cloud: bool
    use_local_docker: bool
    project_dir: Path
    log_func: Callable
    # Dictionary to store arbitrary data from setup steps (kept for potential future use)
    step_data: Dict[str, any] = field(default_factory=dict, init=False)
    # Dictionary to store secrets intended for GitHub Actions
    github_secrets: Dict[str, str] = field(default_factory=dict, init=False)
    # Dictionary to store environment variables for the project's .env file
    project_env: Dict[str, str] = field(default_factory=dict, init=False)
    # Stores the names of secrets that *already exist* in the GitHub repo
    existing_github_secrets: Optional[List[str]] = None
    # Store general database connection details
    # db_info: Optional[Dict[str, any]] = field(default=None, init=False)