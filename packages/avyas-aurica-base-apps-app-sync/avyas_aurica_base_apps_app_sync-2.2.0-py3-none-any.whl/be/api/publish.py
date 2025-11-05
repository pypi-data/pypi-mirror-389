"""
Publish endpoint - Publish apps to GitHub repository
Replaces S3 upload with Git push to GitHub
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
    from src.github_publisher import GitHubPublisher
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


@router.post("/", response_model=PublishResponse, summary="Publish app to GitHub", tags=['app-sync'])
@protected
async def publish_to_github(request: Request, req: PublishRequest):
    """
    Publish a local app to GitHub repository.
    
    This endpoint commits and pushes app changes to GitHub.
    Users can then install the app using the GitHub package format.
    
    Steps:
    1. Check for changes in the app directory
    2. Commit changes with message
    3. Optionally create a git tag
    4. Push to GitHub remote
    
    Args:
        request: FastAPI request object
        req: PublishRequest with app_name, optional commit_message, tag, and push flag
        
    Returns:
        PublishResponse with publish details and install command
        
    Examples:
        ```json
        {
            "app_name": "weather-app",
            "commit_message": "Update weather API endpoint",
            "tag": "weather-app-v1.2.0",
            "push": true
        }
        ```
    """
    user = get_current_user(request)
    print(f"📤 User {user.username} publishing app: {req.app_name}")
    
    try:
        publisher = GitHubPublisher(apps_dir)
        result = publisher.publish_app(
            req.app_name,
            commit_message=req.commit_message,
            tag=req.tag,
            push=req.push
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Publish failed'))
        
        # Handle case where nothing was published
        if result.get('skipped'):
            return PublishResponse(
                success=True,
                message=f"No changes to publish for '{request.app_name}'",
                app_name=request.app_name,
                version=result.get('version')
            )
        
        message = f"Successfully published '{request.app_name}'"
        if result.get('tag'):
            message += f" with tag {result['tag']}"
        
        return PublishResponse(
            success=True,
            message=message,
            app_name=request.app_name,
            version=result.get('version'),
            commit_hash=result.get('commit_hash'),
            branch=result.get('branch'),
            tag=result.get('tag'),
            install_command=result.get('install_command')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publish failed: {str(e)}")


class AppStatusResponse(BaseModel):
    """Response model for app status."""
    app_name: str
    has_changes: bool
    current_branch: str
    last_commit: Optional[dict] = None
    repo_url: Optional[str] = None


@router.get("/status/{app_name}", response_model=AppStatusResponse, summary="Get app git status", tags=['app-sync'])
@protected
async def get_app_status(app_name: str):
    """
    Get git status for an app.
    
    Shows if there are uncommitted changes, current branch, and last commit.
    
    Args:
        app_name: Name of the app
        
    Returns:
        AppStatusResponse with git status information
    """
    try:
        publisher = GitHubPublisher(apps_dir)
        status = publisher.get_app_status(app_name)
        
        if 'error' in status:
            raise HTTPException(status_code=404, detail=status['error'])
        
        return AppStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
