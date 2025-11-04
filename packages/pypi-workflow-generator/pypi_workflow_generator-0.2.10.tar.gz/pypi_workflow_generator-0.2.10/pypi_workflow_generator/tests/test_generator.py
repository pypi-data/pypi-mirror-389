from pypi_workflow_generator.generator import generate_workflow

def test_generate_workflow_default_arguments(tmp_path):
    """Test workflow generation with default arguments."""
    output_dir = tmp_path / ".github" / "workflows"
    result = generate_workflow(python_version='3.11', output_filename='pypi-publish.yml', release_on_main_push=False, test_path='.', base_output_dir=output_dir, verbose_publish=False)

    assert result['success']
    assert 'file_path' in result
    assert 'message' in result

    output_file = output_dir / 'pypi-publish.yml'
    assert output_file.exists()

    with open(output_file, 'r') as f:
        content = f.read()

    assert "python-version: '3.11'" in content
    assert "tags:" in content
    assert "- 'v*.*.*'" in content
    assert "if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')" in content
    assert "run: python -m pytest ." in content


def test_generate_workflow_custom_arguments(tmp_path):
    """Test workflow generation with custom arguments."""
    output_dir = tmp_path / ".github" / "workflows"
    result = generate_workflow(python_version='3.9', output_filename='custom-pypi-publish.yml', release_on_main_push=True, test_path='tests', base_output_dir=output_dir, verbose_publish=True)

    assert result['success']
    assert 'file_path' in result
    assert 'message' in result

    output_file = output_dir / 'custom-pypi-publish.yml'
    assert output_file.exists()

    with open(output_file, 'r') as f:
        content = f.read()

    assert "python-version: '3.9'" in content
    assert "branches: [ main ]" in content
    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in content
    assert "run: python -m pytest tests" in content
    assert "verbose: true" in content