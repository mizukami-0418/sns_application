# forms.py
from collections.abc import Mapping, Sequence
from typing import Any
from wtforms.form import Form
from wtforms.fields import (
  StringField, FileField, PasswordField, SubmitField, HiddenField
)
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError
from flaskr.models import User

class LoginForm(Form):
  """
  ログインフォームを表すWTFormsフォームクラス。

  Attributes:
      email (StringField): メールアドレスを入力するフィールド。
      password (PasswordField): パスワードを入力するフィールド。
      confirm_password (PasswordField): パスワードの確認を入力するフィールド。
      submit (SubmitField): ログインを実行するための送信ボタン。
  """
  email = StringField('メール：', validators=[DataRequired(), Email()])
  password = PasswordField(
    'パスワード：',
    validators=[DataRequired(), EqualTo('confirm_password', message='パスワードが一致しません')]
  )
  confirm_password = PasswordField('確認用パスワード', validators=[DataRequired()])
  submit = SubmitField('ログイン')

class RegisterForm(Form):
  """
  ユーザー登録フォームを表すWTFormsフォームクラス。

  Attributes:
      email (StringField): メールアドレスを入力するフィールド。
      username (StringField): ユーザー名を入力するフィールド。
      submit (SubmitField): 登録を実行するための送信ボタン。

  Methods:
      validate_email: メールアドレスが既に登録されているかどうかを検証するメソッド。
          Raises:
              ValidationError: 登録済みのメールアドレスの場合に発生する例外。
  """
  email = StringField(
    'メールアドレス：',
    validators=[DataRequired(), Email('メールアドレスに誤りがあります')]
  )
  username = StringField('ユーザー名：', validators=[DataRequired()])
  submit = SubmitField('登録')
  
  # 登録済みのメールアドレスは登録できないvalidateを作成
  def validate_email(self, field):
    if User.select_user_by_email(field.data):
      raise ValidationError('登録済みのメールアドレスです')

# パスワード設定用のフォーム
class ResetPasswordForm(Form):
  password = PasswordField(
    'パスワード',
    validators=[DataRequired(), EqualTo('confirm_password', message='パスワードが一致しません')]
  )
  confirm_password = PasswordField(
    'パスワード確認：', validators=[DataRequired()]
  )
  submit = SubmitField('パスワードを更新する')
  def validate_password(self, field):
    if len(field.data) < 10:
      raise ValidationError('パスワードは10文字以上で入力してください')

class ForgotPasswordForm(Form):
  email = StringField('メールアドレス：', validators=[DataRequired(), Email])
  submit = SubmitField('パスワードを再設定する')
  
  def validate_email(self, field):
    if not User.select_user_by_email(field.data):
      raise ValidationError('メールアドレスは存在しません')