from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from datetime import datetime, UTC

db = SQLAlchemy()

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(30), unique=True)
#     email = db.Column(db.String(50), unique=True)
#     password = db.Column(db.String(80))
#     account_type = db.Column(db.String(10))


class Account(db.Model):
    __tablename__ = "user_bank_account"
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(80))
    balance = db.Column(db.DECIMAL(15, 4), nullable=False)

    def to_dict(self, exclude_password=True):
        di = {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "password": self.password,
            "balance": self.balance,
            "email": self.email,
        }
        if exclude_password:
            di.pop("password")
        return di.copy()


class Transactions(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    from_account = db.Column(db.String(100), nullable=False)
    to_account = db.Column(db.String(100), nullable=False)
    amount = db.Column(sa.DECIMAL(15, 4))
    priority = db.Column(db.String(20), default="default")
    txn_status = db.Column(sa.String(20), nullable=False)
    txn_description = db.Column(sa.Text, default=None)
    timestamp = db.Column(sa.DateTime(), default=lambda x: datetime.now(UTC))

    def __str__(self) -> str:
        return f"xxx{self.from_account[-4:-1]} -> xxx{self.to_account[-4:-1]} -- {self.txn_status}"

    def to_dict(self):
        return {
            "id": self.id,
            "from_account": self.from_account,
            "to_account": self.to_account,
            "amount": self.amount,
            "priority": self.priority,
            "txn_status": self.txn_status,
            "txn_description": self.txn_description,
            "timestamp": self.timestamp,
        }


class Alerts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(100), nullable=False)
    created_date: datetime = db.Column(
        sa.DateTime(), default=lambda x: datetime.now(UTC)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "created_date": self.created_date.isoformat(),
        }
