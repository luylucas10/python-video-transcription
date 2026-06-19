## ADDED Requirements

### Requirement: Project uses uv-managed Python
The project SHALL use uv as the documented dependency, environment, lockfile, and execution workflow.

#### Scenario: Recreate project environment
- **WHEN** a developer follows the setup instructions on Windows
- **THEN** the project creates or recreates `.venv` using uv and installs dependencies from project metadata and lockfile

#### Scenario: Run application through uv
- **WHEN** a developer runs the documented command
- **THEN** the application starts through `uv run` and executes the Python module or console script without requiring manual activation

### Requirement: Project pins a compatible Python version
The project SHALL document and pin a Python version compatible with the implementation and dependencies.

#### Scenario: Python version selected
- **WHEN** the environment is recreated
- **THEN** uv uses the pinned Python version for `.venv`

### Requirement: Executable packaging is unsupported
The project SHALL remove PyInstaller and build-to-exe instructions from the supported workflow.

#### Scenario: Install dev dependencies
- **WHEN** development dependencies are installed
- **THEN** PyInstaller is not installed as a required development dependency

#### Scenario: Read setup documentation
- **WHEN** a user reads the README
- **THEN** the documented run path uses Python and uv rather than a generated executable
