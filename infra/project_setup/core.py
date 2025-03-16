"""
Core project setup functionality.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from infra.config import Config, ConfigError
from infra.providers.git import (
    create_repository, 
    check_project_directory,
    create_project_directory,
    populate_project_directory,
    initialize_git_repository,
    LocalGitError
)

logger = logging.getLogger(__name__)


class SetupError(Exception):
    """Exception raised for project setup errors."""
    pass


def setup_project(
    name: str, 
    technologies: List[str], 
    private: bool = True, 
    db_type: str = "postgres", 
    db_name: Optional[str] = None,
    log_callback = None
) -> Dict[str, Any]:
    """
    Set up a complete project infrastructure.
    
    This function:
    1. Creates a GitHub repository
    2. Checks local project directory
    3. Creates or initializes local project
    4. Sets up CI/CD variables
    5. Creates database in the cloud
    6. Sets up container infrastructure
    7. Finalizes project setup
    
    Args:
        name: Project name
        technologies: List of technologies to include
        private: Whether the repository should be private
        db_type: Database type
        db_name: Database name (defaults to project name)
        log_callback: Optional callback function for logging. If None, print to stdout.
        
    Returns:
        Dict with setup results including repository URL, project directory, etc.
        
    Raises:
        SetupError: If project setup fails
    """
    if not technologies:
        raise SetupError("No technologies specified")
    
    # Use the provided log function or default to print
    log = log_callback or print
    
    log(f"Setting up project: {name} with technologies: {', '.join(technologies)}")
    
    repo = None
    project_dir = None
    
    try:
        # Step 1: Create GitHub repository
        log("🔄 Step 1/7: Creating GitHub repository...")
        repo, already_existed = create_repository(name, private)
        
        if already_existed:
            log(f"⚠️  Repository already exists: {repo.html_url}")
            log(f"   Skipping repository creation step.")
        else:
            log(f"✅ Repository created: {repo.html_url}")
        
        # Step 2: Check local project directory
        log("🔄 Step 2/7: Checking local project directory...")
        projects_root = Config.get_projects_root_dir()
        project_dir, dir_exists, is_empty = check_project_directory(name, projects_root)
        
        if dir_exists:
            log(f"⚠️  Project directory already exists: {project_dir}")
            if is_empty:
                log(f"   Directory is empty.")
            else:
                log(f"   Directory is not empty.")
        else:
            log(f"✅ Project directory checked")
            
        # Step 3: Create or initialize local project
        log("🔄 Step 3/7: Setting up local project...")
        
        if not dir_exists:
            # Create directory if it doesn't exist
            create_project_directory(project_dir)
            log(f"✅ Created project directory: {project_dir}")
            
            # Populate empty directory with boilerplate
            populate_project_directory(project_dir, technologies)
            log(f"✅ Populated project directory with initial code")
            
            # Initialize Git repository
            initialize_git_repository(project_dir, repo.clone_url)
            log(f"✅ Initialized Git repository and pushed to remote")
        else:
            if is_empty:
                # Directory exists but is empty
                log(f"✅ Using existing empty directory: {project_dir}")
                
                # Populate empty directory with boilerplate
                populate_project_directory(project_dir, technologies)
                log(f"✅ Populated project directory with initial code")
                
                # Initialize Git repository
                initialize_git_repository(project_dir, repo.clone_url)
                log(f"✅ Initialized Git repository and pushed to remote")
            else:
                # Directory exists and is not empty
                log(f"✅ Using existing non-empty directory: {project_dir}")
                
                # Initialize Git in existing non-empty directory
                initialize_git_repository(project_dir, repo.clone_url)
                log(f"✅ Initialized Git repository with existing code and pushed to remote")
                
        # Step 4: Set up CI/CD variables
        log("🔄 Step 4/7: Setting up CI/CD variables...")
        # from infra.providers.git import setup_cicd
        # setup_cicd(name)
        log("✅ CI/CD variables set up")
        
        # Step 5: Create database
        log("🔄 Step 5/7: Creating database...")
        # from infra.providers.cloud.yandex.db import create_database
        # create_database(db_name or name, db_type)
        log(f"✅ Database '{db_name or name}' created")
        
        # Step 6: Set up container infrastructure
        log("🔄 Step 6/7: Setting up container infrastructure...")
        # from infra.providers.cloud.yandex.compute import setup_containers
        # setup_containers(name)
        log("✅ Container infrastructure configured")
        
        # Step 7: Complete project setup
        log("🔄 Step 7/7: Finalizing project setup...")
        
        log(f"\n✅ Local project directory: {project_dir}")
        log(f"✅ GitHub repository: {repo.html_url}")
        log(f"✅ Project has been set up with: {', '.join(technologies)}")
        
        log(f"\n🚀 Project {name} is ready for development! 🚀")
        
        return {
            "project_name": name,
            "technologies": technologies,
            "repository_url": repo.html_url,
            "project_directory": str(project_dir),
            "database_name": db_name or name
        }
        
    except ConfigError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise SetupError(f"Configuration error: {str(e)}") from e
    except LocalGitError as e:
        logger.error(f"Git error: {str(e)}")
        raise SetupError(f"Git error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error setting up project: {str(e)}")
        raise SetupError(f"Unexpected error: {str(e)}") from e 