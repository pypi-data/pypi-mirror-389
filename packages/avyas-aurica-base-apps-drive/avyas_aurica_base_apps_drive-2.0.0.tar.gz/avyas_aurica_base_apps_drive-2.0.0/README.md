# Drive - Global Storage Service

Universal storage API that provides the Digital Twin with access to all app data directories and project code.

## Features

- **App Data Access**: Read/write files in any app's data directory
- **Data Separation**: Each app has its own data directory
- **File Operations**: List, read, write, delete files
- **Directory Management**: Create and manage directories
- **Project Code Access**: Read-only access to project source code
- **Safe Operations**: Path validation and security checks

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
apps/
  {app-name}/
    data/          # App-specific data directory
      ...
    be/            # Backend code (read-only)
    fe/            # Frontend code (read-only)
```

## Usage Examples

```python
# List files in chat-app data directory
GET /drive/api/list?path=apps/chat-app/data

# Read a file
GET /drive/api/read?path=apps/chat-app/data/conversations.json

# Write a file
POST /drive/api/write
{
  "path": "apps/chat-app/data/settings.json",
  "content": "{\"theme\": \"dark\"}"
}

# Read project code (read-only)
GET /drive/api/read-code?path=apps/chat-app/be/storage.py
```

## Security

- Apps can read/write their own data directory
- Project code is read-only
- Path traversal protection
- User authentication required
- All operations are auditable
