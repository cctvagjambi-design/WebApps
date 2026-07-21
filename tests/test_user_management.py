import os
import tempfile
import unittest

from werkzeug.security import generate_password_hash

from app import User, app, db


class UserManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        app.config.update(TESTING=True, SECRET_KEY="test-secret", SQLALCHEMY_DATABASE_URI=f"sqlite:///{self.db_path}")
        self.client = app.test_client()

        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            root = User(username="root", password_hash=generate_password_hash("root"), is_root=True)
            alice = User(username="alice", password_hash=generate_password_hash("secret"), is_root=False)
            db.session.add_all([root, alice])
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_dir.cleanup()

    def test_root_can_list_users(self):
        self.client.post("/login", data={"username": "root", "password": "root"}, follow_redirects=True)

        response = self.client.get("/users")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"alice", response.data)

    def test_regular_user_can_change_their_own_password(self):
        self.client.post("/login", data={"username": "alice", "password": "secret"}, follow_redirects=True)

        response = self.client.post(
            "/change-password",
            data={"current_password": "secret", "new_password": "newpass", "confirm_password": "newpass"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            updated_user = User.query.filter_by(username="alice").first()
            self.assertTrue(updated_user.check_password("newpass"))

    def test_root_can_change_another_user_password(self):
        self.client.post("/login", data={"username": "root", "password": "root"}, follow_redirects=True)

        response = self.client.post(
            "/users/2/change-password",
            data={"new_password": "newpass2", "confirm_password": "newpass2"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            updated_user = User.query.filter_by(username="alice").first()
            self.assertTrue(updated_user.check_password("newpass2"))


if __name__ == "__main__":
    unittest.main()
