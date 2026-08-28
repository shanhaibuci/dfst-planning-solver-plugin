# DFST Planning Solver Plugin

面向 ChatGPT/Codex 的 DFST 场景求解插件。插件包含 `dfst-planning-solver` Skill；Gateway MCP 使用用户自己的 PAT，凭证不会存放在本仓库中。

## 安装

```bash
codex plugin marketplace add shanhaibuci/dfst-planning-solver-plugin
```

随后在 Plugins Directory 中安装 **DFST 场景求解**，并开启新的会话。

## 首次接入

1. 在 Gateway 用户中心创建 scope 为 `gateway:api` 的 PAT。
2. 将 PAT 保存到本地项目 `.env` 的 `GATEWAY_MCP_PAT`，不要粘贴到聊天或提交到 Git。
3. 使用插件开始场景求解。Skill 会检查 Gateway MCP 状态、验证 PAT，并在获得用户授权后完成 Codex MCP 配置。
4. 按提示重启 Codex 扩展或恢复 CLI 会话，随后通过只读工具验证连接。

## 安全说明

- 不要把 PAT、认证 Header、生产密钥或 `.env` 提交到本仓库。
- 当前版本仍使用手动 PAT；OAuth 不在本版本范围内。
- Gateway 认证入口在投入外部使用前应配置 HTTPS。

## 目录

```text
.agents/plugins/marketplace.json
plugins/dfst-planning-solver/
  .codex-plugin/plugin.json
  skills/dfst-planning-solver/
```
