# OpenSpec MCP 使用指南

## 什么是 MCP 服务器？

MCP (Model Context Protocol) 服务器是一个后台服务，它让 AI 助手（如 Cursor）能够调用特定的工具。OpenSpec MCP 服务器提供了管理 OpenSpec 项目的工具。

## 重要概念

### MCP 服务器不是命令行工具！

当你运行 `python -m openspec_mcp` 时，服务器会启动并等待接收命令。它**不会**显示帮助信息或交互式界面。

```bash
# ❌ 错误用法 - 这会让服务器等待输入
python -m openspec_mcp --help

# ✅ 正确用法 - 通过 MCP Inspector 测试
npx @modelcontextprotocol/inspector python -m openspec_mcp

# ✅ 正确用法 - 在 Cursor 中配置使用
# （见下文配置说明）
```

## 使用方式

### 方式 1: 使用 MCP Inspector 测试（开发/调试）

MCP Inspector 是一个 Web 界面，用于测试 MCP 服务器。

#### 启动 Inspector

```bash
cd openspec-mcp
npx @modelcontextprotocol/inspector python -m openspec_mcp
```

这会：
1. 启动 MCP 服务器
2. 打开浏览器显示 Inspector 界面
3. 显示所有可用的工具

#### 在 Inspector 中测试

1. **查看工具列表**
   - 左侧 "Tools" 面板显示所有可用工具
   - 点击工具名称查看详情

2. **测试工具调用**
   - 选择一个工具（如 `init_openspec`）
   - 填写参数（如果需要）
   - 点击 "Call Tool" 按钮
   - 查看返回结果

3. **示例测试流程**
   ```
   1. 选择 init_openspec 工具
   2. 不需要参数，直接点击 Call Tool
   3. 查看返回结果：
      {
        "success": true,
        "message": "OpenSpec initialized successfully",
        "data": {...}
      }
   
   4. 选择 list_changes 工具
   5. 点击 Call Tool
   6. 查看当前的变更列表
   ```

### 方式 2: 在 Cursor 中配置使用（实际工作）

这是日常使用的方式。配置后，Cursor 中的 AI 可以自动调用 OpenSpec 工具。

#### 步骤 1: 创建配置文件

在你的**用户目录**创建配置文件：

**Windows:**
```
C:\Users\你的用户名\.kiro\settings\mcp.json
```

**macOS/Linux:**
```
~/.kiro/settings/mcp.json
```

#### 步骤 2: 添加配置

将以下内容复制到 `mcp.json`：

```json
{
  "mcpServers": {
    "openspec": {
      "command": "python",
      "args": ["-m", "openspec_mcp"],
      "env": {
        "OPENSPEC_DEBUG": "false"
      },
      "disabled": false,
      "autoApprove": [
        "list_changes",
        "list_specs",
        "show_change",
        "read_spec",
        "read_tasks"
      ]
    }
  }
}
```

**配置说明：**
- `command`: 使用 `python` 命令
- `args`: 运行 `openspec_mcp` 模块
- `autoApprove`: 自动批准只读操作（提高速度）
- `disabled`: 设为 `false` 启用服务器

#### 步骤 3: 重启 Cursor

配置文件修改后，需要重启 Cursor 才能生效。

#### 步骤 4: 测试连接

在 Cursor 中问 AI：

```
你好，请列出所有 OpenSpec 变更
```

或者：

```
What OpenSpec tools are available?
```

如果配置成功，AI 会调用 `list_changes` 工具并返回结果。

### 方式 3: 在项目中配置（推荐）

如果你想在特定项目中使用，可以在项目根目录创建配置：

```
你的项目/.kiro/settings/mcp.json
```

使用相同的配置内容。这样配置只对当前项目生效。

## 实际使用示例

配置完成后，你可以在 Cursor 中这样使用：

### 初始化 OpenSpec

```
你: 请在这个项目中初始化 OpenSpec

AI: [调用 init_openspec 工具]
    ✓ OpenSpec 已初始化
    创建了以下目录：
    - openspec/specs/
    - openspec/changes/
    - openspec/project.md
```

### 创建变更提案

```
你: 创建一个添加用户认证功能的变更提案

AI: [调用 create_proposal 工具]
    ✓ 变更提案已创建：openspec/changes/add-user-auth
    
    [调用 show_change 工具]
    我已经创建了初始提案，包含：
    - proposal.md：变更说明
    - tasks.md：5 个实现任务
    - specs/auth/spec.md：需求规格
    
    需要我帮你完善内容吗？
```

### 查看进度

```
你: 显示所有变更的进度

AI: [调用 list_changes 工具]
    当前有 2 个活跃变更：
    
    1. add-user-auth (40% 完成)
       - 2/5 任务已完成
    
    2. update-payment (75% 完成)
       - 6/8 任务已完成
```

### 更新任务状态

```
你: 把 add-user-auth 的第一个任务标记为完成

AI: [调用 update_task_status 工具]
    ✓ 任务 1 已标记为完成
    进度：3/5 任务 (60%)
```

## 调试技巧

### 启用调试模式

在配置中添加：

```json
{
  "mcpServers": {
    "openspec": {
      "command": "python",
      "args": ["-m", "openspec_mcp"],
      "env": {
        "OPENSPEC_DEBUG": "true",
        "OPENSPEC_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### 查看日志

日志会输出到 Cursor 的开发者控制台（stderr）。

在 Cursor 中：
1. 打开开发者工具（通常是 F12 或 Ctrl+Shift+I）
2. 查看 Console 标签
3. 搜索 "openspec_mcp" 查看日志

### 常见问题

#### 1. "MCP server not responding"

**原因**：配置文件有语法错误或路径不对

**解决**：
- 检查 JSON 语法（使用 JSON 验证器）
- 确认 Python 在 PATH 中：`python --version`
- 确认包已安装：`pip show openspec-mcp`

#### 2. "OpenSpec not initialized"

**原因**：项目还没有初始化 OpenSpec

**解决**：
```
你: 请初始化 OpenSpec
```

#### 3. AI 没有调用工具

**原因**：配置可能没有生效

**解决**：
- 重启 Cursor
- 检查配置文件路径
- 明确要求 AI 使用工具：
  ```
  请使用 OpenSpec MCP 工具列出所有变更
  ```

## 开发模式配置

如果你在开发 OpenSpec MCP，使用这个配置：

```json
{
  "mcpServers": {
    "openspec-dev": {
      "command": "python",
      "args": ["-m", "openspec_mcp"],
      "env": {
        "OPENSPEC_DEBUG": "true",
        "PYTHONPATH": "D:/github/specMcp/openspec-mcp/src"
      },
      "disabled": false
    }
  }
}
```

这样会使用本地源码而不是安装的包。

## 发布后使用 uvx

发布到 PyPI 后，可以使用更简单的配置：

```json
{
  "mcpServers": {
    "openspec": {
      "command": "uvx",
      "args": ["openspec-mcp"],
      "disabled": false,
      "autoApprove": [
        "list_changes",
        "list_specs",
        "show_change",
        "read_spec",
        "read_tasks"
      ]
    }
  }
}
```

`uvx` 会自动下载和运行最新版本，无需手动安装。

## 总结

### MCP 服务器的工作原理

```
┌─────────────┐
│   Cursor    │  用户在 Cursor 中与 AI 对话
└──────┬──────┘
       │
       │ AI 决定调用工具
       ▼
┌─────────────┐
│ MCP Client  │  Cursor 内置的 MCP 客户端
└──────┬──────┘
       │
       │ 通过 stdio 发送 JSON-RPC 请求
       ▼
┌─────────────┐
│ MCP Server  │  OpenSpec MCP 服务器
│(openspec-mcp)│  处理请求并返回结果
└──────┬──────┘
       │
       │ 读写文件
       ▼
┌─────────────┐
│  openspec/  │  你的 OpenSpec 项目文件
│  ├─ specs/  │
│  └─ changes/│
└─────────────┘
```

### 关键点

1. **MCP 服务器不是 CLI 工具**
   - 不要直接运行 `python -m openspec_mcp`
   - 通过 Inspector 或 Cursor 使用

2. **配置文件很重要**
   - 必须正确配置才能在 Cursor 中使用
   - 修改后需要重启 Cursor

3. **调试使用 Inspector**
   - 开发和测试时使用 Inspector
   - 可以直接看到工具调用和返回结果

4. **实际使用在 Cursor 中**
   - 配置好后，自然地与 AI 对话
   - AI 会自动决定何时调用工具

## 下一步

1. ✅ 使用 MCP Inspector 测试所有工具
2. ✅ 在 Cursor 中配置 MCP 服务器
3. ✅ 创建一个测试项目试用
4. ✅ 阅读 PUBLISHING.md 了解如何发布到 PyPI

需要帮助？查看 [QUICKSTART.md](QUICKSTART.md) 或 [README.md](README.md)。
