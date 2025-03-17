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
    # Get templates from physical directories
    base_dir = Path(__file__).parent
    logger.debug(f"Templates base directory: {base_dir}")
    
    # Find all directories that don't start with underscore
    physical_templates = [d.name for d in base_dir.iterdir() 
                         if d.is_dir() and not d.name.startswith('__')]
    logger.debug(f"Template directories found: {physical_templates}")
    
    # Use only physically present templates
    templates = physical_templates
    
    # Custom templates defined in config
    urls = Config.get_template_urls()
    for template_name, url in urls.items():
        if url and template_name not in templates:
            templates.append(template_name)
    
    logger.debug(f"Available templates: {templates}")        
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
    logger.debug(f"Looking for template '{template_name}' in base directory: {base_dir}")
    
    # Check if template directory exists
    template_dir = base_dir / template_name
    logger.debug(f"Template directory path: {template_dir}, exists: {template_dir.exists()}")
    
    if template_dir.exists():
        logger.debug(f"Template found at: {template_dir}")
        return template_dir
        
    # If not, raise an error
    logger.error(f"Template '{template_name}' not found at: {template_dir}")
    raise TemplateError(f"Template '{template_name}' not found")


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
    force_existing_dir: bool = False,
) -> Path:
    """
    Generate a project boilerplate from a template.
    
    Args:
        project_name: Name of the project
        template_name: Name of the template to use
        output_dir: Directory to create the project in (defaults to current directory)
        context: Additional context variables for the template
        initialize_git: Whether to initialize a Git repository
        force_existing_dir: If True, will use the existing directory even if it already exists
        
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
        if project_dir.exists() and not force_existing_dir:
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
            
        # Get local template path
        logger.info(f"Using local template for {template_name}")
        template_dir = _get_template_path(template_name)
        
        # Copy template to project directory
        if force_existing_dir and project_dir.exists():
            # Just copy all files directly
            logger.debug(f"Using existing directory: {project_dir}")
            # Use shutil.copytree with dirs_exist_ok=True to copy into existing directory
            shutil.copytree(template_dir, project_dir, dirs_exist_ok=True)
        else:
            # Create a new directory with the template
            logger.debug(f"Creating new directory: {project_dir}")
            shutil.copytree(template_dir, project_dir)
        
        # Initialize Git repository if requested
        if initialize_git:
            _initialize_git_repo(project_dir)
            
        logger.info(f"Boilerplate generated successfully at {project_dir}")
        return project_dir
        
    except TemplateError:
        # Re-raise template errors without cleanup
        raise
    except Exception as e:
        logger.error(f"Failed to generate boilerplate: {str(e)}")
        # Clean up if project directory was created
        if project_dir.exists():
            logger.debug(f"Cleaning up project directory: {project_dir}")
            shutil.rmtree(project_dir)
            # Get original exception's stack trace but create new exception with updated message
            if isinstance(e, FileExistsError) and str(e).find(str(project_dir)) >= 0:
                # If this was a "directory exists" error but we've now removed it,
                # raise a different error that better explains what happened
                raise TemplateError(f"Error during project creation. The directory was removed for retry.") from e
        raise TemplateError(f"Failed to generate boilerplate: {str(e)}") from e 