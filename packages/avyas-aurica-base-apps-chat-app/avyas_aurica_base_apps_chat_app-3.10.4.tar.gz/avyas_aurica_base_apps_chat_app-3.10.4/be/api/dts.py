"""
DT Management API - CRUD operations for Digital Twins
DTs are discovered by scanning folders in data/ directory
Each DT has its own folder with a dt.json metadata file
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

router = APIRouter()

# Root data directory - each subdirectory is a potential DT
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data"


class DTCreate(BaseModel):
    name: str
    type: str  # personal, business, agent, app
    description: Optional[str] = None
    capabilities: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class DTUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[dict] = None
    status: Optional[str] = None  # active, inactive, archived


def get_dt_folder(dt_id: str) -> Path:
    """Get the folder path for a DT"""
    return DATA_DIR / dt_id


def load_dt_metadata(dt_id: str) -> Optional[dict]:
    """Load DT metadata from dt.json file in its folder"""
    dt_folder = get_dt_folder(dt_id)
    metadata_file = dt_folder / "dt.json"
    
    if not metadata_file.exists():
        return None
    
    try:
        return json.loads(metadata_file.read_text())
    except Exception as e:
        print(f"Error loading DT metadata for {dt_id}: {e}")
        return None


def save_dt_metadata(dt_id: str, metadata: dict):
    """Save DT metadata to dt.json file in its folder"""
    dt_folder = get_dt_folder(dt_id)
    dt_folder.mkdir(parents=True, exist_ok=True)
    
    metadata_file = dt_folder / "dt.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))


def get_apps_dir() -> Path:
    """Get the apps directory"""
    return DATA_DIR.parent / "apps"


def discover_app_dts() -> List[dict]:
    """Discover DTs from installed apps"""
    app_dts = []
    apps_dir = get_apps_dir()
    
    if not apps_dir.exists():
        return app_dts
    
    # Scan all app directories
    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir() or app_dir.name.startswith('.'):
            continue
        
        # Check if app has app.json
        app_json = app_dir / "app.json"
        if not app_json.exists():
            continue
        
        try:
            app_info = json.loads(app_json.read_text())
            app_name = app_info.get("name", app_dir.name)
            
            # Check if app has ideas in data folder
            app_data_dir = DATA_DIR / app_name / "ideas"
            ideas_count = 0
            if app_data_dir.exists():
                ideas_count = len(list(app_data_dir.glob("*.md")))
            
            # Create DT for app
            dt = {
                "id": f"dt_app_{app_name}",
                "name": app_name,
                "type": "app",
                "description": app_info.get("description", f"App: {app_name}"),
                "capabilities": ["app", "ideas"] if ideas_count > 0 else ["app"],
                "metadata": {
                    "version": app_info.get("version", "unknown"),
                    "app_path": f"apps/{app_name}",
                    "data_path": f"data/{app_name}",
                    "ideas_count": ideas_count
                },
                "status": "active",
                "created_at": datetime.fromtimestamp(app_dir.stat().st_ctime).isoformat(),
                "updated_at": datetime.fromtimestamp(app_dir.stat().st_mtime).isoformat()
            }
            app_dts.append(dt)
            
        except Exception as e:
            print(f"Error loading app DT for {app_dir.name}: {e}")
    
    return app_dts


def discover_dts() -> List[dict]:
    """Discover all DTs by scanning data directory and apps"""
    dts = []
    
    # 1. Discover app DTs from apps directory
    app_dts = discover_app_dts()
    dts.extend(app_dts)
    
    # 2. Discover user/custom DTs from data directory
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return dts
    
    # Scan all subdirectories in data/
    for item in DATA_DIR.iterdir():
        if not item.is_dir():
            continue
        
        # Skip app data directories (already handled above) and special directories
        if item.name.startswith('.'):
            continue
        
        # Check if this is an app data directory
        is_app_dir = any(dt["metadata"].get("data_path") == f"data/{item.name}" for dt in app_dts)
        if is_app_dir:
            continue
        
        dt_id = item.name
        
        # Try to load metadata from dt.json
        metadata = load_dt_metadata(dt_id)
        
        if metadata:
            # Has metadata file
            dts.append(metadata)
        else:
            # No metadata file - create default metadata
            # Assume it's a user DT if the folder name looks like a user ID
            dt = {
                "id": dt_id,
                "name": dt_id,
                "type": "user" if len(dt_id) > 30 else "unknown",
                "description": f"Digital Twin: {dt_id}",
                "capabilities": [],
                "metadata": {
                    "data_path": str(item.relative_to(DATA_DIR.parent))
                },
                "status": "active",
                "created_at": datetime.fromtimestamp(item.stat().st_ctime).isoformat(),
                "updated_at": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            }
            # Save the generated metadata
            save_dt_metadata(dt_id, dt)
            dts.append(dt)
    
    return dts


@router.post("")
async def create_dt(dt: DTCreate, auth_context: dict = None):
    """Create a new Digital Twin"""
    dt_id = f"dt_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_dt = {
        "id": dt_id,
        "name": dt.name,
        "type": dt.type,
        "description": dt.description,
        "capabilities": dt.capabilities,
        "metadata": dt.metadata,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "created_by": auth_context.get("user_id") if auth_context else None
    }
    
    # Save metadata to dt.json in DT's folder
    save_dt_metadata(dt_id, new_dt)
    
    # Create threads subfolder
    threads_dir = get_dt_folder(dt_id) / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)
    
    return {"success": True, "dt": new_dt}


@router.get("")
async def list_dts(
    type: Optional[str] = None,
    status: Optional[str] = None,
    auth_context: dict = None
):
    """List all Digital Twins by discovering folders in data directory"""
    dts = discover_dts()
    
    # Apply filters
    if type:
        dts = [d for d in dts if d.get("type") == type]
    if status:
        dts = [d for d in dts if d.get("status") == status]
    
    return {"success": True, "dts": dts, "count": len(dts)}


@router.get("/{dt_id}")
async def get_dt(dt_id: str, auth_context: dict = None):
    """Get a specific DT by ID"""
    # Check if it's an app DT
    if dt_id.startswith("dt_app_"):
        app_name = dt_id.replace("dt_app_", "")
        app_dts = discover_app_dts()
        dt = next((d for d in app_dts if d["id"] == dt_id), None)
    else:
        dt = load_dt_metadata(dt_id)
    
    if not dt:
        raise HTTPException(status_code=404, detail="DT not found")
    
    # Count threads
    threads_dir = get_dt_folder(dt_id) / "threads"
    threads_count = 0
    if threads_dir.exists():
        threads_count = len([f for f in threads_dir.iterdir() if f.is_file() and f.suffix == '.json'])
    
    dt["threads_count"] = threads_count
    
    return {"success": True, "dt": dt}


@router.put("/{dt_id}")
async def update_dt(
    dt_id: str,
    updates: DTUpdate,
    auth_context: dict = None
):
    """Update a DT"""
    dt = load_dt_metadata(dt_id)
    
    if not dt:
        raise HTTPException(status_code=404, detail="DT not found")
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    dt.update(update_data)
    dt["updated_at"] = datetime.now().isoformat()
    
    save_dt_metadata(dt_id, dt)
    
    return {"success": True, "dt": dt}


@router.delete("/{dt_id}")
async def delete_dt(dt_id: str, auth_context: dict = None):
    """Delete a DT (removes dt.json file, folder remains)"""
    dt = load_dt_metadata(dt_id)
    
    if not dt:
        raise HTTPException(status_code=404, detail="DT not found")
    
    # Remove the dt.json file (but keep the folder and its data)
    dt_folder = get_dt_folder(dt_id)
    metadata_file = dt_folder / "dt.json"
    if metadata_file.exists():
        metadata_file.unlink()
    
    return {"success": True, "message": "DT deleted"}


@router.get("/{dt_id}/threads")
async def get_dt_threads(dt_id: str, auth_context: dict = None):
    """Get all threads for a DT, including ideas for app DTs"""
    # Check if it's an app DT
    if dt_id.startswith("dt_app_"):
        app_name = dt_id.replace("dt_app_", "")
        app_dts = discover_app_dts()
        dt = next((d for d in app_dts if d["id"] == dt_id), None)
    else:
        dt = load_dt_metadata(dt_id)
    
    if not dt:
        raise HTTPException(status_code=404, detail="DT not found")
    
    threads = []
    
    # 1. Load regular threads
    threads_dir = get_dt_folder(dt_id) / "threads"
    if threads_dir.exists():
        for thread_file in threads_dir.glob("*.json"):
            if thread_file.name == "threads.json":
                continue
            try:
                thread_data = json.loads(thread_file.read_text())
                if isinstance(thread_data, list):
                    # It's a messages file, create thread metadata
                    thread_id = thread_file.stem
                    threads.append({
                        "id": thread_id,
                        "dt_id": dt_id,
                        "title": thread_id,
                        "type": "conversation",
                        "message_count": len(thread_data),
                        "updated_at": datetime.fromtimestamp(thread_file.stat().st_mtime).isoformat()
                    })
            except Exception as e:
                print(f"Error loading thread {thread_file}: {e}")
    
    # 2. If it's an app DT, also include ideas as threads
    if dt.get("type") == "app":
        app_name = dt_id.replace("dt_app_", "")
        ideas_dir = DATA_DIR / app_name / "ideas"
        
        if ideas_dir.exists():
            for idea_file in ideas_dir.glob("*.md"):
                try:
                    # Read first line as title
                    content = idea_file.read_text()
                    title = content.split('\n')[0].strip('# ').strip() if content else idea_file.stem
                    
                    threads.append({
                        "id": f"idea_{idea_file.stem}",
                        "dt_id": dt_id,
                        "title": f"💡 {title}",
                        "type": "idea",
                        "filename": idea_file.name,
                        "message_count": 0,
                        "updated_at": datetime.fromtimestamp(idea_file.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    print(f"Error loading idea {idea_file}: {e}")
    
    return {"success": True, "threads": threads, "count": len(threads)}


@router.post("/{dt_id}/threads")
async def create_thread(
    dt_id: str,
    title: str,
    description: Optional[str] = None,
    thread_type: str = "conversation",
    auth_context: dict = None
):
    """Create a new thread for a DT"""
    dt = load_dt_metadata(dt_id)
    
    if not dt:
        raise HTTPException(status_code=404, detail="DT not found")
    
    threads_dir = get_dt_folder(dt_id) / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)
    
    thread_id = f"thread_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_thread = {
        "id": thread_id,
        "dt_id": dt_id,
        "title": title,
        "description": description,
        "type": thread_type,
        "status": "active",
        "message_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Create thread messages file
    thread_messages_file = threads_dir / f"{thread_id}.json"
    thread_messages_file.write_text(json.dumps([], indent=2))
    
    return {"success": True, "thread": new_thread}


@router.get("/{dt_id}/threads/{thread_id}")
async def get_thread_messages(
    dt_id: str,
    thread_id: str,
    auth_context: dict = None
):
    """Get messages for a specific thread"""
    threads_dir = get_dt_folder(dt_id) / "threads"
    thread_messages_file = threads_dir / f"{thread_id}.json"
    
    if not thread_messages_file.exists():
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = json.loads(thread_messages_file.read_text())
    
    return {"success": True, "messages": messages, "count": len(messages)}


@router.post("/{dt_id}/threads/{thread_id}/messages")
async def add_thread_message(
    dt_id: str,
    thread_id: str,
    content: str,
    role: str = "user",
    auth_context: dict = None
):
    """Add a message to a thread"""
    threads_dir = get_dt_folder(dt_id) / "threads"
    thread_messages_file = threads_dir / f"{thread_id}.json"
    
    if not thread_messages_file.exists():
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = json.loads(thread_messages_file.read_text())
    
    new_message = {
        "id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    messages.append(new_message)
    thread_messages_file.write_text(json.dumps(messages, indent=2))
    
    return {"success": True, "message": new_message}
