# UV 开发工作流

本文档介绍如何使用 [uv](https://docs.astral.sh/uv/) 管理 Gradle File Downloader 项目。

## 什么是 uv？

uv 是一个极速的 Python 包管理器，用 Rust 编写，可以替代 pip、virtualenv、pipenv 等工具：

- ⚡ **极速**：比 pip 快 10-100 倍
- 🔒 **可靠**：内置依赖解析和锁定
- 🛠️ **现代**：支持 PEP 517/518/621 标准
- 🎯 **简单**：一个工具解决所有包管理需求

## 安装 uv

### Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 pip
```bash
pip install uv
```

## 项目设置

### 克隆项目
```bash
git clone <repository-url>
cd GradleFileDownloader
```

### 基本设置
```bash
# 创建虚拟环境 (Python 3.7+)
uv venv

# 安装项目依赖
uv sync

# 激活虚拟环境 (可选)
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### 开发环境设置
```bash
# 安装所有依赖 (包括开发依赖)
uv sync --all-extras

# 安装 pre-commit hooks
uv run pre-commit install
```

## 常用命令

### 依赖管理

```bash
# 添加新的依赖
uv add requests

# 添加开发依赖
uv add --dev pytest

# 移除依赖
uv remove requests

# 同步依赖 (安装 pyproject.toml 中定义的所有依赖)
uv sync

# 更新依赖
uv lock --upgrade
uv sync
```

### 运行项目

```bash
# 运行测试
uv run python test_basic.py

# 启动 GUI
uv run gradle-downloader gui

# 使用安装的命令行工具
uv run gradle-downloader search gson
uv run gfd download com.google.gson:gson:2.8.9

# 或使用短命令
uv run gfd search gson
```

### 开发工具

```bash
# 代码格式化
uv run black src/ test_basic.py

# 代码检查
uv run flake8 src/ test_basic.py
uv run mypy src/

# 运行测试
uv run pytest

# 所有检查
uv run pre-commit run --all-files
```

### 构建和发布

```bash
# 构建项目
uv build

# 发布到测试 PyPI
uv publish --index-url https://test.pypi.org/simple/

# 发布到正式 PyPI
uv publish
```

## Makefile 集成

项目包含一个 Makefile 来简化常用命令：

```bash
# 查看所有可用命令
make help

# 安装项目依赖
make install

# 安装开发依赖
make install-dev

# 运行测试
make test-basic

# 代码检查和格式化
make lint
make format

# 启动应用
make run-gui
make run-cli ARGS="search gson"
make gfd ARGS="download com.google.gson:gson:2.8.9"

# 清理构建文件
make clean
```

## 项目结构

使用 uv 管理的项目结构：

```
GradleFileDownloader/
├── pyproject.toml          # 项目配置和依赖
├── uv.lock                 # 锁定的依赖版本 (自动生成)
├── .venv/                  # 虚拟环境 (uv 创建)
├── Makefile                # 便捷命令 (Linux/macOS)
├── scripts.ps1             # 便捷命令 (Windows)
├── requirements.txt        # pip 兼容性 (可选)
├── src/
│   └── gradle_downloader/  # 主包
└── tests/                  # 测试文件 (计划中)
```

## 配置文件说明

### pyproject.toml

核心配置文件，包含：

- **项目元数据**：名称、版本、描述、作者等
- **依赖管理**：运行时和开发依赖
- **构建配置**：如何打包项目
- **工具配置**：black、mypy、pytest 等工具的设置
- **入口点**：命令行脚本和 GUI 脚本

### uv.lock

锁定文件，包含：

- 精确的依赖版本
- 依赖的依赖 (传递依赖)
- 跨平台兼容性信息

**注意**：这个文件应该提交到版本控制系统。

## 工作流示例

### 日常开发

```bash
# 1. 获取最新代码
git pull

# 2. 同步依赖 (如果 pyproject.toml 有变化)
uv sync

# 3. 开发和测试
uv run gfd search gson
uv run python test_basic.py

# 4. 代码检查
make lint
make format

# 5. 提交代码
git add .
git commit -m "feat: add new feature"
```

### 添加新功能

```bash
# 1. 添加需要的依赖
uv add beautifulsoup4

# 2. 开发功能...

# 3. 测试
uv run python test_basic.py

# 4. 更新文档

# 5. 提交
git add .
git commit -m "feat: add HTML parsing support"
```

### 发布新版本

```bash
# 1. 更新版本号 (在 pyproject.toml 中)
# 2. 更新 CHANGELOG

# 3. 构建
uv build

# 4. 测试发布
uv publish --index-url https://test.pypi.org/simple/

# 5. 正式发布
uv publish

# 6. 创建 git tag
git tag v1.0.1
git push --tags
```

## 故障排除

### 常见问题

1. **虚拟环境问题**
   ```bash
   # 删除并重新创建
   rm -rf .venv
   uv venv
   uv sync
   ```

2. **依赖冲突**
   ```bash
   # 强制更新依赖解析
   uv lock --upgrade
   uv sync
   ```

3. **缓存问题**
   ```bash
   # 清除 uv 缓存
   uv cache clean
   ```

4. **权限问题** (Windows)
   ```powershell
   # 以管理员身份运行 PowerShell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### 性能提示

- **并行安装**：uv 自动并行下载和安装包
- **缓存优化**：uv 智能缓存避免重复下载
- **网络优化**：使用最近的 PyPI 镜像

## 迁移指南

### 从 pip 迁移

如果已有 `requirements.txt`：

```bash
# 1. 创建 pyproject.toml (或手动转换)
uv init

# 2. 添加依赖
uv add -r requirements.txt

# 3. 移除旧文件 (可选)
rm requirements.txt
```

### 从 pipenv 迁移

```bash
# 1. 导出依赖
pipenv requirements > requirements.txt

# 2. 用 uv 安装
uv add -r requirements.txt

# 3. 清理
rm Pipfile Pipfile.lock requirements.txt
```

## 最佳实践

1. **总是使用 `uv sync`** 而不是 `uv add` 来安装已定义的依赖
2. **提交 `uv.lock`** 到版本控制确保可重现的构建
3. **使用 `--dev`** 标志管理开发依赖
4. **定期更新依赖** 使用 `uv lock --upgrade`
5. **使用 Makefile** 简化常用命令

## 参考资源

- [uv 官方文档](https://docs.astral.sh/uv/)
- [Python 打包指南](https://packaging.python.org/)
- [PEP 621](https://peps.python.org/pep-0621/) - pyproject.toml 标准 