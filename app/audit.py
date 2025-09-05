from .models import AuditLog
from . import db
from flask import g

def audit(action: str, target_type: str | None=None, target_id: int | None=None, meta: dict | None=None, actor_user_id: int | None=None):
    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip=getattr(g, "client_ip", None),
        ua=getattr(g, "user_agent", None),
        metadata=meta or {},
    )
    db.session.add(log)
    db.session.commit()
