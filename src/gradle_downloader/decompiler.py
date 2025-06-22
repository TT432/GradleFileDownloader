"""
反编译模块
使用 CFR 反编译器将 JAR 文件反编译为源码
"""

import os
import subprocess
import tempfile
import zipfile
import shutil
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

class JavaDecompiler:
    """Java 反编译器"""
    
    CFR_DOWNLOAD_URL = "https://github.com/leibnitz27/cfr/releases/latest/download/cfr-0.152.jar"
    
    def __init__(self, cfr_path: Optional[str] = None):
        self.cfr_path = cfr_path
        if not self.cfr_path:
            self.cfr_path = self._ensure_cfr_available()
    
    def _ensure_cfr_available(self) -> str:
        """确保 CFR 反编译器可用"""
        cfr_dir = os.path.join(os.path.expanduser("~"), ".gradle_downloader")
        cfr_path = os.path.join(cfr_dir, "cfr.jar")
        
        if os.path.exists(cfr_path):
            return cfr_path
        
        logger.info("Downloading CFR decompiler...")
        os.makedirs(cfr_dir, exist_ok=True)
        
        try:
            response = requests.get(self.CFR_DOWNLOAD_URL, stream=True)
            response.raise_for_status()
            
            with open(cfr_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"CFR decompiler downloaded to: {cfr_path}")
            return cfr_path
            
        except Exception as e:
            logger.error(f"Failed to download CFR decompiler: {e}")
            raise
    
    def check_java_available(self) -> bool:
        """检查 Java 是否可用"""
        try:
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def decompile_jar(self, jar_path: str, output_dir: str, callback=None) -> bool:
        """
        反编译 JAR 文件
        
        Args:
            jar_path: JAR 文件路径
            output_dir: 输出目录
            callback: 进度回调函数
            
        Returns:
            是否成功反编译
        """
        if not os.path.exists(jar_path):
            logger.error(f"JAR file not found: {jar_path}")
            return False
        
        if not self.check_java_available():
            logger.error("Java is not available. Please install Java to use decompilation feature.")
            return False
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 使用 CFR 反编译
            cmd = [
                'java', '-jar', self.cfr_path,
                jar_path,
                '--outputdir', output_dir,
                '--silent', 'true',
                '--recover', 'true',
                '--allowcorrecting', 'true',
                '--caseinsensitivefs', 'true'
            ]
            
            if callback:
                callback(0, 100, "Starting decompilation...")
            
            logger.info(f"Decompiling {jar_path} to {output_dir}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                if callback:
                    callback(100, 100, "Decompilation completed")
                logger.info(f"Successfully decompiled {jar_path}")
                return True
            else:
                logger.error(f"Decompilation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Decompilation timed out")
            return False
        except Exception as e:
            logger.error(f"Decompilation error: {e}")
            return False
    
    def create_sources_jar(self, decompiled_dir: str, output_jar_path: str) -> bool:
        """
        将反编译的源码打包成 sources JAR
        
        Args:
            decompiled_dir: 反编译的源码目录
            output_jar_path: 输出的 sources JAR 路径
            
        Returns:
            是否成功创建
        """
        try:
            os.makedirs(os.path.dirname(output_jar_path), exist_ok=True)
            
            with zipfile.ZipFile(output_jar_path, 'w', zipfile.ZIP_DEFLATED) as jar_file:
                for root, dirs, files in os.walk(decompiled_dir):
                    for file in files:
                        if file.endswith('.java'):
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, decompiled_dir)
                            jar_file.write(file_path, arc_name)
            
            logger.info(f"Created sources JAR: {output_jar_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create sources JAR: {e}")
            return False
    
    def decompile_and_package(self, jar_path: str, output_dir: str = "downloads", callback=None) -> Optional[str]:
        """
        反编译 JAR 并打包成 sources JAR
        
        Args:
            jar_path: 原始 JAR 文件路径
            output_dir: 输出目录
            callback: 进度回调函数
            
        Returns:
            生成的 sources JAR 路径，失败时返回 None
        """
        # 创建临时目录用于反编译
        with tempfile.TemporaryDirectory() as temp_dir:
            decompiled_dir = os.path.join(temp_dir, "decompiled")
            
            # 反编译
            if not self.decompile_jar(jar_path, decompiled_dir, callback):
                return None
            
            # 生成 sources JAR 路径
            jar_name = os.path.basename(jar_path)
            if jar_name.endswith('.jar'):
                jar_name = jar_name[:-4]
            sources_jar_name = f"{jar_name}-sources.jar"
            sources_jar_path = os.path.join(output_dir, sources_jar_name)
            
            # 打包成 sources JAR
            if self.create_sources_jar(decompiled_dir, sources_jar_path):
                return sources_jar_path
            
        return None
    
    def extract_sources_to_directory(self, jar_path: str, output_dir: str, callback=None) -> bool:
        """
        反编译 JAR 并提取源码到目录
        
        Args:
            jar_path: 原始 JAR 文件路径
            output_dir: 输出目录
            callback: 进度回调函数
            
        Returns:
            是否成功
        """
        return self.decompile_jar(jar_path, output_dir, callback) 