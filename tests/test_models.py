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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
from tests.test_base import BaseTestCase
from decimal import Decimal
from service.models import Product, Category, DataValidationError
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(BaseTestCase):
    """Test Cases for Product Model"""

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a product from the database"""
        product = ProductFactory()
        product.create()
        # Read the product by ID
        found_product = Product.find(product.id)
        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a product in the database"""
        product = ProductFactory()
        product.create()
        # Update the product
        product.name = "Updated Product Name"
        product.update()
        updated_product = Product.find(product.id)
        self.assertEqual(updated_product.name, "Updated Product Name")

    def test_delete_a_product(self):
        """It should Delete a product from the database"""
        product = ProductFactory()
        product.create()
        product_id = product.id
        # Delete the product
        product.delete()
        deleted_product = Product.find(product_id)
        self.assertIsNone(deleted_product)

    def test_list_all_products(self):
        """It should List all products in the database"""
        products = Product.all()
        self.assertEqual(products, [])

        # Create two products
        product1 = ProductFactory()
        product1.create()

        product2 = ProductFactory()
        product2.create()

        # Check if both products are present
        products = Product.all()
        self.assertEqual(len(products), 2)

    def test_find_by_name(self):
        """It should Find a product by name"""
        Product(name="Apple", description="Red apple", price=1.00, available=True, category=Category.FOOD).create()
        Product(name="Banana", description="Yellow banana", price=0.50, available=True, category=Category.FOOD).create()

        products = Product.find_by_name("Apple")
        self.assertEqual(len(products.all()), 1)
        self.assertEqual(products.first().description, "Red apple")

    def test_find_by_category(self):
        """It should Find a product by category"""
        product = ProductFactory(category=Category.CLOTHS)
        product.create()
        products = Product.find_by_category(Category.CLOTHS)
        self.assertGreater(len(products.all()), 0)
        self.assertEqual(products.first().category, Category.CLOTHS)

    def test_find_by_availability(self):
        """It should Find products by availability"""
        Product(
            name="Available Product",
            description="In Stock",
            price=100.0,
            available=True,
            category=Category.TOOLS
        ).create()

        Product(
            name="Unavailable Product",
            description="Out of Stock",
            price=150.0, available=False,
            category=Category.TOOLS
        ).create()

        available_products = Product.find_by_availability(True)
        unavailable_products = Product.find_by_availability(False)

        self.assertGreater(len(available_products.all()), 0)
        self.assertGreater(len(unavailable_products.all()), 0)
        self.assertTrue(available_products.first().available)
        self.assertFalse(unavailable_products.first().available)

    def test_deserialize_with_missing_field(self):
        """It should raise DataValidationError when a required field is missing"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({"description": "desc", "price": "10.0", "available": True, "category": "FOOD"})

    def test_deserialize_with_invalid_availability_type(self):
        """It should raise DataValidationError for non-boolean availability"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({
                "name": "Item",
                "description": "desc",
                "price": "10.0",
                "available": "yes",  # invalid type
                "category": "FOOD"
            })

    def test_deserialize_with_invalid_category(self):
        """It should raise DataValidationError for invalid category"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({
                "name": "Item",
                "description": "desc",
                "price": "10.0",
                "available": True,
                "category": "NOT_A_REAL_CATEGORY"
            })

    def test_deserialize_with_none(self):
        """It should raise DataValidationError when None is passed"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(None)

    def test_update_without_id(self):
        """It should raise DataValidationError when updating with no ID"""
        product = ProductFactory()
        product.id = None
        with self.assertRaises(DataValidationError):
            product.update()

    def test_find_by_price_as_string(self):
        """It should find by price when passed as a string"""
        product = ProductFactory(price=Decimal("19.99"))
        product.create()
        products = Product.find_by_price("19.99")
        self.assertEqual(len(products.all()), 1)
