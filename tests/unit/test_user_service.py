import unittest
from services.user_management_service.routes import get_user_details


class TestUserService(unittest.TestCase):
    def test_get_user_details(self):
        user_id = 1
        response = get_user_details(user_id)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json)


if __name__ == "__main__":
    unittest.main()
