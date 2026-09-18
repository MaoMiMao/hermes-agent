"""Run only in a disposable container with an empty DATA_DIR."""
import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone

Path(os.environ['DATA_DIR']).mkdir(parents=True, exist_ok=True)
os.environ['WEBUI_EMBED_ALLOWED_ORIGINS'] = 'http://localhost:8088'
os.environ['WEBUI_EMBED_AUTO_CREATE'] = 'true'
from fastapi import FastAPI
from fastapi.testclient import TestClient
from open_webui.routers import auths
from open_webui.utils.external_tokens import ExternalTokens

app = FastAPI()
app.include_router(auths.router, prefix='/api/v1/auths')
password = secrets.token_urlsafe(24)
with TestClient(app, client=('192.168.1.10', 1234)) as client:
    response = client.post('/api/v1/auths/signup', json={'email':'admin@example.com','name':'Admin','password':password})
    assert response.status_code == 200, response.text
    admin = {'Authorization':'Bearer '+response.json()['token']}
    client.cookies.clear()
    assert client.get('/api/v1/auths/external-tokens').status_code == 401
    config = {'name':'业务系统','starts':None,'ends':None,'networks':['192.168.1.0/24']}
    now = datetime.now(timezone.utc)
    invalid = {**config,'starts':now.isoformat(),'ends':(now-timedelta(seconds=1)).isoformat()}
    assert client.post('/api/v1/auths/external-tokens',json=invalid,headers=admin).status_code == 400
    assert client.post('/api/v1/auths/external-tokens',json={**config,'networks':['invalid']},headers=admin).status_code == 400
    response = client.post('/api/v1/auths/external-tokens',json=config,headers=admin)
    assert response.status_code == 200, response.text
    credential = response.json()
    assert client.get('/api/v1/auths/external-tokens/'+credential['id']+'/credential',headers=admin).json()['token'] == credential['token']
    listing = client.get('/api/v1/auths/external-tokens',headers=admin).json()
    assert credential['token'] not in str(listing) and 'digest' not in str(listing)
    payload = {'email':'embed+test@example.com','username':'张三 & 李四','token':credential['token']}
    response = client.post('/api/v1/auths/embed/login',json=payload)
    assert response.status_code == 200, response.text
    session = response.json()
    assert session['role'] == 'user' and session['email'] == payload['email']
    assert client.post('/api/v1/auths/embed/login',json=payload).json()['id'] == session['id']
    ordinary = {'Authorization':'Bearer '+session['token']}
    assert client.get('/api/v1/auths/',headers=ordinary).json()['id'] == session['id']
    assert client.get('/api/v1/auths/external-tokens/'+credential['id']+'/credential',headers=ordinary).status_code == 401
    assert client.get('/api/v1/auths/external-tokens',headers=ordinary).status_code == 401
    assert client.post('/api/v1/auths/external-tokens',json=config,headers=ordinary).status_code == 401
    assert client.put('/api/v1/auths/external-tokens/'+credential['id'],json=config,headers=ordinary).status_code == 401
    assert client.delete('/api/v1/auths/external-tokens/'+credential['id'],headers=ordinary).status_code == 401
    assert client.post('/api/v1/auths/embed/login',json={**payload,'email':'admin@example.com'}).status_code == 403
    for constraints in (
        {'networks':['192.168.2.0/24']},
        {'starts':(now+timedelta(days=1)).isoformat()},
        {'ends':(now-timedelta(days=1)).isoformat()},
    ):
        response = client.put('/api/v1/auths/external-tokens/'+credential['id'],json={**config,**constraints},headers=admin)
        assert response.status_code == 200, response.text
        assert client.post('/api/v1/auths/embed/login',json=payload,headers={'X-Forwarded-For':'192.168.2.1'}).status_code == 401
    assert client.put('/api/v1/auths/external-tokens/'+credential['id'],json={**config,'networks':['192.168.1.10']},headers=admin).status_code == 200
    assert client.post('/api/v1/auths/embed/login',json=payload).status_code == 200
    assert client.put('/api/v1/auths/external-tokens/'+credential['id'],json={**config,'enabled':False},headers=admin).status_code == 200
    assert client.post('/api/v1/auths/embed/login',json=payload).status_code == 401
    assert client.put('/api/v1/auths/external-tokens/'+credential['id'],json={**config,'enabled':True},headers=admin).status_code == 200
    assert client.post('/api/v1/auths/embed/login',json=payload).status_code == 200
    origins = ['https://portal.example.com']
    assert client.put('/api/v1/auths/external-tokens/'+credential['id'],json={**config,'enabled':True,'origins':origins},headers=admin).status_code == 200
    page = client.get('/api/v1/auths/embed',params={'token':credential['token']})
    assert page.status_code == 200 and page.headers['content-security-policy'] == 'frame-ancestors https://portal.example.com'
    assert client.put('/api/v1/auths/external-tokens/'+credential['id'],json={**config,'origins':['https://portal.example.com/path']},headers=admin).status_code == 400
    assert client.delete('/api/v1/auths/external-tokens/'+credential['id'],headers=admin).status_code == 200
    assert client.post('/api/v1/auths/embed/login',json=payload).status_code == 401
    assert not client.get('/api/v1/auths/external-tokens',headers=admin).json()
    assert client.get('/api/v1/auths/external-tokens/'+credential['id']+'/credential',headers=admin).status_code == 404
    response = client.post('/api/v1/auths/signin',json={'email':'admin@example.com','password':password})
    assert response.status_code == 200, response.text
    assert client.get('/api/v1/auths/embed').status_code == 200
    assert client.post('/api/v1/auths/embed/tickets',json={}).status_code == 404

store = ExternalTokens(Path(os.environ['DATA_DIR'])/'ip-tests.sqlite3', 'test-only-secret')
raw = store.create('ipv6',None,None,['2001:db8::/32'],'admin')['token']
assert store.authorize(raw,'2001:db8::1') and not store.authorize(raw,'2001:db9::1')
raw = store.create('mapped',None,None,['192.168.1.0/24'],'admin')['token']
assert store.authorize(raw,'::ffff:192.168.1.10')
print('PASS: admin CRUD permissions, secret hash storage, time/IP limits, spoofed header rejection, auto-create, reuse, admin login blocked, revocation and password login')

print('PASS: new Token credentials can be copied by administrators')
