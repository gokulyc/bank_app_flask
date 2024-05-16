from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField
from wtforms.validators import InputRequired, Email
import uuid


class RegisterForm(FlaskForm):
    id = StringField(label="ID", default=uuid.uuid4())
    username = StringField("Username", validators=[InputRequired()])
    name = StringField("Name", validators=[InputRequired()])
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    balance = DecimalField("Balance", validators=[InputRequired()])
    # account_type = SelectField(
    #     "Account Type",
    #     validators=[InputRequired()],
    #     choices=[("regular", "Regular"), ("premium", "Premium")],
    # )
