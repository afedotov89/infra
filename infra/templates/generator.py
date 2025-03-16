"""
Project template generator for creating boilerplate projects.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

import jinja2
from git import Repo

from infra.config import Config

logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """Exception raised for template errors."""
    pass


def list_available_templates() -> List[str]:
    """
    List available project templates.
    
    Returns:
        List[str]: List of template names
    """
    # Built-in templates
    templates = ["django", "react", "django-react"]
    
    # Custom templates defined in config
    urls = Config.get_template_urls()
    for template_name, url in urls.items():
        if url and template_name not in templates:
            templates.append(template_name)
            
    return templates


def _get_template_path(template_name: str) -> Path:
    """
    Get the path to a template directory.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Path: Path to the template directory
        
    Raises:
        TemplateError: If template does not exist
    """
    # Base directory for templates
    base_dir = Path(__file__).parent
    
    # Check if template directory exists
    template_dir = base_dir / template_name
    if template_dir.exists():
        return template_dir
        
    # If not, raise an error
    raise TemplateError(f"Template '{template_name}' not found")


def _clone_template_from_repo(
    template_name: str, 
    target_dir: Path,
) -> Path:
    """
    Clone a template from a Git repository.
    
    Args:
        template_name: Name of the template
        target_dir: Directory to clone the template to
        
    Returns:
        Path: Path to the cloned repository
        
    Raises:
        TemplateError: If cloning fails
    """
    urls = Config.get_template_urls()
    url = urls.get(template_name)
    
    if not url:
        raise TemplateError(f"No repository URL configured for template '{template_name}'")
    
    try:
        logger.info(f"Cloning template from {url}")
        Repo.clone_from(url, target_dir)
        return target_dir
    except Exception as e:
        logger.error(f"Failed to clone template repository: {str(e)}")
        raise TemplateError(f"Failed to clone template repository: {str(e)}")


def _render_templates(
    source_dir: Path,
    target_dir: Path,
    context: Dict[str, str],
    file_extensions: List[str] = [".py", ".html", ".js", ".jsx", ".ts", ".tsx", ".md", ".yml", ".yaml", ".json"],
) -> None:
    """
    Recursively render template files with context variables.
    
    Args:
        source_dir: Source directory with templates
        target_dir: Target directory to write rendered files
        context: Context variables for templates
        file_extensions: File extensions to process as templates
        
    Raises:
        TemplateError: If rendering fails
    """
    try:
        # Create Jinja2 environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(source_dir),
            keep_trailing_newline=True,
        )
        
        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy and render files
        for item in source_dir.iterdir():
            target_item = target_dir / item.name
            
            # Skip .git directory
            if item.name == ".git":
                continue
                
            # Process directories recursively
            if item.is_dir():
                _render_templates(item, target_item, context, file_extensions)
            # Render template files
            elif any(item.name.endswith(ext) for ext in file_extensions):
                try:
                    template_content = item.read_text()
                    # Check if file contains Jinja2 placeholders
                    if "{{" in template_content or "{%" in template_content:
                        # Create template from content
                        template = env.from_string(template_content)
                        rendered_content = template.render(**context)
                        
                        # Write rendered content
                        target_item.parent.mkdir(parents=True, exist_ok=True)
                        target_item.write_text(rendered_content)
                    else:
                        # Just copy the file
                        shutil.copy2(item, target_item)
                except Exception as e:
                    logger.warning(f"Failed to render template {item}: {str(e)}")
                    # Copy the file as-is if rendering fails
                    shutil.copy2(item, target_item)
            # Copy other files
            else:
                shutil.copy2(item, target_item)
    except Exception as e:
        logger.error(f"Failed to render templates: {str(e)}")
        raise TemplateError(f"Failed to render templates: {str(e)}")


def _initialize_git_repo(project_dir: Path) -> None:
    """
    Initialize a new Git repository in the project directory.
    
    Args:
        project_dir: Project directory
        
    Raises:
        TemplateError: If Git initialization fails
    """
    try:
        logger.info(f"Initializing Git repository in {project_dir}")
        repo = Repo.init(project_dir)
        
        # Add all files to Git
        repo.git.add(A=True)
        
        # Initial commit
        repo.git.commit(m="Initial commit from Infra template")
        
        logger.info("Git repository initialized with initial commit")
    except Exception as e:
        logger.error(f"Failed to initialize Git repository: {str(e)}")
        raise TemplateError(f"Failed to initialize Git repository: {str(e)}")


def generate_boilerplate(
    project_name: str,
    template_name: str,
    output_dir: Optional[Union[str, Path]] = None,
    context: Optional[Dict[str, str]] = None,
    initialize_git: bool = True,
) -> Path:
    """
    Generate a project boilerplate from a template.
    
    Args:
        project_name: Name of the project
        template_name: Name of the template to use
        output_dir: Directory to create the project in (defaults to current directory)
        context: Additional context variables for the template
        initialize_git: Whether to initialize a Git repository
        
    Returns:
        Path: Path to the generated project
        
    Raises:
        TemplateError: If boilerplate generation fails
    """
    if template_name not in list_available_templates():
        raise TemplateError(f"Unknown template: {template_name}")
    
    # Set up directories
    if output_dir is None:
        output_dir = Path.cwd()
    elif isinstance(output_dir, str):
        output_dir = Path(output_dir)
        
    project_dir = output_dir / project_name
    
    try:
        # Check if project directory already exists
        if project_dir.exists():
            logger.warning(f"Project directory {project_dir} already exists")
            raise TemplateError(f"Project directory {project_dir} already exists")
            
        logger.info(f"Generating {template_name} boilerplate for {project_name}")
        
        # Merge default context with provided context
        template_context = {
            "project_name": project_name,
            "project_name_snake": project_name.replace("-", "_").lower(),
        }
        if context:
            template_context.update(context)
            
        # Try using local template first
        try:
            template_dir = _get_template_path(template_name)
            # Copy template to project directory
            shutil.copytree(template_dir, project_dir)
        except TemplateError:
            # If local template doesn't exist, try cloning from repository
            _clone_template_from_repo(template_name, project_dir)
        
        # Render templates in project directory
        _render_templates(project_dir, project_dir, template_context)
        
        # Initialize Git repository if requested
        if initialize_git:
            _initialize_git_repo(project_dir)
            
        logger.info(f"Boilerplate generated successfully at {project_dir}")
        return project_dir
        
    except Exception as e:
        logger.error(f"Failed to generate boilerplate: {str(e)}")
        # Clean up if project directory was created
        if project_dir.exists():
            shutil.rmtree(project_dir)
        raise TemplateError(f"Failed to generate boilerplate: {str(e)}") 