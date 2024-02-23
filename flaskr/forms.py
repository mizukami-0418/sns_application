# forms.py
from collections.abc import Mapping, Sequence
from typing import Any
from flask_wtf import FlaskForm
from wtforms.fields import (
  StringField, FileField, PasswordField, SubmitField, HiddenField, TextAreaField
)
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError, validators
from flaskr.models import User, UserConnect
from flask_login import current_user
from flask import flash

class LoginForm(FlaskForm):
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

class RegisterForm(FlaskForm):
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
class ResetPasswordForm(FlaskForm):
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

class ForgotPasswordForm(FlaskForm):
  """
  パスワードを忘れた場合のフォームクラス。

  Attributes:
    email (StringField): メールアドレスを入力するフィールド。
    submit (SubmitField): フォームを送信するためのボタン。

  Methods:
    validate_email: 入力されたメールアドレスが存在するか検証するメソッド。
  """
  email = StringField('メールアドレス：', validators=[DataRequired()])
  submit = SubmitField('パスワードを再設定する')
  
  def validate_email(self, field):
    if not User.select_user_by_email(field.data):
      raise ValidationError('メールアドレスは存在しません')

class UserForm(FlaskForm):
  """
  ユーザー情報を更新するためのフォームクラス。

  Attributes:
    email (StringField): メールアドレス入力フィールド。
    username (StringField): ユーザー名入力フィールド。
    picture_path (FileField): プロフィール画像のアップロードフィールド。
    submit (SubmitField): フォームの送信ボタン。
  """
  email = StringField(
    'メールアドレス：',
    validators=[DataRequired(), Email('メールアドレスに誤りがあります')]
  )
  username = StringField('ユーザー名：', validators=[DataRequired()])
  picture_path = FileField('プロフィール画像')
  submit = SubmitField('登録情報更新')
  
  def validate(self):
    """
    フォームのバリデーションメソッド。

    Returns:
      bool: バリデーションの結果。Trueならバリデーション成功、Falseなら失敗。
    """
    if not super(FlaskForm, self).validate():
      return False
    user = User.select_user_by_email(self.email.data)
    if user:
      if user.id != int(current_user.get_id()):
        flash('メールアドレスは既に登録済みです')
        return False
    return True

class ChangePasswordForm(FlaskForm):
  """
  パスワード変更用のフォームクラス。

  Attributes:
    password (PasswordField): 新しいパスワードの入力フィールド。
    confirm_password (PasswordField): パスワード確認のための入力フィールド。
    submit (SubmitField): フォームの送信ボタン。
  """
  password = PasswordField('更新パスワード：', validators=[DataRequired()])
  confirm_password = PasswordField('パスワード確認：', validators=[DataRequired()])
  submit = SubmitField('パスワードを更新する')
  
  def validate_confirm_password(form, field):
    """
    パスワード確認のバリデーションメソッド。

    Args:
      form (ChangePasswordForm): フォームのインスタンス。
      field (PasswordField): パスワード確認の入力フィールド。

    Raises:
      ValidationError: パスワードが一致しない場合に発生。
    """
    if form.password.data != field.data:
      raise ValidationError('パスワードが一致しません')
  
  def validate_password(self, field):
    """
    パスワードのバリデーションメソッド。

    Args:
      field (PasswordField): パスワードの入力フィールド。

    Raises:
      ValidationError: パスワードが10文字未満の場合に発生。
    """
    if len(field.data) < 10:
      raise ValidationError('パスワードは10文字以上で入力してください')

class UserSearchForm(FlaskForm):
  """
  ユーザー検索用のフォームクラス。

  Attributes:
    username (StringField): 検索するユーザー名の入力フィールド。
    submit (SubmitField): フォームの送信ボタン。
  """
  username = StringField(
    'ユーザー名を入力してください', validators=[DataRequired()]
  )
  submit = SubmitField('検索')

class ConnectForm(FlaskForm):
  """
  友達接続のためのフォームクラス。

  Attributes:
    connect_condition (HiddenField): 友達接続の条件を指定するための隠しフィールド。
    to_user_id (HiddenField): 接続対象のユーザーIDを指定するための隠しフィールド。
    submit (SubmitField): フォームの送信ボタン。
  """
  connect_condition = HiddenField()
  to_user_id = HiddenField()
  submit = SubmitField()
  
class MessageForm(FlaskForm):
  """
  メッセージ送信のためのフォームクラス。

  Attributes:
    to_user_id (HiddenField): メッセージの送信先ユーザーIDを指定するための隠しフィールド。
    message (TextAreaField): 送信するメッセージの入力フィールド。
    submit (SubmitField): フォームの送信ボタン。
  """
  to_user_id = HiddenField()
  message = TextAreaField('メッセージ')
  submit = SubmitField('送信')
  
  def validate(self):
    """
    フォームのバリデーションメソッド。

    Returns:
      bool: バリデーションの結果。Trueならバリデーション成功、Falseなら失敗。
    """
    if not super(FlaskForm, self).validate():
      return False
    is_friend = UserConnect.is_friend(self.to_user_id.data)
    if not is_friend:
      return False
    return True
  
class ContactForm(FlaskForm):
    body = TextAreaField('お問い合わせ内容', validators=[DataRequired()])
    submit = SubmitField('送信')