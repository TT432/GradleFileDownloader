"""
核心下载逻辑模块
处理 Maven/Gradle 仓库的搜索和下载功能
"""

import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import List, Optional, Tuple, Dict
import logging

from .config import config_manager

logger = logging.getLogger(__name__)

class RepositoryManager:
    """Maven 仓库管理器"""
    
    def __init__(self, repositories: List[str] = None, repository_names: List[str] = None):
        """
        初始化仓库管理器
        
        Args:
            repositories: 直接指定仓库URL列表
            repository_names: 指定仓库名称列表（从配置中获取URL）
        """
        if repositories:
            self.repositories = repositories
        elif repository_names:
            self.repositories = config_manager.get_repository_urls(repository_names)
        else:
            self.repositories = config_manager.get_repository_urls()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GradleFileDownloader/1.0.0'
        })
    
    def parse_dependency(self, dependency: str) -> Tuple[str, str, str]:
        """
        解析依赖字符串
        支持格式：
        - group:artifact:version
        - group.artifact:version
        """
        if dependency.count(':') == 2:
            group, artifact, version = dependency.split(':')
        elif dependency.count(':') == 1:
            group_artifact, version = dependency.split(':')
            if '.' in group_artifact:
                parts = group_artifact.split('.')
                group = '.'.join(parts[:-1])
                artifact = parts[-1]
            else:
                raise ValueError("Invalid dependency format")
        else:
            raise ValueError("Invalid dependency format. Use 'group:artifact:version' or 'group.artifact:version'")
        
        return group, artifact, version
    
    def get_metadata_url(self, repo_url: str, group: str, artifact: str) -> str:
        """构建 Maven 元数据 URL"""
        group_path = group.replace('.', '/')
        return urljoin(repo_url, f"{group_path}/{artifact}/maven-metadata.xml")
    
    def get_artifact_url(self, repo_url: str, group: str, artifact: str, version: str, classifier: str = None, extension: str = "jar") -> str:
        """构建构件 URL"""
        group_path = group.replace('.', '/')
        filename = f"{artifact}-{version}"
        if classifier:
            filename += f"-{classifier}"
        filename += f".{extension}"
        return urljoin(repo_url, f"{group_path}/{artifact}/{version}/{filename}")
    
    def check_artifact_exists(self, url: str) -> bool:
        """检查构件是否存在"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            # 2xx 和 3xx 状态码都表示文件存在（包括重定向）
            return 200 <= response.status_code < 400
        except requests.RequestException:
            return False
    
    def download_file(self, url: str, output_path: str, callback=None) -> bool:
        """下载文件"""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback:
                            callback(downloaded, total_size)
            
            logger.info(f"Downloaded: {url} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def find_available_versions(self, group: str, artifact: str) -> List[str]:
        """查找可用版本"""
        versions = []
        
        for repo_url in self.repositories:
            try:
                metadata_url = self.get_metadata_url(repo_url, group, artifact)
                response = self.session.get(metadata_url, timeout=10)
                
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    versioning = root.find('versioning')
                    if versioning is not None:
                        versions_elem = versioning.find('versions')
                        if versions_elem is not None:
                            for version in versions_elem.findall('version'):
                                if version.text and version.text not in versions:
                                    versions.append(version.text)
            except Exception as e:
                logger.warning(f"Failed to get versions from {repo_url}: {e}")
        
        return sorted(versions, reverse=True)  # 最新版本在前
    
    def download_sources(self, dependency: str, output_dir: str = "downloads", callback=None) -> Optional[str]:
        """
        下载源码 JAR
        返回下载的文件路径，如果失败返回 None
        """
        try:
            group, artifact, version = self.parse_dependency(dependency)
        except ValueError as e:
            logger.error(f"Invalid dependency format: {e}")
            return None
        
        # 尝试从每个仓库下载 sources JAR
        for repo_url in self.repositories:
            sources_url = self.get_artifact_url(repo_url, group, artifact, version, "sources")
            
            if self.check_artifact_exists(sources_url):
                filename = f"{artifact}-{version}-sources.jar"
                output_path = os.path.join(output_dir, group.replace('.', os.sep), artifact, version, filename)
                
                if self.download_file(sources_url, output_path, callback):
                    return output_path
        
        logger.warning(f"Sources JAR not found for {dependency}")
        return None
    
    def download_binary(self, dependency: str, output_dir: str = "downloads", callback=None) -> Optional[str]:
        """
        下载二进制 JAR (用于反编译)
        返回下载的文件路径，如果失败返回 None
        """
        try:
            group, artifact, version = self.parse_dependency(dependency)
        except ValueError as e:
            logger.error(f"Invalid dependency format: {e}")
            return None
        
        # 尝试从每个仓库下载二进制 JAR
        for repo_url in self.repositories:
            binary_url = self.get_artifact_url(repo_url, group, artifact, version)
            
            if self.check_artifact_exists(binary_url):
                filename = f"{artifact}-{version}.jar"
                output_path = os.path.join(output_dir, group.replace('.', os.sep), artifact, version, filename)
                
                if self.download_file(binary_url, output_path, callback):
                    return output_path
        
        logger.warning(f"Binary JAR not found for {dependency}")
        return None
    
    def search_artifact(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        搜索构件 (简单实现，基于 Maven Central 搜索)
        """
        search_url = "https://search.maven.org/solrsearch/select"
        params = {
            'q': query,
            'rows': max_results,
            'wt': 'json'
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for doc in data.get('response', {}).get('docs', []):
                results.append({
                    'group': doc.get('g', ''),
                    'artifact': doc.get('a', ''),
                    'version': doc.get('latestVersion', ''),
                    'description': doc.get('description', ''),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [] 