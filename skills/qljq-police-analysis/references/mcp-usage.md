# MCP 调用示例

以下示例展示参数形状，不是固定业务值；单位 ID 和标签编码必须先由 MCP 基础工具解析。

## 统计

```json
{"startTime":"2026-08-06 00:00:00","endTime":"2026-08-06 23:59:59","level":"2","currentOrgId":"<分局ID>","parentOrgId":["<市局ID>"]}
```
调用：`getTotalStatus`。

## 多维明细

```json
{"startTime":"2026-08-06 00:00:00","endTime":"2026-08-06 23:59:59","userdwdm":"<单位ID>","jqay":["<案由编码>"],"jqdj":["01","02"]}
```
调用：`queryQljqList`；汇总问题改用 `queryQljqZtqk`。不需要的可选字段省略。

## 人员

```json
{"startTime":"2026-08-01 00:00:00","endTime":"2026-08-06 23:59:59","xqdwList":["<单位ID>"],"needBaseData":1}
```
调用：`fxryPageList`。只有授权的画像查询才将 `needBaseData` 改为 `0`。

## 周边

1. `queryLocationByName({"query":"地点名称"})`。
2. 从返回结果读取 `location` 的经度和纬度。
3. `findQyzbjq({"startTime":"...","endTime":"...","xzb":"<经度>","yzb":"<纬度>","distance":1000})`。

MCP 工具返回 JSON 或 `dataStore`；保留原始字段，不把工具响应中的百分比重新计算。
