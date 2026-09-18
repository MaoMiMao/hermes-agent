"""Admin-managed external token iframe login; password signin remains unchanged."""
import asyncio
import os
from datetime import datetime
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from open_webui.env import DATA_DIR, WEBUI_SECRET_KEY, WEBUI_AUTH, WEBUI_AUTH_TRUSTED_EMAIL_HEADER
from open_webui.internal.db import get_async_session
from open_webui.models.auths import Auths
from open_webui.models.config import Config
from open_webui.models.users import Users
from open_webui.utils.auth import get_password_hash, get_admin_user
from open_webui.utils.external_tokens import ExternalTokens, normalize_networks
from open_webui.utils.groups import apply_default_group_assignment
from open_webui.utils.misc import validate_email_format

router = APIRouter()
tokens = ExternalTokens(Path(DATA_DIR) / 'external-tokens.sqlite3', WEBUI_SECRET_KEY)


def settings():
    origins = [value.strip() for value in os.getenv('WEBUI_EMBED_ALLOWED_ORIGINS', '').split(',') if value.strip()]
    if not origins:
        raise HTTPException(503, 'Embed login is not configured')
    if not WEBUI_AUTH or WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
        raise HTTPException(503, 'Enable WEBUI_AUTH and remove trusted-header authentication for dual login')
    for origin in origins:
        if origin == "*":
            continue
        parsed = urlsplit(origin)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise HTTPException(503, 'Embed origins must be exact HTTP(S) origins without paths')
    return origins


class ExternalLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    username: str = Field(min_length=1, max_length=100)
    token: str = Field(min_length=32, max_length=256)


class ExternalTokenForm(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    starts: datetime | None = None
    ends: datetime | None = None
    networks: list[str] = Field(default_factory=list, max_length=100)
    enabled: bool = True
    origins: list[str] = Field(default_factory=list, max_length=100)

    def values(self):
        if not self.name.strip():
            raise HTTPException(400, '请输入系统名称')
        for value in (self.starts, self.ends):
            if value is not None and value.tzinfo is None:
                raise HTTPException(400, '有效时间必须包含时区')
        starts = self.starts.timestamp() if self.starts else None
        ends = self.ends.timestamp() if self.ends else None
        if starts is not None and ends is not None and ends <= starts:
            raise HTTPException(400, '结束时间必须晚于开始时间')
        try:
            networks = normalize_networks(self.networks)
        except ValueError:
            raise HTTPException(400, 'IP 格式错误，请输入 IPv4/IPv6 地址或 CIDR 网段')
        origins = list(dict.fromkeys(v.strip() for v in self.origins if v.strip()))
        for origin in origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or any(c.isspace() for c in origin):
                raise HTTPException(400, '跨域设置请输入完整 HTTP(S) 来源，不带路径或末尾斜线')
        return self.name.strip(), starts, ends, networks, self.enabled, origins


@router.get('/external-tokens')
async def list_external_tokens(response: Response, admin=Depends(get_admin_user)):
    response.headers['Cache-Control'] = 'no-store'
    return await asyncio.to_thread(tokens.list)


@router.post('/external-tokens')
async def create_external_token(body: ExternalTokenForm, response: Response, admin=Depends(get_admin_user)):
    response.headers['Cache-Control'] = 'no-store'
    name, starts, ends, networks, enabled, origins = body.values()
    return await asyncio.to_thread(tokens.create, name, starts, ends, networks, admin.id, enabled, origins)


@router.put('/external-tokens/{identifier}')
async def update_external_token(identifier: str, body: ExternalTokenForm, admin=Depends(get_admin_user)):
    if not await asyncio.to_thread(tokens.update, identifier, *body.values()):
        raise HTTPException(404, 'Token 不存在或已撤销')
    return {'success': True}


@router.delete('/external-tokens/{identifier}')
async def delete_external_token(identifier: str, admin=Depends(get_admin_user)):
    if not await asyncio.to_thread(tokens.delete, identifier):
        raise HTTPException(404, 'Token 不存在')
    return {'success': True}


@router.get('/external-tokens/{identifier}/credential')
async def get_external_credential(identifier: str, response: Response, admin=Depends(get_admin_user)):
    response.headers['Cache-Control'] = 'no-store'
    try:
        return {'token': await asyncio.to_thread(tokens.recover, identifier)}
    except KeyError:
        raise HTTPException(404, 'Token 不存在')
    except ValueError as error:
        raise HTTPException(409, str(error))


@router.get('/embed', response_class=HTMLResponse)
async def embed_page(request: Request):
    origins = settings()
    raw = request.query_params.get('token', '')
    if raw:
        if len(raw) > 256 or not await asyncio.to_thread(tokens.authorize, raw, request.client.host if request.client else ''):
            raise HTTPException(401, '外部 Token 无效或访问受限')
        configured = await asyncio.to_thread(tokens.origins_for, raw)
        if configured:
            origins = configured
    html = Path(__file__).with_name('embed_login.html').read_text(encoding='utf-8')
    return HTMLResponse(html,
                        headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
                                 'Content-Security-Policy': "frame-ancestors " + ' '.join(origins)})


@router.post('/embed/login')
async def external_login(body: ExternalLoginRequest, request: Request, response: Response,
                         db: AsyncSession = Depends(get_async_session)):
    settings()
    # request.client is resolved by the ASGI server's trusted-proxy configuration.
    # Never parse arbitrary X-Forwarded-For here.
    peer = request.client.host if request.client else ''
    if not await asyncio.to_thread(tokens.authorize, body.token, peer):
        raise HTTPException(401, '外部 Token 无效、未生效、已过期、已撤销或 IP 不允许')
    email = body.email.strip().lower()
    if not validate_email_format(email) or not body.username.strip():
        raise HTTPException(400, 'Invalid email or username')
    payload = {'email': email, 'name': body.username.strip()}
    # Avoid the normal signup helper's first-user admin promotion.
    if not await Users.has_users(db=db):
        raise HTTPException(409, 'Create the initial administrator using normal signup first')
    user = await Users.get_user_by_email(payload['email'], db=db)
    if not user:
        if os.getenv('WEBUI_EMBED_AUTO_CREATE', 'false').lower() != 'true':
            raise HTTPException(403, 'Ask an administrator to create this user first')
        try:
            user = await Auths.insert_new_auth(email=payload['email'], name=payload['name'],
                password=await get_password_hash(secrets.token_urlsafe(32)), role='user', db=db)
        except IntegrityError:
            await db.rollback()
            user = await Users.get_user_by_email(payload['email'], db=db)
        if not user:
            raise HTTPException(500, 'Unable to create user')
        await apply_default_group_assignment(await Config.get('ui.default_group_id'), user.id, db=db)
    user = await Auths.authenticate_user_by_email(payload['email'], db=db)
    if not user or user.role != 'user':
        raise HTTPException(403, '外部登录仅允许普通用户；管理员请使用密码登录')
    from open_webui.routers.auths import create_session_response
    response.headers['Cache-Control'] = 'no-store'
    return await create_session_response(request, user, db, response, set_cookie=True, source='embed')
