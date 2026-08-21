# 基础数据工具目录

| MCP 工具 | 必要参数 | 原服务路径 | 用途 |
|---|---|---|---|
| `getDwTree` | 无 | `GET /ds-jzzl-web/common/v2/getDwTree` | 组织树 |
| `getAyTree` | 无 | `GET /ds-jzzl-web/common/getAyTree` | 案由树 |
| `findRyLabels` | 无 | `GET /ds-jzzl-web/ryyh/findRyLabels` | 人员来源标签 |
| `getBqCs` | 无 | `POST /jqyp/dwfx/basedata/getBqCs` | 场所标签 |
| `getAllCategoryBqModel` | `xqdw` | `POST /jqyp/model/bq/getAllCategoryBqModel` | 单位警情标签 |
| `getBjfs` | 无 | `POST /jqyp/dwfx/basedata/getBjfs` | 报警方式 |
| `getNld` | 无 | `POST /jqyp/dwfx/basedata/getNld` | 年龄段 |
| `getQysx` | 无 | `POST /jqyp/dwfx/basedata/getQysx` | 区域属性：01 街面、02 社区、03 楼宇、04 虚拟 |
| `getBqRy` | 无 | `POST /jqyp/dwfx/basedata/getBqRy` | 人员标签 |
| `queryLyList` | 无 | `GET /jqyp/dwfx/detail/queryLyList` | 警情来源 |
| `queryLocationByName` | `query` | `GET /ds-extract-web/v1/ai/agent/local` | 地址转经纬度 |
| `findJqLabels` | 无 | `GET /ds-jzzl-web/sjyh/findJqLabels` | 警情类型标签 |

返回值通常是 `dataStore` 树/数组；无数据时按“无数据”处理。
