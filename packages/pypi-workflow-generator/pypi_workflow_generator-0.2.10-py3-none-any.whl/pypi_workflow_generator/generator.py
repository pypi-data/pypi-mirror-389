"""
Core workflow generation logic.

This module contains the shared business logic used by both:
- MCP server mode (server.py)
- CLI mode (cli.py / main.py)
"""

import os
import subprocess
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

def generate_workflow(
    python_version: str = '3.11',
    output_filename: str = 'pypi-publish.yml',
    release_on_main_push: bool = False,
    test_path: str = '.',
    base_output_dir: Optional[str] = None,
    verbose_publish: bool = False,
    include_release_workflow: bool = True
) -> Dict[str, Any]:
    """
    Generate GitHub Actions workflow for PyPI publishing.

    Args:
        python_version: Python version to use in workflow
        output_filename: Name of generated workflow file
        release_on_main_push: Trigger release on main branch push
        test_path: Path to tests directory
        base_output_dir: Custom output directory (default: .github/workflows)
        verbose_publish: Enable verbose mode for publish actions
        include_release_workflow: Also generate create-release.yml workflow (default: True)

    Returns:
        Dict with success status and generated file path(s)

    Raises:
        FileNotFoundError: If pyproject.toml or setup.py missing
        ValueError: If parameters are invalid
    """
    # Validation
    if not os.path.exists('pyproject.toml') or not os.path.exists('setup.py'):
        raise FileNotFoundError(
            "Project not initialized. Run 'pypi-workflow-generator-init' first."
        )

    # Get template directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(script_dir))
    template = env.get_template('pypi_publish.yml.j2')

    # Render template
    workflow_content = template.render(
        python_version=python_version,
        release_on_main_push=release_on_main_push,
        verbose_publish=verbose_publish,
        test_path=test_path
    )

    # Construct output path
    output_dir = base_output_dir if base_output_dir else os.path.join(
        os.getcwd(), '.github', 'workflows'
    )
    os.makedirs(output_dir, exist_ok=True)
    full_output_path = os.path.join(output_dir, output_filename)

    # Write workflow file
    with open(full_output_path, 'w') as f:
        f.write(workflow_content)

    result = {
        'success': True,
        'file_path': full_output_path,
        'message': f"Successfully generated {full_output_path}",
        'files_created': [full_output_path]
    }

    # Also generate release workflow by default
    if include_release_workflow:
        release_result = generate_release_workflow(
            base_output_dir=base_output_dir
        )
        if release_result['success']:
            result['files_created'].append(release_result['file_path'])
            result['message'] += f"\nSuccessfully generated {release_result['file_path']}"

    return result


def initialize_project(
    package_name: str,
    author: str,
    author_email: str,
    description: str,
    url: str,
    command_name: str
) -> Dict[str, Any]:
    """
    Initialize a new Python project with pyproject.toml and setup.py.

    Args:
        package_name: Name of the Python package
        author: Author name
        author_email: Author email
        description: Package description
        url: Project URL
        command_name: Command-line entry point name

    Returns:
        Dict with success status and created files
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(script_dir))

    # Render pyproject.toml
    pyproject_template = env.get_template('pyproject.toml.j2')
    pyproject_content = pyproject_template.render()

    # Render setup.py
    setup_template = env.get_template('setup.py.j2')
    setup_content = setup_template.render(
        package_name=package_name,
        author=author,
        author_email=author_email,
        description=description,
        url=url,
        command_name=command_name
    )

    # Write files
    with open('pyproject.toml', 'w') as f:
        f.write(pyproject_content)

    with open('setup.py', 'w') as f:
        f.write(setup_content)

    return {
        'success': True,
        'files_created': ['pyproject.toml', 'setup.py'],
        'message': 'Successfully initialized project with pyproject.toml and setup.py'
    }


def create_git_release(version: str) -> Dict[str, Any]:
    """
    Create and push a git release tag.

    Args:
        version: Version string (e.g., 'v1.0.0')

    Returns:
        Dict with success status

    Raises:
        subprocess.CalledProcessError: If git commands fail
    """
    try:
        # Create tag
        subprocess.run(['git', 'tag', version], check=True, capture_output=True, text=True)

        # Push tag
        subprocess.run(['git', 'push', 'origin', version], check=True, capture_output=True, text=True)

        return {
            'success': True,
            'version': version,
            'message': f'Successfully created and pushed tag {version}'
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Error creating or pushing tag: {e.stderr if e.stderr else str(e)}'
        }
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'git not found',
            'message': 'Git is not installed or not in PATH'
        }


def generate_release_workflow(
    output_filename: str = 'create-release.yml',
    base_output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate GitHub Actions workflow for automated release creation.

    This workflow allows users to create releases via GitHub Actions UI,
    automating version calculation, tag creation, and GitHub Release generation.

    Args:
        output_filename: Name of generated workflow file (default: 'create-release.yml')
        base_output_dir: Custom output directory (default: .github/workflows)

    Returns:
        Dict with:
            - success (bool): Whether generation succeeded
            - file_path (str): Full path to generated file
            - message (str): Status message

    Example:
        >>> result = generate_release_workflow()
        >>> print(result['message'])
        Successfully generated .github/workflows/create-release.yml
    """
    # Get template directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(script_dir))
    template = env.get_template('create_release.yml.j2')

    # Render template (no variables needed for Phase 1)
    workflow_content = template.render()

    # Construct output path
    output_dir = base_output_dir if base_output_dir else os.path.join(
        os.getcwd(), '.github', 'workflows'
    )
    os.makedirs(output_dir, exist_ok=True)
    full_output_path = os.path.join(output_dir, output_filename)

    # Write workflow file
    with open(full_output_path, 'w') as f:
        f.write(workflow_content)

    return {
        'success': True,
        'file_path': full_output_path,
        'message': f"Successfully generated {full_output_path}"
    }
