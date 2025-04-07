# Infra Toolkit

This directory contains the core logic for the infrastructure automation toolkit, designed to streamline the setup and management of new software projects.

## Core Concepts & Architecture

The toolkit follows a modular approach to handle configuration, project setup orchestration, and interactions with external services (like Git providers and cloud platforms).

### 1. Configuration Management (`infra/config.py`)

-   **Purpose:** Centralizes the loading and accessing of all external configurations and credentials.
-   **Mechanism:** The `Config` class loads settings from an `.env` file (located based on the `INFRA_ENV_FILE` environment variable or defaulting to `.env` in the project root) or directly from environment variables.
-   **Usage:** Provides static methods like `Config.get(...)`, `Config.get_github_credentials()`, `Config.get_yandex_cloud_credentials()`, etc., to retrieve specific settings. This avoids scattering environment variable access across the codebase.
-   **Error Handling:** Raises `ConfigError` if essential settings (e.g., `GITHUB_API_TOKEN`) are missing, ensuring the application doesn't run in an improperly configured state.
-   **Example:** See `.env.example` for required and optional variables.

### 2. Project Setup Orchestration (`infra/project_setup/`)

-   **Coordinator:** The main logic resides in `infra/project_setup/core.py`, specifically the `setup_project` function. This function orchestrates the entire process of creating a new project.
-   **Context Object (`ProjectSetupContext`):** Defined in `infra/project_setup/types.py`, this `dataclass` acts as a container for all parameters and state relevant to a single project setup task (e.g., project name, chosen technologies, DB settings, target directory, cloud flags, logging function).
-   **Data Flow:** An instance of `ProjectSetupContext` is created at the beginning of `setup_project` and passed sequentially through various helper functions responsible for specific steps (e.g., creating Git repo, setting up Python environment, creating database, running template-specific logic). This keeps the state organized and function signatures clean.
-   **Environment Setup (`infra/project_setup/environment.py`):** Contains functions for setting up common environment components like Python virtual environments (`setup_python_environment`), databases (`setup_database`), and frontend dependencies (`setup_frontend_environment`). These functions typically receive the `ProjectSetupContext`.

### 3. Project Templates (`infra/templates/`)

-   **Purpose:** Provide starting points for different types of projects (e.g., `webapp`, `chatbot`, `zero`).
-   **Structure:** Each template resides in its own subdirectory.
-   **Customization:** Templates can include a `template_setup.py` file containing a `setup(ctx: ProjectSetupContext)` function. The main `setup_project` function dynamically imports and executes this `setup` function if it exists, allowing templates to perform specific environment setup tasks (like setting up separate backend/frontend environments as seen in `infra/templates/webapp/template_setup.py`).

### 4. Providers (`infra/providers/`)

-   **Purpose:** Encapsulate interactions with external services or systems.
-   **Structure:** Organized by provider type (e.g., `git`, `cloud`, `local`). Submodules handle specific implementations (e.g., `infra/providers/git/github.py`, `infra/providers/cloud/yandex/`).
-   **Usage:** Functions within these modules are called by the core setup logic or template setup scripts to perform actions like creating repositories, setting secrets, or provisioning cloud resources.

## Adding New Features

Here's a general guide on how to extend the toolkit:

1.  **New Configuration:**
    *   If the feature requires new secrets or settings (e.g., an API key for a new service):
        *   Add the variable to `.env.example`.
        *   Add a corresponding `get_..._settings()` method to the `Config` class (`infra/config.py`) to provide structured access.

2.  **New Project Setup Step:**
    *   If the feature adds a step to the project creation process (e.g., setting up a new type of service):
        *   Implement the core logic, often within a new function or module (potentially under `infra/providers/` if it involves an external service, or `infra/project_setup/` if it's a core environment step).
        *   Ensure the function accepts the `ProjectSetupContext` if it needs project-specific information or needs to modify the shared state (like adding connection details to `ctx.db_info`).
        *   Modify `setup_project` in `infra/project_setup/core.py` to call your new function at the appropriate point in the sequence.
        *   If the step requires new user inputs or parameters, add corresponding fields to the `ProjectSetupContext` dataclass (`infra/project_setup/types.py`) and update the callers (CLI, GUI) to collect this information.

3.  **New Project Template:**
    *   Create a new directory under `infra/templates/`.
    *   Populate it with the necessary boilerplate files and directory structure.
    *   If the template requires specific setup logic beyond the standard steps, create a `template_setup.py` file within its directory with a `setup(ctx: ProjectSetupContext)` function.
    *   Register the new template in the `PROJECT_TEMPLATES` dictionary in `infra/cli.py`.

4.  **New Provider Integration:**
    *   If integrating with a new external service (e.g., a different cloud provider, a new code hosting platform):
        *   Create appropriate subdirectories and modules under `infra/providers/`.
        *   Implement functions to interact with the provider's API, using credentials/settings obtained via the `Config` class.
        *   Update the core setup logic (`infra/project_setup/core.py`) or relevant template setup scripts to utilize these new provider functions.

5.  **CLI/GUI Updates:**
    *   Expose new options or commands by modifying `infra/cli.py` (using `click` decorators).
    *   Update the GUI views (e.g., `infra/gui/project/project_setup_view.py`) to include UI elements for the new features or options.