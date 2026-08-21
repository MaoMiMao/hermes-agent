# qljq-analysis MCP 工具总目录

原 MCP server 通过 Spring AI `MethodToolCallbackProvider` 暴露 32 个业务工具，分为基础数据、报告指标和警情专题三组。技能运行时调用 MCP 工具名，不直接拼接 HTTP 请求；HTTP 路径仅用于排查服务映射。

## 基础数据（12）

`getDwTree`, `getAyTree`, `findRyLabels`, `getBqCs`, `getAllCategoryBqModel`, `getBjfs`, `getNld`, `getQysx`, `getBqRy`, `queryLyList`, `queryLocationByName`, `findJqLabels`。

## 报告指标（11）

`getTotalStatus`, `getJqBq`, `getJqTimePeriodAnalysis`, `getJqay`, `statJqNumAndPer`, `getRyChartPatternStat`, `getYhryByAgeAndTags`, `getStakeholderStability`, `getObsceneGamblingFraud`, `statJqNumAndPerTotal`, `getFjOrPcsPmqk`。

## 警情专题（9）

`fxryPageList`, `yhdzInfoList`, `findQtsj`, `findQtsjSwxpt`, `findfxft`, `queryQljqZtqk`, `queryQljqList`, `findQyzbjq`, `repeatJqQueryType`。

原 server 配置为 streamable HTTP，MCP endpoint 为 `/mcp`，默认端口 `28030`，名称 `qljq-analysis-mcp`，版本 `1.0.0`。地址、令牌和人员接口凭据属于部署机密，不复制到技能文件。
