# 场景分析与 ImageVersion 选择

## 分析目标

先理解用户要解决的规划问题，再选择 ImageVersion。不要一开始要求用户手写 Gateway JSON。

使用最少必要问题确认：

- **对象**：要规划、分配、排序或选择什么；
- **资源**：由哪些人员、车辆、设备或时段承担；
- **规则**：时间窗、班次、技能、容量、区域、顺序、必须或禁止关系；
- **目标**：用户希望降低或提高什么，以及哪些目标不能牺牲；
- **规模**：主要对象数量、资源数量、日期范围、区域和运行频率；
- **地图**：涉及的国家或地区、图商要求以及是否已有距离矩阵；用户提供的地址或地点名称可作为初始输入，不要求用户补充 POI ID 或经纬度；
- **数据**：数据库、Excel、CSV、API、手工表及可提供的脱敏样例；
- **输出**：期望获得的分配、路线、排程、得分、未安排对象或其他结果；
- **运行方式**：一次性试算还是日常重复运行。

把用户明确不能改变的规则标为硬约束，把偏好和优化方向标为目标或软偏好。含义不清时列为未决问题，不自行分类。

## 地图默认推荐

场景需要地图且用户没有指定图商时，依据业务地点推荐：

- 中国境内默认推荐 `AMAP`；
- 中国境外默认推荐 `HERE`；
- 跨境、地区不明确或用户已有指定图商时不自动选择。

推荐前必须确认候选 ImageVersion 的 `supported_map_providers` 包含该图商。不支持默认图商时只展示当前版本实际支持的选择，不把区域默认当成 ImageVersion 能力事实。默认推荐可以并入后续业务参数确认，不为明显的单一区域场景单独增加一轮技术提问。

## 查询候选能力

1. 调用 `gateway.image_versions.list_available` 获取当前用户可用版本。
2. 列表为空时说明当前账号没有可用 ImageVersion，停止创建流程并引导用户联系管理员。
3. 对与场景相关的候选调用 `gateway.image_versions.get_detail`。
4. 只依据 Gateway 返回的能力说明、适用和不适用场景、`limits`、`supported_map_providers` 及可用状态比较。
5. 忽略 `import_status` 非 `succeeded` 或明显不可创建的版本。

`get_detail` 即使返回 `constraint_override_schema`、`constraint_override_defaults` 或 `constraint_presets`，本阶段也只缓存为候选版本详情，不解释、不推荐、不选择约束方案，不设置罚分。约束内容必须等 ImageVersion 确认并完成参数阶段的 Schema 组合后再处理。

用户直接给出 ImageVersion ID 或名称时也要实时验证权限、启用状态和详情，不直接沿用历史信息。

## 推荐与确认

先输出一个首选和必要时的备选，分别说明：

- 适配的业务问题；
- 推荐依据；
- 规模、地图或输入限制；
- 当前信息不足或不适用之处。

完成推荐后再集中列出需要用户准备或确认的关键数据。使用面向业务用户的能力名称和理由；除非排障或消除歧义所必需，不把 ImageVersion ID、内部状态或 Schema 术语作为主要表达。

单独询问是否采用推荐 ImageVersion 时，紧跟一个不超过 20 个汉字的业务推荐理由，例如“适合派单与路径规划”。不要在该问题中同时选择约束方案、罚分或其他下游参数。

让用户明确确认一个 ImageVersion。只有一个可用候选也不等于用户已确认；不得把版本推荐和约束方案选择合并为同一个问题。用户偏好可以影响版本推荐，但不得作为未定义创建字段提交 Gateway。

## 阶段产物

阶段结束时形成场景摘要和版本选择摘要：

```yaml
scenario:
  objects: []
  resources: []
  rules: []
  objectives: []
  scale: {}
  data_sources: []
  expected_outputs: []
  open_questions: []
image_version:
  id: "<confirmed id>"
  reason: "<selection reason>"
  limitations: []
  confirmed: true
```

只有 ImageVersion 已确认时才能读取其 `request_schema`。场景仍有未决问题不一定阻止进入参数构建，但影响版本适用性或硬约束的问题必须先解决。
