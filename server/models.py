import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from server.database import Base

class Produce(Base):
    __tablename__ = "produce"

    id = Column(Integer, primary_key=True, index=True)
    name_ne = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)
    scientific_name = Column(String(255), nullable=True)
    category = Column(String(50), nullable=False, default="veggies")
    district = Column(String(100), nullable=False)
    district_ne = Column(String(255), nullable=False)
    district_label = Column(String(255), nullable=False)
    farmer_ne = Column(String(255), nullable=False)
    farmer_en = Column(String(255), nullable=False)
    verified = Column(Boolean, default=True)
    price = Column(Numeric(10, 2), nullable=False)
    unit_ne = Column(String(100), default="प्रति १ के.जी.")
    unit_en = Column(String(100), default="per 1 kg")
    freshness_ne = Column(String(255), default="टिपेको १८ घण्टा")
    freshness_en = Column(String(255), default="18 hrs since harvest")
    is_organic = Column(Boolean, default=True)
    tag_ne = Column(String(255), default="बारीबाट Direct")
    tag_en = Column(String(255), default="Direct from farm")
    description_ne = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    image_url = Column(Text, nullable=False)
    stock_kg = Column(Numeric(10, 2), default=100.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = relationship("OrderItem", back_populates="produce")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), default="Residential Customer")
    customer_phone = Column(String(50), nullable=True)
    society_cluster = Column(String(255), nullable=False)
    delivery_type = Column(String(50), nullable=False, default="hub")
    delivery_day = Column(String(50), default="wednesday")
    payment_method = Column(String(50), nullable=False, default="esewa")
    payment_status = Column(String(50), default="pending")
    subtotal_amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    delivery_fee = Column(Numeric(10, 2), nullable=False, default=0.0)
    jute_deposit = Column(Numeric(10, 2), nullable=False, default=30.0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    order_status = Column(String(50), default="confirmed")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    produce_id = Column(Integer, ForeignKey("produce.id", ondelete="SET NULL"), nullable=True)
    item_name_ne = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    produce = relationship("Produce", back_populates="order_items")


class FarmerBatch(Base):
    __tablename__ = "farmer_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(50), unique=True, nullable=False, index=True)
    farmer_name = Column(String(255), nullable=False)
    district = Column(String(255), nullable=False)
    crop_name = Column(String(255), nullable=False)
    weight_kg = Column(Numeric(10, 2), nullable=False)
    grade = Column(String(50), default="Grade A (उत्कृष्ट)")
    ready_time = Column(String(255), nullable=True)
    est_payout = Column(Numeric(10, 2), nullable=False)
    status = Column(String(100), default="संकलन केन्द्र पुग्यो")
    created_at = Column(DateTime, default=datetime.utcnow)


class DispatchTruck(Base):
    __tablename__ = "dispatch_trucks"

    id = Column(Integer, primary_key=True, index=True)
    truck_code = Column(String(50), unique=True, nullable=False)
    route_name = Column(String(255), nullable=False)
    driver_name = Column(String(255), nullable=False)
    vehicle_no = Column(String(100), nullable=False)
    capacity_kg = Column(Numeric(10, 2), nullable=False)
    loaded_kg = Column(Numeric(10, 2), default=0.0)
    departure_time = Column(String(100), nullable=False)
    status = Column(String(100), default="लोडिङ हुँदैछ")


class SmsLog(Base):
    __tablename__ = "sms_logs"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    recipients_count = Column(Integer, default=1)
    category = Column(String(50), default="farmer_alert")
    sent_at = Column(DateTime, default=datetime.utcnow)
