from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(_l('Ник'), validators=[DataRequired()])
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Запомнить меня'))
    submit = SubmitField(_l('Войти'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Ник'), validators=[DataRequired()])
    email = StringField(_l('Электропочта'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Повторение пароля'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Зарегистрироваться'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Этот ник уже занят.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Эта элекропочта уже используется другим аккаунтом.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Электропочта'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Восстановить'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Повторение пароля'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Сохранить'))
