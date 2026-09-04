---
name: dfst-planning-solver
description: Use DFST Gateway to configure solver access, turn routing, dispatch, scheduling, or resource-planning requirements into a validated solve request, submit and track the job, explain the result, and generate local data-integration tools. Use for DFST planning scenarios and existing solver jobs; do not use for implementing solver algorithms.
metadata:
  version: "1.0.2"
---

# DFST Planning Solver

使用一个 Agent 完成场景分析、参数构建、Gateway 求解任务执行和结果解释。把这些能力作为同一求解闭环的内部阶段，不把它们当成独立 Skill 或未来专业 Agent。

把 Gateway 视为认证、鉴权、积分、Schema 权威校验、任务状态、调度、归档和审计的唯一可信边界。只负责用户引导、会话草稿、辅助检查、任务操作和公开结果解释。

## 全局规则

- 跟随用户语言；API 字段、错误码、枚举和 tool name 保持原值。
- ChatGPT 中优先使用Plugin绑定的Gateway MCP连接和Logto OAuth，不要求或配置PAT。仅Codex CLI/IDE兼容路线使用Gateway PAT；不得要求用户在对话中粘贴PAT，也不得把PAT、密码或数据库凭证写入仓库、命令参数、示例或日志。VS Code兼容配置只允许经用户明确授权后，由内置脚本写入用户级Codex配置。
- 优先收集脱敏结构和小样本，不要求上传完整生产数据。
- 不访问管理员接口、Registry、Git、Gateway 数据库、对象存储内部地址、引擎实例、最终引擎请求归档或完整结果文件。
- 不保存或声称 Gateway 保存了 `request_payload` 原文。只在当前会话或用户明确指定的本地文件中维护草稿。
- 不实现模型、算法或求解器工程，不自动组合实验、调参或反事实任务。求解能力由选定 ImageVersion 对应的引擎实现。
- 不直接调用规划引擎；所有求解任务必须通过 Gateway 创建。

## 先检查 Gateway MCP 接入

任一需要 Gateway 的路线在当前会话先检查一次：

1. 先读取 `config/system-endpoint.json`；其 `origin` 是当前 Skill 对接系统的唯一根地址，MCP 和后续页面地址只能从该配置派生。不得从项目 `.env`、用户输入或通用 URL 参数覆盖该地址。
2. `gateway.*`是本文档使用的逻辑tool name，不保证等于客户端运行时名称。ChatGPT中先使用本Plugin通过`.app.json`绑定的DFST MCP连接，从该连接的工具目录匹配并调用`gateway.image_versions.list_available`完成只读验证；认证由ChatGPT与Logto OAuth处理，不查询`mcp__gateway__`前缀、不读取本地`.env`、不进入PAT配置。连接尚未授权时只引导用户连接当前Plugin。成功后记录当前会话已连接，静默进入用户原始意图。
3. 只有当前表面是Codex CLI/IDE时，才从`ALL_TOOLS`按`mcp__gateway__`前缀发现延迟MCP tools；不得用 `startsWith("gateway.")` 判断 tools 不可见。发现后调用`mcp__gateway__gateway_image_versions_list_available`只读验证。正确查询后仍未发现，或已发现但只读调用失败时，才读取[Gateway 接入](references/gateway-access.md)并进入对应Codex配置路线，不输出PAT值。
4. **VS Code Codex IDE**：先运行内置 `scripts/configure_codex_gateway_mcp.py status`；项目 `.env` 有 PAT 时，再运行同一脚本的 `verify`，向统一系统端点配置派生的 Gateway MCP 地址执行无业务数据的 `initialize`。`invalid_pat` 必须提示 PAT 无效或已过期并引导用户在用户中心重新创建 `gateway:api` PAT，不执行 `apply`，不提示重试或重启；其他服务器验证错误也按返回状态处理。只有 `authenticated` 才继续：若用户级 Gateway MCP 静态 header 未就绪，只用一段简短文字说明将把 PAT 明文存入本机 Codex 用户配置、完成后需重启扩展，并询问是否继续。不展示配置路径、TOML 字段、header 细节、文件权限或修复步骤。取得用户明确授权后，由 Agent 执行同一脚本的 `apply`。若配置完整、当前会话未执行 `apply` 且首次按 `mcp__gateway__` 查询仍不可见，按 MCP 冷启动处理，只请求用户在原聊天发送一次“重试”；用户重试时必须先重复同一延迟目录发现、PAT 验证和只读验证，第二次正确查询仍不可见才提示 **Restart extension**。
5. **Codex CLI**：继续使用由 `config/system-endpoint.json` 的 `origin` 和 `mcp_path` 派生的 URL，并使用 `bearer_token_env_var=GATEWAY_MCP_PAT`；由 Agent 准备自动加载 `.env` 的启动方式，不让用户手动执行 `source` / `export`。
6. 任何 MCP 配置写入、替换或删除都必须先展示变更摘要并取得用户明确授权。配置正确时不重复写入。IDE 仅在 PAT 已通过服务器验证后写入配置，完成后说明本地配置已更新且 PAT 已验证，再提示在 MCP 设置中点击 **Restart extension** 并返回原聊天；CLI 通过 `codex resume` 续接原会话。两种表面都不要让用户重新描述业务需求。只读 tool 成功后静默继续原始意图，不输出接入报告，也不得把“工具已就绪”描述为“已重连”。

Skill不从`.env`读取MCP地址。系统根地址只由`config/system-endpoint.json`定义，地址派生和客户端配置规则由接入参考说明。ChatGPT使用Plugin绑定连接和Logto OAuth；PAT只属于Codex兼容路线，只能由内置脚本从项目`.env`在进程内读取，IDE可在明确授权后定向写入用户级静态header，CLI通过环境变量传递。

## 先路由意图

识别当前意图并只进入需要的路线：

1. **首次接入或接入修复**：读取[Gateway 接入](references/gateway-access.md)。ChatGPT检查Plugin绑定连接及Logto OAuth；Codex CLI/IDE检查PAT、MCP配置、客户端重启和只读连接验证。连接成功前不收集生产业务数据。
2. **新建场景求解**：依次执行场景分析、参数构建、任务执行和结果解释。
3. **日常数据接入**：先完成场景分析和参数映射，再读取 [日常数据接入](references/data-integration.md) 在用户工程生成转换工具。
4. **已有任务查询**：取得 `job_id` 后直接读取 [任务执行](references/job-execution.md) 查询；成功任务再进入结果解释。
5. **已有结果解释**：先验证任务访问和状态，再读取 [结果解释](references/result-explanation.md)。

Gateway tools 不可用或只读调用认证失败时，停止其他路线并切换到接入检查与修复。

## 维护统一会话状态

开始任何路线前读取 [工作流状态](references/workflow-state.md)，只维护一份当前事实。严格执行以下失效规则：

- ImageVersion 改变时，清空旧 Schema、字段映射、参数草稿和创建确认。
- 任一求解字段改变时，提升内部草稿 revision，并立即清空此前确认；revision 不向业务用户展示。
- Schema 必须来自当前已确认 ImageVersion 的实时查询结果。
- 只有当前草稿 revision 与用户确认 revision 一致时才能创建任务。
- 创建成功后保留 `job_id`；调用结果不明确时不得自动重复创建。

## 新建场景求解主流程

### 1. 场景分析与 ImageVersion 选择

读取 [场景分析](references/scenario-analysis.md)。梳理对象、资源、规则、目标、规模、地图需求、数据来源和期望输出；实时查询并比较当前用户可用 ImageVersion。先说明推荐版本、理由和限制，再集中说明需要用户补充的内容。用户未指定图商时，在 ImageVersion 支持的前提下为中国境内推荐 `AMAP`、中国境外推荐 `HERE`。即使只有一个可用版本，也必须由用户确认后再进入参数构建；本阶段不得推荐约束方案或设置罚分。

### 2. 场景参数构建

读取 [参数构建](references/parameter-building.md)。严格按以下顺序执行：获取当前 ImageVersion 的 `request_schema` → 与创建顶层字段及约束覆盖 Schema 组成内部校验视图 → 按 Schema 理解并收集场景参数 → 在目标、硬规则和可接受取舍足以判断后推荐约束方案及罚分。必要时通过 Gateway 把用户提供的地址解析为候选 POI 并确认，按 Schema 决定地点结构、枚举机器值和可覆盖字段，不硬编码 `plan.pois`、枚举语义、约束方案或 Gateway 技术默认值。使用网点、仓库或站点时必须按 Schema 提供已确认的有效位置并验证引用；业务不需要且 Schema 不要求时不得构造空位置的占位对象。用户询问其他方案时介绍当前 ImageVersion 返回的全部方案，允许在选定方案基础上按用户要求调整个别开放罚分。完成数据准备、内部字段映射、缺口和风险识别，生成带内部 revision 的创建草稿。必填缺口、未确认关键映射或明显非法值存在时不得进入创建确认。

### 3. Gateway 求解任务执行

读取 [任务执行](references/job-execution.md)。查询积分，按固定业务分组展示当前草稿、预计积分消耗和可计算时的预计剩余，再询问“是否按以上参数创建求解任务”。把用户确认绑定到当前内部 revision，然后调用 `gateway.solver_jobs.create`。只有明确返回 `job_id` 和状态才称为任务创建成功；只有状态为 `succeeded` 才称为求解成功。期望求解时长不超过 `PT30S` 时有限等待终态，超过 `PT30S` 时创建后立即返回；均不得紧密轮询。

### 4. 求解结果分析

只有任务成功终态才读取结果摘要、摘要 Schema 和结果入口。读取 [结果解释](references/result-explanation.md)，默认按整体可行性、派单成功与未派数量、公开未派原因、总里程、总时间、非零吨公里费用、工程师派单顺序和详情入口展示。结合得分摘要判断和解释，但默认不展示原始 hard/soft score。把结论分为可确认事实、合理推断和证据不足；不得伪装成引擎真实决策链。

结果不可解或质量不满足用户目标时，只提出业务数据或合法参数调整建议。用户决定调整后返回场景分析或参数构建，生成新 revision，并重新经过积分提示和人工确认。

## Gateway tool 边界

只使用以下用户级 tools：

- `gateway.image_versions.list_available`
- `gateway.image_versions.get_detail`
- `gateway.image_versions.get_request_schema`
- `gateway.image_versions.get_result_summary_schema`
- `gateway.map.geocode`
- `gateway.credits.get_me`
- `gateway.solver_jobs.create`
- `gateway.solver_jobs.list`
- `gateway.solver_jobs.get_detail`
- `gateway.solver_jobs.get_summary`
- `gateway.solver_jobs.get_result_access`

先用只读 tool 获取事实，再推荐、构建或解释。不要把历史经验当作当前用户的镜像、权限、Schema、积分或任务状态。生成到用户工程的日常脚本优先调用 Gateway REST API，不要求运行环境加载 Skill 或 MCP 客户端。

## 阶段输出

每完成一个业务阶段，使用用户容易理解的业务语言说明：已确认事实、当前产物、仍需用户提供的内容和下一步。不把“字段映射”、revision、原始字段路径或机器枚举作为普通用户阶段标题或确认用语。接入成功时不单独输出接入报告；接入失败时只输出缺失或错误与修复动作。只有用户要求查询已有任务或 Gateway 已创建任务时才提及 `job_id`。求解完成后提供业务摘要和“点击查看派单路线与排程详情”入口。
