# Gateway 求解任务执行

## 创建前检查与确认

只接受当前 ImageVersion、Schema 和参数构建阶段已经完成的草稿。调用 `gateway.credits.get_me`，然后使用业务语言按固定分组展示，不输出无层次的流水账：

1. **求解设置**：求解能力名称、图商和期望求解时长；
2. **资源与任务**：工程师、车辆等资源，以及待处理工单或其他对象的数量和关键属性；
3. **地点与时间**：已确认地点、日期范围、工作时段、服务时长和时间要求；
4. **规则与约束**：业务目标、不可违反规则、选定约束方案的中文名称和主要取舍，以及单独调整的罚分；没有额外调整时不展开整份分值表；
5. **风险与待确认**：必须为空或已由用户明确接受；同类事项归类展示，不逐条堆成流水账；
6. **积分**：当前余额、预计消耗和可计算时的预计剩余。

预计消耗使用当前 ImageVersion 详情中的 `base_credit_cost`、`duration_credit_per_10s` 和当前 `expected_solve_duration` 计算：

```text
base_credit_cost + ceil(求解秒数 / 10) × duration_credit_per_10s
```

结果保留 4 位小数，并明确“预计消耗仅供创建前确认，实际冻结积分以 Gateway 创建结果返回的 credit_cost 为准”。不得硬编码单价或从其他 ImageVersion 沿用价格。历史 ImageVersion 没有公开价格时说明暂时无法预估，不自行猜测。

统一询问：“是否按以上参数创建求解任务？”不向用户展示 revision、“字段映射”、原始字段路径或其他内部状态。只有用户在看到该摘要后作出明确肯定答复，才能把当前内部 revision 记为 `confirmed_revision` 并调用 `gateway.solver_jobs.create`。

此前的“可以”“继续”等回复不能跨草稿复用。任一创建字段变化后立即清空确认，重新执行辅助检查、积分查询、摘要展示和确认。

## 创建任务

调用 `gateway.solver_jobs.create` 时只传当前草稿中的合法字段。只有 tool 明确返回非空 `job_id` 和任务状态时，才能判定求解任务创建成功并保存：

- `job_id`；
- Gateway 返回的初始状态；
- Gateway 返回的积分费用或冻结信息；
- 推荐的下一次查询时机。

创建成功不等于方案生成成功：

- `created`、`queued`、`preparing_engine`、`engine_starting`、`running`、`pending_confirmation`：只说明任务已创建或正在处理；
- `succeeded`：才能说明求解成功并进入结果解释；
- `failed`、`canceled`、`timed_out`、`archive_failed`：说明任务曾创建成功，但本次求解或归档没有成功。

Gateway 返回字段或业务错误时，保留 `code`、`message` 和 `details` 事实，给出对应修正建议。修改草稿后必须生成新 revision 并重新确认。

## 结果不明确时

创建调用超时、断连或返回结果不明确时不得自动再次创建：

1. 调用 `gateway.solver_jobs.list` 检查近期同一 ImageVersion 的任务；
2. 只有能够确认对应任务时才记录其 `job_id`；
3. 仍无法确认时要求用户人工核对；
4. 不创建“替代任务”。

调度或归档阶段失败可能已经生成任务记录。有 `job_id` 时查询该任务，不重新创建。

## 查询状态

已有 `job_id` 时先调用 `gateway.solver_jobs.get_detail` 验证访问和状态。只在用户需要持续等待时有限轮询，避免紧密循环；长任务返回 `job_id` 并建议稍后继续查询。

新建任务按 `expected_solve_duration` 分流：

- 不超过 `PT30S`：在当前交互中有限等待并查询终态；达到短任务等待边界仍未完成时，说明任务仍在运行，返回 `job_id` 和后续入口后停止轮询；
- 超过 `PT30S`：创建成功后立即返回任务信息，不在当前交互中等待终态；
- 任一路线都不得通过高频查询模拟等待，也不得因为状态查询失败创建替代任务。

- `created`、`queued`、`preparing_engine`、`engine_starting`、`running`：解释当前阶段，不声称已有结果。
- `pending_confirmation`：说明平台仍在确认，不把待定结果当成成功。
- `succeeded`：进入结果解释，调用结果摘要、摘要 Schema 和结果入口。
- `failed`、`canceled`、`timed_out`、`archive_failed`：只解释公开安全错误和下一步，不推测内部堆栈。

调用 `gateway.solver_jobs.get_result_access` 后只使用 `detail_page_url`。绝对 URL 原样返回；相对 URL 只与 `../config/system-endpoint.json` 中的 `origin` 合并。用户可见链接文案统一为“点击查看派单路线与排程详情”。不得构造下载或对象存储地址。
