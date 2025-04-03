from tests.test_base import BaseTestCase
from service.common import status


class TestErrorHandlers(BaseTestCase):
    """Test error handlers"""

    def test_unsupported_media_type(self):
        """It should return 415 Unsupported Media Type"""
        response = self.client.post("/products", data="{}", content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_method_not_allowed(self):
        """It should return 405 Method Not Allowed"""
        response = self.client.put("/products")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_not_found(self):
        """It should return 404 Not Found"""
        response = self.client.get("/products/999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_internal_server_error(self):
        """It should return 500 Internal Server Error"""
        response = self.client.get("/cause-error")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
