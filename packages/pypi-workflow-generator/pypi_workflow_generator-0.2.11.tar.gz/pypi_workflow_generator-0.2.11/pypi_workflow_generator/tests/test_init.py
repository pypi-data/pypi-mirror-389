import os
from pypi_workflow_generator.generator import initialize_project

def test_init_project(tmp_path):
    """Test project initialization."""
    # Change the current working directory to the temporary directory
    os.chdir(tmp_path)

    # Run the initialize_project function
    result = initialize_project(package_name='my-package', author='My Name', author_email='my.email@example.com', description='My new package.', url='https://github.com/my-username/my-package', command_name='my-command')

    # Assert the function returned success
    assert result['success']
    assert 'files_created' in result
    assert 'message' in result

    # Assert that the files have been created
    assert os.path.exists('pyproject.toml')
    assert os.path.exists('setup.py')

    # Assert that the contents of the files are correct
    with open('pyproject.toml', 'r') as f:
        pyproject_content = f.read()
    assert "[build-system]" in pyproject_content
    assert "requires = [\"setuptools>=61.0\", \"setuptools_scm[toml]>=6.2\"]" in pyproject_content
    assert "build-backend = \"setuptools.build_meta\"" in pyproject_content
    assert "[tool.setuptools_scm]" in pyproject_content
    assert "version_scheme = \"post-release\"" in pyproject_content

    with open('setup.py', 'r') as f:
        setup_content = f.read()
    assert "name='my-package'," in setup_content
    assert "author='My Name'," in setup_content
    assert "author_email='my.email@example.com'," in setup_content
    assert "description='My new package.'," in setup_content
    assert "url='https://github.com/my-username/my-package'," in setup_content
    assert "'my-command=my-package.main:main'," in setup_content
