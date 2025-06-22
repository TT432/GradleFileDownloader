# Cursor MCP 设置指南

## 🎯 快速配置 Cursor 使用 MCP

与 Claude Desktop 不同，Cursor 有自己的 MCP 配置方式。本指南将帮您正确配置。

## 📋 前提条件

1. **更新 Cursor**: 确保使用最新版本 (>= 0.45.7)
2. **启用 MCP**: Settings > Features > MCP Servers

## HTTP 模式（推荐）

### 1. 启动 MCP 服务器
```bash
# 在项目目录下启动服务器
uv run gfd mcp --host 127.0.0.1 --port 8001
```

### 2. 配置 Cursor
方式 A - 通过界面：
1. 打开 `Settings > MCP`
2. 点击 "Add new global MCP server"
3. 输入配置：
```json
{
  "mcpServers": {
    "gradle-file-downloader": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```