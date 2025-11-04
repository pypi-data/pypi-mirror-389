"""
Tests for release workflow generation.
"""
import os
from pathlib import Path
from pypi_workflow_generator.generator import generate_release_workflow, generate_workflow


def test_generate_release_workflow_default(tmp_path: Path):
    """Test release workflow generation with default arguments."""
    output_dir = tmp_path / ".github" / "workflows"
    result = generate_release_workflow(
        base_output_dir=str(output_dir)
    )

    assert result['success']
    assert 'file_path' in result
    assert 'message' in result

    output_file = output_dir / 'create-release.yml'
    assert output_file.exists()

    with open(output_file, 'r') as f:
        content = f.read()

    # Verify workflow structure
    assert "name: Create Release" in content
    assert "workflow_dispatch" in content
    assert "release_type" in content
    assert "patch" in content
    assert "minor" in content
    assert "major" in content
    assert "Create GitHub Release" in content
    assert "generate-notes" in content


def test_generate_release_workflow_custom_filename(tmp_path: Path):
    """Test release workflow with custom filename."""
    output_dir = tmp_path / ".github" / "workflows"
    result = generate_release_workflow(
        output_filename='my-release.yml',
        base_output_dir=str(output_dir)
    )

    assert result['success']

    output_file = output_dir / 'my-release.yml'
    assert output_file.exists()

    with open(output_file, 'r') as f:
        content = f.read()

    assert "workflow_dispatch" in content


def test_generate_release_workflow_creates_directory(tmp_path: Path):
    """Test that workflow generation creates output directory if needed."""
    output_dir = tmp_path / ".github" / "workflows"
    assert not output_dir.exists()

    result = generate_release_workflow(
        base_output_dir=str(output_dir)
    )

    assert result['success']
    assert output_dir.exists()
    assert (output_dir / 'create-release.yml').exists()


def test_generate_workflow_includes_release_by_default(tmp_path: Path):
    """Test that generate_workflow creates both workflows by default."""
    # Create dummy pyproject.toml and setup.py for validation
    (tmp_path / 'pyproject.toml').write_text('[build-system]')
    (tmp_path / 'setup.py').write_text('from setuptools import setup\nsetup()')

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        output_dir = tmp_path / ".github" / "workflows"
        result = generate_workflow(
            python_version='3.11',
            base_output_dir=str(output_dir)
        )

        assert result['success']
        assert 'files_created' in result
        assert len(result['files_created']) == 2

        # Both workflows should exist
        assert (output_dir / 'pypi-publish.yml').exists()
        assert (output_dir / 'create-release.yml').exists()

    finally:
        os.chdir(original_cwd)


def test_generate_workflow_skip_release(tmp_path: Path):
    """Test that generate_workflow can skip release workflow."""
    # Create dummy pyproject.toml and setup.py for validation
    (tmp_path / 'pyproject.toml').write_text('[build-system]')
    (tmp_path / 'setup.py').write_text('from setuptools import setup\nsetup()')

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        output_dir = tmp_path / ".github" / "workflows"
        result = generate_workflow(
            python_version='3.11',
            base_output_dir=str(output_dir),
            include_release_workflow=False
        )

        assert result['success']
        assert len(result['files_created']) == 1

        # Only publish workflow should exist
        assert (output_dir / 'pypi-publish.yml').exists()
        assert not (output_dir / 'create-release.yml').exists()

    finally:
        os.chdir(original_cwd)
