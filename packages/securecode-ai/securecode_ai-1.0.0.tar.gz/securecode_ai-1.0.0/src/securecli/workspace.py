"""
Workspace management for SecureCLI
Handles isolated environments for different projects/configurations
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .config import ConfigManager


class WorkspaceManager:
    """Manages isolated workspaces for different projects"""
    
    def __init__(self, workspaces_dir: Optional[str] = None):
        if workspaces_dir:
            self.workspaces_dir = Path(workspaces_dir)
        else:
            self.workspaces_dir = Path.cwd() / "workspaces"
        
        self.workspaces_dir.mkdir(exist_ok=True)
        self.current_workspace: Optional[str] = None
        
        # Load current workspace from state file
        self._load_current_workspace()
    
    def _load_current_workspace(self) -> None:
        """Load current workspace from state file"""
        state_file = self.workspaces_dir / ".current_workspace"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    workspace_name = f.read().strip()
                    if self.workspace_exists(workspace_name):
                        self.current_workspace = workspace_name
            except Exception:
                pass
    
    def _save_current_workspace(self) -> None:
        """Save current workspace to state file"""
        state_file = self.workspaces_dir / ".current_workspace"
        
        try:
            with open(state_file, 'w') as f:
                f.write(self.current_workspace or "")
        except Exception:
            pass
    
    def list_workspaces(self) -> List[str]:
        """List all available workspaces"""
        workspaces = []
        
        for item in self.workspaces_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                workspaces.append(item.name)
        
        return sorted(workspaces)
    
    def workspace_exists(self, name: str) -> bool:
        """Check if workspace exists"""
        workspace_path = self.workspaces_dir / name
        return workspace_path.exists() and workspace_path.is_dir()
    
    def create_workspace(self, name: str, template: Optional[str] = None) -> str:
        """
        Create a new workspace
        
        Args:
            name: Workspace name
            template: Optional template to copy from
            
        Returns:
            Path to created workspace
        """
        if not self._is_valid_workspace_name(name):
            raise ValueError(f"Invalid workspace name: {name}")
        
        workspace_path = self.workspaces_dir / name
        
        if workspace_path.exists():
            raise ValueError(f"Workspace already exists: {name}")
        
        # Create workspace directory structure
        workspace_path.mkdir(parents=True)
        
        # Create subdirectories
        (workspace_path / "artifacts").mkdir()
        (workspace_path / "reports").mkdir()
        (workspace_path / "cache").mkdir()
        (workspace_path / "logs").mkdir()
        (workspace_path / "sessions").mkdir()
        
        # Create workspace metadata
        metadata = {
            "name": name,
            "created": datetime.utcnow().isoformat(),
            "created_by": os.getenv('USER', 'unknown'),
            "template": template,
            "version": "1.0.0"
        }
        
        metadata_file = workspace_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Copy template if specified
        if template and self.workspace_exists(template):
            self._copy_workspace_template(template, name)
        
        # Create default workspace config
        self._create_default_workspace_config(workspace_path)
        
        return str(workspace_path)
    
    def _is_valid_workspace_name(self, name: str) -> bool:
        """Validate workspace name"""
        if not name or len(name) > 50:
            return False
        
        # Allow alphanumeric, hyphens, underscores
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
    
    def _copy_workspace_template(self, template_name: str, new_name: str) -> None:
        """Copy workspace template"""
        template_path = self.workspaces_dir / template_name
        new_path = self.workspaces_dir / new_name
        
        # Copy config files
        config_files = ['config.yml', 'profiles.yml']
        for config_file in config_files:
            src = template_path / config_file
            if src.exists():
                shutil.copy2(src, new_path / config_file)
    
    def _create_default_workspace_config(self, workspace_path: Path) -> None:
        """Create default workspace configuration"""
        config_content = """# Workspace-specific configuration
# This file overrides global configuration for this workspace

# Example workspace settings:
# repo:
#   path: /path/to/your/project
#   exclude:
#     - "test_data/"
#     - "*.log"
# 
# mode: deep
# 
# domain:
#   profiles:
#     - web3:solidity
# 
# output:
#   dir: ./reports
"""
        
        config_file = workspace_path / "config.yml"
        with open(config_file, 'w') as f:
            f.write(config_content)
    
    def use_workspace(self, name: str) -> None:
        """Switch to a workspace"""
        if not self.workspace_exists(name):
            raise ValueError(f"Workspace does not exist: {name}")
        
        self.current_workspace = name
        self._save_current_workspace()
        
    def configure_workspace_paths(self, config_manager) -> None:
        """Configure output paths to use current workspace directories"""
        if not self.current_workspace:
            return
            
        # Set workspace-specific output directories
        reports_dir = self.get_reports_dir()
        logs_dir = self.get_logs_dir()
        
        if reports_dir:
            config_manager.set('output.dir', reports_dir)
        if logs_dir:
            config_manager.set('logging.file', f"{logs_dir}/securecli.log")
    
    def delete_workspace(self, name: str, force: bool = False) -> None:
        """
        Delete a workspace
        
        Args:
            name: Workspace name
            force: Force deletion without confirmation
        """
        if not self.workspace_exists(name):
            raise ValueError(f"Workspace does not exist: {name}")
        
        if name == self.current_workspace:
            self.current_workspace = None
            self._save_current_workspace()
        
        workspace_path = self.workspaces_dir / name
        
        if not force:
            # TODO: Add confirmation in CLI
            pass
        
        shutil.rmtree(workspace_path)
    
    def get_workspace_path(self, name: Optional[str] = None) -> Optional[str]:
        """Get path to workspace"""
        workspace_name = name or self.current_workspace
        
        if not workspace_name:
            return None
        
        if self.workspace_exists(workspace_name):
            return str(self.workspaces_dir / workspace_name)
        
        return None
    
    def get_workspace_config(self, name: Optional[str] = None) -> ConfigManager:
        """Get configuration manager for workspace"""
        workspace_name = name or self.current_workspace
        
        if not workspace_name or not self.workspace_exists(workspace_name):
            # Return default config manager
            return ConfigManager()
        
        workspace_path = self.workspaces_dir / workspace_name
        config_file = workspace_path / "config.yml"
        
        # Create config manager with workspace config
        config_manager = ConfigManager(str(config_file) if config_file.exists() else None)
        
        # Load workspace-specific overrides
        if config_file.exists():
            config_manager.load_workspace_config(str(workspace_path))
        
        return config_manager
    
    def get_workspace_metadata(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get workspace metadata"""
        workspace_name = name or self.current_workspace
        
        if not workspace_name or not self.workspace_exists(workspace_name):
            return {}
        
        workspace_path = self.workspaces_dir / workspace_name
        metadata_file = workspace_path / "metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {}
    
    def get_artifacts_dir(self, name: Optional[str] = None) -> Optional[str]:
        """Get artifacts directory for workspace"""
        workspace_path = self.get_workspace_path(name)
        
        if workspace_path:
            artifacts_dir = Path(workspace_path) / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)
            return str(artifacts_dir)
        
        return None
    
    def get_reports_dir(self, name: Optional[str] = None) -> Optional[str]:
        """Get reports directory for workspace"""
        workspace_path = self.get_workspace_path(name)
        
        if workspace_path:
            reports_dir = Path(workspace_path) / "reports"
            reports_dir.mkdir(exist_ok=True)
            return str(reports_dir)
        
        return None
    
    def get_cache_dir(self, name: Optional[str] = None) -> Optional[str]:
        """Get cache directory for workspace"""
        workspace_path = self.get_workspace_path(name)
        
        if workspace_path:
            cache_dir = Path(workspace_path) / "cache"
            cache_dir.mkdir(exist_ok=True)
            return str(cache_dir)
        
        return None

    def get_logs_dir(self, name: Optional[str] = None) -> Optional[str]:
        """Get logs directory for workspace"""
        workspace_path = self.get_workspace_path(name)
        
        if workspace_path:
            logs_dir = Path(workspace_path) / "logs"
            logs_dir.mkdir(exist_ok=True)
            return str(logs_dir)
        
        return None

    def get_sessions_dir(self, name: Optional[str] = None) -> Optional[str]:
        """Get sessions directory for workspace"""
        workspace_path = self.get_workspace_path(name)
        
        if workspace_path:
            sessions_dir = Path(workspace_path) / "sessions"
            sessions_dir.mkdir(exist_ok=True)
            return str(sessions_dir)
        
        return None
    
    def clean_workspace(self, name: Optional[str] = None) -> None:
        """Clean workspace cache and temporary files"""
        workspace_name = name or self.current_workspace
        
        if not workspace_name or not self.workspace_exists(workspace_name):
            return
        
        workspace_path = self.workspaces_dir / workspace_name
        
        # Clean cache directory
        cache_dir = workspace_path / "cache"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir()
        
        # Clean logs directory
        logs_dir = workspace_path / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                log_file.unlink()
    
    def export_workspace(self, name: str, export_path: str) -> None:
        """Export workspace to archive"""
        if not self.workspace_exists(name):
            raise ValueError(f"Workspace does not exist: {name}")
        
        workspace_path = self.workspaces_dir / name
        
        # Create tar.gz archive
        import tarfile
        
        with tarfile.open(export_path, 'w:gz') as tar:
            tar.add(workspace_path, arcname=name)
    
    def import_workspace(self, archive_path: str, name: Optional[str] = None) -> str:
        """Import workspace from archive"""
        import tarfile
        
        # Extract archive
        with tarfile.open(archive_path, 'r:gz') as tar:
            # Get workspace name from archive or use provided name
            if not name:
                members = tar.getnames()
                if members:
                    name = Path(members[0]).parts[0]
                else:
                    raise ValueError("Could not determine workspace name from archive")
            
            if self.workspace_exists(name):
                raise ValueError(f"Workspace already exists: {name}")
            
            # Extract to workspaces directory
            tar.extractall(self.workspaces_dir)
            
            # Rename if necessary
            extracted_path = self.workspaces_dir / Path(archive_path).stem
            final_path = self.workspaces_dir / name
            
            if extracted_path != final_path:
                extracted_path.rename(final_path)
        
        return name