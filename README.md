# MCP SQL Agent
- **Reference:**
    - https://www.youtube.com/watch?v=cxl3tPWLOQ8
    - https://github.com/bitswired/demos/tree/main/projects/introduction-to-mcp-with-sql-agent

# Python Package Manager (UV)
- `uv init`: start project
- `uv python pin 3.12.0`: set python version
    - `requires-python` in **pyproject.toml**: Declares the minimum or exact Python version
    - `.python-version`: Define Python version to use for the project.
- `uv add <LIBRARY-NAME>`: To add python library to `pyproject.toml` and `uv.lock`
- `uv remove <LIBRARY-NAME>`: To remove python library from `pyproject.toml` and `uv.lock`
- `uv sync`: installs dependencies from `uv.lock`
- `uv lock`: run only if manually edit `pyproject.toml`, it will regenerate `uv.lock` based on `pyproject.toml`
- `uv pip list`: to list down all python packages