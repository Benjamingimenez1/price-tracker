from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, index=True, nullable=False)
    username   = Column(String, unique=True, index=True, nullable=False)
    hashed_pw  = Column(String, nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    products = relationship("Product", back_populates="owner", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    name          = Column(String, nullable=False)
    url           = Column(Text, nullable=False)
    current_price = Column(Float, nullable=True)
    alert_price   = Column(Float, nullable=True)
    is_active     = Column(Boolean, default=True)
    last_checked  = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner   = relationship("User", back_populates="products")
    history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price      = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="history")
