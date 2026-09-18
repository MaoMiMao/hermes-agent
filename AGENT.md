# 本地定制维护说明

本文档仅记录此工作区本地维护的部署定制，不是 Hermes 的上游开发指南。
上游贡献规范请阅读 `AGENTS.md`。

## 当前默认部署边界（2026-09-14）

`docker-compose.yaml` 用于 Open WebUI + Hermes，保留 MarkItDown/OCR，
不启用 knowledge-base、不挂载其应用或数据、不发布 4178 端口。
第三方 knowledge-base 集成本身继续保留：`docker-compose.yml`、
`Dockerfile.knowledge-base` 和 `docker/s6-rc.d/knowledge-base/` 仍用于原知识库部署。
不要将知识库专用配置复制到 Open WebUI 的 Compose 中。

## 来源

已提交的本地部署基线为：

```text
0d501ba386 feat: integrate offline document and knowledge base runtime
e259c95de9 feat(api): stream reasoning and offline model inventory
```

以下文件或配置块来自该本地集成；合并上游 Hermes Agent 变更时必须保留：

- `Dockerfile`：离线安装 MarkItDown/OCR，以及 UTF-8 区域设置。
- `docker-compose.yml`：知识库服务接入、宿主机挂载、离线运行设置、内部 API
  Server 访问与明确的端口映射。
- `Dockerfile.knowledge-base`：基于 s6-overlay 的知识库服务层。
- `gateway/platforms/api_server.py`：思考、推理和状态回调的透传；会话 SSE
  事件；离线模型清单入口。
- `gateway/platforms/api_server_runs.py`：上游拆分 `/v1/runs` 后，本地回调
  适配与稳定工具调用 ID。
- 下文列出的未跟踪发布辅助文件：它们是本地部署产物，应明确决定是否纳入提交，
  不应当作上游文件处理。

不要在本文档中记录或恢复与本地扩展无关的上游 API Server、SSE、模型清单、桌面端、
CLI 或一般 Git 合并改动。

## 离线 MarkItDown 与 OCR

`Dockerfile` 将依赖安装到镜像内 Hermes 自己的虚拟环境：

```dockerfile
RUN --mount=type=bind,from=markitdown_wheels,target=/opt/markitdown-wheels,readonly \
    uv pip install \
        --python /opt/hermes/.venv/bin/python \
        --no-index \
        --find-links=/opt/markitdown-wheels \
        "markitdown[audio-transcription,az-content-understanding,az-doc-intel,docx,outlook,pdf,pptx,xls,xlsx,youtube-transcription]==0.1.7" \
        "markitdown-ocr==0.1.0"
```

本地构建要求：

- 使用 BuildKit，并以名为 `markitdown_wheels` 的构建上下文传入 wheel 目录。
- wheel 仓库必须包含与镜像 Python 3.13、目标 CPU 架构匹配的完整依赖闭包。
- 调用 MarkItDown 时使用 `/opt/hermes/.venv/bin/python`；系统 Python 或 CLI
  使用的 Python 可能无法识别 Hermes 虚拟环境内已安装的包。
- `markitdown-ocr` 仍需独立安装，不能由 `markitdown[all]` 替代。

使用全部具名 converter extras 替代 `all`：MarkItDown 0.1.7 的 `all` 单独约束
`youtube-transcript-api~=1.0.0`，与 Hermes 的 `1.2.4` 冲突；其正式提供的
`youtube-transcription` extra 没有该版本限制。此处保留所有转换组件，
不降级 Hermes 的字幕依赖。离线 HTML 转换验证不代表 YouTube 远程调用验证。

构建时 Hermes 的 `uv sync` 固定使用 `/usr/bin/python3.13`，源码复制完成后仅将
镜像内的 `.python-version` 写为 `3.13`，不改变开发工作区的版本约定。
MarkItDown 安装使用 Hermes 已安装依赖的版本约束；若 wheel 仓库无法满足这些
版本，构建应失败，需补齐兼容 wheel，不应解除约束覆盖 Hermes 依赖。
最终镜像执行 OCR 插件加载和 HTML 转 Markdown 检查；这些检查不调用模型，
不代表完成了真实扫描文档 OCR 验证。当前源码构建的全环境 `uv pip check`
会报告 MSAL 要求 `cryptography<49`，但项目的安全修复 override 固定为
`cryptography>=50,<51`。该检查不理解项目 override，因此不作为此 Dockerfile
的构建门槛；保留该基线差异，不降级密码库，也不宣称全环境依赖检查通过。

运行文档转换时直接使用 `/opt/hermes/.venv/bin/python` 或
`/opt/hermes/.venv/bin/markitdown`，不要使用 `uvx` 创建独立环境，也不要通过
普通 `uv run` 或 `uv sync` 同步镜像内环境：MarkItDown 是额外安装的离线依赖，
未列入 Hermes 的 `uv.lock`，精确同步可能将其删除。

示例：

```bash
docker buildx build \
  --build-context markitdown_wheels=/opt/app/repository/wheels \
  -t ds-hermes-agent .
```

本机验证统一在 `wsl -d Ubuntu-24.04` 中执行，仓库路径为
`/mnt/d/Project/AI/hermes-agent`。已检查的 Python 3.13 wheel 目录为
`/opt/app/repository/wheels-py313-amd64`，但其中缺少 OCR 包及 `python-docx`
等传递依赖；验证时将该目录的 wheels 与 `/opt/app/repository/wheels/` 中的
wheels 合并到临时目录
`/tmp/hermes-markitdown-validation-wheels` 后传给构建上下文。
uv 按解释器和平台选择兼容 wheel。PyMuPDF 的 `cp310-abi3` wheel 可用于此 Python 3.13 环境；无需只按文件名
含有 `cp313` 筛选。以上是本机目录现状，发布前仍需验证实际 wheel 闭包。

2026-09-14 在上述 WSL 环境构建 `ds-hermes-agent:markitdown-validation` 成功。
构建期 OCR 插件加载和 HTML 转换通过；新镜像以 UID 10000 运行 DOCX、文本 PDF
转换通过。直接 `python` 与 `uv run --no-sync python` 均解析到
`/opt/hermes/.venv`（Python 3.13.5），MarkItDown 0.1.7、OCR 0.1.0、Hermes 的
youtube-transcript-api 1.2.4 均保留。未验证真实 OCR 模型调用或 YouTube 请求。
该标签为本地验证镜像，未替换 Compose 部署镜像。

## Compose 运行时定制

`docker-compose.yml` 面向本地知识库部署：

- Hermes 持久化数据：`/opt/ds-hermes/data/hermes:/opt/data`。
- 知识库持久化目录：
  `/opt/ds-hermes/data/knowledge_repository:/opt/knowledge_repository`。
- 知识库应用挂载：
  `${KNOWLEDGE_BASE_APP_DIR:-/opt/app/llm-wiki-explorer}:/opt/knowledge-base:ro`。
- 知识库前端通过 `http://127.0.0.1:8642` 调用容器内部 Hermes API；不要将容器
  端口 `8642` 映射到宿主机。
- 默认只将端口 `4178` 映射到回环地址。需要远程访问时，应明确调整宿主机地址或端口。
- `HERMES_DISABLE_LAZY_INSTALLS=1`、`UV_OFFLINE=1`、`PIP_NO_INDEX=1`、npm 离线
  配置和 Hugging Face 离线配置均为有意设置，用于阻止首次对话期间联网下载或安装依赖。

镜像和 Compose 均设置了 `LANG=C.UTF-8`、`LC_ALL=C.UTF-8`、`PYTHONUTF8=1` 与
`PYTHONIOENCODING=UTF-8`。修改 Docker 或 Compose 时须保留这些设置，以确保挂载目录
中的中文文件名和文档内容保持 UTF-8。

若宿主机上传文件时由 `root` 创建，容器内可能没有读取权限。重启容器不能修复宿主机
文件的属主或权限；无法修改属主时，应在宿主机上通过 ACL 为配置的
`HERMES_UID:HERMES_GID` 授予目录的读取和遍历权限。

## 网关思考链路扩展

本地提交 `e259c95de9` 为 Hermes API 网关增加了对 Agent 回调的端到端透传。
该扩展只负责传输 Agent 已提供的增量事件，不自行生成推理内容。

### 回调与 SSE 事件

`gateway/platforms/api_server.py` 中：

- `APIServerAdapter._create_agent()` 将 `reasoning_callback`、
  `thinking_callback` 与 `status_callback` 传递给 `AIAgent`。
- `_run_agent()` 持续向下透传相同的三个回调，避免普通会话路径丢失事件。
- `POST /api/sessions/{session_id}/chat/stream` 的 SSE 流会发送：
  - `reasoning.delta`：推理增量，字段为 `message_id`、`delta`。
  - `thinking.delta`：思考展示增量，字段为 `message_id`、`text`。
  - `status.update`：状态更新，字段为 `message_id`、`kind`、`text`。

消费者必须将三类事件与普通 `assistant.delta` 区分处理。没有收到
`reasoning.delta` 仅表示当前 Agent 或模型没有调用该回调，不能据此判定模型或
MarkItDown 安装异常。

### `/v1/runs` 路径

上游后来将 `/v1/runs` 的实现从 `api_server.py` 拆分到
`gateway/platforms/api_server_runs.py`。本地在合并提交 `29c7caf7ce` 中将扩展
迁移到拆分后的执行路径：

- `_reasoning_cb`、`_thinking_cb`、`_status_cb` 将 Agent 回调转换为相同名称的
  run SSE 事件。
- `_tool_start_cb`、`_tool_complete_cb` 保留 `tool_call_id`，使工具开始与完成
  事件可以稳定配对。
- 通过 `_create_agent()` 传入所有回调；不要为了恢复本地行为而把旧的、完整的
  `/v1/runs` 实现复制回 `api_server.py`。

后续合并若再次移动 runs 代码，应以新的上游模块结构为准，并将以上回调、事件字段和
`tool_call_id` 配对逻辑迁移到新的实际执行路径。

### 离线模型清单

本地同一提交还扩展了：

```text
GET /api/model/options?offline=true
```

该参数调用 `build_local_model_options_payload()`，只基于本地配置构造模型选择器数据，
避免刷新提供商目录、价格或远程模型信息。离线部署的知识库和 Dashboard 应优先使用该
入口；不带 `offline=true` 的请求仍可能进行清单扩充。

## 本地知识库发布文件

以下文件目前仅存在于本地工作区，构成本地部署流程：

- `DEPLOYMENT.knowledge-base.zh-CN.md`
- `knowledge-base.env.example`
- `scripts/build-knowledge-base-image.sh`
- `scripts/package-knowledge-base-image.sh`

`scripts/build-knowledge-base-image.sh` 构建知识库前端，并将其 `dist/` 与
`server.mjs` 打入 `ds-hermes-workspace`。
`scripts/package-knowledge-base-image.sh` 导出该镜像、生成 SHA256 校验文件，并将
Compose 与环境变量模板复制到镜像归档文件旁。

将这些文件加入提交前，检查镜像标签、源码目录和目标部署路径。它们遵循本地发布约定，
不是通用的上游默认配置。

## 上游合并边界

未来合并上游时，保留以上本地文件和配置块；不要将已合入开源项目的变更重新作为本地
补丁引入。工作区有未提交改动时，合并前先保存，并检查是否存在未解决的索引冲突：

```bash
git diff --name-only --diff-filter=U
git ls-files -u
```
