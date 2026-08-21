# 报告工具目录

时间均为 `yyyy-MM-dd HH:mm:ss`。`level=1/2/3` 分别表示市局/分局/派出所；组织 ID 应由 `getDwTree` 获取。

| MCP 工具 | 参数摘要 | 原服务路径 | 返回/用途 |
|---|---|---|---|
| `getTotalStatus` | `startTime,endTime,level,currentOrgId,parentOrgId[]` | `POST /ds-jzzl-web/ddyh/dwReport/getJqSummary` | 总量、日均、同比、环比、层级排名、分类列表、涉网专项数 |
| `getJqBq` | `startTime,endTime,bqbhList[]` | `POST /ds-jzzl-web/sjyh/getSjList` + `countSjlyNum` | 标签总数、来源分布、派出所分布 |
| `getJqTimePeriodAnalysis` | `startTime,endTime,xqdws[],level` | `POST /ds-jzzl-web/ddyh/dwReport/getJqTimePeriodAnalysis` | 24 小时本期/同期、7 日/30 日均值 |
| `getJqay` | `startTime,endTime,jqay[]` | `POST /ds-jzzl-web/jqcx/get110DwAyStat` | 案由数量及同比/环比 |
| `statJqNumAndPer` | `startTime,endTime,xqdws,level` | `POST /ds-jzzl-web/ddyh/statRegionJqNum` | 单位数量及同环比 |
| `getRyChartPatternStat` | `startTime,endTime` | `POST ds-jzzl-web/ryyh/getRyChartPatternStat` | AI 人员标签统计 |
| `getYhryByAgeAndTags` | `startTime,endTime,minAge,maxAge,personTagList[]` | `POST /ds-jzzl-web/ryyh/findRyyhInfoList`, `getRyLbNumV2`, `getRyDwDis` | 风险人员数量、来源和辖区分布 |
| `getStakeholderStability` | `startTime,endTime` | `POST /ds-jzzl-rcfx-web/rcsjmc/queryRcSjmcList` | 涉众涉稳热词事件 |
| `getObsceneGamblingFraud` | `startTime,endTime` | `POST ds-jzzl-rcfx-web/rcsjmc/querySwxptList` | 涉黄赌诈热词事件 |
| `statJqNumAndPerTotal` | `startTime,endTime,xqdws[]` | `POST /ds-jzzl-web/ddyh/statRegionJqNum` | 派出所/分局排名 |
| `getFjOrPcsPmqk` | `startTime,endTime,xqdws,level` | `POST /ds-jzzl-web/ddyh/statRegionJqNum` | 指定 level 机构排名 |

同比区间为本期起止时间向前一年；环比区间按本期持续时长向前平移。接口返回的百分比字段需原样保留。
