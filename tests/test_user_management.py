import unittest
from datetime import date

from werkzeug.security import generate_password_hash

from app import DeliverySlip, User, app, db


class UserManagementTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"check_same_thread": False}},
        )
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
            db.session.close()

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

    def test_any_logged_in_user_can_register_delivery_slip(self):
        self.client.post("/login", data={"username": "alice", "password": "secret"}, follow_redirects=True)

        response = self.client.post(
            "/delivery/register",
            data={
                "slip_number": "SLIP-001",
                "customer_name": "Budi",
                "equipment": "Laptop",
                "delivery_date": "2026-07-22",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            slip = DeliverySlip.query.filter_by(slip_number="SLIP-001").first()
            self.assertIsNotNone(slip)
            self.assertEqual(slip.created_by.username, "alice")

    def test_any_logged_in_user_can_update_another_users_delivery_slip(self):
        with app.app_context():
            alice = User.query.filter_by(username="alice").first()
            slip = DeliverySlip(
                slip_number="SLIP-002",
                customer_name="Citra",
                equipment="Printer",
                delivery_date=date(2026, 7, 22),
                status="terdaftar",
                created_by=alice,
            )
            db.session.add(slip)
            db.session.commit()
            slip_id = slip.id

        self.client.post("/login", data={"username": "root", "password": "root"}, follow_redirects=True)
        response = self.client.post(
            f"/delivery/{slip_id}/update",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            updated_slip = DeliverySlip.query.get(slip_id)
            self.assertEqual(updated_slip.status, "mencetak")


if __name__ == "__main__":
    unittest.main()
