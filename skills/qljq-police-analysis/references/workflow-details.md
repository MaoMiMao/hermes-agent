# 技能职责迁移说明

意图识别、时间补全、多意图拆分和最终回答风格由 Hermes 主智能体负责。本技能不重新分类用户问题。

主智能体传入 `intent`、时间、单位和筛选条件后，本技能负责 MCP 工具调用、编码解析、结果校验和模板渲染。

请按意图读取以下独立模板：

- `person-template.md`
- `event-template.md`
- `location-template.md`
- `statistics-template.md`
- `report-template.md`

MaxKB 工作流中提到的 `getJqDetailsByWrj`、`getNightImportantPeriod`、`getQyzbBqjq` 当前未在 qljq-analysis-mcp 的 32 个工具中暴露。遇到这些能力时必须报告 MCP 能力缺失，不能调用不存在的工具或伪造结果。
