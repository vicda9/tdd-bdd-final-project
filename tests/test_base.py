import os
import logging
from unittest import TestCase
from service import app
from service.models import db

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


class BaseTestCase(TestCase):
    """Base class for all tests to share setup and teardown"""

    @classmethod
    def setUpClass(cls):
        """Runs once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        # Properly delete all data from all tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()
