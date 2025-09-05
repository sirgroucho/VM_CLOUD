from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from . import db, bcrypt

class AuditLog(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[int | None] = mapped_column(Integer)
    ip: Mapped[str | None] = mapped_column(String(64))
    ua: Mapped[str | None] = mapped_column(String(256))
    metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user|admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    services = relationship("UserService", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.check_password_hash(self.password_hash, password)
        except ValueError:
            return False

class Service(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # 'minecraft','media','nextcloud'
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # optional display URL
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class UserService(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("service.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="member")
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="services")
    service = relationship("Service")

class Application(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_services: Mapped[str] = mapped_column(String(255), default="")  # CSV of service codes
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|accepted|denied
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64))
    ua: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Device(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="devices")

    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and datetime.utcnow() > self.expires_at:
            return False
        return True
