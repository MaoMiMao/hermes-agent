---
name: qljq-police-analysis
description: "当主智能体已经识别出人员、事件、地点、统计或报告意图，需要使用 qljq-analysis-mcp 查询真实警情数据时调用。负责 MCP 工具选择、机构/标签编码解析、参数组装、结果校验和按场景模板输出；不负责顶层意图识别、不猜测数据、不直接调用后端 HTTP。"
---

# QLJQ MCP 使用技能

## 职责边界

主智能体负责：

- 从用户话术识别 `person`、`event`、`location`、`statistics`、`report` 五类意图。
- 补全相对时间、确认查询单位、拆分多意图，并把自然语言转换为结构化查询上下文。
- 决定用户是否有权限查看人员敏感字段，以及最终回答的语言和详细程度。

本技能负责：

- 根据已给出的意图和上下文调用 `qljq-analysis-mcp`。
- 在缺少单位 ID、案由/标签编码或坐标时调用基础码表工具解析，不猜编码。
- 选择完成目标所需的最少业务工具，严格组装参数并校验返回口径。
- 把原始 MCP 结果交给主智能体，或按指定模板生成可直接展示的结果。

不要在本技能中重新做顶层意图分类，也不要输出思维链。主智能体未提供 `intent` 时，返回缺少上下文的结构化提示，让主智能体补齐。

## 输入契约

主智能体应尽量传入以下上下文：

```json
{
  "intent": "person | event | location | statistics | report",
  "query": "已补全的用户问题",
  "startTime": "yyyy-MM-dd HH:mm:ss",
  "endTime": "yyyy-MM-dd HH:mm:ss",
  "orgName": "用户指定单位或上海市公安局",
  "orgId": "已解析的当前单位 ID",
  "parentOrgIds": ["上级单位 ID"],
  "level": "1 | 2 | 3",
  "filters": {},
  "outputTemplate": "person | event | location | statistics | report",
  "needSensitivePersonData": false
}
```

`startTime`、`endTime`、`intent` 是最低要求。`orgId`、`parentOrgIds`、`level` 缺失时先调用 `getDwTree`；筛选条件使用中文名称时，先调用对应码表再传编码数组。无时间时由主智能体按业务规则补全，本技能不自行假设日期。

## MCP 连接与调用原则

运行环境必须连接名为 `qljq-analysis-mcp` 的 MCP server。只调用 MCP 工具名，不直接拼接 HTTP 路径；endpoint、令牌和人员详情凭据不写入技能。MCP 未连接、工具不存在、超时或返回错误时，返回明确的依赖/工具错误，不伪造结果。

执行顺序固定为：

1. 校验输入上下文和时间格式。
2. 解析缺失的机构、案由、警情标签、人员标签、场所、报警方式、年龄段、区域属性或来源编码。
3. 按下表选择最少业务工具，准备完整参数；只执行已选工具。
4. 保留原始返回中的数量、分母、同比/环比字段和空结果状态，不用明细自行求总数。
5. 根据 `outputTemplate` 读取对应模板，返回结论、关键数字和口径；没有模板要求时返回结构化原始结果摘要。

无参数基础码表可在同一会话缓存约 30 分钟；不要重复请求同一份码表。所有时间参数必须是 `yyyy-MM-dd HH:mm:ss`。

## 意图到 MCP 工具映射

### `person` 人员

- 风险人员列表、按姓名/证件号/电话/警单号筛选：`fxryPageList`。
- 风险人员标签、年龄或多标签分布：`getRyChartPatternStat`、`getYhryByAgeAndTags`。
- 仅列表传 `needBaseData=1`。只有主智能体明确授权且确有业务需要时才传 `needBaseData=0`，因为它会补充地址、电话、前科和历史警情等敏感信息。
- 输出读取 `references/person-template.md`。

### `event` 事件/警情明细

- 警单号、单事件详情或证据记录：`queryQljqList`，以 `sjdbh` 精确过滤并保留原始字段。
- 群体性事件：`findQtsj`；涉网新平台事件：`findQtsjSwxpt`；防汛防台：`findfxft`。
- 重点重复警情：`repeatJqQueryType`，`type` 与 `jfTypeList` 使用接口约定编码。
- 输出读取 `references/event-template.md`。

### `location` 地点

- 地址文字必须先调用 `queryLocationByName(query)` 取得 `(经度,纬度)`，再调用 `findQyzbjq(startTime,endTime,xzb,yzb,distance)`；默认 `distance=1000` 米，除非主智能体指定其他距离。
- 隐患地点和风险评分：`yhdzInfoList`。
- 只有一级、二级警情进入周边明细；无则输出“周边暂无二级及以上风险警情”。成功查询后附带包含时间、坐标和距离的页面 URL。输出读取 `references/location-template.md`。

### `statistics` 统计

- 辖区总量、日均、同比、环比、分类、排名：`getTotalStatus`，必须传 `startTime,endTime,level,currentOrgId,parentOrgId`。
- 指定案由及同环比：先 `getAyTree` 解析 `jqay`，再 `getJqay`。
- 24 小时高发时段：`getJqTimePeriodAnalysis`。
- 机构排名：`getFjOrPcsPmqk` 或 `statJqNumAndPerTotal`；`level=2` 分局，`level=3` 派出所。
- 多维聚合：`queryQljqZtqk`；标签统计及来源/派出所分布：`getJqBq`，标签编码来自 `getAllCategoryBqModel` 或 `findJqLabels`。
- 输出读取 `references/statistics-template.md`。

### `report` 报告

报告不是单独的数据接口，而是按主智能体给出的报告范围组合统计工具；优先 `getTotalStatus`，按报告要求追加一个或多个案由、时段、排名、标签或明细工具，不要无目的遍历接口。输出读取 `references/report-template.md`，所有结论必须能回溯到真实 MCP 返回。

## 通用筛选编码

`queryQljqZtqk` 和 `queryQljqList` 的通用筛选字段包括 `lylx`、`userdwdm`、`jqay`、`keywords`、`sjdbh`、`dmxzqhList`、`dzType`、`ssxq`、`ssfj`、`qysx`、`bq`、`nld`、`xb`、`mz`、`jqbq`、`bjfs`、`jqdj`、`wp`、`cl`。编码来源和完整参数见 `references/base-data-catalog.md`、`references/alarm-catalog.md`、`references/report-catalog.md`。

不要用中文名称代替编码；不要混用人员标签和警情标签；`jqdj` 使用 `01/02/03/04` 表示一级至四级。

## 错误、空结果与敏感数据

- 空结果表示接口没有数据，不能替换成数字 0。
- 工具超时、依赖未连接、字段脱敏或返回结构异常，要说明具体状态和受影响的结论。
- 身份证号、电话、住址、前科等默认脱敏，只在主智能体传入 `needSensitivePersonData=true` 且用户明确需要时展示。
- 不从历史对话、示例、缓存或模型常识补充数字；缓存必须同时匹配时间、单位和查询口径。

## 参考资料导航

- `references/mcp-usage.md`：常用 MCP 调用的参数形状。
- `references/base-data-catalog.md`：机构、案由、标签、码表和地理编码工具。
- `references/report-catalog.md`：态势、趋势、案由、指标和排名工具。
- `references/alarm-catalog.md`：警情明细、人员、地点和专题工具。
- `references/person-template.md`、`event-template.md`、`location-template.md`、`statistics-template.md`、`report-template.md`：按主智能体意图分别读取的输出模板。
