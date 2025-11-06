"""
Install endpoint - Install apps from package registries (PyPI, npm, GitHub)
Replaces S3 download with public package manager support
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
    from src.app_package_manager import AppPackageManager
    from src.aurica_auth import protected, get_current_user, public
except ImportError as e:
    print(f"Warning: Import error: {e}")
    def auth_required(func):
        return func
    def public(func):
        return func
    def get_current_user(request, required=True):
        return {"username": "unknown", "user_id": "unknown"}

router = APIRouter()

# Get apps directory from environment or use default
import os
apps_dir = Path(os.getenv('APPS_DIR', Path(__file__).parent.parent.parent.parent.parent / "apps"))


class InstallRequest(BaseModel):
    """Request model for install endpoint."""
    package_ref: str  # e.g., "npm:@myorg/myapp@1.0.0", "pypi:myorg-myapp@1.0.0", "github:myorg/myapp@v1.0.0"
    force: bool = False  # Force reinstall even if already installed


class InstallResponse(BaseModel):
    """Response model for install endpoint."""
    success: bool
    message: str
    app_name: str
    version: Optional[str] = None
    registry: Optional[str] = None
    files_count: Optional[int] = None


@router.post("/", response_model=InstallResponse, summary="Install app from package registry", tags=['app-sync'])
@protected
async def install_app(request: Request, req: InstallRequest):
    """
    Install an app from a package registry (PyPI, npm, GitHub).
    
    This endpoint downloads apps from public package managers.
    No S3 required - uses standard package infrastructure.
    
    Package reference formats:
    - PyPI: `pypi:namespace-appname@1.0.0`
    - npm: `npm:@namespace/appname@1.0.0`
    - GitHub: `github:owner/repo@v1.0.0` or `github:owner/repo@main`
    
    Args:
        request: FastAPI request object
        req: InstallRequest with package_ref and optional force flag
        
    Returns:
        InstallResponse with installation details
        
    Examples:
        ```json
        {
            "package_ref": "npm:@acme/weather-app@1.2.3",
            "force": false
        }
        ```
        
        ```json
        {
            "package_ref": "github:acme/auth-app@v2.0.0",
            "force": true
        }
        ```
    """
    user = get_current_user(request)
    print(f"📦 User {user.username} installing app: {req.package_ref}")
    
    try:
        manager = AppPackageManager(apps_dir)
        result = manager.install_app(req.package_ref, force=req.force)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Installation failed'))
        
        # Reload the app dynamically into the running application
        # (whether it was just installed or already exists)
        app_name = result['app_name']
        try:
            from src.main import app_loader, app
            
            if app_loader:
                was_loaded = app_name in app_loader.apps
                
                if was_loaded:
                    print(f"🔄 App '{app_name}' already loaded, reloading with updated code...")
                    # Force reload by removing and re-adding
                    # First, remount the app with fresh code
                    success = await app_loader.load_app_on_demand(app_name, force_reload=True)
                    if success:
                        # Remount the app to the main FastAPI instance
                        sub_app = app_loader.create_app_fastapi(app_name)
                        if sub_app:
                            # Note: FastAPI doesn't have unmount, but remounting should work
                            app.mount(f"/{app_name}", sub_app)
                            print(f"✅ Successfully reloaded and remounted app '{app_name}' at /{app_name}")
                    else:
                        print(f"⚠️  Failed to reload app '{app_name}', may require restart")
                else:
                    print(f"🔄 App '{app_name}' not found in runtime, loading...")
                    success = await app_loader.load_app_on_demand(app_name)
                    
                    if success:
                        # Mount the new app to the main FastAPI instance
                        sub_app = app_loader.create_app_fastapi(app_name)
                        if sub_app:
                            app.mount(f"/{app_name}", sub_app)
                            print(f"✅ Successfully mounted app '{app_name}' at /{app_name}")
                    else:
                        print(f"⚠️  Failed to load app '{app_name}', may require restart")
        except Exception as reload_error:
            print(f"⚠️  Error reloading app '{app_name}': {reload_error}")
            import traceback
            traceback.print_exc()
            # Don't fail the request - app was installed successfully
        
        return InstallResponse(
            success=True,
            message=f"Successfully installed '{result['app_name']}'",
            app_name=result['app_name'],
            version=result.get('version'),
            registry=result.get('registry'),
            files_count=result.get('files_count')
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")


class UninstallRequest(BaseModel):
    """Request model for uninstall endpoint."""
    app_name: str


class UninstallResponse(BaseModel):
    """Response model for uninstall endpoint."""
    success: bool
    message: str
    app_name: str


@router.delete("/", response_model=UninstallResponse, summary="Uninstall an app", tags=['app-sync'])
@protected
async def uninstall_app(request: Request, req: UninstallRequest):
    """
    Uninstall an app from the system.
    
    Args:
        request: FastAPI request object
        req: UninstallRequest with app_name
        
    Returns:
        UninstallResponse with result
    """
    user = get_current_user(request)
    print(f"🗑️  User {user.username} uninstalling app: {req.app_name}")
    
    try:
        manager = AppPackageManager(apps_dir)
        result = manager.uninstall_app(req.app_name)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error', 'Uninstall failed'))
        
        return UninstallResponse(
            success=True,
            message=f"Successfully uninstalled '{request.app_name}'",
            app_name=request.app_name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uninstall failed: {str(e)}")


class ListInstalledResponse(BaseModel):
    """Response model for list installed apps."""
    apps: list


class RegistryResponse(BaseModel):
    """Response model for registry apps."""
    apps: dict


@router.get("/registry", response_model=RegistryResponse, summary="Get available apps from registry", tags=['app-sync'])
@public
async def get_registry_apps():
    """
    Get list of all available apps from the app registry.
    This endpoint is public - no authentication required.
    
    The registry is served from the backend's config directory as a server asset.
    Fetches latest version info from PyPI for each package.
    
    Returns:
        RegistryResponse with all apps available for installation
    """
    try:
        import json
        import os
        
        # Check server asset locations only (single source of truth: backend config)
        possible_paths = [
            Path("/workspace/config/app-registry.json"),  # Production (Vercel)
            Path(os.getcwd()) / "config" / "app-registry.json",  # Local dev from backend root
            Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be" / "config" / "app-registry.json",  # Local dev relative path
        ]
        
        registry_path = None
        for path in possible_paths:
            if path.exists():
                registry_path = path
                print(f"📋 Found registry at: {registry_path}")
                break
        
        if not registry_path:
            print(f"⚠️  Registry not found in any of: {possible_paths}")
            return RegistryResponse(apps={})
        
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        apps = registry.get('apps', {})
        
        # Fetch latest version from PyPI for each app (with timeout)
        try:
            import sys
            backend_path = Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be" / "src"
            if str(backend_path.parent) not in sys.path:
                sys.path.insert(0, str(backend_path.parent))
            
            from src.package_registry import get_registry_manager
            registry_mgr = get_registry_manager()
            
            print(f"🔍 Fetching PyPI versions for {len(apps)} apps...")
            for app_name, app_info in apps.items():
                package_ref = app_info.get('package_ref', '')
                if package_ref.startswith('pypi:'):
                    try:
                        print(f"  📦 Fetching {app_name}...")
                        pkg_info = registry_mgr.get_package_info(package_ref)
                        app_info['latest_version'] = pkg_info.version
                        print(f"  ✅ {app_name}: v{pkg_info.version}")
                    except Exception as e:
                        print(f"  ⚠️  Could not fetch version for {app_name}: {e}")
                        app_info['latest_version'] = None
                else:
                    app_info['latest_version'] = None
        except Exception as e:
            print(f"⚠️  Could not fetch PyPI versions: {e}")
            import traceback
            traceback.print_exc()
            # Continue without versions rather than failing
        
        print(f"📦 Loaded {len(apps)} apps from registry")
        return RegistryResponse(apps=apps)
        
    except Exception as e:
        print(f"❌ Error loading registry: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load registry: {str(e)}")


@router.get("/installed", response_model=ListInstalledResponse, summary="List installed apps", tags=['app-sync'])
@protected
async def list_installed_apps(request: Request):
    """
    List all apps installed from package registries.
    
    Returns:
        ListInstalledResponse with list of installed apps and their details
    """
    user = get_current_user(request)
    print(f"📦 User {user.username} listing installed apps")
    
    try:
        manager = AppPackageManager(apps_dir)
        apps = manager.list_installed_apps()
        
        return ListInstalledResponse(apps=apps)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list apps: {str(e)}")
