import datetime
import re
from typing import Any, Self

from src.consts import GENDERS
from src.scoring import get_score, get_interests
from src.settings import ADMIN_LOGIN


class BaseModel:
    fields = None

    def validate(self):
        pass

    def __new__(cls, **kwargs) -> Self:  # TODO: можно добавить обработку *args
        instance = super().__new__(cls)
        fields = [
            key for key, value in cls.__dict__.items() if isinstance(value, Field)
        ]
        instance.fields = fields
        for field in fields:
            field_cls: Field = cls.__dict__[field]
            if field_cls.required and field not in kwargs:
                raise ValueError(f"Атрибут {field_cls} обязателен")
            setattr(instance, field, kwargs.get(field))
        instance.validate()
        return instance


class Field:
    def __init__(self, required: bool = False, nullable: bool = False):
        self.required = required
        self.nullable = nullable

    def __str__(self):
        return self.__class__.__name__

    def __set_name__(self, owner, name):
        self.private_name = "_" + name

    def validate(self, value) -> Any:
        return value

    def __get__(self, instance, owner):
        return getattr(instance, self.private_name, None)

    def __set__(self, instance, value):
        if not (self.nullable and value is None):
            self.validate(value)
        setattr(instance, self.private_name, value)


class CharField(Field):
    def validate(self, value: str) -> str:
        validated_value = super().validate(value)
        if not isinstance(validated_value, str):
            raise ValueError("CharField должен иметь значение с типом str")
        return validated_value


class EmailField(CharField):
    def validate(self, value: str) -> str:
        validated_value = super().validate(value)
        if not re.match(r"[^@]+@[^@]+\.[^@]+", validated_value):
            raise ValueError("invalid email")
        return validated_value


class PhoneField(Field):
    def validate(self, value: str) -> str:
        validated_value = super().validate(str(value))
        if not re.match(r"^\+?(44)?(0|7)\d{9,13}$", validated_value):
            raise ValueError("invalid phone")
        return validated_value


class DateField(CharField):
    def validate(self, value: str) -> datetime.date:
        validated_value = super().validate(value)
        try:
            date = datetime.datetime.strptime(str(validated_value), "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("invalid date")
        return date


class BirthDayField(DateField):
    def validate(self, value: str) -> datetime.date:
        validated_value = super().validate(value)
        if datetime.datetime.now().year - validated_value.year > 70:
            raise ValueError("invalid BirthDayField")
        return validated_value


class GenderField(Field):
    def validate(self, value: int) -> str:
        if not isinstance(value, int) or not 0 <= value <= 2:
            raise ValueError("invalid GenderField")
        return GENDERS[value]


class ClientIDsField(Field):
    def validate(self, value) -> Any:
        if (
            not value
            or not isinstance(value, list)
            or not all(isinstance(item, (int, float)) for item in value)
        ):
            raise ValueError("ClientIDsField должен быть списком из чисел")
        return value


class ArgumentsField(Field):
    pass


class ClientsInterestsRequest(BaseModel):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def calculate(self) -> dict[str, Any]:
        return {client_id: get_interests() for client_id in self.client_ids}

    def set_context(self, ctx: dict[str, Any]) -> None:
        ctx["nclients"] = len(self.client_ids)


class OnlineScoreRequest(BaseModel):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self) -> None:
        if (
            None not in (self.phone, self.email)
            or None not in (self.first_name, self.last_name)
            or None not in (self.gender, self.birthday)
        ):
            return
        raise ValueError("error")

    def calculate(self) -> dict[str, Any]:
        return {
            "score": get_score(
                self.phone,
                self.email,
                self.birthday,
                self.gender,
                self.first_name,
                self.last_name,
            )
        }

    def set_context(self, ctx: dict[str, Any]) -> None:
        ctx["has"] = [
            field for field in self.fields if self.__getattribute__(field) is not None
        ]


class MethodRequest(BaseModel):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self) -> bool:
        return self.login == ADMIN_LOGIN
