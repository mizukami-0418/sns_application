# forms.py
from collections.abc import Mapping, Sequence
from typing import Any
from wtforms.form import Form
from wtforms.fields import (
  StringField, FileField, PasswordField, SubmitField, HiddenField
)
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError, validators
from flaskr.models import User
from flask_login import current_user
from flask import flash

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
  """
  パスワードリセット用のフォームクラス。

  Attributes:
    password (PasswordField): パスワードを入力するフィールド。
    confirm_password (PasswordField): パスワードの確認を入力するフィールド。
    submit (SubmitField): フォームを送信するためのボタン。

  Methods:
    validate_confirm_password: パスワードと確認用パスワードの一致を確認するメソッド。
    validate_password: パスワードが指定の条件を満たしているか検証するメソッド。
  """
  password = PasswordField('パスワード：', validators=[DataRequired()])
  confirm_password = PasswordField('パスワード確認：', validators=[DataRequired()])
  submit = SubmitField('パスワードを更新する')
  
  def validate_confirm_password(form, field):
    if form.password.data != field.data:
      raise ValidationError('パスワードが一致しません')
  
  def validate_password(self, field):
    if len(field.data) < 10:
      raise ValidationError('パスワードは10文字以上で入力してください')

class ForgotPasswordForm(Form):
  """
  パスワードを忘れた場合のフォームクラス。

  Attributes:
    email (StringField): メールアドレスを入力するフィールド。
    submit (SubmitField): フォームを送信するためのボタン。

  Methods:
    validate_email: 入力されたメールアドレスが存在するか検証するメソッド。
  """
  email = StringField('メールアドレス：', validators=[DataRequired(), Email()])
  submit = SubmitField('パスワードを再設定する')
  
  def validate_email(self, field):
    if not User.select_user_by_email(field.data):
      raise ValidationError('メールアドレスは存在しません')

class UserForm(Form):
  email = StringField(
    'メールアドレス：',
    validators=[DataRequired(), Email('メールアドレスに誤りがあります')]
  )
  username = StringField('ユーザー名：', validators=[DataRequired()])
  picture_path = FileField('プロフィール画像')
  submit = SubmitField('登録情報更新')
  
  def validate(self):
    if not super(Form, self).validate():
      return False
    user = User.select_user_by_email(self.email.data)
    if user:
      if user.id != int(current_user.get_id()):
        flash('メールアドレスは既に登録済みです')
        return False
    return True

class ChangePasswordForm(Form):
  password = PasswordField('更新パスワード：', validators=[DataRequired()])
  confirm_password = PasswordField('パスワード確認：', validators=[DataRequired()])
  submit = SubmitField('パスワードを更新する')
  
  def validate_confirm_password(form, field):
    if form.password.data != field.data:
      raise ValidationError('パスワードが一致しません')
  
  def validate_password(self, field):
    if len(field.data) < 10:
      raise ValidationError('パスワードは10文字以上で入力してください')

  