# Gradle File Downloader

一个功能强大的 Python 工具，用于从 Gradle/Maven 仓库下载依赖的源码文件。当源码不可用时，自动使用反编译器生成源码。

## 功能特性

- 🔍 **智能下载**：优先下载 `-sources.jar` 文件，不存在时自动下载并反编译二进制 JAR
- 🌐 **多仓库支持**：默认支持 Maven Central、Apache Maven 等主流仓库，支持配置自定义仓库
- 🔧 **仓库管理**：轻松添加、删除、切换仓库，支持指定特定仓库进行下载
- 🖥️ **双界面模式**：提供命令行 (CLI) 和图形用户界面 (GUI)
- 🎨 **可视化仓库管理**：GUI 提供直观的仓库管理界面，无需命令行操作
- 🔧 **高级反编译**：使用 CFR 反编译器，自动处理依赖关系
- 📦 **批量处理**：支持搜索、版本查询等实用功能
- 🚀 **现代化设计**：美观的 GUI 界面和友好的 CLI 体验

## 安装

### 前置要求

- Python 3.7+
- Java 8+ (用于反编译功能)
- [uv](https://docs.astral.sh/uv/) (推荐) 或 pip

### 使用 uv 安装 (推荐)

```bash
# 安装 uv (如果还没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 使用 pip 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

## 🎯 开始使用

### 使用 uv (推荐)
1. **安装 uv**：`curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **设置项目**：`uv venv && uv sync`
3. **测试功能**：`uv run python test_basic.py`
4. **启动工具**：`uv run gradle-downloader --help` 或 `uv run gfd --help`

### 使用 pip
1. **安装依赖**：`pip install -r requirements.txt`
2. **测试功能**：`python test_basic.py`
3. **启动工具**：`pip install -e .` 然后 `gradle-downloader --help`

## 使用方法

### 图形界面 (GUI)

启动图形界面：

```bash
# 使用 uv
uv run gradle-downloader gui

# 或使用 pip (先安装项目)
pip install -e .
gradle-downloader gui
```

GUI 功能：
- **下载源码标签页**：输入依赖信息，选择仓库和输出目录，一键下载
- **仓库选择**：支持从配置的仓库中选择或使用全部仓库
- **仓库管理标签页**：可视化管理所有仓库配置
  - 查看所有已配置的仓库列表
  - 添加新仓库（输入名称和URL）
  - 删除选中的仓库
  - 一键重置为默认仓库配置
- **反编译 JAR 标签页**：选择本地 JAR 文件进行反编译
- **实时日志**：显示下载和反编译过程
- **进度显示**：实时更新操作状态

### 命令行 (CLI)

#### 下载依赖源码

```bash
# 基本用法
uv run gradle-downloader download com.google.guava:guava:31.1-jre
# 或使用短命令
uv run gfd download com.google.guava:guava:31.1-jre

# 指定输出目录
uv run gfd download com.google.gson:gson:2.8.9 -o ./sources

# 指定使用特定仓库
uv run gfd download com.google.guava:guava:31.1-jre --repo-names maven-central

# 仅下载源码（不反编译）
uv run gfd download com.google.guava:guava:31.1-jre --sources-only

# 强制下载二进制包并反编译
uv run gfd download com.google.gson:gson:2.8.9 --force-binary

# 使用自定义仓库 URL
uv run gfd download org.springframework:spring-core:5.3.21 -r https://repo.spring.io/milestone/
```

#### 搜索依赖

```bash
# 搜索相关依赖
uv run gfd search guava

# 限制搜索结果数量
uv run gfd search "google gson" -n 5
```

#### 查询版本

```bash
# 查询可用版本
uv run gfd versions com.google.guava:guava
uv run gfd versions org.springframework:spring-core
```

#### 反编译 JAR 文件

```bash
# 反编译本地 JAR 文件
uv run gfd decompile ./mylib.jar -o ./decompiled
```

#### 启动 GUI

```bash
# 启动图形界面
uv run gradle-downloader gui
```

#### 仓库管理

```bash
# 列出所有配置的仓库
uv run gfd repo list

# 添加新仓库
uv run gfd repo add my-repo https://my.repo.com/maven/

# 删除仓库
uv run gfd repo remove my-repo

# 重置为默认仓库配置
uv run gfd repo reset
```

### 支持的依赖格式

工具支持以下两种依赖格式：

1. **标准格式**：`group:artifact:version`
   ```
   com.google.guava:guava:31.1-jre
   org.springframework:spring-core:5.3.21
   ```

2. **简化格式**：`group.artifact:version`
   ```
   com.google.guava:31.1-jre
   org.springframework.core:5.3.21
   ```

## 配置选项

### 仓库配置

#### 默认仓库

工具默认使用以下仓库（按优先级排序）：

1. **maven-central**: `https://repo1.maven.org/maven2/`
2. **apache-maven**: `https://repo.maven.apache.org/maven2/`
3. **jcenter**: `https://jcenter.bintray.com/`

#### 仓库管理

仓库配置保存在用户目录的 `~/.gradle-downloader/config.json` 文件中。

**添加仓库**：
```bash
# 添加新仓库
uv run gfd repo add spring-milestone https://repo.spring.io/milestone/
uv run gfd repo add my-nexus https://nexus.company.com/repository/maven-public/
```

**使用指定仓库**：
```bash
# 使用特定仓库下载
uv run gfd download com.example:artifact:1.0.0 --repo-names spring-milestone

# 使用多个仓库
uv run gfd download com.example:artifact:1.0.0 --repo-names maven-central,spring-milestone
```

**仓库管理命令**：
```bash
# 查看所有仓库
uv run gfd repo list

# 删除仓库
uv run gfd repo remove spring-milestone

# 重置为默认配置
uv run gfd repo reset
```

### 临时自定义仓库

也可以通过 `-r` 参数临时使用自定义仓库：

```bash
uv run gfd download group:artifact:version -r https://your-custom-repo.com/maven2/
```

### 输出目录结构

下载的文件按以下结构组织：

```
downloads/
├── com/
│   └── google/
│       └── guava/
│           └── guava/
│               └── 31.1-jre/
│                   ├── guava-31.1-jre.jar
│                   └── guava-31.1-jre-sources.jar
└── org/
    └── springframework/
        └── spring-core/
            └── 5.3.21/
                ├── spring-core-5.3.21.jar
                └── spring-core-5.3.21-sources.jar
```

## 反编译功能

### CFR 反编译器

工具使用 [CFR (Class File Reader)](https://github.com/leibnitz27/cfr) 作为 Java 反编译器：

- **自动下载**：首次使用时自动下载 CFR
- **高质量输出**：生成可读性强的 Java 源码
- **容错处理**：智能处理混淆和复杂结构

### Java 环境检查

反编译功能需要 Java 运行环境：

```bash
# 检查 Java 是否可用
java -version
```

如果没有安装 Java，请从 [Oracle](https://www.oracle.com/java/technologies/downloads/) 或 [OpenJDK](https://openjdk.org/) 下载安装。

## 高级用法

### 批量下载

创建依赖列表文件 `dependencies.txt`：

```
com.google.guava:guava:31.1-jre
com.google.gson:gson:2.8.9
org.springframework:spring-core:5.3.21
```

使用脚本批量下载：

```bash
#!/bin/bash
while IFS= read -r line; do
    if [[ ! -z "$line" && ! "$line" =~ ^#.* ]]; then
        echo "Downloading: $line"
        uv run gfd download "$line"
    fi
done < dependencies.txt
```

### 日志配置

启用详细日志：

```bash
uv run gfd download com.google.guava:guava:31.1-jre --verbose
```

保存日志到文件：

```bash
uv run gfd download com.google.guava:guava:31.1-jre --log-file ./download.log
```

## 故障排除

### 常见问题

1. **网络连接问题**
   - 检查网络连接
   - 尝试使用代理或镜像仓库

2. **Java 不可用**
   ```
   错误: 需要安装 Java 才能使用反编译功能
   ```
   - 安装 Java 8+ 运行环境
   - 确保 `java` 命令在 PATH 中

3. **依赖不存在**
   ```
   错误: 未找到二进制 JAR
   ```
   - 检查依赖格式是否正确
   - 使用搜索功能确认依赖存在
   - 尝试其他版本

4. **权限问题**
   - 确保对输出目录有写权限
   - 在 Linux/macOS 上可能需要 `sudo`

### 调试模式

启用调试输出：

```bash
uv run gfd download com.google.guava:guava:31.1-jre --verbose --log-file debug.log
```

## 项目结构

```
GradleFileDownloader/
├── pyproject.toml          # 项目配置和依赖 (uv 管理)
├── uv.lock                 # 锁定的依赖版本 (uv 生成)
├── Makefile                # 便捷的 make 命令 (Linux/macOS)
├── scripts.ps1             # 便捷的 PowerShell 脚本 (Windows)
├── requirements.txt        # Python 依赖 (pip 兼容)
├── README.md               # 项目说明文档
├── UV_WORKFLOW.md          # uv 工作流详细说明
├── LICENSE                 # MIT 许可证
├── .gitignore              # Git 忽略文件
├── test_basic.py           # 基本功能测试
├── .venv/                  # uv 虚拟环境
└── src/
    └── gradle_downloader/
        ├── __init__.py     # 包初始化
        ├── core.py         # 核心下载逻辑
        ├── decompiler.py   # 反编译功能
        ├── cli.py          # 命令行界面
        ├── gui.py          # 图形用户界面
        └── utils.py        # 工具函数
```

## 开发与贡献

### 开发环境设置

#### 使用 uv (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd GradleFileDownloader

# 创建虚拟环境并安装所有依赖 (包括开发依赖)
uv venv
uv sync --all-extras

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装开发工具
uv add --dev pytest black flake8 mypy pre-commit
```

#### 使用 pip

```bash
# 克隆项目
git clone <repository-url>
cd GradleFileDownloader

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 便捷脚本

项目提供了便捷脚本来简化常用操作：

#### Linux/macOS (Makefile)
```bash
make help           # 查看所有可用命令
make install        # 安装依赖
make test-basic     # 运行测试
make run-gui        # 启动 GUI
make run-cli ARGS="search gson"    # 运行 CLI
make gfd ARGS="download junit:junit:4.13.2"  # 快捷命令
```

#### Windows (PowerShell)
```powershell
.\scripts.ps1 help          # 查看所有可用命令
.\scripts.ps1 install       # 安装依赖
.\scripts.ps1 test-basic    # 运行测试
.\scripts.ps1 run-gui       # 启动 GUI
.\scripts.ps1 gfd search gson      # 运行 CLI
```

### 运行测试

#### 使用 uv

```bash
# 运行基本功能测试
uv run python test_basic.py

# 运行单元测试 (如果有的话)
uv run pytest

# 测试 CLI 功能
uv run gfd search gson

# 测试 GUI 功能  
uv run gradle-downloader gui

# 使用完整命令名
uv run gradle-downloader search gson
uv run gfd download com.google.gson:gson:2.8.9

# 使用便捷脚本 (Windows)
.\scripts.ps1 gfd search gson
.\scripts.ps1 gfd download com.google.gson:gson:2.8.9
```

#### 使用 pip

```bash
# 先安装项目
pip install -e .

# 测试 CLI 功能
gfd search gson

# 测试 GUI 功能
gradle-downloader gui

# 运行基本功能测试
python test_basic.py
```

## 许可证

本项目基于 MIT 许可证开源。详见 LICENSE 文件。

## 更新日志

### v1.0.0 (2024-01-01)

- ✨ 初始版本发布
- 🚀 支持从 Maven/Gradle 仓库下载源码
- 🔧 集成 CFR 反编译器
- 🖥️ 提供 CLI 和 GUI 双界面
- 📦 支持依赖搜索和版本查询

## 支持

如果您遇到问题或有功能建议，请：

1. 查看本 README 的故障排除部分
2. 查看 [UV_WORKFLOW.md](UV_WORKFLOW.md) 了解 uv 使用详情
3. 搜索现有的 Issue
4. 创建新的 Issue 并提供详细信息

## 相关文档

- [UV_WORKFLOW.md](UV_WORKFLOW.md) - uv 包管理器详细使用指南
- [pyproject.toml](pyproject.toml) - 项目配置和依赖管理
- [Makefile](Makefile) - 便捷的开发命令 (Linux/macOS)
- [scripts.ps1](scripts.ps1) - 便捷的 PowerShell 脚本 (Windows)

---

**注意**：本工具仅用于学习和研究目的。请遵守相关软件的许可证条款，尊重知识产权。 