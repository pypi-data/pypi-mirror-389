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

def generate_workflows(
    python_version: str = '3.11',
    test_path: str = '.',
    base_output_dir: Optional[str] = None,
    verbose_publish: bool = False
) -> Dict[str, Any]:
    """
    Generate GitHub Actions workflows for PyPI publishing.

    Generates 3 workflow files:
        - _reusable-test-build.yml (shared test/build logic)
        - release.yml (manual releases via GitHub UI)
        - test-pr.yml (PR testing to TestPyPI)

    Args:
        python_version: Python version to use in workflow (default: '3.11')
        test_path: Path to tests directory (default: '.')
        base_output_dir: Custom output directory (default: .github/workflows)
        verbose_publish: Enable verbose mode for publish actions (default: False)

    Returns:
        Dict with:
            - success (bool): Whether generation succeeded
            - files_created (list): Paths to generated files
            - message (str): Status message

    Raises:
        FileNotFoundError: If pyproject.toml or setup.py missing
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

    # Construct output directories
    output_dir = base_output_dir if base_output_dir else os.path.join(
        os.getcwd(), '.github', 'workflows'
    )
    scripts_dir = os.path.join(os.getcwd(), 'scripts')

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    files_created = []

    # Template context
    context = {
        'python_version': python_version,
        'test_path': test_path,
        'verbose_publish': verbose_publish
    }

    # Generate each workflow file
    workflow_templates = [
        ('_reusable_test_build.yml.j2', '_reusable-test-build.yml'),
        ('release.yml.j2', 'release.yml'),
        ('test_pr.yml.j2', 'test-pr.yml')
    ]

    for template_name, output_filename in workflow_templates:
        template = env.get_template(template_name)
        content = template.render(**context)

        full_output_path = os.path.join(output_dir, output_filename)
        with open(full_output_path, 'w') as f:
            f.write(content)

        files_created.append(full_output_path)

    # Generate script files
    script_templates = [
        ('scripts/calculate_version.sh.j2', 'calculate_version.sh')
    ]

    for template_name, output_filename in script_templates:
        template = env.get_template(template_name)
        content = template.render(**context)

        full_output_path = os.path.join(scripts_dir, output_filename)
        with open(full_output_path, 'w') as f:
            f.write(content)

        # Make script executable
        os.chmod(full_output_path, 0o755)

        files_created.append(full_output_path)

    return {
        'success': True,
        'files_created': files_created,
        'message': f"Successfully generated {len(files_created)} files:\n" +
                   "\n".join(f"  - {f}" for f in files_created)
    }


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


