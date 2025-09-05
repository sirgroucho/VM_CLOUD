import hashlib, uuid
from datetime import datetime, timedelta, timezone
import jwt
from flask import current_app
from .models import Device
from . import db

def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def mint_device_token(user_id: int, role: str, services: list[str], long_lived: bool=False) -> tuple[str, Device]:
    # long_lived => 365 days, else 90 days
    days = 365 if long_lived else 90
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=days)
    jti = uuid.uuid4().hex

    payload = {
        "sub": str(user_id),
        "role": role,
        "services": services,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "scope": "device"
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")
    d = Device(user_id=user_id, name="device", jti=jti, token_hash=hash_token(token),
               issued_at=datetime.utcnow(), expires_at=exp.replace(tzinfo=None))
    db.session.add(d)
    db.session.commit()
    return token, d

def revoke_device(device: Device):
    device.revoked_at = datetime.utcnow()
    db.session.commit()

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        token_hash = hash_token(token)
        d: Device | None = db.session.query(Device).filter_by(jti=payload.get("jti")).first()
        if not d or d.token_hash != token_hash or not d.is_active():
            return None
        return payload
    except Exception:
        return None
