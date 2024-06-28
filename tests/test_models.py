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
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

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

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_product(self):
        """It should read a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        remote = Product.find(product.id)
        self.assertEqual(remote.name, product.name)
        self.assertEqual(remote.description, product.description)
        self.assertEqual(Decimal(remote.price), product.price)
        self.assertEqual(remote.available, product.available)
        self.assertEqual(remote.category, product.category)

    def test_update_product(self):
        """It should update a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        print(str(product))
        old_id = product.id
        new_description = "new description"
        product.description = new_description
        product.update()
        self.assertEqual(old_id, product.id)
        self.assertEqual(new_description, product.description)
        catalog = Product.all()
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0].id, old_id)
        self.assertEqual(catalog[0].description, new_description)
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_product(self):
        """It should delete a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)
        num_insertions = 5
        for _ in range(num_insertions):
            product = ProductFactory()
            product.id = None
            product.create()
        catalog = Product.all()
        for counter, _ in enumerate(catalog):
            catalog[counter].delete()
            self.assertEqual(len(Product.all()), num_insertions - (counter+1))

    def test_list_all_products(self):
        """It should list all products"""
        num_insertions = 5
        inserted_products = []
        for _ in range(num_insertions):
            product = ProductFactory()
            product.id = None
            product.create()
            inserted_products.append(product)
        self.assertEqual(len(Product.all()), len(inserted_products))
        remote_products = Product.all()
        lists_diff = [item for item in remote_products if item not in inserted_products]
        self.assertEqual(len(lists_diff), 0)

    def test_find_product_by_name(self):
        """It should find products by name"""
        num_insertions = 10
        inserted_products = []
        # Create a set of products
        for _ in range(num_insertions):
            product = ProductFactory()
            product.id = None
            product.create()
            inserted_products.append(product)
        # Check that the product creates can be found by name and found products have the same name
        for product in inserted_products:
            query = Product.find_by_name(product.name)
            # Get all the products from the query
            found_products = list(query)
            self.assertNotEqual(len(found_products), 0)
            # Check if all found products have the same name as the product used in the search
            different_names_product = [p for p in found_products if p.name != product.name]
            self.assertEqual(len(different_names_product), 0)

    def test_find_product_by_availability(self):
        """It should find products by availability"""
        num_insertions = 10
        available_products = []
        unavailable_products = []
        # Create a set of products divided in available and unavaliable
        for _ in range(num_insertions):
            product = ProductFactory()
            product.id = None
            product.create()
            if product.available:
                available_products.append(product)
            else:
                unavailable_products.append(product)
        available_query = Product.find_by_availability(True)
        unavailable_query = Product.find_by_availability(False)
        # get all theproducts from the queries
        found_available_products = list(available_query)
        found_unavailable_products = list(unavailable_query)
        # Check that the number of items are the same
        self.assertEqual(len(available_products), len(found_available_products))
        self.assertEqual(len(unavailable_products), len(found_unavailable_products))
        # Check that all the queried items are correct
        available_products_diff = [p for p in available_products if p not in found_available_products]
        unavailable_products_diff = [p for p in unavailable_products if p not in found_unavailable_products]
        self.assertEqual(len(available_products_diff), 0)
        self.assertEqual(len(unavailable_products_diff), 0)

    def test_find_product_by_category(self):
        """It should find products by category"""
        num_insertions = 10
        category_dict = {}
        all_products = []
        # Create a set of products divided in categories
        for counter in range(num_insertions):
            product = ProductFactory()
            product.id = None
            product.create()
            category_dict[product.category] = []
            all_products.append(product)
        for product in all_products:
            category_dict[product.category].append(product)
        # Check that the read products per category are correct
        for key in category_dict:
            query = Product.find_by_category(key)
            query_products = [p for p in query]
            self.assertEqual(len(query_products), len(category_dict[key]))
            diff = [p for p in category_dict[key] if p not in query_products]
            self.assertEqual(len(diff), 0)

    def test_find_product_by_price(self):
        """It should find products by price"""
        num_insertions = 10
        category_dict = {}
        all_products = []
        # Create a set of products divided in categories
        for counter in range(num_insertions):
            product = ProductFactory()
            product.id = None
            product.create()
            category_dict[product.price] = []
            all_products.append(product)
        for product in all_products:
            category_dict[product.price].append(product)
        # Check that the read products per category are correct
        for key in category_dict:
            query = Product.find_by_price(key)
            query_products = [p for p in query]
            self.assertEqual(len(query_products), len(category_dict[key]))
            diff = [p for p in category_dict[key] if p not in query_products]
            self.assertEqual(len(diff), 0)
            # Test passing price as an string
            query = Product.find_by_price(str(key))
            query_products = [p for p in query]
            self.assertEqual(len(query_products), len(category_dict[key]))
            diff = [p for p in category_dict[key] if p not in query_products]
            self.assertEqual(len(diff), 0)
