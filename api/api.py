from ninja import NinjaAPI, Router, Body, File
from ninja import Form
from ninja.files import UploadedFile
from ninja.security import HttpBearer
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from functools import wraps
from typing import List, Optional
from decimal import Decimal
from .models import *
from .schemas import *


class TokenAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            token_obj = Token.objects.get(key=token)
            request.user = token_obj.user
            return token_obj.user
        except Token.DoesNotExist:
            return None

auth = TokenAuth()


def permission_required(check_func):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or not check_func(user):
                raise HttpError(403, "Нет доступа")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

def is_staff(user):
    return user.is_staff

def is_manager(user):
    return user.groups.filter(name='менеджеры').exists()

router = Router()

# === AUTH ===
@router.post("/auth/login", response={200: LoginOut, 401: ErrorOut}, summary="Вход в систему", tags=["Аутентификация"])
def login(request, data: LoginIn):
    user = authenticate(username=data.username, password=data.password)
    if user is None:
        return 401, {"detail": "Неверные учетные данные"}
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key}

@router.post("/auth/register", response={200: LoginOut, 400: ErrorOut}, summary="Регистрация пользователя", tags=["Аутентификация"])
def register(request, data: RegisterIn):
    if User.objects.filter(username=data.username).exists():
        return 400, {"detail": "Пользователь с таким именем уже существует"}
    user = User.objects.create_user(
        username=data.username,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email
    )
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key}

# === ADMIN ===
@router.get("/admin/manager-requests", response={200: List[ManagerOut]}, auth=auth, summary="Список заявок на менеджера", tags=["Администрирование"])
@permission_required(is_staff)
def list_manager_requests(request, status: str = None):
    allowed_statuses = ['ожидает рассмотрения', 'одобрен']
    if status and status not in allowed_statuses:
        return 400, {"detail": "Недопустимый статус фильтрации"}
    qs = ManagerRequest.objects.filter(status=status) if status else ManagerRequest.objects.all()
    return [ManagerOut(id=req.id, user=req.user, status=req.status, created_at=req.created_at) for req in qs]

@router.post("/admin/approve-manager/{request_id}", response={200: dict, 404: ErrorOut}, auth=auth, summary="Подтвердить заявку на менеджера", tags=["Администрирование"])
@permission_required(is_staff)
def approve_manager_request(request, request_id: int):
    try:
        req_obj = ManagerRequest.objects.get(id=request_id, status='ожидает рассмотрения')
    except ManagerRequest.DoesNotExist:
        return 404, {"detail": "Запрос не найден или уже обработан"}
    user = req_obj.user
    group, _ = Group.objects.get_or_create(name='менеджеры')
    user.groups.add(group)
    req_obj.status = 'одобрен'
    req_obj.save()
    return {"message": "Пользователь стал менеджером."}

# === USERS ===
@router.get("/user/users/", response={200: List[UserOut], 403: ErrorOut}, auth=auth, summary="Список пользователей", tags=["Пользователи"])
@permission_required(is_manager)
def list_users(request):
    return User.objects.all()

@router.post("/user/request-manager", response={200: dict, 400: ErrorOut}, auth=auth, summary="Запрос на роль менеджера", tags=["Пользователи"])
def request_manager(request):
    user = request.user
    if user.groups.filter(name='менеджеры').exists():
        return 400, {"detail": "Вы уже менеджер"}
    if ManagerRequest.objects.filter(user=user, status='ожидает рассмотрения').exists():
        return 400, {"detail": "Заявка уже подана"}
    ManagerRequest.objects.create(user=user)
    return {"message": "Заявка принята"}

# === CATEGORIES ===
@router.get("/categories", response={200: List[CategoryOut]}, summary="Список категорий", tags=["Категории"])
def list_categories(request):
    return Category.objects.all()

@router.get("/categories/{slug}", response=CategoryOut, summary="Категория по slug", tags=["Категории"])
def get_category(request, slug: str):
    return get_object_or_404(Category, slug=slug)

@router.get("/categories/{slug}/products", response=List[ProductOut], summary="Товары категории", tags=["Категории"])
def get_products_in_category(request, slug: str):
    category = get_object_or_404(Category, slug=slug)
    return category.products.all()

@router.post("/categories", response=CategoryOut, auth=auth, summary="Создать категорию", tags=["Категории"])
@permission_required(is_manager)
def create_category(request, category: CategoryIn):
    return Category.objects.create(title=category.title, slug=category.slug)

@router.patch("/categories/{slug}", response=CategoryOut, auth=auth, summary="Обновить категорию", tags=["Категории"])
@permission_required(is_manager)
def partial_update_category(request, slug: str, data: CategoryUpdate = Body(...)):
    category = get_object_or_404(Category, slug=slug)
    if data.title is not None:
        category.title = data.title
    if data.slug is not None:
        category.slug = data.slug
    category.save()
    return category

@router.delete("/categories/{slug}", auth=auth, summary="Удалить категорию", tags=["Категории"])
@permission_required(is_manager)
def delete_category(request, slug: str):
    category = get_object_or_404(Category, slug=slug)
    category.delete()
    return {"success": True}

# === PRODUCTS ===
@router.get("/products", response=List[ProductOut], summary="Список товаров", tags=["Товары"])
def list_products(request, min_price: Optional[float] = None, max_price: Optional[float] = None,
                  title: Optional[str] = None, description: Optional[str] = None):
    products = Product.objects.all()
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)
    if title:
        products = products.filter(title__icontains=title)
    if description:
        products = products.filter(description__icontains=description)
    return products

@router.get("/products/{product_id}", response={200: ProductOut, 404: dict}, summary="Товар по ID", tags=["Товары"])
def get_product(request, product_id: int):
    return get_object_or_404(Product, id=product_id)

@router.post("/products", response={201: ProductOut}, auth=auth, summary="Создать товар", tags=["Товары"])
@permission_required(is_manager)
def create_product(
    request,
    title: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    image: UploadedFile = File(...)
):
    category_obj = Category.objects.filter(slug=category).first()
    if not category_obj:
        return 404, {"error": "Категория не найдена"}
    product = Product.objects.create(
        title=title,
        category=category_obj,
        description=description,
        price=price,
        image=image
    )
    return 201, product


@router.patch("/products/{product_id}", response={200: ProductOut, 404: dict}, auth=auth, summary="Обновить товар", tags=["Товары"])
@permission_required(is_manager)
def update_product(
    request,
    product_id: int,
    title: str = Form(None),
    category: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    image: UploadedFile = File(None)
):
    product = get_object_or_404(Product, id=product_id)
    if category:
        category_obj = Category.objects.filter(slug=category).first()
        if not category_obj:
            return 404, {"error": "Категория не найдена"}
        product.category = category_obj
    if title:
        product.title = title
    if description:
        product.description = description
    if price is not None:
        product.price = price
    if image:
        product.image = image
    product.save()
    return product

@router.delete("/products/{product_id}", auth=auth, summary="Удалить товар", tags=["Товары"])
@permission_required(is_manager)
def delete_product(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return {"success": True}

# === ORDERS ===
@router.get("/orders", response={200: List[OrderOut]}, auth=auth, summary="Все заказы", tags=["Заказы"])
@permission_required(is_manager)
def get_all_orders(request):
    return Order.objects.all().prefetch_related("items__product")

@router.get("/orders/my", response=List[OrderOut], auth=auth, summary="Мои заказы", tags=["Заказы"])
def get_my_orders(request):
    return Order.objects.filter(user=request.user).prefetch_related("items__product")

@router.get("/orders/user/{user_id}", response={200: List[OrderOut], 403: ErrorOut}, auth=auth, summary="Заказы пользователя", tags=["Заказы"])
@permission_required(is_manager)
def get_user_orders(request, user_id: int):
    target_user = get_object_or_404(User, id=user_id)
    return Order.objects.filter(user=target_user).prefetch_related("items__product")

@router.post("/orders", response={200: OrderOut, 400: ErrorOut}, auth=auth, summary="Создать заказ из избранного", tags=["Заказы"])
def create_order_from_wishlist(request):
    wishlist = WishlistItem.objects.filter(user=request.user)
    if not wishlist.exists():
        return 400, {"detail": "Избраное пустое"}
    status = OrderStatus.objects.get(name="Новый")
    order = Order.objects.create(user=request.user, status=status, total=0)
    total = Decimal("0.00")
    for item in wishlist:
        item_total = item.product.price * item.quantity
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, cost=item_total)
        total += item_total
    order.total = total
    order.save()
    wishlist.delete()
    return order

@router.put("/orders/{order_id}/status", response={200: OrderOut}, auth=auth, summary="Изменить статус заказа", tags=["Заказы"])
@permission_required(is_manager)
def update_order_status(request, order_id: int, status_id: int):
    order = get_object_or_404(Order, id=order_id)
    status = get_object_or_404(OrderStatus, id=status_id)
    order.status = status
    order.save()
    return order

# === WISHLIST ===
@router.get("/wishlist", response=List[WishlistItemOut], auth=auth, summary="Избранное", tags=["Избранное"])
def get_wishlist(request):
    return WishlistItem.objects.filter(user=request.user)

@router.get("/wishlist/user/{user_id}", response=List[WishlistItemOut], auth=auth, summary="Избранное пользователя", tags=["Избранное"])
@permission_required(is_manager)
def get_user_wishlist_for_manager(request, user_id: int):
    target_user = get_object_or_404(User, id=user_id)
    return WishlistItem.objects.filter(user=target_user)

@router.post("/wishlist", response=WishlistItemOut, auth=auth, summary="Добавить в избранное", tags=["Избранное"])
def add_to_wishlist(request, data: WishlistItemIn):
    product = get_object_or_404(Product, id=data.product_id)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product,
                                                       defaults={"quantity": data.quantity})
    if not created:
        item.quantity += data.quantity
        item.save()
    return item

@router.delete("/wishlist/{product_id}", response=dict, auth=auth, summary="Удалить из избранного", tags=["Избранное"])
def remove_from_wishlist(request, product_id: int):
    item = get_object_or_404(WishlistItem, user=request.user, product_id=product_id)
    item.delete()
    return {"success": True}

@router.delete("/wishlist/{product_id}/decrement", response=dict, auth=auth, summary="Уменьшить в избранном", tags=["Избранное"])
def decrement_from_wishlist(request, product_id: int):
    item = get_object_or_404(WishlistItem, user=request.user, product_id=product_id)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return {"success": True}

# === API OBJECT ===
api = NinjaAPI(title="Api Магазин", version="1.0")
api.add_router("/", router)
