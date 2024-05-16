from models import Account, Transactions, Alerts

# from flask_app_db_factory import get_test_env_app, db
import pytest
from sample_data import accounts, transactions_sample
from werkzeug.security import generate_password_hash
from main import app, db


def add_accounts_data(db):
    for acc in accounts:
        db.session.add(
            Account(
                id=acc["id"],
                name=acc["name"],
                email=acc["email"],
                username=acc["username"],
                balance=acc["balance"],
                password=generate_password_hash(acc["password"], method="scrypt"),
            )
        )
        db.session.commit()


def add_txns_sample_data(db):
    for txn in transactions_sample:
        db.session.add(Transactions(**txn))
        db.session.commit()


@pytest.fixture(scope="class")
def app_obj():
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db",
            "WTF_CSRF_ENABLED": False,
        }
    )

    yield app


@pytest.fixture(scope="class")
def db_obj(app_obj):
    db.init_app(app_obj)
    with app_obj.app_context():
        db.create_all()
        try:
            add_accounts_data(db)
            add_txns_sample_data(db)
        except Exception as e:
            print(e)
    yield db
    try:
        with app_obj.app_context():
            db.drop_all()
    except Exception as e:
        print(e)
        print("unable to drop tables.")


@pytest.fixture
def test_client(app_obj):
    app = app_obj
    return app.test_client()
