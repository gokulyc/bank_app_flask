from models import db, Account, Transactions, Alerts

from flask import Flask


# def get_test_env_app():
#     app = Flask(__name__)
#     app.config[
#         "SQLALCHEMY_DATABASE_URI"
#     ] = "sqlite:///test.db"  # Use your actual database URI
#     app.config["SECRET_KEY"] = "secret123!@#"
#     # db.init_app(app)
#     return app

def get_prod_env_app():
    app = Flask(__name__)
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = "sqlite:///prod.db"  # Use your actual database URI
    app.config["SECRET_KEY"] = "secret123!@#"
    # db.init_app(app)
    return app

if __name__ == "__main__":
        # data: Transactions = Transactions.query.all()
        # print([t.to_dict() for t in data])
        ...
