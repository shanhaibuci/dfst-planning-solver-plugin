# Gateway MCP 接入检查与配置

## 当前接入契约

Skill 对接系统的地址只在 `../config/system-endpoint.json` 配置一次。开始接入检查前读取该文件，并使用其 `origin` 与 `mcp_path` 派生下列地址：

| 项目 | 当前值或派生规则 |
| --- | --- |
| 系统 origin | `system-endpoint.json` 的 `origin` |
| MCP Server 名 | `gateway` |
| Streamable HTTP MCP URL | `{origin}{mcp_path}` |
| PAT 环境变量 | `GATEWAY_MCP_PAT` |
| PAT 本地备选位置 | 当前项目根目录 `.env` 的 `GATEWAY_MCP_PAT` |
| PAT scope | `gateway:api` |
| 用户中心 | `{origin}/static/index.html#/account` |
| MCP 接入页 | `{origin}/static/index.html#/mcp` |

Skill 不从 `.env`、命令行参数或会话输入读取或覆盖 MCP URL。`agents/openai.yaml` 不声明 MCP dependency，避免市场安装时只生成 URL 的半成品配置；完整 MCP 配置由下面的接入工作流按客户端表面写入。

## 默认行为：正常时静默继续

只在配置缺失、配置错误、PAT 未加载、认证失败或网络不可达时提示用户。配置完整并且只读 Gateway tool 成功时，不输出接入报告，直接继续用户原始任务。

1. **先发现延迟 tools**：`gateway.image_versions.list_available` 等是逻辑名称。Codex 可能不在首轮工具列表直接展示可选 MCP tools，而只在 `ALL_TOOLS` 中提供规范化运行时名称。必须先按 `mcp__gateway__` 前缀查询 `ALL_TOOLS`；不得用 `startsWith("gateway.")` 查询运行时目录，也不得仅凭首轮静态列表缺少 `gateway.*` 判断 tools 不可见。
2. **tools 已发现**：优先调用 `mcp__gateway__gateway_image_versions_list_available`（逻辑名称 `gateway.image_versions.list_available`）作为只读验证。成功后静默继续，不输出“已重连”或其他接入报告。
3. **tools 确实不可见**：只有按 `mcp__gateway__` 正确查询延迟工具目录仍无结果，才识别当前是 VS Code Codex IDE 还是 Codex CLI，然后只执行对应路线。
4. **VS Code Codex IDE**：运行 `configure_codex_gateway_mcp.py status`，项目 `.env` 有 PAT 时紧接着运行 `verify`。`verify` 使用 `system-endpoint.json` 派生的受信 Gateway MCP URL 发送无业务数据的 `initialize`，只返回归一化状态；不要求用户运行终端命令。只有 `authenticated` 才继续本地配置或冷启动判断。状态完整、PAT 已验证、当前会话未执行 `apply` 且首次正确查询仍不可见时，才视为可能的 MCP 冷启动竞态，只请求用户在当前聊天发送一次“重试”，不提示重启扩展。下一轮必须先再次按 `mcp__gateway__` 查询并重新运行 `verify`；发现后执行只读验证并继续原任务，第二次正确查询仍不可见时才提示 **Restart extension**。
5. **Codex CLI**：使用 `codex mcp get gateway --json` 检查配置，并用 `check_gateway_pat.py` 检查环境变量或 `.env` 来源；不直接打印 `~/.codex/config.toml`。
6. **缺少 PAT**：只列出缺失项，引导用户在用户中心创建 scope 为 `gateway:api` 的 PAT，并通过安全方式存入当前项目 `.env`。不得让用户把 PAT 粘贴到对话。
7. **配置需修复**：先展示差异、目标路径、认证方式、密钥存储方式和重启影响；只在用户明确授权后执行修复。
8. **配置已更新**：只有 `verify=authenticated` 才允许执行 `apply`；完成后说明本地配置已更新且 PAT 已验证，并直接提示 **Restart extension**，不进入冷启动重试分支。
9. **认证或网络失败**：保留正确配置，只进入对应修复，不重复添加 MCP，不直连引擎。

`status` 只验证本地配置和 PAT 是否匹配，不代表 PAT 有效；`mcp_pat_config_matches_dotenv=true` 只表示两个本地值相同。`verify` 验证固定 Gateway MCP 入口是否接受 PAT，但不代表当前轮次已经取得 MCP tool。Codex 的可选 MCP tools 可能采用延迟发现；`gateway.*` 与 `mcp__gateway__*` 的名称差异不是连接失败。新会话也可能在可选 MCP server 初始化完成前冻结首轮工具目录；只有 PAT 已验证且正确查询延迟目录仍无结果时才进入这种冷启动分支并先在原聊天重试一轮。Codex 当前没有把新配置的 MCP 热加载进已运行进程的通用接口，因此 IDE 确实更新配置后仍要求重启扩展并回到原聊天；CLI 重启后用 `codex resume` 续接同一条会话。两种表面都不得要求用户新建会话或重新输入原需求。

接入阶段不展示或询问 `job_id`，除非用户明确要求查询已有任务。

## VS Code Codex IDE 自动配置

VS Code 扩展不会自动加载项目 `.env`。Agent 必须运行下列内置脚本，而不是让用户执行命令。

在运行状态脚本前，先在 Codex code-mode 的延迟目录完成一次实际发现。等价逻辑如下；运行时调用名使用 `mcp__gateway__` 前缀，文档中的 `gateway.*` 只表达用户级能力边界：

```javascript
const gatewayTools = ALL_TOOLS.filter(
  ({ name }) => name.startsWith("mcp__gateway__"),
);

if (gatewayTools.some(
  ({ name }) => name === "mcp__gateway__gateway_image_versions_list_available",
)) {
  await tools.mcp__gateway__gateway_image_versions_list_available({});
}
```

若发现 `mcp__gateway__gateway_image_versions_list_available`，立即调用对应只读 tool。只有 `gatewayTools` 为空时才继续下面的配置状态检查。用户发送“重试”后必须重新执行上述发现，不得沿用上一轮空结果。

本地只读检查：

```bash
python3 <skill-dir>/scripts/configure_codex_gateway_mcp.py status --project-root <project-root>
```

脚本只返回 PAT 来源、URL 是否匹配、认证方式和用户级配置路径，不返回 PAT 或其他配置内容。字段 `mcp_pat_config_matches_dotenv` 只表达本地配置值与 `.env` 值是否一致，不得解释为鉴权成功。

项目 `.env` 存在 PAT 时，在任何配置写入、冷启动重试或扩展重启判断前执行服务器验证：

```bash
python3 <skill-dir>/scripts/configure_codex_gateway_mcp.py verify --project-root <project-root>
```

`verify` 只向脚本从 `system-endpoint.json` 派生的受信 Gateway MCP URL 发送一次不含业务数据的 `initialize` 请求，不接受调用方覆盖 URL。输出只包含 `auth_status`、HTTP 状态和安全错误码：

- `authenticated`：PAT 已被服务器接受，可以继续检查或修复本地 MCP 配置；
- `invalid_pat`：明确提示“Gateway PAT 无效或已过期，请在用户中心重新创建 scope 为 `gateway:api` 的 PAT，并安全更新当前项目 `.env`。”停止当前路线，不执行 `apply`，不提示“重试”或 **Restart extension**；
- `unreachable`：提示 Gateway 网络不可达，保留配置，不提示重启；
- `mcp_unavailable`、`forbidden`、`protocol_error`、`server_error` 或 `unexpected_response`：说明对应的 Gateway 入口或服务异常，保留配置，不把 tools 为空归因于冷启动。

脚本不输出 PAT、`Authorization` header、原始响应或底层异常文本。不得使用 `curl`、通用 URL 参数或手工读取 PAT 代替该动作。

当 PAT 已验证、配置全部匹配、当前会话没有执行 `apply` 且首次按 `mcp__gateway__` 查询仍不可见时，只输出：

> Gateway 工具尚未在本轮加载完成。请在当前聊天发送“重试”，我会继续原任务。

记录本次启动重试，避免循环提示。用户重试后，先重新按 `mcp__gateway__` 查询延迟目录；若 tools 仍不可见则重新运行 `verify`，只有 PAT 仍为 `authenticated` 才继续。若 tools 已发现，调用只读 tool 验证并静默继续，不得使用“已重连”。若第二次正确查询仍不可见且 PAT 仍有效，只输出：

> Gateway MCP 配置已存在，但工具仍未载入。请在 **MCP servers** 中点击 **Restart extension**，然后回到当前聊天。

当 `pat_source=project_dotenv`、`verify=authenticated`，但 `mcp_url_matches=false`、`mcp_auth!=static_header` 或 `mcp_pat_config_matches_dotenv=false` 时，Agent 只输出一次简短确认：

> Gateway MCP 需要修复。我可以从项目 `.env` 读取 PAT 并存入本机 Codex 用户配置（明文）；完成后需点击 **Restart extension**。是否继续？

不在用户输出中展示配置路径、`mcp_servers.gateway`、`Authorization` header、`0600` 或内部修复步骤。这些仍是脚本必须遵守的实现约束，不是需要用户理解的接入流程。

用户明确授权后，由 Agent 执行：

```bash
python3 <skill-dir>/scripts/configure_codex_gateway_mcp.py apply --project-root <project-root>
```

`apply` 不接收 PAT 参数，不输出 PAT，并在写入前重新执行同一受信入口验证；验证不再是 `authenticated` 时拒绝写入。验证成功后只替换用户级 `mcp_servers.gateway` 段并原子写入。不得手工读取 `.env` 或 `config.toml`，不得把静态 header 写入项目 `.codex/config.toml`。

成功时只输出：“本地配置已更新，Gateway PAT 已验证。请在 **MCP servers** 中点击 **Restart extension**，然后回到当前聊天。”不要输出配置报告、CLI 启动或 `resume` 命令。

## Codex CLI PAT 检查结果

内置脚本只返回下列三个字段：

```json
{"configured":true,"source":"environment","loaded_in_process":true}
```

- `source=environment`：PAT 已在当前进程就绪。
- `source=project_dotenv`：当前项目 `.env` 已声明 PAT，但需要启动方式加载后才能供 MCP 使用。
- `source=missing`：两个固定位置都未发现 PAT。
- `source=project_dotenv_unreadable`：只说明 `.env` 无法安全检查，不尝试其他路径。

## Codex CLI 配置修复

只读检查：

```bash
codex mcp get gateway --json
```

期望配置：

下列 `{origin}{mcp_path}` 和 `<system-mcp-url>` 都表示从 `system-endpoint.json` 读取并派生的实际值，执行命令时不得把占位符作为字面值传入。

```text
name = gateway
url = {origin}{mcp_path}
bearer_token_env_var = GATEWAY_MCP_PAT
```

`bearer_token_env_var` 为 `null`、缺失或不等于 `GATEWAY_MCP_PAT` 时，该配置不完整。即使 URL 正确也不得只提示重启。

未配置时，获得用户确认后执行：

```bash
codex mcp add gateway \
  --url <system-mcp-url> \
  --bearer-token-env-var GATEWAY_MCP_PAT
```

同名配置不匹配时，先展示差异和修复动作，获得用户确认后再删除并重建。命令中只包含 PAT 环境变量名，不包含 PAT 值。

获得用户确认后的 Codex 修复命令：

```bash
codex mcp remove gateway
codex mcp add gateway \
  --url <system-mcp-url> \
  --bearer-token-env-var GATEWAY_MCP_PAT
```

如果 PAT 两个固定位置都缺失，引导用户在用户中心创建 scope 为 `gateway:api` 的 PAT，并保存到 `GATEWAY_MCP_PAT` 环境变量或当前项目根目录 `.env`。不要求用户在对话中粘贴 PAT。

## Codex CLI 重启并续接原会话

Agent 完成 MCP 配置和 `.env` 自动加载准备后，给出一条续接命令，而不是要求用户“开新会话再重新调用 Skill”。已有启动脚本时优先使用：

```bash
<project-launcher> resume --last
```

启动脚本必须把 `resume --last` 原样透传给 `codex`。若能安全获得当前 `CODEX_THREAD_ID`，可用该 ID 代替 `--last` 精确续接，但不得为此读取或遍历其他会话记录。

恢复后保留原对话上下文，首先通过一个只读 Gateway tool 验证连接，成功后直接继续重启前的用户意图。认证失败时检查 PAT 是否完整、过期、吊销，以及是否使用 Gateway PAT 而非其他平台 PAT。

## 其他客户端配置示例

下列示例中的 `{origin}{mcp_path}` 同样必须替换为统一系统端点配置派生的实际 MCP URL。

### VS Code 内置 MCP（非 Codex 扩展）

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "gateway-mcp-pat",
      "description": "Gateway MCP PAT",
      "password": true
    }
  ],
  "servers": {
    "gateway": {
      "type": "http",
      "url": "{origin}{mcp_path}",
      "headers": {
        "Authorization": "Bearer ${input:gateway-mcp-pat}"
      }
    }
  }
}
```

### Harness

先在 Harness 中创建文本 Secret（例如 `gateway_pat_secret`），Secret 值保存完整认证头值 `Bearer <your Gateway PAT>`，再导入或创建下列 MCP Server Connector：

```yaml
connector:
  name: Gateway MCP
  identifier: gateway_mcp
  type: Mcp
  spec:
    serverUrl: "{origin}{mcp_path}"
    auth:
      type: CustomHeader
      spec:
        headerName: Authorization
        headerValueRef: gateway_pat_secret
    executeOnDelegate: false
```

`headerValueRef` 只填写 Harness 文本 Secret 标识，不直接填写 PAT；按部署网络选择 Harness Manager 或 Delegate 执行连接测试。

## Tool 目录

| Tool | 用途 |
| --- | --- |
| `gateway.image_versions.list_available` | 查询当前用户可用版本 |
| `gateway.image_versions.get_detail` | 查询能力、限制、图商和覆盖项 |
| `gateway.image_versions.get_request_schema` | 获取输入 Schema |
| `gateway.image_versions.get_result_summary_schema` | 获取摘要结构 |
| `gateway.map.geocode` | 将地址或地点关键字解析为候选 POI 和坐标 |
| `gateway.credits.get_me` | 查询当前积分 |
| `gateway.solver_jobs.create` | 确认后创建任务 |
| `gateway.solver_jobs.list` | 查询用户任务列表 |
| `gateway.solver_jobs.get_detail` | 查询任务详情和状态 |
| `gateway.solver_jobs.get_summary` | 查询结果摘要 |
| `gateway.solver_jobs.get_result_access` | 获取 Gateway 详情页入口 |

## 外部 Agent 渠道边界

- **外部 Agent 市场**：Skill 可以携带上述检查和接入工作流，但客户端是否允许动态写入 MCP 配置、是否需要重启以及正式 OAuth/审核要求仍由对应渠道决定。若不允许动态配置，Skill 只输出最小必要的手动配置步骤。
