import os
import tempfile
import unittest

from app import app
import database


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.app = app.test_client()

        # Point database module to temp db
        database.DB_PATH = self.db_path
        database.init_db(self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_unauthenticated_dashboard_redirect(self):
        response = self.app.get("/", follow_redirects=True)
        self.assertIn("Iniciar sesión".encode("utf-8"), response.data)
        self.assertIn("Por favor inicia sesión para acceder.".encode("utf-8"), response.data)

    def test_registration_success(self):
        response = self.app.post(
            "/register",
            data={
                "username": "newuser",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertIn("Generador de".encode("utf-8"), response.data)
        self.assertIn("newuser".encode("utf-8"), response.data)

    def test_registration_password_mismatch(self):
        response = self.app.post(
            "/register",
            data={
                "username": "newuser",
                "password": "password123",
                "confirm_password": "differentpassword",
            },
            follow_redirects=True,
        )
        self.assertIn("Las contraseñas no coinciden.".encode("utf-8"), response.data)

    def test_registration_short_password(self):
        response = self.app.post(
            "/register",
            data={
                "username": "newuser",
                "password": "123",
                "confirm_password": "123",
            },
            follow_redirects=True,
        )
        self.assertIn("La contraseña debe tener al menos 6 caracteres.".encode("utf-8"), response.data)

    def test_registration_duplicate_username(self):
        database.create_user("existinguser", "password123", self.db_path)
        response = self.app.post(
            "/register",
            data={
                "username": "existinguser",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertIn("El nombre de usuario ya está registrado.".encode("utf-8"), response.data)

    def test_login_success_and_logout(self):
        database.create_user("user1", "password123", self.db_path)

        # Login
        response = self.app.post(
            "/login",
            data={"username": "user1", "password": "password123"},
            follow_redirects=True,
        )
        self.assertIn("Bienvenido de nuevo".encode("utf-8"), response.data)
        self.assertIn("user1".encode("utf-8"), response.data)

        # Logout
        logout_response = self.app.get("/logout", follow_redirects=True)
        self.assertIn("Has cerrado sesión correctamente.".encode("utf-8"), logout_response.data)

        # Dashboard protected after logout
        dash_response = self.app.get("/", follow_redirects=True)
        self.assertIn("Por favor inicia sesión para acceder.".encode("utf-8"), dash_response.data)

    def test_login_invalid_credentials(self):
        database.create_user("user1", "password123", self.db_path)

        response = self.app.post(
            "/login",
            data={"username": "user1", "password": "wrongpassword"},
            follow_redirects=True,
        )
        self.assertIn("Usuario o contraseña incorrectos.".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
