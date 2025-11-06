"""
Ideas API - Manage improvement ideas for apps/DTs
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path
import os

router = APIRouter()

DATA_DIR = Path("/Users/amit/aurica/code/data")


class IdeaThread(BaseModel):
    content: str
    status: Optional[str] = "open"  # open, in_progress, implemented, closed


class IdeaUpdate(BaseModel):
    content: str
    author: Optional[str] = None


def get_app_ideas_dir(app_name: str):
    """Get ideas directory for an app"""
    ideas_dir = DATA_DIR / app_name / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    return ideas_dir


def load_idea_file(app_name: str, filename: str):
    """Load an idea file"""
    ideas_dir = get_app_ideas_dir(app_name)
    idea_file = ideas_dir / filename
    
    if not idea_file.exists():
        raise HTTPException(status_code=404, detail="Idea file not found")
    
    content = idea_file.read_text()
    
    # Get file stats
    stats = idea_file.stat()
    
    return {
        "filename": filename,
        "content": content,
        "size": stats.st_size,
        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
    }


def save_idea_file(app_name: str, filename: str, content: str):
    """Save an idea file"""
    ideas_dir = get_app_ideas_dir(app_name)
    idea_file = ideas_dir / filename
    idea_file.write_text(content)


@router.get("/{app_name}")
async def list_app_ideas(app_name: str):
    """List all idea files for an app"""
    ideas_dir = get_app_ideas_dir(app_name)
    
    if not ideas_dir.exists():
        return {"success": True, "ideas": [], "count": 0}
    
    ideas = []
    for file in ideas_dir.glob("*.md"):
        stats = file.stat()
        ideas.append({
            "filename": file.name,
            "title": file.stem.replace("_", " ").title(),
            "size": stats.st_size,
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
        })
    
    return {"success": True, "ideas": ideas, "count": len(ideas)}


@router.get("/{app_name}/{filename}")
async def get_idea(app_name: str, filename: str):
    """Get a specific idea file"""
    idea = load_idea_file(app_name, filename)
    return {"success": True, "idea": idea}


@router.put("/{app_name}/{filename}")
async def update_idea(
    app_name: str,
    filename: str,
    update: IdeaUpdate
):
    """Update an idea file"""
    # Load existing content
    idea = load_idea_file(app_name, filename)
    
    # Add update to the end with timestamp
    timestamp = datetime.now().isoformat()
    author = update.author or "Anonymous"
    
    updated_content = idea["content"]
    updated_content += f"\n\n---\n\n## Update - {timestamp}\n**Author:** {author}\n\n{update.content}\n"
    
    # Save updated content
    save_idea_file(app_name, filename, updated_content)
    
    return {
        "success": True,
        "message": "Idea updated",
        "idea": {
            "filename": filename,
            "content": updated_content
        }
    }


@router.post("/{app_name}")
async def create_idea(
    app_name: str,
    title: str,
    content: str,
    author: Optional[str] = None
):
    """Create a new idea file for an app"""
    # Create filename from title
    filename = title.lower().replace(" ", "_") + ".md"
    
    # Check if file already exists
    ideas_dir = get_app_ideas_dir(app_name)
    idea_file = ideas_dir / filename
    
    if idea_file.exists():
        raise HTTPException(status_code=400, detail="Idea with this title already exists")
    
    # Create markdown content
    timestamp = datetime.now().isoformat()
    author_name = author or "Anonymous"
    
    md_content = f"""# {title}

**Created:** {timestamp}  
**Author:** {author_name}  
**App:** {app_name}

---

{content}
"""
    
    # Save file
    save_idea_file(app_name, filename, md_content)
    
    return {
        "success": True,
        "idea": {
            "filename": filename,
            "title": title,
            "content": md_content
        }
    }


@router.get("")
async def list_all_ideas():
    """List ideas from all apps"""
    all_ideas = []
    
    for app_dir in DATA_DIR.iterdir():
        if not app_dir.is_dir():
            continue
        
        ideas_dir = app_dir / "ideas"
        if not ideas_dir.exists():
            continue
        
        for file in ideas_dir.glob("*.md"):
            stats = file.stat()
            all_ideas.append({
                "app": app_dir.name,
                "filename": file.name,
                "title": file.stem.replace("_", " ").title(),
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
    
    # Sort by modified date
    all_ideas.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"success": True, "ideas": all_ideas, "count": len(all_ideas)}


@router.get("/{app_name}/threads")
async def get_idea_threads(app_name: str, idea_filename: str):
    """Get discussion threads for an idea"""
    ideas_dir = get_app_ideas_dir(app_name)
    threads_file = ideas_dir / f".threads_{idea_filename}.json"
    
    if not threads_file.exists():
        return {"success": True, "threads": [], "count": 0}
    
    threads = json.loads(threads_file.read_text())
    return {"success": True, "threads": threads, "count": len(threads)}


@router.post("/{app_name}/threads")
async def create_idea_thread(
    app_name: str,
    idea_filename: str,
    thread: IdeaThread
):
    """Create a discussion thread for an idea"""
    ideas_dir = get_app_ideas_dir(app_name)
    threads_file = ideas_dir / f".threads_{idea_filename}.json"
    
    if threads_file.exists():
        threads = json.loads(threads_file.read_text())
    else:
        threads = []
    
    thread_id = f"thread_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    new_thread = {
        "id": thread_id,
        "idea_filename": idea_filename,
        "content": thread.content,
        "status": thread.status,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "messages": []
    }
    
    threads.append(new_thread)
    threads_file.write_text(json.dumps(threads, indent=2))
    
    return {"success": True, "thread": new_thread}
