# 开发指南 - 使用 uv 运行和调试

本指南说明如何使用 `uv` 在本地运行和调试 mcp-slicer 项目。

## 前提条件

1. **安装 Python 3.13+**

   - 确保已安装 Python 3.13 或更高版本
   - 项目已配置 `.python-version` 文件，指定使用 Python 3.13

2. **安装 uv**
   - Windows:
     ```powershell
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - Mac:
     ```bash
     brew install uv
     ```
   - 其他平台: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

## 项目设置

### 1. 同步依赖

使用 `uv sync` 创建虚拟环境并安装所有依赖：

```bash
uv sync
```

这会：

- 创建虚拟环境（如果不存在）
- 根据 `pyproject.toml` 和 `uv.lock` 安装所有依赖
- 在开发模式下安装项目本身

### 2. 激活虚拟环境（可选）

虽然 `uv run` 会自动使用虚拟环境，但如果你想手动激活：

```bash
# Windows (Git Bash)
source .venv/Scripts/activate

# 或者直接使用 uv 的虚拟环境
uv venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows CMD
```

## 运行项目

### 方式 1: 使用 uv run（推荐）

直接运行项目：

```bash
uv run mcp-slicer
```

或者使用 Python 模块方式：

```bash
uv run python -m mcp_slicer.main
```

### 方式 2: 使用 uvx（全局运行）

如果你已经安装了项目，可以使用：

```bash
uvx mcp-slicer
```

### 方式 3: 在开发模式下运行

使用 `uv run` 执行入口脚本：

```bash
uv run python src/mcp_slicer/main.py
```

## 调试项目

### 使用 Python 调试器 (pdb)

在代码中添加断点：

```python
import pdb; pdb.set_trace()
```

然后运行：

```bash
uv run python src/mcp_slicer/main.py
```

### 使用 VS Code 调试

1. 创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: MCP Slicer",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/src/mcp_slicer/main.py",
      "console": "integratedTerminal",
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "python": "${workspaceFolder}/.venv/Scripts/python.exe"
    }
  ]
}
```

2. 在代码中设置断点
3. 按 F5 开始调试

### 使用命令行调试

运行并启用调试模式：

```bash
# 使用 Python 的 -m pdb 模块
uv run python -m pdb src/mcp_slicer/main.py

# 或使用 ipdb（如果已安装）
uv run ipdb src/mcp_slicer/main.py
```

## 开发模式安装

如果你想在开发模式下安装项目，使代码更改立即生效：

```bash
uv sync --dev
```

或者使用 pip 的开发模式：

```bash
uv pip install -e .
```

## 测试 MCP 服务器

MCP 服务器通常通过 stdio 与客户端通信。要测试服务器：

1. **确保 3D Slicer Web Server 正在运行**

   - 打开 3D Slicer
   - 启用 Web Server 模块
   - 确保端口 2016 可用

2. **直接运行服务器**（用于测试）：

```bash
uv run mcp-slicer
```

## 通过网页调试查看 MCP 工具

### 方法 1: 使用 MCP Inspector（推荐）

MCP Inspector 提供了一个网页界面，可以交互式地查看和测试 MCP 服务器提供的工具。

#### 安装 MCP Inspector

MCP Inspector 需要通过 Node.js 和 npm 安装：

```bash
# 确保已安装 Node.js (https://nodejs.org/)
# 然后全局安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector
```

#### 使用 MCP Inspector

1. **确保 3D Slicer Web Server 正在运行**：

   - 打开 3D Slicer
   - 启用 Web Server 模块
   - 确保端口 2016 可用

2. **启动 MCP Inspector**（会自动启动 mcp-slicer 服务器）：

```bash
# 方式 1: 使用 uvx 方式运行（推荐）
mcp-inspector uvx mcp-slicer

# 方式 2: 使用 uv run 方式
mcp-inspector uv run mcp-slicer

# 方式 3: 直接运行 Python 模块
mcp-inspector uv run python -m mcp_slicer.main
```

**注意**：MCP Inspector 会自动启动 mcp-slicer 服务器，你不需要单独运行 `uv run mcp-slicer`。

3. **访问网页界面**：

   - MCP Inspector 会自动启动一个本地 Web 服务器
   - 打开浏览器，访问 `http://localhost:5173`（默认端口）
   - 如果端口被占用，检查终端输出，会显示实际使用的端口

4. **在网页界面中**：

   - **Tools 选项卡**：查看所有可用的工具列表

     - `list_nodes` - 列出 Slicer MRML 节点
     - `execute_python_code` - 在 Slicer 中执行 Python 代码
     - `capture_screenshot` - 捕获 Slicer 视图截图

   - **测试工具**：点击任意工具，输入参数，然后点击 "Call Tool" 测试

   - **查看响应**：查看工具返回的结果和错误信息

#### 使用 Python 版本的 MCP Inspector（如果可用）

如果 MCP Python SDK 提供了 inspector 工具：

```bash
# 安装 MCP inspector（如果作为 Python 包提供）
uv add mcp-inspector

# 运行 inspector
uv run mcp-inspector uv run mcp-slicer
```

### 方法 2: 使用命令行查看工具列表

如果你想快速查看服务器提供的工具，可以使用项目中的测试脚本：

```bash
uv run python test_tools.py
```

这个脚本会列出所有可用的工具及其参数说明。

### 方法 3: 直接查看源代码

项目定义了三个主要工具，可以在 `src/mcp_slicer/mcp_server.py` 中查看：

1. **`list_nodes`** - 列出和过滤 Slicer MRML 节点
2. **`execute_python_code`** - 在 Slicer 环境中执行 Python 代码
3. **`capture_screenshot`** - 捕获 Slicer 视图的实时截图

### 调试技巧

1. **查看服务器日志**：
   MCP 服务器通过 stdio 通信，错误信息会输出到控制台

2. **测试单个工具**：
   使用 MCP Inspector 的网页界面，可以单独测试每个工具，无需完整的客户端

3. **检查 Slicer Web Server 连接**：
   确保 3D Slicer 的 Web Server 正在运行：

   ```bash
   # 测试连接
   curl http://localhost:2016/slicer/mrml/names
   ```

4. **查看工具参数**：
   在 MCP Inspector 网页界面中，每个工具都会显示详细的参数说明和示例

## 常见问题

### 问题 1: Python 版本不匹配

如果遇到 Python 版本错误：

```bash
# 检查当前 Python 版本
python --version

# 使用 uv 指定 Python 版本
uv sync --python 3.13
```

### 问题 2: 依赖安装失败

```bash
# 清理并重新同步
rm -rf .venv
uv sync
```

### 问题 3: 虚拟环境路径问题

确保使用项目根目录下的虚拟环境：

```bash
# 检查虚拟环境位置
uv venv --python 3.13
```

## 开发工作流

典型的开发工作流：

```bash
# 1. 克隆项目后，首次设置
uv sync

# 2. 进行代码修改

# 3. 运行测试
uv run python src/mcp_slicer/main.py

# 4. 如果修改了依赖，更新锁文件
uv lock

# 5. 重新同步
uv sync
```

## 环境变量

如果需要设置环境变量：

```bash
# Windows
set SLICER_WEB_SERVER_URL=http://localhost:2016/slicer
uv run mcp-slicer

# Linux/Mac
SLICER_WEB_SERVER_URL=http://localhost:2016/slicer uv run mcp-slicer
```

## 在 Cursor 中配置本地开发版本

要在 Cursor 中使用本地开发版本的 mcp-slicer 进行调试，需要在 MCP 配置文件中指定本地路径。

### 配置方法

编辑 `~/.cursor/mcp.json`（Windows: `%USERPROFILE%\.cursor\mcp.json`），添加以下配置：

```json
{
  "mcpServers": {
    "slicer": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_slicer.main"],
      "cwd": "D:\\ClineWorkSpace\\mcp-slicer",
      "env": {}
    }
  }
}
```

**配置说明**：

- `command`: 使用 `uv` 命令
- `args`: 使用 `uv run` 运行 Python 模块
- `cwd`: 项目根目录的绝对路径（Windows 使用双反斜杠 `\\`）
- `env`: 可以添加环境变量，例如：
  ```json
  "env": {
    "SLICER_WEB_SERVER_URL": "http://localhost:2016/slicer"
  }
  ```

### 替代配置方案

#### 方案 1: 使用虚拟环境中的 Python（不推荐，但可用）

如果 `uv` 不在 PATH 中，可以直接使用虚拟环境中的 Python：

```json
{
  "mcpServers": {
    "slicer": {
      "command": "D:\\ClineWorkSpace\\mcp-slicer\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_slicer.main"],
      "cwd": "D:\\ClineWorkSpace\\mcp-slicer",
      "env": {
        "PYTHONPATH": "D:\\ClineWorkSpace\\mcp-slicer\\src"
      }
    }
  }
}
```

#### 方案 2: 使用 uvx（如果已发布到 PyPI）

如果你想测试发布版本：

```json
{
  "mcpServers": {
    "slicer": {
      "command": "uvx",
      "args": ["mcp-slicer"],
      "env": {}
    }
  }
}
```

### 验证配置

1. **重启 Cursor**：修改 MCP 配置后需要重启 Cursor 才能生效

2. **检查 MCP 服务器状态**：

   - 在 Cursor 中，你应该能看到 MCP 服务器的连接状态
   - 如果连接失败，检查 Cursor 的日志或输出面板

3. **测试工具**：
   - 在 Cursor 中尝试使用 `@slicer` 查看可用的工具
   - 确保 3D Slicer Web Server 正在运行

### 调试提示

- **查看日志**：MCP 服务器通过 stdio 通信，错误信息会出现在 Cursor 的 MCP 日志中
- **代码热重载**：修改代码后，需要重启 Cursor 或重新连接 MCP 服务器才能生效
- **环境变量**：可以在 `env` 字段中设置 `SLICER_WEB_SERVER_URL` 来覆盖默认的 Slicer 服务器地址

## 更多信息

- [uv 官方文档](https://docs.astral.sh/uv/)
- [MCP 协议文档](https://modelcontextprotocol.io/)
- [3D Slicer Web Server 文档](https://slicer.readthedocs.io/en/latest/user_guide/modules/webserver.html)
- [Cursor MCP 配置文档](https://docs.cursor.com/mcp)
