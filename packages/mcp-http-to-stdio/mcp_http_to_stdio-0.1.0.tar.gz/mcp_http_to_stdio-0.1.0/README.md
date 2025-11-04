# MCP HTTP-to-STDIO Bridge for Claude Desktop Integration

This Python script enables Claude Desktop to connect to MyAlly's Share Server via the MCP protocol.

## Overview

**Purpose:** Bridge Claude Desktop's stdio-based MCP protocol to MyAlly's HTTP-based Share Server MCP endpoint.

**Architecture:**
```
Claude Desktop (stdio) ←→ mcp_http_to_stdio.py (HTTP) ←→ MyAlly Share Server
```

## Prerequisites

- Python 3.8+
- MyAlly backend running (Share Server must be mounted)
- Valid share key from workspace owner

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install mcp-http-to-stdio
```

This will install the package globally and make the `mcp-http-to-stdio` command available system-wide.

### Option 2: Install from Source

If you're developing or testing:

```bash
git clone https://github.com/your-org/agentic-enterprise.git
cd agentic-enterprise/packages/mcp-http-to-stdio
pip install -e .
```

### Getting a Share Key

1. Ensure MyAlly backend is running:
   ```bash
   cd services/myally
   start_backend.bat  # Windows
   ./start_backend.sh # Linux/macOS
   ```

2. Obtain a share key from the workspace owner:
   - Owner goes to **Settings → Workspace Sharing → Manage Keys**
   - Owner creates a share key for your email
   - Owner reveals and copies the share key (starts with `ally_share_`)

## Configuration for Claude Desktop

### Location of Configuration File

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

### Configuration Format

#### After PyPI Installation (Recommended)

If you installed via `pip install mcp-http-to-stdio`:

```json
{
  "mcpServers": {
    "myally-workspace": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url",
        "http://localhost:8081/share/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "ally_share_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

#### From Source Installation

If you're running from source:

```json
{
  "mcpServers": {
    "myally-workspace": {
      "command": "python",
      "args": [
        "-m",
        "mcp_http_to_stdio",
        "--url",
        "http://localhost:8081/share/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "ally_share_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

**Important:**
- Replace `ally_share_xxx...` in `env.ALLY_SHARE_KEY` with your actual share key
- If Share Server is on a different host/port, update the `--url` parameter
- **Security:** Share key is passed via environment variable (not visible in process list)

### Remote Server Configuration

If MyAlly backend is running on a remote server:

```json
{
  "mcpServers": {
    "myally-remote": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url",
        "https://myally-server.example.com/share/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "ally_share_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

## Usage

After configuring Claude Desktop:

1. **Restart Claude Desktop** to load the new MCP server
2. **Verify connection:** Type in Claude: "What MCP tools are available?"
3. **Use shared workspaces:** Claude will see shared workspaces as tools with names from the `mcp_tool_name` field

### Example Interaction

```
You: What workspaces are shared with me?

Claude: I can see the following shared workspaces via MCP:
- ally_project_alpha: Development workspace for Project Alpha
- ally_docs_team: Team documentation workspace

You: Query the ally_project_alpha workspace: What files are in the project?

Claude: [Uses the ally_project_alpha MCP tool to query the shared workspace]
```

## Conversation Continuity

Each workspace tool maintains conversation history through the `conversation_id` parameter, enabling multi-turn interactions with full context.

### How It Works

**Every response includes the conversation_id in two places:**

1. **In the response text** (at the beginning):
   ```
   <conversationId>conv_abc123...</conversationId>

   [Actual response content here]
   ```

2. **In response metadata** (programmatic access):
   ```json
   {
     "result": {
       "content": [...],
       "_meta": {
         "conversation_id": "conv_abc123...",
         "workspace_id": "ws_xyz...",
         "tool_name": "sales_knowledge"
       }
     }
   }
   ```

### Starting a New Conversation

**Omit the `conversation_id` parameter:**

```json
{
  "name": "sales_knowledge",
  "arguments": {
    "query": "What are our top 5 customers?"
  }
}
```

**Response:**
```
<conversationId>conv_abc123...</conversationId>

Here are the top 5 customers:
1. Acme Corp - $500K
2. TechStart - $350K
...
```

### Continuing a Conversation

**Include the `conversation_id` from the previous response:**

```json
{
  "name": "sales_knowledge",
  "arguments": {
    "query": "Show me details for the top 3",
    "conversation_id": "conv_abc123..."
  }
}
```

**Response:**
```
<conversationId>conv_abc123...</conversationId>

Detailed information for Acme Corp, TechStart, and BlueSky Inc:

Acme Corp:
- Total revenue: $500K
- Contract date: 2024-01-15
...
```

Claude will have full context from the previous query about "top 5 customers" and understand that "the top 3" refers to those customers.

### Example Multi-Turn Conversation

```
User: Ask sales_knowledge: "What accounts did we close last month?"

Claude: [Calls tool with no conversation_id]
Response: <conversationId>conv_abc123...</conversationId>
          We closed 3 accounts last month: Acme Corp, TechStart, BlueSky Inc...

User: "What was the total value?"

Claude: [Calls tool with conversation_id="conv_abc123..."]
Response: <conversationId>conv_abc123...</conversationId>
          The total value of accounts closed last month was $1.2M...

User: "Which one was the largest?"

Claude: [Calls tool with conversation_id="conv_abc123..."]
Response: <conversationId>conv_abc123...</conversationId>
          Acme Corp was the largest at $500K...
```

### Best Practices

- **Extract conversation_id:** Claude should parse the `<conversationId>` tag from each response
- **Reuse for follow-ups:** Pass the same conversation_id for contextual queries
- **Start fresh when needed:** Omit conversation_id for unrelated topics
- **One conversation per topic:** Don't mix unrelated queries in the same conversation
- **Visible in responses:** The XML tag makes the ID clearly visible for debugging

### Error Handling

**Invalid conversation_id format:**
```json
{"error": "Invalid conversation_id format: must start with 'conv_'"}
```

**Conversation not found:**
```json
{"error": "Conversation conv_invalid... not found"}
```

**Wrong workspace:**
```json
{"error": "Conversation conv_xyz... does not belong to workspace 'sales_knowledge'"}
```

### Technical Details

- **Format:** `conv_` followed by UUID (e.g., `conv_f47ac10b-58cc-4372-a567-0e02b2c3d479`)
- **Validation:** Server validates format, existence, and workspace ownership
- **SDK Sessions:** Backend automatically maintains Claude SDK session_id for conversation history
- **Cross-workspace:** conversation_ids are workspace-specific (can't use across different tools)

## Command Line Arguments

```bash
python mcp_http_to_stdio.py --help
```

**Arguments:**
- `--share-key` (required): Your share key for authentication
- `--url` (optional): Share Server MCP endpoint URL (default: `http://localhost:8081/share/mcp`)
- `--timeout` (optional): Request timeout in seconds (default: 300)

## Logging

Logs are written to two locations:
1. **File:** `mcp_http_to_stdio.log` (in the same directory as the script)
2. **stderr:** Visible in Claude Desktop's developer console

### Viewing Logs

**During development:**
```bash
tail -f mcp_http_to_stdio.log
```

**In Claude Desktop:**
- Enable developer mode in settings
- Open developer console
- Look for MCP-related messages

## Troubleshooting

### Issue: "Invalid or expired share key"

**Cause:** Share key is incorrect, expired, or deleted

**Solution:**
1. Verify share key is correct (starts with `ally_share_`)
2. Ask workspace owner to regenerate key if expired
3. Check backend logs: `services/myally/dist/logs/backend.log`

### Issue: "Connection refused" or "Failed to connect"

**Cause:** MyAlly backend is not running or URL is incorrect

**Solution:**
1. Verify backend is running: `curl http://localhost:8080/api/v1/health` (main backend)
2. Verify Share Server is running: `curl http://localhost:8081/share/health`
2. Check Share Server status in UI: **Settings → Workspace Sharing → Server Status**
3. Verify URL in configuration matches backend location

### Issue: "Tool not found" or "No shared workspaces"

**Cause:** No workspaces are shared with your user, or workspace sharing is not enabled

**Solution:**
1. Ask workspace owner to share workspace with your email
2. Verify owner enabled sharing: **Settings → Workspace Sharing → Share Workspace** (toggle ON)
3. Verify owner granted you access: **Settings → Workspace Sharing → Manage Access** (your email checked)

### Issue: Claude Desktop doesn't see the MCP server

**Cause:** Configuration file is malformed or in wrong location

**Solution:**
1. Verify JSON syntax is valid (use https://jsonlint.com)
2. Check file location matches your OS
3. Restart Claude Desktop after configuration changes
4. Check Claude Desktop logs for MCP initialization errors

## Security Notes

- **Share keys are sensitive:** Treat them like passwords
- **Do not commit share keys** to version control
- **Rotate share keys regularly:** Owner can delete and regenerate in UI
- **Rate limiting:** 10 failed authentication attempts = 30-minute IP ban
- **Encryption:** Share keys are bcrypt-hashed in backend database

## Advanced Configuration

### Multiple Workspaces from Different Owners

You can add multiple MCP servers, one per share key:

```json
{
  "mcpServers": {
    "myally-project-alpha": {
      "command": "python",
      "args": [
        "/path/to/mcp_http_to_stdio.py",
        "--share-key", "ally_share_key_from_owner_1",
        "--url", "http://localhost:8080/share/mcp"
      ]
    },
    "myally-docs-team": {
      "command": "python",
      "args": [
        "/path/to/mcp_http_to_stdio.py",
        "--share-key", "ally_share_key_from_owner_2",
        "--url", "http://localhost:8080/share/mcp"
      ]
    }
  }
}
```

### Performance Configuration

#### Custom Timeout

Default timeout is 5 minutes (300 seconds). To customize, add the `--timeout` parameter:

```json
{
  "mcpServers": {
    "myally-workspace": {
      "command": "python",
      "args": [
        "/path/to/mcp_http_to_stdio.py",
        "--share-key", "ally_share_xxx...",
        "--url", "http://localhost:8081/share/mcp",
        "--timeout", "600"
      ]
    }
  }
}
```

**Timeout parameter:**
- `--timeout` (optional): Request timeout in seconds (default: 300)
- Increase for complex queries that require extensive tool usage
- Decrease for simple queries if you want faster failure detection

#### Connection Pooling

The wrapper automatically configures optimized connection pooling:

**Features:**
- **Keep-alive:** HTTP connections are reused between requests
- **Retry logic:** Automatic retry on transient errors (429, 500-504) with exponential backoff
- **Connection pool:** 10 cached connections to prevent reconnection overhead
- **Performance:** Reduces "Resetting dropped connection" messages

**Connection Pool Configuration:**
- Max retries: 3 attempts
- Backoff factor: 1 second (1s, 2s, 4s delays)
- Pool size: 10 connections
- Keep-alive: Enabled by default

These settings are optimized for typical workspace query patterns and do not require tuning.

## Technical Details

### Protocol Flow

1. **Claude Desktop sends JSON-RPC request** via stdin:
   ```json
   {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
   ```

2. **Wrapper forwards to Share Server** via HTTP POST:
   ```http
   POST /share/mcp HTTP/1.1
   Host: localhost:8081
   x-ally-share-key: ally_share_xxx...
   Content-Type: application/json

   {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
   ```

3. **Share Server authenticates and processes:**
   - Validates share key (bcrypt comparison)
   - Returns list of accessible workspaces as MCP tools

4. **Wrapper returns response** via stdout:
   ```json
   {
     "jsonrpc": "2.0",
     "result": {
       "tools": [
         {
           "name": "ally_project_alpha",
           "description": "Development workspace for Project Alpha",
           ...
         }
       ]
     },
     "id": 1
   }
   ```

### Supported MCP Methods

1. **`tools/list`**: Discover shared workspaces as tools
2. **`tools/call`**: Execute query against shared workspace (buffered response)

### Performance Characteristics

**Typical Response Times:**
- `initialize`: <100ms (protocol handshake)
- `tools/list`: <500ms (database query)
- `tools/call`: 10-60 seconds (agent execution + tool usage)

**Why tool calls are slow:**

The `tools/call` method executes a full agent query in the shared workspace:

```
Claude Desktop → Wrapper → Share Server → Agent Queue → Worker → Claude API
                                                          ↓
                                                     Tool Execution
                                                     (directory_tree, read_files, etc.)
                                                          ↓
                                                     Multiple Turns
                                                     (reasoning + tool usage)
```

**Factors affecting execution time:**
1. **Query complexity:** Simple info retrieval vs. multi-step reasoning
2. **Tool usage:** Number and type of tools invoked by agent
3. **Workspace size:** Large codebases take longer to index/search
4. **API latency:** Network latency to Anthropic API
5. **Max turns:** Higher `max_turns` parameter allows more reasoning cycles

**Expected behavior:**
- ✅ 10-30 seconds: Normal for typical workspace queries
- ⚠️ 30-60 seconds: Expected for complex multi-tool queries
- ❌ 60+ seconds: Consider reducing `max_turns` or simplifying query

**Performance logging:**

The wrapper logs timing information for monitoring:
```
2025-10-30 17:50:52 - INFO - Executing tool call: sales_knowledge
2025-10-30 17:51:20 - INFO - Request completed in 28.45s
2025-10-30 17:51:20 - WARNING - Slow request detected (28.45s) - this is expected for complex agent queries
```

**Connection stability:**

The wrapper uses persistent HTTP connections with keep-alive. You may see these debug messages:
```
DEBUG - Resetting dropped connection: localhost
```

This is **normal behavior** - urllib3 is simply re-establishing an idle connection. The wrapper's connection pooling ensures minimal overhead.

### Authentication Flow

```
1. Client includes x-ally-share-key header
2. Share Server validates key:
   - Checks if key exists in database
   - Verifies bcrypt hash matches
   - Checks if key is revoked
3. If valid: Execute query as workspace owner (impersonation)
4. If invalid: Return 401 error + increment rate limit counter
```

## Related Documentation

- **Share Server Overview:** `REQUIREMENTS/WORKSPACE-remote.md`
- **Implementation Guide:** `REQUIREMENTS/WORKSPACE-remote-implementation-steps.md`
- **Backend Architecture:** `services/myally/README.md`
- **Share Server Code:** `services/myally/app/workspace_share_server/`

## Support

For issues or questions:
1. Check backend logs: `services/myally/dist/logs/backend.log`
2. Check wrapper logs: `mcp_http_to_stdio.log`
3. Review Share Server status in MyAlly UI
4. Open GitHub issue with logs and configuration (redact share keys!)
