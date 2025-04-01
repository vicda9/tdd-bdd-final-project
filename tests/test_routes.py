######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"

######################################################################
#  T E S T   C A S E S
######################################################################


class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

############################################################
# Utility function to bulk create products
############################################################

    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)

        return products

######################################################################
#  T E S T   C A S E S
######################################################################

    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_product(self):
        """It should Read a single Product"""
        test_product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)

    def test_update_product(self):
        """It should Update an existing Product"""
        test_product = self._create_products()[0]
        new_data = test_product.serialize()
        new_data["name"] = "Updated Name"
        response = self.client.put(f"{BASE_URL}/{test_product.id}", json=new_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Updated Name")

    def test_delete_product(self):
        """It should Delete a Product"""
        test_product = self._create_products()[0]
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_products(self):
        """It should List all Products"""
        self._create_products(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 3)

    def test_find_product_by_name(self):
        """It should Find a Product by Name"""
        self._create_products(3)
        response = self.client.get(BASE_URL, query_string={"name": "Hat"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_find_product_by_category(self):
        """It should Find Products by Category"""
        self._create_products(3)
        response = self.client.get(BASE_URL, query_string={"category": "CLOTHS"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_find_product_by_availability(self):
        """It should Find Products by Availability"""
        self._create_products(3)
        response = self.client.get(BASE_URL, query_string={"available": "True"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

############################################################
# E R R O R   T E S T S
############################################################

    def test_bad_request(self):
        """It should return a 400 Bad Request"""
        response = self.client.post(BASE_URL, json={"wrong_key": "value"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """It should return a 405 Method Not Allowed"""
        response = self.client.put(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unsupported_media_type(self):
        """It should return 415 Unsupported Media Type"""
        response = self.client.post(BASE_URL, data="{}", content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_not_found(self):
        """It should return 404 Not Found"""
        response = self.client.get(f"{BASE_URL}/9999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_internal_server_error(self):
        """It should return 500 Internal Server Error"""
        response = self.client.get("/cause-error")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.get_json()
        self.assertEqual(data["error"], "Internal Server Error")

    def test_missing_content_type(self):
        """It should return 415 if no Content-Type header"""
        response = self.client.post(BASE_URL, data='{}')  # No content-type
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_find_product_by_invalid_category(self):
        """It should return 400 for invalid category filter"""
        response = self.client.get(BASE_URL, query_string={"category": "INVALID"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_with_invalid_data(self):
        """It should return 400 on invalid update data"""
        product = self._create_products()[0]
        invalid_data = {
            "name": "Bad Update",
            "description": "Invalid category",
            "price": "20.00",
            "available": True,
            "category": "INVALID"
        }
        response = self.client.put(f"{BASE_URL}/{product.id}", json=invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
