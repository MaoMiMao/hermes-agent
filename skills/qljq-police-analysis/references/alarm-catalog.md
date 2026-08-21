# 警情专题工具目录

时间均为 `yyyy-MM-dd HH:mm:ss`；组织 ID 和筛选编码来自基础码表技能。

| MCP 工具 | 参数摘要 | 原服务路径 | 返回/用途 |
|---|---|---|---|
| `fxryPageList` | `startTime,endTime,needBaseData`；可选 `zjhm,xm,rydh,xqdwList,jqdhList` | `POST /ds-jzzl-web/ryyh/findRyyhInfoList`，并补充人员详情 | 风险人员列表；0 补充详情，1 仅基础 |
| `yhdzInfoList` | `startTime,endTime`；可选 `xqdwsList[]` | `POST /ds-jzzl-model/riskAddAnalysis/riskListFilterSearchInPage` | 隐患地点、风险级别、近月/近年统计 |
| `findQtsj` | `startTime,endTime,pageNo,pageSize`；可选 `xqdwsList[]` | `POST /ds-jzzl-rcfx-web/rcsjmc/queryRcSjmcList` | 群体性事件 |
| `findQtsjSwxpt` | `startTime,endTime,pageNo,pageSize`；可选 `xqdwsList[]` | `POST /ds-jzzl-rcfx-web/rcsjmc/querySwxptList` | 涉网新平台事件 |
| `findfxft` | `startTime,endTime` | `GET /ywc/fxft/agg` | 防汛防台警情 |
| `queryQljqZtqk` | `startTime,endTime`；其余多维筛选可选 | `POST /jqyp/dwfx/graph/getZtqk` | 警情汇总统计 |
| `queryQljqList` | `startTime,endTime`；其余多维筛选可选 | `POST /jqyp/dwfx/detail/list` | 警情明细列表 |
| `findQyzbjq` | `startTime,endTime,xzb,yzb,distance` | `POST /ds-jzzl-web/jqcx/getJqStatByAddrPoint` | 坐标周边统计和明细 |
| `repeatJqQueryType` | `startTime,endTime,type,jfTypeList[]`；可选 `xqdws[]` | `POST /ds-jzzl-web/repeatJq/queryData/queryType/queryQs/queryFj` | 重点重复警情总数、类型、近七日、机构分布 |

## 共用筛选字段

`lylx` 来源、`userdwdm` 当前单位、`jqay` 案由、`keywords` 关键词、`sjdbh` 警情单号、`dmxzqhList` 行政区划、`dzType` 地址类型、`ssxq` 辖区、`ssfj` 分局、`qysx` 区域属性、`bq` 人员标签、`nld` 年龄段、`xb` 性别、`mz` 民族、`jqbq` 警情标签、`bjfs` 报警方式、`jqdj` 警情等级、`wp` 随警物品、`cl` 随警车辆。

无筛选条件时省略或传空数组。`jqdj` 编码为 01/02/03/04（一级至四级）。
