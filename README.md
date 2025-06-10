## API Магазин — Django Ninja

Проект представляет собой API-интерфейс для онлайн-магазина с поддержкой:

* регистрации/логина через токены
* разграничения прав пользователей (админ, менеджер, пользователь)
* управления категориями и товарами
* заказов, избранного, фильтрации и загрузки изображений


## Установка и запуск

1. Склонируйте или скачайте репозиторий:

```bash
git clone https://github.com/MosZsa/Lab2Ninjaapi
cd Lab2Ninjaapi
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Создайте и примените миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Запустите сервер:

```bash
python manage.py runserver
```

5. Откройте документацию API:

```
http://127.0.0.1:8000/docs
````

## Основные эндпоинты

### Аутентификация

* `POST /auth/register` — регистрация
* `POST /auth/login` — вход (получение токена)



### Категории

* `GET /categories` — список
* `GET /categories/{slug}` — конкретная категория
* `POST /categories` — создать (менеджер)
* `PATCH /categories/{slug}` — редактировать
* `DELETE /categories/{slug}` — удалить



### Товары

* `GET /products` — список (фильтрация: цена, название, описание)
* `GET /products/{id}` — получить товар
* `POST /products` — создать (менеджер, **поддержка загрузки изображений**)
* `PATCH /products/{id}` — редактировать
* `DELETE /products/{id}` — удалить

При создании товара:

* `title` — строка
* `description` — строка
* `price` — число
* `category` — slug категории
* `image` — файл (jpg/png и др.)


### Избранное

* `GET /wishlist` — моё избранное
* `POST /wishlist` — добавить товар
* `DELETE /wishlist/{product_id}` — удалить
* `DELETE /wishlist/{product_id}/decrement` — уменьшить количество



### Заказы

* `GET /orders/my` — мои заказы
* `POST /orders` — создать заказ из избранного
* `GET /orders` — все заказы (менеджер)
* `PUT /orders/{id}/status` — сменить статус (менеджер)


### Администрирование

* `GET /admin/manager-requests` — заявки на менеджеров
* `POST /admin/approve-manager/{request_id}` — одобрить заявку



## Работа с изображениями

* Загруженные изображения сохраняются в папке `images/`.
* Доступны по пути `/media/images/...`. Например `http://127.0.0.1:8000/media/images/Samsung_QLED.png`
* Отображаются в API (`GET /products`) в поле `image`.



## Тестирование

```bash
python manage.py test
```

Тесты покрывают:

* категории (создание, удаление, slug)
* товары (фильтрация, ошибки, доступ)
* валидацию схем и токенов

## Примеры пользователей

| Имя      | Пароль                       |
| -------- | ---------------------------- |
| admin    | admin                        |
| manager1 | pass                         |
| manager2 | pass                         |
| user1    | pass                         |
| user2    | pass                         |

