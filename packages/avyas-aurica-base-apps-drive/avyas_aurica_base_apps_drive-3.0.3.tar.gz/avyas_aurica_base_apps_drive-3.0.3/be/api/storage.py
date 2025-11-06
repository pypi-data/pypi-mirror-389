"""
Drive Storage API - Universal file system access for Digital Twin

Provides secure access to:
- App data directories (read/write)
- Project source code (read-only)
- File and directory operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import os
from datetime import datetime

router = APIRouter()

# Base paths
APPS_DIR = Path(__file__).parent.parent.parent.parent  # /apps directory
PROJECT_ROOT = APPS_DIR.parent  # /code directory
DATA_DIR = PROJECT_ROOT / "data"  # /data directory (centralized storage)


class WriteFileRequest(BaseModel):
    """Request to write a file"""
    path: str
    content: str
    create_dirs: bool = True


class CreateDirRequest(BaseModel):
    """Request to create a directory"""
    path: str


def validate_path(path_str: str, allow_write: bool = False) -> Path:
    """
    Validate and resolve a path safely.
    
    Args:
        path_str: Relative path (e.g., 'chat-app/chat/conversations.json' for data, 
                  or 'apps/chat-app/be/storage.py' for code)
        allow_write: Whether to allow write operations
    
    Returns:
        Resolved absolute path
    
    Raises:
        HTTPException: If path is invalid or unsafe
    """
    try:
        # Remove leading slash if present
        path_str = path_str.lstrip('/')
        
        # Handle empty path - default to data directory root for listing
        if not path_str:
            return DATA_DIR.resolve()
        
        # Determine if this is code access or data access
        if path_str.startswith('apps/'):
            # Code access - read-only access to apps directory
            target_path = (PROJECT_ROOT / path_str).resolve()
            try:
                target_path.relative_to(APPS_DIR)
            except ValueError:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: Path must be within apps directory"
                )
            
            # Code is always read-only
            if allow_write:
                raise HTTPException(
                    status_code=403,
                    detail=f"Write access denied: Cannot write to apps directory (code is read-only)"
                )
        else:
            # Data access - centralized data directory
            target_path = (DATA_DIR / path_str).resolve()
            try:
                target_path.relative_to(DATA_DIR)
            except ValueError:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: Path must be within data directory"
                )
        
        return target_path
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {str(e)}")


@router.get("/list")
async def list_directory(
    path: str = Query("", description="Directory path relative to apps/ (empty for apps root)"),
    include_hidden: bool = Query(False, description="Include hidden files")
) -> Dict[str, Any]:
    """
    List files and directories at the given path.
    
    Returns:
        Directory listing with file metadata
    """
    target_path = validate_path(path)
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    
    if not target_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
    
    items = []
    try:
        for item in sorted(target_path.iterdir()):
            # Skip hidden files unless requested
            if not include_hidden and item.name.startswith('.'):
                continue
            
            stat = item.stat()
            
            # Compute relative path based on whether it's in data or apps
            try:
                rel_path = str(item.relative_to(DATA_DIR))
            except ValueError:
                try:
                    rel_path = str(item.relative_to(PROJECT_ROOT))
                except ValueError:
                    rel_path = item.name
            
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": rel_path
            })
        
        # Determine the display path
        try:
            display_path = str(target_path.relative_to(DATA_DIR))
        except ValueError:
            try:
                display_path = str(target_path.relative_to(PROJECT_ROOT))
            except ValueError:
                display_path = path or "/"
        
        return {
            "path": display_path or "/",
            "items": items,
            "count": len(items)
        }
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing directory: {str(e)}")


@router.get("/read")
async def read_file(
    path: str = Query(..., description="File path relative to apps/")
) -> Dict[str, Any]:
    """
    Read file contents.
    
    Returns:
        File contents and metadata
    """
    target_path = validate_path(path)
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    
    if not target_path.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
    
    try:
        # Try to read as text
        content = target_path.read_text(encoding='utf-8')
        is_binary = False
    except UnicodeDecodeError:
        # Binary file
        content = f"[Binary file: {target_path.suffix}]"
        is_binary = True
    
    stat = target_path.stat()
    
    return {
        "path": path,
        "content": content,
        "is_binary": is_binary,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": target_path.suffix
    }


@router.post("/write")
async def write_file(request: WriteFileRequest) -> Dict[str, Any]:
    """
    Write content to a file.
    Only allowed in app data directories.
    
    Returns:
        Success confirmation
    """
    target_path = validate_path(request.path, allow_write=True)
    
    try:
        # Create parent directories if requested
        if request.create_dirs:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        target_path.write_text(request.content, encoding='utf-8')
        
        stat = target_path.stat()
        
        return {
            "success": True,
            "path": request.path,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")


@router.delete("/delete")
async def delete_file(
    path: str = Query(..., description="File path relative to apps/")
) -> Dict[str, Any]:
    """
    Delete a file.
    Only allowed in app data directories.
    
    Returns:
        Success confirmation
    """
    target_path = validate_path(path, allow_write=True)
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    
    if target_path.is_dir():
        raise HTTPException(status_code=400, detail="Use delete-dir to delete directories")
    
    try:
        target_path.unlink()
        return {
            "success": True,
            "path": path,
            "deleted": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.post("/create-dir")
async def create_directory(request: CreateDirRequest) -> Dict[str, Any]:
    """
    Create a directory.
    Only allowed in app data directories.
    
    Returns:
        Success confirmation
    """
    target_path = validate_path(request.path, allow_write=True)
    
    try:
        target_path.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "path": request.path,
            "created": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating directory: {str(e)}")


@router.get("/list-apps")
async def list_apps() -> Dict[str, Any]:
    """
    List all available apps in the project.
    
    Returns:
        List of apps with their metadata
    """
    apps = []
    
    try:
        for app_dir in sorted(APPS_DIR.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith('.'):
                continue
            
            app_json = app_dir / "app.json"
            if not app_json.exists():
                continue
            
            try:
                metadata = json.loads(app_json.read_text())
                
                # Check for data directory
                data_dir = app_dir / "data"
                has_data = data_dir.exists() and data_dir.is_dir()
                
                apps.append({
                    "name": metadata.get("name", app_dir.name),
                    "version": metadata.get("version", "unknown"),
                    "description": metadata.get("description", ""),
                    "has_data": has_data,
                    "has_backend": (app_dir / "be").exists(),
                    "has_frontend": (app_dir / "fe").exists()
                })
            except Exception as e:
                print(f"Warning: Could not load {app_dir.name}: {e}")
                continue
        
        return {
            "apps": apps,
            "count": len(apps),
            "apps_dir": str(APPS_DIR.relative_to(PROJECT_ROOT))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing apps: {str(e)}")


@router.get("/read-code")
async def read_code(
    path: str = Query(..., description="Code file path relative to apps/")
) -> Dict[str, Any]:
    """
    Read project source code (read-only).
    Provides access to app source code for context.
    
    Returns:
        Source code contents
    """
    target_path = validate_path(path, allow_write=False)
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    
    if not target_path.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
    
    # Restrict to source code files
    allowed_extensions = {'.py', '.js', '.ts', '.json', '.html', '.css', '.md', '.txt', '.yaml', '.yml', '.toml'}
    if target_path.suffix not in allowed_extensions:
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied: Can only read source code files ({', '.join(allowed_extensions)})"
        )
    
    try:
        content = target_path.read_text(encoding='utf-8')
        stat = target_path.stat()
        
        return {
            "path": path,
            "content": content,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "language": target_path.suffix.lstrip('.'),
            "read_only": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get storage statistics and information.
    
    Returns:
        Storage statistics
    """
    try:
        # Count apps
        app_count = sum(1 for d in APPS_DIR.iterdir() 
                       if d.is_dir() and (d / "app.json").exists())
        
        # Calculate total size of data directories
        total_data_size = 0
        app_data_sizes = {}
        
        for app_dir in APPS_DIR.iterdir():
            if not app_dir.is_dir():
                continue
            
            data_dir = app_dir / "data"
            if data_dir.exists():
                size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
                total_data_size += size
                if size > 0:
                    app_data_sizes[app_dir.name] = {
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 2)
                    }
        
        return {
            "total_apps": app_count,
            "total_data_size_mb": round(total_data_size / (1024 * 1024), 2),
            "apps_with_data": app_data_sizes,
            "apps_directory": str(APPS_DIR.relative_to(PROJECT_ROOT)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
