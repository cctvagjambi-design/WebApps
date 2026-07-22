import unittest
from io import BytesIO

from openpyxl import Workbook

from app import Equipment, User, app, db
from werkzeug.security import generate_password_hash


class EquipmentImportTests(unittest.TestCase):
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
            user = User(username="alice", password_hash=generate_password_hash("secret"), is_root=False)
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.close()

    def test_import_equipment_from_excel(self):
        self.client.post("/login", data={"username": "alice", "password": "secret"}, follow_redirects=True)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Equipment"
        sheet.append(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"])
        sheet.append(["", "", "", "EQ-100", "SN-100", "", "", "", "", "", "", "Model A", "", "", "", "Budi", "Jakarta"])
        sheet.append(["", "", "", "EQ-200", "SN-200", "", "", "", "", "", "", "Model B", "", "", "", "Citra", "Bandung"])

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        response = self.client.post(
            "/tools/import-equipment",
            data={"file": (buffer, "equipment.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            equipment = Equipment.query.order_by(Equipment.equipment_number.asc()).all()
            self.assertEqual(len(equipment), 2)
            self.assertEqual(equipment[0].equipment_number, "EQ-100")
            self.assertEqual(equipment[0].serial_number, "SN-100")
            self.assertEqual(equipment[0].model, "Model A")
            self.assertEqual(equipment[0].customer_name, "Budi")
            self.assertEqual(equipment[0].address, "Jakarta")

    def test_equipment_listing_page_shows_imported_records(self):
        self.client.post("/login", data={"username": "alice", "password": "secret"}, follow_redirects=True)

        with app.app_context():
            equipment = Equipment(equipment_number="EQ-300", serial_number="SN-300", model="Model C", customer_name="Dewi", address="Surabaya")
            db.session.add(equipment)
            db.session.commit()

        response = self.client.get("/tools/equipment")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"EQ-300", response.data)
        self.assertIn(b"Model C", response.data)

    def test_equipment_listing_page_supports_search(self):
        self.client.post("/login", data={"username": "alice", "password": "secret"}, follow_redirects=True)

        with app.app_context():
            equipment = Equipment(equipment_number="EQ-400", serial_number="SN-400", model="Model D", customer_name="Rina", address="Medan")
            db.session.add(equipment)
            db.session.commit()

        response = self.client.get("/tools/equipment?q=Rina")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"EQ-400", response.data)


if __name__ == "__main__":
    unittest.main()
