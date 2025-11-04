# pypi-workflow-generator

A dual-mode tool (MCP server + CLI) for generating GitHub Actions workflows for Python package publishing to PyPI.

## Features

- ✅ **Dual-Mode Operation**: Works as MCP server for AI agents OR traditional CLI for developers
- ✅ **PyPI Trusted Publishers**: Secure publishing without API tokens
- ✅ **Automated Versioning**: Uses setuptools_scm for git-based versioning
- ✅ **Pre-release Testing**: Automatic TestPyPI publishing on pull requests
- ✅ **Production Publishing**: Automatic PyPI publishing on version tags
- ✅ **Complete Project Initialization**: Generates pyproject.toml and setup.py
- ✅ **Release Management**: Simple git tag creation for triggering releases

## Installation

```bash
pip install pypi-workflow-generator
```

## Usage

This package can be used in three ways:

### 1. MCP Mode (For AI Agents)

For AI agents with MCP support (Claude Code, Continue.dev, Cline):

**Add to `claude_desktop_config.json` or `claude_config.json`**:
```json
{
  "mcpServers": {
    "pypi-workflow-generator": {
      "command": "mcp-pypi-workflow-generator"
    }
  }
}
```

The agent can now use these tools:
- `generate_workflow` - Generate GitHub Actions workflows (both publishing and release)
- `generate_release_workflow` - Generate only the release creation workflow **NEW!**
- `initialize_project` - Create pyproject.toml and setup.py
- `create_release` - Create and push git release tags

**Example conversation**:
```
You: "Please set up a PyPI publishing workflow for my Python project"

Claude: I'll help you set up a complete PyPI publishing workflow.

[Calls initialize_project and generate_workflow tools]

✅ Created:
  - pyproject.toml
  - setup.py
  - .github/workflows/pypi-publish.yml

Next steps:
1. Configure Trusted Publishers on PyPI
2. Create a release: pypi-release patch
```

### 2. CLI Mode (For Developers)

**Initialize a new project**:
```bash
pypi-workflow-generator-init \
  --package-name my-awesome-package \
  --author "Your Name" \
  --author-email "your.email@example.com" \
  --description "My awesome Python package" \
  --url "https://github.com/username/my-awesome-package" \
  --command-name my-command
```

**Generate workflow**:
```bash
pypi-workflow-generator --python-version 3.11
```

**Create a release**:
```bash
pypi-release patch  # or 'minor' or 'major'
```

### 3. Programmatic Use

```python
from pypi_workflow_generator import generate_workflow, initialize_project

# Initialize project
initialize_project(
    package_name="my-package",
    author="Your Name",
    author_email="your@email.com",
    description="My package",
    url="https://github.com/user/repo",
    command_name="my-cmd"
)

# Generate workflow
generate_workflow(
    python_version="3.11",
    release_on_main_push=False
)
```

## Generated Workflows

This tool now generates **TWO** GitHub Actions workflows by default:

### 1. PyPI Publishing Workflow (`pypi-publish.yml`)

Handles automated package publishing:

- **Automated Testing**: Runs pytest on every PR and release
- **Pre-release Publishing**: TestPyPI publishing on PRs with version like `1.0.0.dev123`
- **Production Publishing**: PyPI publishing on version tags
- **Trusted Publishers**: No API tokens needed (OIDC authentication)
- **setuptools_scm**: Automatic versioning from git tags

### 2. Release Creation Workflow (`create-release.yml`) **NEW!**

Enables manual release creation via GitHub UI:

- **Manual Trigger**: Click a button in GitHub Actions to create releases
- **Automatic Version Calculation**: Choose major/minor/patch, version is calculated automatically
- **Git Tag Creation**: Creates and pushes version tags
- **GitHub Releases**: Auto-generates release notes from commits
- **Triggers Publishing**: Tag push automatically triggers the PyPI publish workflow

## Creating Releases

You have **two ways** to create releases:

### Option 1: GitHub Actions UI (Recommended) **NEW!**

**Prerequisites**: Create a `RELEASE_PAT` secret (see [Setting Up Automated Release Publishing](#setting-up-automated-release-publishing))

1. Go to **Actions** tab in your repository
2. Select **Create Release** workflow
3. Click **Run workflow**
4. Choose release type:
   - **patch**: Bug fixes (0.1.0 → 0.1.1)
   - **minor**: New features (0.1.1 → 0.2.0)
   - **major**: Breaking changes (0.2.0 → 1.0.0)
5. (Optional) Specify custom token secret name if not using `RELEASE_PAT`
6. Click **Run workflow**

The workflow will:
- Calculate the next version number
- Create and push a git tag
- Create a GitHub Release with auto-generated notes
- **Automatically trigger the PyPI publish workflow** (requires RELEASE_PAT)
- Publish your package to PyPI

**Benefits**: Works from anywhere, full automation, easy for AI agents to use.

### Option 2: CLI (Local)

```bash
pypi-release patch  # or minor, major
```

This creates and pushes the tag locally, which triggers the publish workflow.

## Workflow Generation Options

```bash
# Generate both workflows (default)
pypi-workflow-generator --python-version 3.11

# Generate only PyPI publishing workflow
pypi-workflow-generator --skip-release-workflow

# Generate only release creation workflow
pypi-workflow-generator-release
```

## Setting Up Trusted Publishers

The generated GitHub Actions workflow (`pypi-publish.yml`) utilizes [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/) for secure package publishing. This method enhances security by allowing your GitHub Actions workflow to authenticate with PyPI using OpenID Connect (OIDC) instead of requiring you to store sensitive API tokens as GitHub secrets.

**Why Trusted Publishers?**
- **Enhanced Security:** Eliminates the need to store PyPI API tokens, reducing the risk of token compromise.
- **Best Practice:** Recommended by PyPI for publishing from automated environments like GitHub Actions.

**How to Set Up Trusted Publishers for Your Project:**

Before your workflow can successfully publish to PyPI or TestPyPI, you must configure Trusted Publishers for your project on the respective PyPI instance.

1. **Log in to PyPI/TestPyPI:**
   - For TestPyPI: Go to `https://test.pypi.org/` and log in.
   - For official PyPI: Go to `https://pypi.org/` and log in.

2. **Navigate to Your Project's Publishing Settings:**
   - Go to your project's management page. The URL will typically look like:
     `https://[test.]pypi.org/manage/project/<your-package-name>/settings/publishing/`
   - Replace `<your-package-name>` with the actual name of your Python package (e.g., `pypi-workflow-generator`).

3. **Add a New Trusted Publisher:**
   - Click on the "Add a new publisher" button.
   - Select "GitHub Actions" as the publisher type.
   - Provide the following details:
     - **Owner:** The GitHub username or organization that owns your repository (e.g., `hitoshura25`).
     - **Repository:** The name of your GitHub repository (e.g., `pypi-workflow-generator`).
     - **Workflow Name:** The name of your workflow file (e.g., `pypi-publish.yml`).
     - **Environment (Optional):** If your GitHub Actions workflow uses a specific environment, specify its name here. Otherwise, leave it blank.

4. **Save the Publisher:** Confirm and save the new publisher.

Once configured, your GitHub Actions workflow will be able to publish packages without needing `PYPI_API_TOKEN` or `TEST_PYPI_API_TOKEN` secrets.

## Setting Up Automated Release Publishing

### Why You Need a Personal Access Token

GitHub Actions workflows triggered by the default `GITHUB_TOKEN` cannot trigger other workflows (security feature to prevent infinite loops). To enable the `create-release.yml` workflow to automatically trigger `pypi-publish.yml` after creating a release tag, you need to provide a Personal Access Token (PAT) with appropriate permissions.

**Without a PAT:** The create-release workflow will successfully create tags and GitHub Releases, but the PyPI publish workflow won't trigger automatically. You would need to manually trigger it.

**With a PAT:** Full automation - create a release via GitHub UI, and your package automatically publishes to PyPI.

### Creating the Required PAT

1. **Generate a Personal Access Token**:
   - Go to GitHub Settings → Developer settings → [Personal access tokens → Tokens (classic)](https://github.com/settings/tokens/new)
   - Click "Generate new token (classic)"
   - Give it a descriptive name: `Release Automation Token for <repo-name>`
   - Set expiration (recommended: 1 year, with calendar reminder to rotate)
   - Select scope: **repo** (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again)

2. **Add Token to Repository Secrets**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `RELEASE_PAT`
   - Value: Paste the token you copied
   - Click "Add secret"

3. **Verify Setup**:
   - Go to Actions tab → Create Release workflow → Run workflow
   - Select release type (patch/minor/major)
   - Leave token secret name as default (`RELEASE_PAT`)
   - The workflow should complete successfully
   - The PyPI publish workflow should trigger automatically
   - Your package should be published to PyPI

### Using a Custom Token Name (Optional)

If your organization uses a different secret name (e.g., `GITHUB_ORG_TOKEN`), you can specify it when running the workflow:

1. Go to Actions → Create Release
2. Click "Run workflow"
3. Fill in:
   - **Release type**: patch/minor/major
   - **Token secret name**: `GITHUB_ORG_TOKEN` (or your custom name)

### Security Considerations

- **Token Scope**: The PAT needs `repo` scope to push tags and trigger workflows
- **Token Rotation**: Set expiration dates and rotate tokens regularly (recommended: annually)
- **Access Control**: Only repository admins can add/view secrets
- **Audit Trail**: GitHub logs all token usage in the repository audit log

### Troubleshooting

**Workflow fails with "Secret 'RELEASE_PAT' not found"**
- You haven't created the PAT or added it to repository secrets
- Follow the steps above to create and add the token

**PyPI publish workflow still doesn't trigger**
- Verify the PAT has `repo` scope (not just `public_repo`)
- Check that the token hasn't expired
- Ensure the token is added to repository secrets (not environment secrets)

**Alternative: Use CLI Method**

If you prefer not to set up a PAT, you can create releases locally using the CLI:
```bash
pypi-release patch  # This runs on your machine, no PAT needed
```
The CLI method pushes tags from your local machine, which doesn't have the GitHub Actions token limitation.

## CLI Options

### `pypi-workflow-generator`

Generate GitHub Actions workflows for PyPI publishing (generates both workflows by default).

```
Options:
  --python-version VERSION    Python version (default: 3.11)
  --output-filename NAME      Workflow filename (default: pypi-publish.yml)
  --release-on-main-push      Trigger release on main branch push
  --test-path PATH            Path to tests (default: .)
  --verbose-publish           Enable verbose publishing
  --skip-release-workflow     Only generate pypi-publish.yml (skip create-release.yml)
```

### `pypi-workflow-generator-init`

Initialize a new Python project with PyPI configuration.

```
Options:
  --package-name NAME         Package name (required)
  --author NAME               Author name (required)
  --author-email EMAIL        Author email (required)
  --description TEXT          Package description (required)
  --url URL                   Project URL (required)
  --command-name NAME         CLI command name (required)
```

### `pypi-release`

Create and push a git release tag (local CLI method).

```
Usage:
  pypi-release {major,minor,patch} [--overwrite]

Arguments:
  {major,minor,patch}  The type of release (major, minor, or patch)

Options:
  --overwrite          Overwrite an existing tag
```

**Note**: The CLI uses semantic versioning (major/minor/patch) for convenience. The MCP tool `create_release` accepts explicit version strings (e.g., "v1.0.0") for flexibility. See [Interface Differences](#interface-differences) below.

### `pypi-workflow-generator-release` **NEW!**

Generate only the release creation workflow.

```
Options:
  --output-filename NAME      Workflow filename (default: create-release.yml)
```

Use this if you already have a PyPI publishing workflow and only want to add the release creation workflow.

## MCP Server Details

The MCP server runs via stdio transport and provides four tools:

**Tool: `generate_workflow`**
- Generates GitHub Actions workflow files (both publishing and release by default)
- Parameters: python_version, output_filename, release_on_main_push, test_path, verbose_publish, include_release_workflow

**Tool: `generate_release_workflow`** **NEW!**
- Generates only the release creation workflow
- Parameters: output_filename

**Tool: `initialize_project`**
- Creates pyproject.toml and setup.py
- Parameters: package_name, author, author_email, description, url, command_name

**Tool: `create_release`**
- Creates and pushes git tag
- Parameters: version

See [MCP-USAGE.md](./MCP-USAGE.md) for detailed MCP configuration and usage.

## Interface Differences

The package provides two interfaces with slightly different APIs for different use cases:

### CLI vs MCP: Release Creation

**CLI Mode** (`pypi-release`):
- Uses semantic versioning keywords: `major`, `minor`, `patch`
- Automatically increments version from latest git tag
- Convenience for developers who want simple versioning

```bash
pypi-release patch      # Creates v1.0.1 (if current is v1.0.0)
pypi-release minor      # Creates v1.1.0
pypi-release major      # Creates v2.0.0
```

**MCP Mode** (`create_release` tool):
- Accepts explicit version strings: `v1.0.0`, `v2.5.3`, etc.
- Direct control over version numbers
- Flexibility for AI agents to determine versions programmatically

```json
{
  "version": "v1.0.0"
}
```

**Why the difference?** The CLI optimizes for human convenience (automatic incrementing), while MCP optimizes for programmatic control (explicit versions).

### Entry Point Naming Convention

The MCP server uses the `mcp-` prefix (industry standard for MCP tools):
- `mcp-pypi-workflow-generator` - Follows MCP ecosystem naming
- Makes it discoverable when searching for MCP servers
- Clearly distinguishes server mode from CLI mode

All other commands use the `pypi-` prefix for CLI operations:
- `pypi-workflow-generator`
- `pypi-workflow-generator-init`
- `pypi-release`

## Architecture

```
User/AI Agent
      │
      ├─── MCP Mode ────────> server.py (MCP protocol)
      │                           │
      ├─── CLI Mode ────────> main.py / init.py / create_release.py
      │                           │
      └─── Programmatic ────> __init__.py
                                  │
                    All modes use shared core:
                                  ▼
                            generator.py
                      (Business logic)
```

## Dogfooding

This project uses itself to generate its own GitHub Actions workflows! The workflow files at:
- `.github/workflows/pypi-publish.yml`
- `.github/workflows/create-release.yml`

Were both created by running:

```bash
pypi-workflow-generator \
  --python-version 3.11 \
  --test-path pypi_workflow_generator/ \
  --verbose-publish
```

This ensures:
- ✅ The tool actually works (we use it ourselves)
- ✅ Both workflows are tested in production
- ✅ The templates stay consistent with real-world usage
- ✅ We practice what we preach
- ✅ Users can see real examples of the generated output

Check the workflow file headers to see the exact command used. Try creating a release using the GitHub Actions UI!

## Development

```bash
# Clone repository
git clone https://github.com/hitoshura25/pypi-workflow-generator.git
cd pypi-workflow-generator

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Build package
python -m build
```

## Contributing

Contributions welcome! Please open an issue or PR.

## License

Apache-2.0

## Links

- **Repository**: https://github.com/hitoshura25/pypi-workflow-generator
- **Issues**: https://github.com/hitoshura25/pypi-workflow-generator/issues
- **PyPI**: https://pypi.org/project/pypi-workflow-generator/
