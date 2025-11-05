# Acemcp

MCP server for codebase indexing and semantic search.

## Installation

```bash
uv add mcp httpx fastapi "uvicorn[standard]" toml websockets
uv sync
```

## Configuration

1. Copy the example secrets file:
```bash
cp .secrets.toml.example .secrets.toml
```

2. Edit `.secrets.toml` with your API credentials:
```toml
[default]
BASE_URL = "https://your-api-endpoint.com"
TOKEN = "your-bearer-token-here"
```

3. (Optional) Customize `settings.toml` for other configurations.

## MCP Configuration

Add the following to your MCP client configuration (e.g., Claude Desktop):

### Basic Configuration

```json
{
  "mcpServers": {
    "acemcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/acemcp",
        "run",
        "acemcp"
      ]
    }
  }
}
```

Replace `/path/to/acemcp` with the actual path to this project.

### Configuration with Command Line Arguments

You can override configuration values using command line arguments:

```json
{
  "mcpServers": {
    "acemcp": {
      "command": "uvx",
      "args": [
        "acemcp",
        "--web-port",
        "8888"
      ]
    }
  }
}
```

**Available command line arguments:**
- `--base-url`: Override BASE_URL configuration
- `--token`: Override TOKEN configuration
- `--index-storage-path`: Override INDEX_STORAGE_PATH configuration
- `--web-port`: Enable web management interface on specified port (e.g., 8080)

### Configuration with Web Management Interface

To enable the web management interface, add the `--web-port` argument:

```json
{
  "mcpServers": {
    "acemcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/acemcp",
        "run",
        "acemcp",
        "--web-port",
        "8080"
      ]
    }
  }
}
```

Then access the management interface at `http://localhost:8080`

## Tools

### index_code

Index a code project for semantic search.

**Parameters:**
- `project_id` (string): Unique identifier for the project
- `project_root_path` (string): Root path of the project to index

**Example:**
```json
{
  "project_id": "my-project",
  "project_root_path": "/path/to/project"
}
```

### search_context

Search for relevant code context based on a query.

**Parameters:**
- `project_id` (string): Project identifier to search within
- `query` (string): Search query string

**Example:**
```json
{
  "project_id": "my-project",
  "query": "How is authentication implemented?"
}
```

## Usage

1. Start the MCP server (automatically started by MCP client)
2. Use `index_code` to index your project
3. Use `search_context` to search for code context

## Data Storage

Indexed project data is stored in `.acemcp_index/projects.json` (configurable via `INDEX_STORAGE_PATH`).

## Web Management Interface

The web management interface provides:
- **Real-time server status** monitoring
- **Live log streaming** via WebSocket
- **Configuration viewing** (current settings)
- **Project statistics** (number of indexed projects)

To enable the web interface, use the `--web-port` argument when starting the server.

**Features:**
- Real-time log display with auto-scroll
- Server status and metrics
- Configuration overview
- Responsive design with Tailwind CSS
- No build step required (uses CDN resources)
