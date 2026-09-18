# 警务助手深色样式

`police-dark.css` 将生产环境 `var.css`、`antd-dark.less` 的藏蓝面板、青蓝强调色、蓝灰边框映射到 Open WebUI 的 Tailwind 色阶和现有组件。没有引入 Ant Design，也不需要下载字体或背景图；原 LESS 引用的 `ditu85.webp` 未提供，因此使用纯 CSS 渐变。

根目录 `docker-compose.yaml` 已将文件只读挂载到 Open WebUI 的 `/static/custom.css` 入口。打包离线部署时需携带 `docker/open-webui` 目录。

在 Ubuntu-24.04 中、项目根目录执行（项目名与原部署保持一致）：

```bash
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml up -d --no-deps open-webui
```

如果使用旧版 Compose 遇到 `ContainerConfig`，先对同一项目执行 `stop open-webui`、`rm -f open-webui`，再执行上面的启动命令。不要删除数据卷。

进入 Open WebUI 的个人设置，在通用设置中选择“深色”主题，然后强制刷新页面。此样式沿用现有主题选择，不覆盖用户已选的浅色或 OLED 深色。首次添加挂载需要重建容器，不需要构建镜像；后续修改 CSS 后强制刷新即可。

覆盖范围：登录页及对话页共用色阶、侧栏、输入面板、发送按钮、弹窗边框、Markdown 文字与链接、键盘焦点和选区。错误/警告/成功继续使用原有语义色。
