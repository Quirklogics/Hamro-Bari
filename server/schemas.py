from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# --- Produce Schemas ---
class ProduceBase(BaseModel):
    name_ne: str
    name_en: str
    scientific_name: Optional[str] = None
    category: str = "veggies"
    district: str
    district_ne: str
    district_label: str
    farmer_ne: str
    farmer_en: str
    verified: bool = True
    price: float
    unit_ne: str = "प्रति १ के.जी."
    unit_en: str = "per 1 kg"
    freshness_ne: str = "टिपेको १८ घण्टा"
    freshness_en: str = "18 hrs since harvest"
    is_organic: bool = True
    tag_ne: str = "बारीबाट Direct"
    tag_en: str = "Direct from farm"
    description_ne: Optional[str] = None
    description_en: Optional[str] = None
    image_url: str
    stock_kg: float = 100.0

class ProduceCreate(ProduceBase):
    pass

class ProduceResponse(ProduceBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Order Schemas ---
class OrderItemCreate(BaseModel):
    produce_id: int
    quantity: float = Field(gt=0)

class OrderItemResponse(BaseModel):
    id: int
    produce_id: Optional[int] = None
    item_name_ne: str
    quantity: float
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: Optional[str] = "Residential Customer"
    customer_phone: Optional[str] = None
    society_cluster: str
    delivery_type: str = "hub"  # 'hub' or 'doorstep'
    payment_method: str = "esewa"  # 'esewa', 'khalti', 'cod'
    discount_code: Optional[str] = None
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: str
    order_no: str
    society_cluster: str
    delivery_type: str
    delivery_day: str
    payment_method: str
    payment_status: str
    subtotal_amount: float
    delivery_fee: float
    jute_deposit: float
    discount_amount: float
    total_amount: float
    order_status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


# --- Farmer Voice Batch Schemas ---
class FarmerBatchCreate(BaseModel):
    farmer_name: str
    district: str
    crop_name: str
    weight_kg: float
    grade: str = "Grade A (उत्कृष्ट)"
    ready_time: Optional[str] = "बिहीबार बिहान ७:०० बजे"
    est_payout: float

class FarmerBatchResponse(BaseModel):
    id: int
    batch_no: str
    farmer_name: str
    district: str
    crop_name: str
    weight_kg: float
    grade: str
    ready_time: Optional[str]
    est_payout: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Logistics & Admin Schemas ---
class DispatchTruckResponse(BaseModel):
    id: int
    truck_code: str
    route_name: str
    driver_name: str
    vehicle_no: str
    capacity_kg: float
    loaded_kg: float
    departure_time: str
    status: str

    class Config:
        from_attributes = True

class SmsBroadcastRequest(BaseModel):
    message: str
    category: str = "farmer_alert"
