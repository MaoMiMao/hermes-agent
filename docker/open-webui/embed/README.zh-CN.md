# 管理员外部 Token + iframe 集成

已替换原签名/票据方案。管理入口：管理员面板 → 设置 → 系统 → 访问控制。

## 使用步骤

1. 重建 Open WebUI 镜像并重建容器（此修改包括前端管理面板）。
2. 使用管理员账号登录，进入“访问控制”，右上角点击“＋”打开创建弹窗。
3. 填写系统名称、可选开始时间、结束时间（可选择不限时），以及可选 IP 白名单。支持单个 IPv4/IPv6 或 CIDR，例如 `192.168.1.10`、`10.0.0.0/8`、`2001:db8::/32`。每行一个或逗号分隔；留空不限制。
4. 点击“创建”。创建时显示明文，同时生成示例 iframe URL；列表可随时复制带 Token 的 URL 模板；列表展示 API Key 摘要、启用状态、IP、到期时间及跨域设置。可以有效期内启用/停用（可恢复），编辑名称、期限、IP、跨域来源，或删除 Token。
5. 第三方页面设置 iframe 地址：

```javascript
const url = new URL('https://助手地址/api/v1/auths/embed');
url.searchParams.set('email', currentUser.email);
url.searchParams.set('username', currentUser.name);
url.searchParams.set('token', systemAccessToken);
document.getElementById('assistant').src = url.toString();
```

```html
<iframe id="assistant" title="警务助手" referrerpolicy="no-referrer"
  style="width:100%;height:100vh;border:0"></iframe>
```

不需要盐值、不需要业务 Token、签名、票据交换或 postMessage。系统访问 Token 由管理员管理。已有普通账户按邮箱复用；允许自动开户时新建普通 user 账户，原有账号密码不变。管理员、pending 及停用账户不能通过该入口登录。自动开户的随机密码如需独立使用，可由管理员另行设置。

## 部署配置

保持 `WEBUI_AUTH=true`，移除两个 `WEBUI_AUTH_TRUSTED_*_HEADER`，确保密码登录不受影响。移除之前的 WEBUI_EMBED_SALT/WEBUI_EMBED_SECRET。

openwebui.env 示例：

```dotenv
WEBUI_EMBED_ALLOWED_ORIGINS=http://localhost:8088,https://portal.example.com
WEBUI_EMBED_AUTO_CREATE=true
```

域名填写完整 origin，不带路径和尾部斜线。`*` 允许任意网站嵌入，但不绕过 Token 校验。该选项控制 iframe 来源，不是访问者 IP。

WSL Ubuntu-24.04 项目目录执行：

```bash
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml build open-webui
docker-compose -p hermes-openwebui --env-file openwebui.env -f docker-compose.yaml up -d --no-deps open-webui
```

旧 Compose 如遇 ContainerConfig，对同项目先 stop open-webui、rm -f open-webui，再 up；不要删除数据卷。

## 简单 iframe 验证

```bash
python3 docker/open-webui/embed/demo.py
```

打开 **http://localhost:8088/**，填写助手地址、邮箱、姓名，以及管理面板生成的 Token，点击“进入助手”。不需要额外密钥或生成签名。该示例只监听本机，不持久化 Token；不要直接双击 HTML，以免 iframe 来源不匹配。

## 时间、IP 和撤销的准确含义

- 起止时间由管理页面本地时区输入，以带时区的 ISO 时间传给服务端，持久化为 Unix 时间。开始留空立即生效，结束留空不限时。
- IP 是浏览器请求到达 Open WebUI 时服务端识别的地址，不是第三方业务服务器的 IP。在 Docker/代理后可能看到代理或 NAT 地址，应按实际部署确认。
- 应用不自行解析 X-Forwarded-For。若使用反向代理，应让 ASGI 服务只信任明确的代理地址，并限制后端只能从该代理访问；不能为了方便信任任意来源转发头。
- 时效、IP、撤销仅作用于新的登录请求，已经签发的普通 Open WebUI 会话按原会话期限存续，不会被本功能强制注销。
- Token 作为系统级访问凭据允许持有者指定任意普通用户邮箱，因此必须只分发给可信第三方。无法用于管理员登录。URL 含凭据，使用 HTTPS，不记录完整查询参数，不公开分享。页面立即清除 URL，设置 no-referrer/no-store；这不能消除代理首次访问日志或父页面 DOM 中的凭据。
- 优先同站点 HTTPS；跨站 iframe 仍受浏览器 Cookie/存储策略限制。代理 CSP/X-Frame-Options 也需要允许业务域名嵌入。

## 持久化与实现

Token 摘要、加密副本和管理信息存入 DATA_DIR/external-tokens.sqlite3，随现有数据卷持久化；备份时连同此文件备份。该实现面向当前单实例/共享本地数据卷 Compose，不支持不同节点各自独立数据卷的统一 Token 管理。

- ExternalTokens.svelte：独立管理员面板组件，作为 SettingsModal.svelte 的独立“访问控制”标签页。
- external_tokens.py：摘要及加密副本持久化、起止时间、删除和 IPv4/IPv6 CIDR 校验。
- embed_auth.py：管理员 CRUD 和独立外部登录接口。
- embed_login.html：从 URL 读取身份与 Token、登录、保存会话并进入首页。
- demo.py/demo.html：纯 URL iframe 验证。
- install.py：`python3 docker/open-webui/embed/install.py ../open-webui` 可将该本地扩展重新安装到源码。
- verify_api.py：仅供无网络临时容器及空 DATA_DIR 验证，不能对生产数据运行。

跨域设置按 Token 配置：填入允许 iframe 嵌入的完整 HTTP(S) origin（不带路径/尾部斜线），生成入口的 CSP frame-ancestors；留空沿用 WEBUI_EMBED_ALLOWED_ORIGINS。此设置不是通用 API CORS 开关，不能绕过浏览器跨站存储策略。

列表“复制 URL”生成 `?email={email}&username={username}&token=真实Token`，第三方需将占位符替换成 URL 编码后的用户邮箱和姓名。浏览器不允许自动复制时显示手动复制窗口。新 Token 使用 WEBUI_SECRET_KEY 派生密钥加密保存原文，仅管理员复制接口可解密，列表接口不返回明文或密文；必须保留原 WEBUI_SECRET_KEY，改变它会导致已保存 Token 无法解密。删除会永久移除记录，前端弹出确认；不要用删除代替可恢复的停用。已建立的会话不受启停/删除即时影响。

列表操作固定为“编辑 / 复制 URL / 删除”，复制按钮不根据历史记录类型切换。不提供旧 Token 导入或旧数据库迁移功能；新建 Token 完整保存加密凭据后即可复制。
