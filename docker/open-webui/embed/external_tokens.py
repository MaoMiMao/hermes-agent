"""External-system entry credentials, hashed for authentication and encrypted for admin URL copying."""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
import ipaddress
import json
import secrets
import sqlite3
import time
import uuid
from pathlib import Path


def normalize_networks(values):
    return list(dict.fromkeys(str(ipaddress.ip_network(value.strip(), strict=False)) for value in values if value.strip()))


class ExternalTokens:
    def __init__(self, path, secret=None):
        self.path = Path(path)
        self.cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())) if secret else None

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE IF NOT EXISTS external_tokens (id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL, name TEXT NOT NULL, starts REAL, ends REAL, networks TEXT NOT NULL, created REAL NOT NULL, revoked REAL, created_by TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, origins TEXT NOT NULL DEFAULT '[]', prefix TEXT NOT NULL DEFAULT '', encrypted TEXT NOT NULL)")
        return db

    def list(self):
        db = self.connect()
        try:
            rows = db.execute('SELECT id, name, starts, ends, networks, created, revoked, created_by, enabled, origins, prefix FROM external_tokens ORDER BY created DESC').fetchall()
            return [{**dict(row), 'networks':json.loads(row['networks']), 'origins':json.loads(row['origins']), 'enabled':bool(row['enabled'])} for row in rows]
        finally:
            db.close()

    def create(self, name, starts, ends, networks, actor, enabled=True, origins=None):
        raw = 'owui_ext_' + secrets.token_urlsafe(32)
        identifier = str(uuid.uuid4())
        db = self.connect()
        try:
            with db:
                db.execute('INSERT INTO external_tokens (id,digest,name,starts,ends,networks,created,revoked,created_by,enabled,origins,prefix,encrypted) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)',
                    (identifier, hashlib.sha256(raw.encode()).hexdigest(), name, starts, ends, json.dumps(networks), time.time(), actor, int(enabled), json.dumps(origins or []), raw[:17], self.cipher.encrypt(raw.encode()).decode() if self.cipher else None))
        finally:
            db.close()
        return {'id':identifier, 'token':raw}

    def update(self, identifier, name, starts, ends, networks, enabled=True, origins=None):
        db = self.connect()
        try:
            with db:
                result = db.execute('UPDATE external_tokens SET name=?, starts=?, ends=?, networks=?, enabled=?, origins=? WHERE id=? AND revoked IS NULL',
                    (name, starts, ends, json.dumps(networks), int(enabled), json.dumps(origins or []), identifier))
            return bool(result.rowcount)
        finally:
            db.close()

    def revoke(self, identifier):
        db = self.connect()
        try:
            with db:
                result = db.execute('UPDATE external_tokens SET revoked=COALESCE(revoked, ?) WHERE id=?', (time.time(), identifier))
            return bool(result.rowcount)
        finally:
            db.close()

    def authorize(self, token, peer):
        db = self.connect()
        try:
            row = db.execute('SELECT * FROM external_tokens WHERE digest=?', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        finally:
            db.close()
        now = time.time()
        if not row or not row['enabled'] or row['revoked'] is not None or (row['starts'] is not None and now < row['starts']) or (row['ends'] is not None and now >= row['ends']):
            return None
        networks = json.loads(row['networks'])
        if networks:
            try:
                address = ipaddress.ip_address(peer)
                if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
                    address = address.ipv4_mapped
                if not any(address in ipaddress.ip_network(net) for net in networks):
                    return None
            except ValueError:
                return None
        return row['id']

    def origins_for(self, token):
        db = self.connect()
        try:
            row = db.execute('SELECT origins FROM external_tokens WHERE digest=?', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            return json.loads(row['origins']) if row else []
        finally:
            db.close()

    def delete(self, identifier):
        db = self.connect()
        try:
            with db:
                result = db.execute('DELETE FROM external_tokens WHERE id=?', (identifier,))
            return bool(result.rowcount)
        finally:
            db.close()

    def recover(self, identifier):
        db = self.connect()
        try:
            row = db.execute('SELECT encrypted FROM external_tokens WHERE id=?', (identifier,)).fetchone()
            if not row:
                raise KeyError(identifier)
            if not row['encrypted'] or not self.cipher:
                raise ValueError('Token 凭据缺失，请删除该记录并重新创建')
            try:
                return self.cipher.decrypt(row['encrypted'].encode()).decode()
            except InvalidToken:
                raise ValueError('Token 解密失败，请检查 WEBUI_SECRET_KEY')
        finally:
            db.close()
