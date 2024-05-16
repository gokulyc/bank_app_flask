# from flask_sqlalchemy import SQLAlchemy
from models import Account, Alerts, Transactions
from werkzeug.security import generate_password_hash
from flask import Response
from werkzeug.http import parse_cookie
from jwt import decode


class TestBankApp:
    def test_example(self, app_obj, db_obj):
        app = app_obj
        with app.app_context():
            txns_count = Transactions.query.count()
            assert txns_count == 18
            acc_count = Account.query.count()
            assert acc_count == 2

    def test_account_register(self, app_obj, test_client, db_obj):
        app = app_obj
        account_data = {
            "username": "gcy",
            "name": "Gokul",
            "email": "gcy@gmail.com",
            "balance": 4000,
            "password": "1234",
        }
        hashed_password = generate_password_hash("1234", "scrypt")
        with app.app_context():
            response: Response = test_client.post("/register", data=account_data)
            # print(response.data)
            assert response.status_code == 302
            # print(Account.query.all())
            acc = Account.query.filter(
                db_obj.and_(Account.email == "gcy@gmail.com", Account.name == "Gokul")
            ).all()
            # print(acc)
            assert len(acc) == 1
            assert acc[0].username == "gcy"
            # print(acc[0].to_dict())

    def test_account_login(self, app_obj, test_client, db_obj):
        app = app_obj
        acc_login = {
            "username": "johndoe123",
            "password": "1234",
        }
        with app.app_context():
            response: Response = test_client.post("/login", data=acc_login)
            assert response.status_code == 302
            cookies = response.headers.getlist("Set-Cookie")
            cookie_attrs = parse_cookie(cookies[0])
            print(cookie_attrs)
            access_token_cookie = cookie_attrs["access_token_cookie"]
            decoded_jwt = decode(
                access_token_cookie, "jwt-secret-string-!@#", ["HS256"]
            )
            # print(decoded_jwt)
            assert decoded_jwt["username"] == "johndoe123"
