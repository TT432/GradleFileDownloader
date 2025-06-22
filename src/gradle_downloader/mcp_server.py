"""MCP Server for Gradle File Downloader.

This module provides a Model Context Protocol (MCP) server that exposes
the Gradle File Downloader functionality as tools that can be used by AI assistants.
"""

import os
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .core import RepositoryManager
from .decompiler import JavaDecompiler
from .config import config_manager
from .utils import validate_dependency_format


# Create the MCP server
mcp = FastMCP("Gradle File Downloader")

# Global instances (config_manager is already imported)


class ArtifactInfo(BaseModel):
    """Information about a downloaded artifact."""
    artifact: str = Field(description="The artifact identifier (group:name:version)")
    files: List[str] = Field(description="List of downloaded files")
    download_path: str = Field(description="Path where files were downloaded")


class RepositoryInfo(BaseModel):
    """Information about a repository."""
    name: str = Field(description="Repository name")
    url: str = Field(description="Repository URL")


@mcp.tool()
def download_artifact(
    artifact: str = Field(description="Artifact to download in format group:name:version"),
    repo_names: Optional[List[str]] = Field(default=None, description="List of repository names to use"),
    repositories: Optional[List[str]] = Field(default=None, description="List of repository URLs to use"),
    output_dir: Optional[str] = Field(default=None, description="Output directory for downloads"),
    include_sources: bool = Field(default=True, description="Include source JARs"),
    include_javadoc: bool = Field(default=True, description="Include Javadoc JARs")
) -> ArtifactInfo:
    """Download an artifact from Maven/Gradle repositories.
    
    Args:
        artifact: The artifact identifier in format group:name:version
        repo_names: List of repository names from configuration
        repositories: List of repository URLs (cannot be used with repo_names)
        output_dir: Output directory (defaults to ./downloads)
        include_sources: Whether to include source JARs
        include_javadoc: Whether to include Javadoc JARs
        
    Returns:
        Information about the downloaded artifact and files
    """
    if repo_names and repositories:
        raise ValueError("Cannot specify both repo_names and repositories")
    
    # Validate artifact format
    if not validate_dependency_format(artifact):
        raise ValueError(f"Invalid artifact format: {artifact}")
    
    # Set up output directory
    if output_dir is None:
        output_dir = "./downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize repository manager
    if repo_names:
        repo_manager = RepositoryManager(repository_names=repo_names)
    elif repositories:
        repo_manager = RepositoryManager(repositories=repositories)
    else:
        repo_manager = RepositoryManager()
    
    # Download files
    files = []
    
    # Download sources if requested
    if include_sources:
        sources_path = repo_manager.download_sources(artifact, output_dir)
        if sources_path:
            files.append(sources_path)
    
    # Download binary jar
    binary_path = repo_manager.download_binary(artifact, output_dir)
    if binary_path:
        files.append(binary_path)
    
    # Note: javadoc download is not implemented in the original code
    # if include_javadoc:
    #     # This would need to be implemented in RepositoryManager
    #     pass
    
    return ArtifactInfo(
        artifact=artifact,
        files=files,
        download_path=output_dir
    )


@mcp.tool()
def decompile_jar(
    jar_path: str = Field(description="Path to the JAR file to decompile"),
    output_dir: Optional[str] = Field(default=None, description="Output directory for decompiled sources")
) -> Dict[str, Any]:
    """Decompile a JAR file to Java source code.
    
    Args:
        jar_path: Path to the JAR file
        output_dir: Output directory (defaults to same directory as JAR)
        
    Returns:
        Information about the decompilation result
    """
    if not os.path.exists(jar_path):
        raise FileNotFoundError(f"JAR file not found: {jar_path}")
    
    if output_dir is None:
        output_dir = os.path.dirname(jar_path)
    
    decompiler = JavaDecompiler()
    success = decompiler.extract_sources_to_directory(jar_path, output_dir)
    
    return {
        "success": success,
        "jar_path": jar_path,
        "output_dir": output_dir,
        "message": "Decompilation completed successfully" if success else "Decompilation failed"
    }


@mcp.tool()
def search_versions(
    group_id: str = Field(description="Group ID of the artifact"),
    artifact_id: str = Field(description="Artifact ID"),
    repo_names: Optional[List[str]] = Field(default=None, description="List of repository names to search")
) -> Dict[str, Any]:
    """Search for available versions of an artifact.
    
    Args:
        group_id: The group ID
        artifact_id: The artifact ID
        repo_names: List of repository names to search
        
    Returns:
        Information about available versions
    """
    # Initialize repository manager
    if repo_names:
        repo_manager = RepositoryManager(repository_names=repo_names)
    else:
        repo_manager = RepositoryManager()
    
    versions = repo_manager.find_available_versions(group_id, artifact_id)
    
    return {
        "group_id": group_id,
        "artifact_id": artifact_id,
        "versions": versions,
        "total_versions": len(versions)
    }


@mcp.tool()
def check_artifact_exists(
    artifact: str = Field(description="Artifact to check in format group:name:version"),
    repo_names: Optional[List[str]] = Field(default=None, description="List of repository names to check")
) -> Dict[str, Any]:
    """Check if an artifact exists in repositories.
    
    Args:
        artifact: The artifact identifier in format group:name:version
        repo_names: List of repository names to check
        
    Returns:
        Information about artifact availability
    """
    # Validate artifact format
    if not validate_dependency_format(artifact):
        raise ValueError(f"Invalid artifact format: {artifact}")
    
    # Parse dependency
    try:
        group_id, artifact_id, version = RepositoryManager().parse_dependency(artifact)
    except ValueError as e:
        raise ValueError(f"Failed to parse artifact: {e}")
    
    # Initialize repository manager
    if repo_names:
        repo_manager = RepositoryManager(repository_names=repo_names)
    else:
        repo_manager = RepositoryManager()
    
    # Check availability in each repository
    results = {}
    repo_urls = config_manager.list_repositories()
    if repo_names:
        repo_urls = {name: url for name, url in repo_urls.items() if name in repo_names}
    
    for repo_name, repo_url in repo_urls.items():
        binary_url = repo_manager.get_artifact_url(repo_url, group_id, artifact_id, version)
        available = repo_manager.check_artifact_exists(binary_url)
        results[repo_name] = {
            "url": repo_url,
            "available": available
        }
    
    return {
        "artifact": artifact,
        "repositories": results,
        "available_in": [name for name, info in results.items() if info["available"]]
    }


@mcp.tool()
def list_repositories() -> List[RepositoryInfo]:
    """List all configured repositories.
    
    Returns:
        List of configured repositories with their names and URLs
    """
    repos = config_manager.list_repositories()
    return [RepositoryInfo(name=name, url=url) for name, url in repos.items()]


@mcp.tool()
def add_repository(
    name: str = Field(description="Repository name"),
    url: str = Field(description="Repository URL")
) -> Dict[str, Any]:
    """Add a new repository to the configuration.
    
    Args:
        name: Repository name
        url: Repository URL
        
    Returns:
        Success status and message
    """
    try:
        config_manager.add_repository(name, url)
        return {
            "success": True,
            "message": f"Repository '{name}' added successfully",
            "name": name,
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to add repository: {str(e)}"
        }


@mcp.tool()
def remove_repository(
    name: str = Field(description="Repository name to remove")
) -> Dict[str, Any]:
    """Remove a repository from the configuration.
    
    Args:
        name: Repository name to remove
        
    Returns:
        Success status and message
    """
    try:
        config_manager.remove_repository(name)
        return {
            "success": True,
            "message": f"Repository '{name}' removed successfully",
            "name": name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to remove repository: {str(e)}"
        }


@mcp.tool()
def reset_repositories() -> Dict[str, Any]:
    """Reset repositories to default configuration.
    
    Returns:
        Success status and message
    """
    try:
        config_manager.reset_to_defaults()
        repos = config_manager.list_repositories()
        return {
            "success": True,
            "message": "Repositories reset to defaults",
            "repositories": repos
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reset repositories: {str(e)}"
        }


@mcp.tool()
def get_download_stats(
    download_dir: str = Field(default="./downloads", description="Download directory to analyze")
) -> Dict[str, Any]:
    """Get statistics about downloaded files.
    
    Args:
        download_dir: Directory to analyze
        
    Returns:
        Statistics about downloaded files
    """
    if not os.path.exists(download_dir):
        return {
            "exists": False,
            "message": f"Download directory does not exist: {download_dir}"
        }
    
    # Count files by type
    stats = {
        "exists": True,
        "directory": download_dir,
        "total_files": 0,
        "jar_files": 0,
        "source_jars": 0,
        "javadoc_jars": 0,
        "pom_files": 0,
        "other_files": 0,
        "total_size_mb": 0.0
    }
    
    total_size = 0
    for root, dirs, files in os.walk(download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            total_size += file_size
            stats["total_files"] += 1
            
            if file.endswith('.jar'):
                stats["jar_files"] += 1
                if '-sources.jar' in file:
                    stats["source_jars"] += 1
                elif '-javadoc.jar' in file:
                    stats["javadoc_jars"] += 1
            elif file.endswith('.pom'):
                stats["pom_files"] += 1
            else:
                stats["other_files"] += 1
    
    stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
    return stats


if __name__ == "__main__":
    # Run the MCP server
    mcp.run() 