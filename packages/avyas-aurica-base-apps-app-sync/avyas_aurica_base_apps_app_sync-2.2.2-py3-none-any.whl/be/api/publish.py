"""
Publish endpoint - Disabled
GitHub publisher functionality has been removed
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import sys

# Add the backend source to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be" / "src"
sys.path.insert(0, str(backend_path.parent))

try:
    from src.aurica_auth import protected, get_current_user
except ImportError as e:
    print(f"Warning: Import error: {e}")
    def protected(func):
        return func
    def get_current_user(request, required=True):
        return type('User', (), {"username": "unknown", "user_id": "unknown"})()

router = APIRouter()

# Get apps directory from environment or use default
import os
apps_dir = Path(os.getenv('APPS_DIR', Path(__file__).parent.parent.parent.parent.parent / "apps"))


class PublishRequest(BaseModel):
    """Request model for publish endpoint."""
    app_name: str  # Required - must specify app name
    commit_message: Optional[str] = None  # Custom commit message
    tag: Optional[str] = None  # Optional git tag (e.g., "weather-app-v1.0.0")
    push: bool = True  # Push to remote (default: True)


class PublishResponse(BaseModel):
    """Response model for publish endpoint."""
    success: bool
    message: str
    app_name: str
    version: Optional[str] = None
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    install_command: Optional[str] = None


@router.post("/", response_model=PublishResponse, summary="Publish app (disabled)", tags=['app-sync'])
@protected
async def publish_to_github(request: Request, req: PublishRequest):
    """
    Publish endpoint - Currently disabled.
    
    GitHub publisher functionality has been removed.
    """
    raise HTTPException(status_code=501, detail="Publish functionality has been removed")


class AppStatusResponse(BaseModel):
    """Response model for app status."""
    app_name: str
    has_changes: bool
    current_branch: str
    last_commit: Optional[dict] = None
    repo_url: Optional[str] = None


@router.get("/status/{app_name}", response_model=AppStatusResponse, summary="Get app status (disabled)", tags=['app-sync'])
@protected
async def get_app_status(app_name: str):
    """
    Get app status endpoint - Currently disabled.
    
    GitHub publisher functionality has been removed.
    """
    raise HTTPException(status_code=501, detail="Status functionality has been removed")
