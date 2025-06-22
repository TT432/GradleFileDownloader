# MCP (Model Context Protocol) 集成

Gradle File Downloader 现在支持 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)，这允许 AI 助手直接使用我们的工具功能。通过 [FastMCP](https://gofastmcp.com/) 框架，您可以让 Claude Desktop、OpenAI API、Anthropic API 或其他支持 MCP 的客户端直接调用下载、反编译、搜索等功能。

## 快速开始

### 启动 MCP 服务器

#### STDIO 模式 (推荐用于 Claude Desktop)
```bash
uv run gfd mcp --stdio
```

#### HTTP 服务器模式 (用于其他客户端)
```bash
uv run gfd mcp --host 127.0.0.1 --port 8000
```

### Claude Desktop 集成

1. 找到 Claude Desktop 的配置文件：
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. 将以下配置添加到配置文件中：
```json
{
  "mcpServers": {
    "gradle-file-downloader": {
      "command": "uv",
      "args": [
        "run",
        "gfd",
        "mcp",
        "--stdio"
      ],
      "cwd": "/path/to/your/GradleFileDownloader"
    }
  }
}
```

3. 重启 Claude Desktop

4. 现在您可以在 Claude Desktop 中要求 AI 助手帮您下载依赖、反编译 JAR 文件等。

## 可用工具

MCP 服务器暴露了以下工具供 AI 助手使用：

### 1. download_artifact
下载 Maven/Gradle 依赖源码和文档

**参数:**
- `artifact` (必需): 格式为 `group:name:version`
- `repo_names` (可选): 仓库名称列表
- `repositories` (可选): 仓库 URL 列表
- `output_dir` (可选): 输出目录，默认为 `./downloads`
- `include_sources` (可选): 是否包含源码 JAR，默认 `true`
- `include_javadoc` (可选): 是否包含文档 JAR，默认 `true`

### 2. decompile_jar
反编译 JAR 文件为 Java 源码

**参数:**
- `jar_path` (必需): JAR 文件路径
- `output_dir` (可选): 输出目录

### 3. search_versions
搜索依赖的可用版本

**参数:**
- `group_id` (必需): Group ID
- `artifact_id` (必需): Artifact ID
- `repo_names` (可选): 搜索的仓库名称列表

### 4. check_artifact_exists
检查依赖是否存在于仓库中

**参数:**
- `artifact` (必需): 格式为 `group:name:version`
- `repo_names` (可选): 检查的仓库名称列表

### 5. list_repositories
列出所有配置的仓库

**无参数**

### 6. add_repository
添加新仓库

**参数:**
- `name` (必需): 仓库名称
- `url` (必需): 仓库 URL

### 7. remove_repository
删除仓库

**参数:**
- `name` (必需): 仓库名称

### 8. reset_repositories
重置仓库配置为默认值

**无参数**

### 9. get_download_stats
获取下载目录的统计信息

**参数:**
- `download_dir` (可选): 分析的目录，默认为 `./downloads`

## 使用示例

一旦配置完成，您可以在 Claude Desktop 中这样使用：

### 下载依赖
> "请帮我下载 Guava 31.1-jre 的源码"

Claude 会调用 `download_artifact` 工具下载 `com.google.guava:guava:31.1-jre`。

### 搜索版本
> "帮我查看 Spring Boot 有哪些可用版本"

Claude 会调用 `search_versions` 工具查找 Spring Boot 的版本。

### 仓库管理
> "添加一个名为 'spring' 的仓库，URL 是 https://repo.spring.io/milestone"

Claude 会调用 `add_repository` 工具添加仓库。

### 反编译
> "反编译这个 JAR 文件: /path/to/mylib.jar"

Claude 会调用 `decompile_jar` 工具进行反编译。

## 高级配置

### HTTP 模式配置

如果使用 HTTP 模式，您需要配置客户端连接到服务器：

```python
from fastmcp.client import FastMCPClient

client = FastMCPClient("http://127.0.0.1:8000")
result = await client.call_tool("download_artifact", {
    "artifact": "com.google.guava:guava:31.1-jre"
})
```

### 自定义工作目录

您可以通过修改 Claude Desktop 配置中的 `cwd` 参数来指定工作目录：

```json
{
  "mcpServers": {
    "gradle-file-downloader": {
      "command": "uv",
      "args": ["run", "gfd", "mcp", "--stdio"],
      "cwd": "/your/custom/working/directory"
    }
  }
}
```

## 故障排除

### 常见问题

1. **Claude Desktop 没有识别到工具**
   - 确保配置文件路径正确
   - 检查 JSON 格式是否有效
   - 重启 Claude Desktop
   - 检查工作目录路径是否正确

2. **MCP 服务器启动失败**
   - 确保安装了 `fastmcp` 依赖：`uv add fastmcp`
   - 检查 Python 环境是否正确
   - 查看错误日志

3. **工具调用失败**
   - 检查网络连接（下载工具需要访问 Maven 仓库）
   - 确保有足够的磁盘空间
   - 检查文件权限

### 日志调试

启用详细日志：
```bash
uv run gfd mcp --stdio --verbose
```

## 安全注意事项

- MCP 服务器会在您的文件系统上下载和创建文件
- 确保只从可信的仓库下载依赖
- 在生产环境中使用时，考虑限制下载目录的权限
- HTTP 模式默认只绑定到 localhost，避免暴露到公网

## 扩展和定制

如果您想添加自定义工具，可以修改 `src/gradle_downloader/mcp_server.py` 文件：

```python
@mcp.tool()
def my_custom_tool(param: str) -> str:
    """我的自定义工具"""
    # 您的逻辑
    return "结果"
```

## 相关链接

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP 文档](https://gofastmcp.com/)
- [Claude Desktop MCP 配置](https://docs.anthropic.com/claude/docs/desktop-configuration) 