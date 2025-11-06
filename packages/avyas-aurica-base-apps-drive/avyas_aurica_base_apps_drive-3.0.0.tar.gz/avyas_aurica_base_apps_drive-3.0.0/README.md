# Drive - Global Storage Service

Universal storage API that manages local machine storage and provides API access to app and user data.

## Overview

Drive is the **local storage manager** for the Aurica platform. It manages the file system on the local machine and provides API-based access to storage:

- **Local Storage Management**: Manages physical storage on the execution node (local machine)
- **API Access**: Apps access storage through Drive's HTTP APIs, not direct file access
- **Isolated Storage**: Each app can only access its own `data/` directory through the API
- **Unified Interface**: Simple read/write operations for all apps via HTTP or StorageClient
- **Code Access**: Read-only API access to project source code
- **User Data**: Stores user-specific data (conversations, DT state, etc.) locally

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Apps (chat-app, etc)                │
│              Access storage via APIs                  │
└──────────────────────────────────────────────────────┘
                        ↓ HTTP/StorageClient
┌──────────────────────────────────────────────────────┐
│              Drive Storage API (HTTP)                 │
│           Manages Local Machine Storage               │
└──────────────────────────────────────────────────────┘
                        ↓ File System Operations
┌──────────────────────────────────────────────────────┐
│          Local File System (Execution Node)           │
│                                                       │
│  code/data/                 - Centralized user data   │
│    chat-app/               - Chat conversations       │
│    digital-twin/           - DT state                 │
│    {app}/                  - Other app data           │
│                                                        │
│  code/apps/                - Application code         │
│    chat-app/be, fe/        - (read-only via API)      │
│    drive/                  - Storage manager          │
└──────────────────────────────────────────────────────┘
```

**Key Principles:**
1. **Drive owns the storage**: Only Drive directly accesses the file system
2. **Apps use APIs**: Apps access their data through Drive's HTTP APIs
3. **StorageClient wraps APIs**: Python apps use StorageClient for convenience
4. **Local machine storage**: All data stored on the execution node locally
5. **Apps cannot write directly**: No app writes files directly - all go through Drive

## Storage Client

Apps use the `StorageClient` class to access their data via Drive's HTTP APIs:

```python
from storage_client import StorageClient

# Initialize client for your app
storage = StorageClient("chat-app")

# StorageClient makes HTTP calls to Drive API internally
# All operations go through Drive - no direct file access

# Read/write JSON
data = storage.read_json("settings.json")  # GET /drive/api/read
storage.write_json("settings.json", {"theme": "dark"})  # POST /drive/api/write

# Read/write text
content = storage.read("notes.txt")  # GET /drive/api/read
storage.write("notes.txt", "Hello world")  # POST /drive/api/write

# List files
files = storage.list("")  # GET /drive/api/list
files = storage.list("subfolder")

# Delete files
storage.delete("temp.json")  # DELETE /drive/api/delete

# Create directories
storage.create_dir("subfolder")  # POST /drive/api/create-dir

# Check existence
if storage.exists("config.json"):
    config = storage.read_json("config.json")
```

## Features

- **Local Storage Management**: Manages physical storage on the execution node
- **API-Based Access**: All apps access storage through HTTP APIs (no direct file access)
- **Data Separation**: Each app has its own isolated data directory
- **File Operations**: List, read, write, delete files via API
- **Directory Management**: Create and manage directories via API
- **Project Code Access**: Read-only API access to project source code
- **Safe Operations**: Path validation and security checks at the API level
- **Storage Client**: Convenient Python wrapper around HTTP APIs

## API Endpoints

### File Operations
- `GET /api/list` - List files/directories in a path
- `GET /api/read` - Read file contents
- `POST /api/write` - Write to a file
- `DELETE /api/delete` - Delete a file
- `POST /api/create-dir` - Create a directory

### Project Access
- `GET /api/list-apps` - List all available apps
- `GET /api/read-code` - Read source code files (read-only)
- `GET /api/stats` - Get storage statistics

## Storage Structure

```
code/
  apps/              # Application code (read-only via Drive API)
    chat-app/
      be/
      fe/
    digital-twin/
      be/
    drive/           # Drive app manages all storage
      be/
  
  data/              # Centralized user data (managed by Drive)
    chat-app/
      chat/
        conversations.json
        messages/
    digital-twin/
      states/
        dt_{user_id}.json
```

**Key Points:**
- `data/` is a sibling to `apps/` at the project root level
- Drive app has full filesystem access to manage `data/`
- Apps access their data via Drive APIs (never directly)
- Each app has its own subdirectory in `data/{app-name}/`

## Usage Examples

### From Another App (Python)

```python
# Import the storage client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "drive" / "be" / "api"))
from storage_client import StorageClient

# Initialize for your app
storage = StorageClient("my-app")

# Read settings
settings = storage.read_json("settings.json") or {"default": True}

# Write data
storage.write_json("user_data.json", {"users": []})

# List files
files = storage.list("")
for file in files:
    print(f"{file['name']}: {file['size']} bytes")
```

### Via HTTP API

```bash
# List files in chat-app data directory
curl http://localhost:8000/drive/api/list?path=chat-app/chat

# Read a file
curl http://localhost:8000/drive/api/read?path=chat-app/chat/conversations.json

# Write a file
curl -X POST http://localhost:8000/drive/api/write \
  -H "Content-Type: application/json" \
  -d '{
    "path": "chat-app/settings.json",
    "content": "{\"theme\": \"dark\"}"
  }'

# Read project code (read-only)
curl http://localhost:8000/drive/api/read-code?path=apps/chat-app/be/storage.py
```

## Security

- **Path Validation**: Prevents directory traversal attacks
- **Write Restrictions**: Apps can only write to their `data/` directory
- **Read Access**: Apps can read their data and all source code
- **Isolation**: Each app's data is isolated from others
- **User Authentication**: All operations require valid JWT (when auth is enabled)
- **Audit Trail**: All operations are logged

## Implementation Notes

### How It Works

1. **Drive manages local storage**: Drive has direct access to the file system
2. **Apps call Drive APIs**: Apps make HTTP requests to Drive endpoints
3. **Drive validates & executes**: Drive validates paths and performs file operations
4. **Data stays local**: All data is stored on the local machine (execution node)

### Migration: chat-app Example

**Before (Direct File Access):**
```python
# chat-app directly accessed files
app_dir = Path(__file__).parent.parent
storage_dir = app_dir / "data" / "chat"

with open(storage_dir / "conversations.json", 'r') as f:
    conversations = json.load(f)
```

**After (API-Based Access via StorageClient):**
```python
# chat-app now uses Drive APIs
storage = StorageClient("chat-app")
conversations = storage.read_json("chat/conversations.json")

# Behind the scenes: StorageClient makes HTTP call to Drive API
# Drive API then accesses: apps/chat-app/data/chat/conversations.json
```

### Apps Using Drive Storage

1. **chat-app**: Stores conversations and messages via Drive API
   - API path: `chat/conversations.json`
   - Physical path: `apps/chat-app/data/chat/conversations.json`
   - Access: Via StorageClient → Drive API → Local file system

2. **digital-twin**: Stores DT state via Drive API
   - API path: `states/dt_{user_id}.json`
   - Physical path: `apps/digital-twin/data/states/dt_{user_id}.json`
   - Access: Via StorageClient → Drive API → Local file system

### Why This Architecture?

- **Centralized control**: All storage operations go through one service
- **Security**: Apps can't access files outside their data directory
- **Consistency**: All apps use the same storage patterns
- **Flexibility**: Easy to add features (caching, replication, cloud sync)
- **Isolation**: Apps are decoupled from storage implementation

### Migration from Direct File Access

If your app currently uses direct file system access, migrate to use Drive APIs via `StorageClient`:

**Before (Direct File System Access):**
```python
# App directly opens files - NO LONGER RECOMMENDED
from pathlib import Path
import json

data_dir = Path(__file__).parent.parent / "data"
with open(data_dir / "config.json", 'r') as f:
    data = json.load(f)
```

**After (API-Based Access via Drive):**
```python
# App uses Drive's storage APIs
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "drive" / "be" / "api"))
from storage_client import StorageClient

storage = StorageClient("my-app")
data = storage.read_json("config.json")

# This makes an HTTP request to Drive API
# Drive then accesses: apps/my-app/data/config.json
```

## Future Enhancements

- [ ] S3/Cloud storage backend support
- [ ] File versioning and history
- [ ] Storage quotas per app
- [ ] Backup and restore functionality
- [ ] Storage usage analytics

