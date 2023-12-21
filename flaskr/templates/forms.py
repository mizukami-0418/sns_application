# forms.py
from wtforms.form import Form
from wtforms.fields import (
    SelectField, FileField, PasswordField, SubmitField, HiddenField
)
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError

from flaskr.models import User

# ログイン用のForm
class LoginForm(Form):
    email = SubmitField(
        "メール: ", validators=[DataRequired(),Email()]
    )
    password = PasswordField(
        "パスワード: ",
        validators=[DataRequired(), EqualTo("confirm_password", message="パスワードが一致しません")]
    )
    confirm_password = PasswordField("パスワード再入力: ", validators=[DataRequired()])
    submit = SubmitField("ログイン")

# 登録用のForm
class RegisterForm(Form):
    email = SubmitField(
        "メール: ", validators=[DataRequired(), Email("メールアドレスが間違っています")]
    )
    username = SubmitField("名前: ", validators=[DataRequired()])
    submit = SubmitField("登録")

    def validate_email(self, field):
        if User.select_user_by_email(field.data):
            raise ValidationError("登録済みのメールアドレスです")