# Open WebUI + Hermes

本地界面名称为“警务助手”，Hermes API 模型别名也配置为“警务助手”。
Open WebUI 默认语言为 `zh-CN`，Hermes Dashboard 默认语言为 `zh`。
已有账号、数据库或浏览器缓存中保存的语言选择仍优先；老账号请在设置中选择简体中文。
名称和 Dashboard 语言源码变更需要重新构建对应镜像。

Chat Completions 流现将 Hermes `reasoning_callback` 转为
`choices[0].delta.reasoning_content`，Open WebUI 可按推理区域显示。
仅展示底层模型实际提供的推理文本；未返回推理的模型不会产生该区域。
状态动画、工具进度与推理不同，未混入此字段。

在 `wsl -d Ubuntu-24.04` 中执行以下命令。此配置独立于现有知识库 Compose，
必须显式指定 `-f docker-compose.yaml` 和项目名，避免选中另一份同名 `.yml`。

此部署仅运行 Open WebUI + Hermes（含 MarkItDown/OCR），不启用 knowledge-base，
也不依赖其源码、应用挂载或 4178 端口。原知识库部署文件和服务定义继续保留，
通过独立的 `docker-compose.yml` 使用。

Hermes Dashboard 随 Hermes 容器启动，默认访问 http://localhost:6060。
使用 Compose 中 `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` 和
`HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` 配置的账号密码登录。
`HERMES_DASHBOARD_BIND` 控制宿主机监听地址，`HERMES_DASHBOARD_PORT` 控制
宿主机端口（默认 6060）；容器内部固定监听 0.0.0.0:6060。

```bash
cd /mnt/d/Project/AI/hermes-agent
cp openwebui.env.example openwebui.env
chmod 600 openwebui.env
openssl rand -hex 32
openssl rand -hex 32
```

将两次生成的值分别填入 `openwebui.env` 的 `API_SERVER_KEY` 和
`WEBUI_SECRET_KEY`。Hermes 镜像默认 `ds-hermes-agent:20260914`；Open WebUI
从相邻源码目录 `../open-webui`（WSL 路径 `/mnt/d/Project/AI/open-webui`）的
Dockerfile 构建，输出本地镜像 `ds-open-webui:20260914`。源码位置可通过
`OPEN_WEBUI_SOURCE_DIR` 调整。此配置不拉取预构建的 Open WebUI 应用镜像；
源码 Dockerfile 仍需下载 Node/Python 基础镜像、npm/Python 依赖及模型权重。

先在 WSL 中构建 Open WebUI（兼容本机 docker-compose 1.29.2）：

```bash
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml build open-webui
```

首次使用先配置 Hermes 的模型提供商、模型及密钥，配置会持久化到独立的数据卷：

```bash
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml run --rm hermes-agent setup
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml up -d --no-build
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml ps
```

访问 http://localhost:3000，首次注册的账号成为管理员。远程访问时修改
`OPEN_WEBUI_BIND`。Hermes API 仅在 Compose 网络内提供服务，地址为
`http://hermes-agent:8642/v1`，不发布宿主机 8642 端口。
Open WebUI 使用 `USE_SLIM=true` 构建，并在运行时设置 `OFFLINE_MODE=true`、
`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`，关闭模型自动更新及版本检查。
默认不配置本地 embedding 模型，文档交给 Hermes/MarkItDown 处理。
离线运行的 Hermes 模型提供商也必须指向可访问的内网服务；此处关闭下载不等于
配置了模型服务。未准备本地权重或分词数据时，不使用 Open WebUI 的本地 RAG、
Whisper 和依赖这些资源的功能。已有数据库中的 RAG 设置可能覆盖环境默认值。

已有 Hermes 配置、skills 和模型密钥不会从现有知识库部署自动迁移。新配置使用
原 `docker-compose.yml` 的 `/opt/ds-hermes/data/hermes:/opt/data`，因此会继续使用
原有配置、会话、skills 和模型密钥；Open WebUI 单独使用 `open-webui-data`。
文档转换直接使用 `/opt/hermes/.venv/bin/python`；如需 uv，使用
`uv run --no-sync`，不要重新同步或通过 uvx 创建另一套文档转换环境。

`working_dir: /opt/data` 只是容器内进程启动时的当前目录，不是数据卷定义。
`HERMES_DATA_DIR` 是宿主机目录，默认保持旧部署路径；若旧路径不同，在
`openwebui.env` 中改为实际路径，不要直接修改容器内的 `/opt/data`。

后续更换 API 地址或密钥，还需检查 Open WebUI 管理员设置中的 Connections：
其数据库可能保留首次启动时的连接配置。不要通过删除数据卷来更新连接。

推理显示需要使用包含上述 Chat Completions 修改的 Hermes 镜像，
只更新 Compose 而继续运行旧镜像不会生效。

查看日志及停止服务（保留数据卷）：

```bash
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml logs --tail=100 hermes-agent open-webui
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml down
```
