# 智能助手与知识库部署

该部署将 Hermes Dashboard、Runs API、智能助手和知识库前端放在同一个
`ds-hermes-workspace` 镜像与容器中。镜像包含知识库前端的 `dist/` 和
`server.mjs`，目标机器不需要 `/opt/app/llm-wiki-explorer` 源码目录。

Hermes 配置、会话、Skills、上传文件和知识库内容不写入镜像，继续通过
Compose 挂载到 `/opt/ds-hermes/data/`，因此重建容器不会丢失数据。

## 构建镜像

构建机需要已有 `ds-hermes-agent:20260818` 基础镜像、Node.js、npm、Docker
和 Buildx。默认前端源码目录为 `/opt/app/llm-wiki-explorer`：

```bash
cd /mnt/d/Project/AI/hermes-agent
scripts/build-knowledge-base-image.sh
```

如目录或镜像标签不同，可以显式指定：

```bash
KNOWLEDGE_BASE_SOURCE_DIR=/path/to/llm-wiki-explorer \
HERMES_BASE_IMAGE=ds-hermes-agent:20260818 \
HERMES_WORKSPACE_IMAGE=ds-hermes-workspace:20260822-chatfix \
scripts/build-knowledge-base-image.sh
```

## 导出镜像

最终镜像的导出包已经包含基础镜像层，不需要另行导出基础镜像：

```bash
scripts/package-knowledge-base-image.sh \
  /path/to/release/ds-hermes-workspace-20260822-chatfix-linux-amd64.tar.gz
```

脚本同时生成 `.sha256` 校验文件。将镜像包、校验文件和
`docker-compose.yml` 一起复制到目标 Linux 机器。

## 目标机部署

```bash
sha256sum -c ds-hermes-workspace-20260822-chatfix-linux-amd64.tar.gz.sha256
docker load -i ds-hermes-workspace-20260822-chatfix-linux-amd64.tar.gz
sudo mkdir -p /opt/ds-hermes/data/hermes
sudo mkdir -p /opt/ds-hermes/data/knowledge_repository
```

在 `docker-compose.yml` 同目录创建 `.env`，至少设置：

```dotenv
API_SERVER_KEY=请填写至少16位的随机密钥
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=请填写Dashboard登录密码
HERMES_WORKSPACE_IMAGE=ds-hermes-workspace:20260822-chatfix
# 可选：该目录下可以放置并分别维护多个知识库
KNOWLEDGE_REPOSITORY_DIR=/opt/ds-hermes/data/knowledge_repository
# 可选：Hermes 配置、会话与 Skills 的持久化目录
HERMES_DATA_DIR=/opt/ds-hermes/data/hermes
# 宿主机访问端口；容器内端口固定为 4178
KNOWLEDGE_BASE_HOST_IP=127.0.0.1
KNOWLEDGE_BASE_HOST_PORT=4178
```

`KNOWLEDGE_REPOSITORY_DIR` 应指向多个知识库的共同父目录。容器内统一显示为
`/opt/knowledge_repository`，在页面中选择其下某个包含 `.wiki-schema.json` 或
`.wiki-schema.md` 的目录即可打开。路径不符合知识库契约时，页面会拒绝打开并
提示该目录不是知识库。

启动：

```bash
HERMES_UID=$(id -u) HERMES_GID=$(id -g) \
docker-compose up -d --no-build
```

验证：

```bash
docker-compose ps
curl -fsS http://127.0.0.1:4178/ >/dev/null
curl -fsS http://127.0.0.1:6060/ >/dev/null
```

知识库页面默认只绑定宿主机 `127.0.0.1:4178`。如果需要使用 14178，设置
`KNOWLEDGE_BASE_HOST_PORT=14178`，不要修改容器端口 4178：

```dotenv
KNOWLEDGE_BASE_HOST_PORT=14178
```

如果需要远程访问，还应显式设置 `KNOWLEDGE_BASE_HOST_IP=0.0.0.0`，并通过
反向代理或 SSH 端口转发暴露，不要直接发布容器内的 8642 API 端口。
