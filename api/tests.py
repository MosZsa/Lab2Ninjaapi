from django.test import TestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group, User
import json
from .models import *

class CategoryApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="manager", password="pass")
        group = Group.objects.create(name="менеджеры")
        self.user.groups.add(group)
        self.token = Token.objects.create(user=self.user)
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token.key}"}
        self.category = Category.objects.create(title="Телевизоры", slug="televizory")

    def test_get_categories_valid(self):
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

    def test_get_categories_invalid_endpoint(self):
        response = self.client.get("/api/category")
        self.assertEqual(response.status_code, 404)

    def test_create_category_valid(self):
        payload = {'title': 'Смартфоны', 'slug': 'smartphones'}
        response = self.client.post('/api/categories', content_type='application/json', data=json.dumps(payload), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Смартфоны')

    def test_create_category_invalid_data(self):
        payload = {'slug': 'no-title'}
        response = self.client.post('/api/categories', content_type='application/json', data=json.dumps(payload), **self.headers)
        self.assertEqual(response.status_code, 422)

    def test_create_category_broken_schema(self):
        response = self.client.post('/api/categories', content_type='text/plain', data='random text', **self.headers)
        self.assertEqual(response.status_code, 400)

    def test_get_category_valid(self):
        response = self.client.get('/api/categories/televizory')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['slug'], 'televizory')

    def test_get_category_invalid_slug(self):
        response = self.client.get('/api/categories/notfound')
        self.assertEqual(response.status_code, 404)

    def test_get_category_broken_slug_type(self):
        response = self.client.get('/api/categories/123!@#')
        self.assertIn(response.status_code, [404, 422])

    def test_delete_category_valid(self):
        response = self.client.delete('/api/categories/televizory', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

    def test_delete_category_invalid_slug(self):
        response = self.client.delete('/api/categories/no-such-slug', **self.headers)
        self.assertEqual(response.status_code, 404)

    def test_get_products_in_category_valid(self):
        Product.objects.create(title="Samsung QLED", category=self.category, price=50000, description="QLED 4K TV")
        response = self.client.get('/api/categories/televizory/products')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_get_products_in_category_invalid_slug(self):
        response = self.client.get('/api/categories/nonexistent/products')
        self.assertEqual(response.status_code, 404)


class ProductApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="manager", password="pass")
        group = Group.objects.create(name="менеджеры")
        self.user.groups.add(group)
        self.token = Token.objects.create(user=self.user)
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token.key}"}
        self.category = Category.objects.create(title="Телевизоры", slug="televizory")
        self.product = Product.objects.create(title="Samsung QLED", category=self.category, price=50000, description="QLED 4K TV")

    def test_list_products_valid(self):
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_list_products_invalid_filter(self):
        response = self.client.get("/api/products?min_price=invalid")
        self.assertEqual(response.status_code, 422)

    def test_list_products_broken_structure(self):
        response = self.client.get("/api/products?min_price=")
        self.assertEqual(response.status_code, 422)

    def test_create_product_valid(self):
        payload = {
            "title": "LG OLED",
            "category": "televizory",
            "description": "Новый OLED телевизор",
            "price": 70000
        }
        response = self.client.post("/api/products", data=json.dumps(payload), content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['title'], "LG OLED")

    def test_create_product_invalid_category(self):
        payload = {
            "title": "LG OLED",
            "category": "no-category",
            "description": "Новый OLED телевизор",
            "price": 70000
        }
        response = self.client.post("/api/products", data=json.dumps(payload), content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 404)
        if response.headers.get("Content-Type") == "application/json":
            self.assertIn("error", response.json())

    def test_create_product_broken(self):
        payload = {
            "title": "LG OLED",
            "description": "Описание",
            "price": 70000
        }
        response = self.client.post("/api/products", data=json.dumps(payload), content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 404)

    def test_get_product_valid(self):
        response = self.client.get(f"/api/products/{self.product.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], "Samsung QLED")

    def test_get_product_invalid(self):
        response = self.client.get("/api/products/999")
        self.assertEqual(response.status_code, 404)

    def test_get_product_broken(self):
        response = self.client.get("/api/products/abc")
        self.assertEqual(response.status_code, 422)

    def test_update_product_valid(self):
        payload = {
            "title": "Обновленный Samsung",
            "category": "televizory",
            "description": "Обновленное описание",
            "price": 60000
        }
        response = self.client.patch(f"/api/products/{self.product.id}", data=json.dumps(payload), content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], "Обновленный Samsung")

    def test_update_product_invalid_category(self):
        payload = {
            "title": "Обновленный Samsung",
            "category": "wrong-category",
            "description": "Обновленное описание",
            "price": 60000
        }
        response = self.client.patch(f"/api/products/{self.product.id}", data=json.dumps(payload), content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 404)

    def test_update_product_broken_schema(self):
        payload = {
            "title": "Samsung",
            "category": "televizory",
            "description": "Описание",
            "price": "cheap"
        }
        response = self.client.patch(f"/api/products/{self.product.id}", data=json.dumps(payload), content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 422)

    def test_delete_product_valid(self):
        response = self.client.delete(f"/api/products/{self.product.id}", **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True})

    def test_delete_product_invalid(self):
        response = self.client.delete("/api/products/999", **self.headers)
        self.assertEqual(response.status_code, 404)

    def test_delete_product_broken(self):
        response = self.client.delete("/api/products/abc", **self.headers)
        self.assertEqual(response.status_code, 422)