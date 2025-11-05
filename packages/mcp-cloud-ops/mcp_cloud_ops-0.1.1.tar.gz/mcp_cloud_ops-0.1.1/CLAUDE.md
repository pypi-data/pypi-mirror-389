# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides read-only, security-hardened wrappers around cloud CLI tools. The server exposes four tools: `aws`, `kubectl`, `helm`, and `search_context`. Each tool enforces read-only operations and requires explicit context/profile specification to prevent accidental operations on wrong environments.

## Architecture

### Core Security Model

The server implements defense-in-depth for safe cloud operations:

1. **Command Validation** (src/cloud_ops/server.py:63-92): `_validate_and_run()` parses commands, validates allowed verbs, and blocks disallowed options before execution
2. **Context Enforcement**: Each tool requires explicit context identification:
   - AWS commands require `--profile` flag
   - kubectl commands require `--context` flag
   - Helm commands require `--kube-context` flag
3. **Read-Only Verbs**: Each tool whitelists only safe, read-only operations (e.g., `get`, `describe`, `list` but never `delete`, `apply`, `create`)

### Tool Implementations

All four tools follow the same pattern defined in `create_server()`:

- **aws** (server.py:98): Enforces `--profile` requirement, allows read operations like describe/get/list, validates at index 1 (after service name)
- **kubectl** (server.py:119): Enforces `--context` requirement, blocks credential flags (`--kubeconfig`, `--as`, `--token`), validates at index 0
- **helm** (server.py:135): Enforces `--kube-context` requirement, allows inspection commands (get/list/status), validates at index 0
- **search_context** (server.py:151): Searches AWS profiles and kubectl contexts by substring, returns matching profiles with regions and EKS cluster ARNs

### Command Parsing

The `_parse_command()` function (server.py:42-60) splits shell commands on operators (`|`, `&&`, `||`, `;`) to validate each command in a pipeline separately. This prevents bypassing validation via command chaining.

## Development Commands

### Running the Server

```bash
# Direct execution
python -m src.cloud_ops.server

# Or using the installed script (after pip install)
mcp-cloud-ops
```

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests with coverage (when tests are added)
pytest

# Run specific test file
pytest tests/test_server.py

# Type checking
mypy src/cloud_ops/

# Linting
ruff check src/
```

## Key Implementation Details

### Proxy Support

The `configure_proxy_session()` function (server.py:23-39) respects HTTP_PROXY, HTTPS_PROXY, and NO_PROXY environment variables for corporate proxy environments.

### Command Index Parameter

The `cmd_index` parameter in `_validate_and_run()` accounts for different CLI structures:
- AWS CLI: `aws <service> <verb>` → cmd_index=1 (validate after service)
- kubectl/helm: `kubectl <verb>` → cmd_index=0 (validate immediately)

### Error Handling

Commands returning non-zero exit codes return structured error messages. Empty stdout with success is treated as successful execution.

## Environment Requirements

- Python ≥3.12
- External CLIs must be installed and in PATH: `aws`, `kubectl`, `helm`
- AWS profiles must be configured in ~/.aws/config
- kubectl contexts must be configured in ~/.kube/config
