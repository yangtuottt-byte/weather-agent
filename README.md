# 天气 Agent

这是一个用于学习 Agent、工具调用和 MCP 的命令行项目。

## 运行

在 WSL 项目目录中激活虚拟环境后运行：

```bash
source .venv/bin/activate
python weather_agent.py
```

API Key 放在项目根目录的 `.env`：

```dotenv
DEEPSEEK_API_KEY=你的Key
```

## 目录

```text
weather_agent.py                 启动入口
src/weather_agent/main.py       Agent 主流程
src/weather_agent/local_tools.py 本地日期和天气工具
src/weather_agent/mcp_runtime.py MCP 连接、发现和调用
src/weather_agent/mcp_servers/   MCP 服务实现
examples/01_basic_agent.py      最初的加法练习
examples/archive/               过程中的旧测试脚本
.env                             本地密钥，不提交到 Git
.venv/                           Python 虚拟环境
```

在 `mcp_servers/` 中增加带有 `@mcp.tool()` 的函数，重启 Agent 后会自动发现该工具。
