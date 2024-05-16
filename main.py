from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest
from flask_jwt_extended import (
    JWTManager,
    current_user,
    jwt_required,
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)
import sqlalchemy as sa
from datetime import datetime, UTC
from decimal import Decimal

from models import Account, Transactions, db, Alerts
from forms import RegisterForm
from sample_data import accounts, transactions_sample
from flask_app_db_factory import get_prod_env_app


app = get_prod_env_app()

app.config[
    "JWT_SECRET_KEY"
] = "jwt-secret-string-!@#"  # Use a real secret key in production
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies", "json", "query_string"]

jwt = JWTManager(app)


@jwt.unauthorized_loader
def custom_unauthorized_response(_err):
    return redirect(url_for("login", message="AnonymousUser"))


@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return redirect(url_for("login", message="TokenExpired"))


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Account.query.filter(Account.username == identity["username"]).one_or_none()


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    # print(form.data)
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method="scrypt")
        new_user = Account(
            id=str(form.id.data),
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            balance=form.balance.data,
            password=hashed_password,
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("dashboard"))
    else:
        print(form.errors)
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = request.args.get("message")
    if request.method == "POST":
        user: Account = Account.query.filter_by(
            username=request.form["username"]
        ).first()
        if user and check_password_hash(user.password, request.form["password"]):
            additional_claims = {**user.to_dict()}
            access_token = create_access_token(
                identity={"username": user.username},
                additional_claims=additional_claims,
            )
            response = redirect("/dashboard")
            set_access_cookies(response, access_token)
            return response
    return render_template("login.html", message=message)


@app.route("/dashboard")
@jwt_required()
def dashboard():
    account: Account = (
        Account.query.filter(Account.username == current_user.username).one().to_dict()
    )
    return render_template("dashboard.html", account=account)


@app.route("/logout", methods=["GET"])
def logout_with_cookies():
    response = redirect("/")
    unset_jwt_cookies(response)
    return response


@app.route("/get_report")
def get_report():
    month = request.args.get("month")
    year = request.args.get("year")
    if not month or not year:
        "month & year requireed"
    txns: list[Transactions] = Transactions.query.filter(
        sa.extract("month", Transactions.timestamp) == int(month)
        and sa.extract("year", Transactions.timestamp) == int(year)
    ).all()

    return jsonify([txn.to_dict() for txn in txns])


@app.route("/transfer", methods=["POST", "GET"])
def transfer():
    if request.method == "GET":
        return render_template("transfer.html")
    from_account_id = request.form.get("from")
    to_account_id = request.form.get("to")
    amount = Decimal(request.form.get("amount"))

    from_account: Account = Account.query.get(from_account_id)
    to_account: Account = Account.query.get(to_account_id)

    if not from_account or not to_account:
        return "Account not found", 404

    if from_account.balance < amount:
        txn = Transactions(
            from_account=from_account.id,
            to_account=to_account.id,
            amount=amount,
            txn_status="InsufficientFunds",
            txn_description="Insufficient balance in Account",
            timestamp=datetime.now(tz=UTC),
        )
        db.session.add(txn)
        db.session.commit()
        db.session.refresh(txn)
        # transactions.append(txn)
        print(str(txn))
        return "Insufficient balance", 400

    from_account.balance -= amount
    to_account.balance += amount
    txn = Transactions(
        from_account=from_account.id,
        to_account=to_account.id,
        amount=amount,
        txn_status="Pending",
        txn_description=None,
        timestamp=datetime.now(tz=UTC),
    )
    db.session.add(txn)
    db.session.commit()
    db.session.refresh(txn)
    print(str(txn))
    return render_template(
        "transfer.html",
        from_account=from_account.id,
        to_account=to_account.id,
        amount=amount,
    )


@app.route("/transactions", methods=["GET"])
def get_transactions():
    txn_statuses = db.session.query(Transactions.txn_status.distinct()).all()
    if txn_statuses:
        txn_statuses = [i[0] for i in txn_statuses]
    print(txn_statuses)
    return render_template(
        "transactions.html",
        results=[txn.to_dict() for txn in Transactions.query.all()],
        txn_type=txn_statuses,
    )


@app.route("/get_notifications", methods=["GET"])
def get_notifications():
    notifications: Alerts = (
        Alerts.query.order_by(db.desc(Alerts.created_date)).limit(15).all()
    )

    return render_template(
        "txn_processed_notifications.html",
        notifications=[n.to_dict() for n in notifications],
    )


@app.route("/manage_priority_tasks", methods=["POST"])
def manage_priority_tasks():
    priority = request.form.get("priority")
    txn_id = request.form.get("txn_id")
    if priority not in ("high", "default"):
        raise BadRequest("Invalid priority (high/ default)")
    if request.method == "POST":
        txn: Transactions = Transactions.query.get_or_404(txn_id)
        if txn.priority != priority:
            txn.priority = priority
            db.session.add(txn)
            db.session.commit()
            flash(f"{txn_id} has been updated with priority = {priority}")
        else:
            flash(f"{txn_id} has already same priority")
    return redirect(url_for("get_transactions"))


def add_accounts_data():
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


def add_txns_sample_data():
    for txn in transactions_sample:
        db.session.add(Transactions(**txn))
        db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.init_app(app)
        try:
            db.drop_all()
            db.create_all()
            add_accounts_data()
            add_txns_sample_data()
        except Exception as e:
            print(e)
    app.run(debug=True)
