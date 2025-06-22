"""
配置管理模块
处理仓库配置的增删改查
"""

import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    DEFAULT_REPOSITORIES = {
        "maven-central": "https://repo1.maven.org/maven2/",
        "apache-maven": "https://repo.maven.apache.org/maven2/",
        "jcenter": "https://jcenter.bintray.com/",
    }
    
    def __init__(self):
        self.config_dir = Path.home() / ".gradle-downloader"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self._load_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(exist_ok=True)
    
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                self.config = {"repositories": self.DEFAULT_REPOSITORIES.copy()}
        else:
            self.config = {"repositories": self.DEFAULT_REPOSITORIES.copy()}
        
        # 确保配置结构正确
        if "repositories" not in self.config:
            self.config["repositories"] = self.DEFAULT_REPOSITORIES.copy()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def list_repositories(self) -> Dict[str, str]:
        """列出所有仓库"""
        return self.config["repositories"].copy()
    
    def add_repository(self, name: str, url: str) -> bool:
        """添加仓库"""
        if not url.endswith('/'):
            url += '/'
        
        self.config["repositories"][name] = url
        try:
            self._save_config()
            logger.info(f"Added repository: {name} -> {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to add repository: {e}")
            return False
    
    def remove_repository(self, name: str) -> bool:
        """删除仓库"""
        if name not in self.config["repositories"]:
            return False
        
        del self.config["repositories"][name]
        try:
            self._save_config()
            logger.info(f"Removed repository: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove repository: {e}")
            return False
    
    def get_repository_url(self, name: str) -> Optional[str]:
        """获取仓库URL"""
        return self.config["repositories"].get(name)
    
    def get_repository_urls(self, names: List[str] = None) -> List[str]:
        """获取仓库URL列表"""
        if names is None:
            return list(self.config["repositories"].values())
        
        urls = []
        for name in names:
            url = self.get_repository_url(name)
            if url:
                urls.append(url)
            else:
                logger.warning(f"Repository not found: {name}")
        
        return urls
    
    def get_repository_names(self) -> List[str]:
        """获取所有仓库名称"""
        return list(self.config["repositories"].keys())
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        self.config["repositories"] = self.DEFAULT_REPOSITORIES.copy()
        try:
            self._save_config()
            logger.info("Reset repositories to defaults")
            return True
        except Exception as e:
            logger.error(f"Failed to reset config: {e}")
            return False


# 全局配置管理器实例
config_manager = ConfigManager() 