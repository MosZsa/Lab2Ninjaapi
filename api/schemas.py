from ninja import Schema, File
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from ninja.files import UploadedFile



class RegisterIn(Schema):
    username: str
    password: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    email: Optional[str] = ""


class LoginIn(Schema):
    username: str
    password: str

class LoginOut(Schema):
    token: str


class ErrorOut(Schema):
    detail: str

class UserOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True



class ManagerOut(Schema):
    id: int
    user: UserOut
    status: str
    created_at: datetime



class CategoryIn(Schema):
    title: str
    slug: str

class CategoryOut(Schema):
    id: int
    title: str
    slug: str

    class Config:
        from_attributes = True


class CategoryUpdate(Schema):
    title: Optional[str]
    slug: Optional[str]


class ProductIn(Schema):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class ProductOut(Schema):
    id: int
    title: str
    category_id: int
    description: str
    price: float
    image: Optional[str] 
    category: CategoryOut

    class Config:
        from_attributes = True


class ProductFilter(Schema):
    min_price: Optional[float]
    max_price: Optional[float]
    title: Optional[str]
    description: Optional[str]


class WishlistItemIn(Schema):
    product_id: int
    quantity: Optional[int] = 1


class WishlistItemOut(Schema):
    id: int
    quantity: int
    product: ProductOut

    class Config:
        from_attributes = True



class StatusOut(Schema):
    id: int
    name: str

    class Config:
        from_attributes = True




class OrderIn(Schema):
    user: int
    status: int
    total: float


class OrderItemOut(Schema):
    id: int
    product: ProductOut
    cost: float
    quantity: int

    class Config:
        from_attributes = True


class OrderItemIn(Schema):
    product: int
    quantity: int


class OrderOut(Schema):
    id: int
    user_id: int
    status: StatusOut
    total: float
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True