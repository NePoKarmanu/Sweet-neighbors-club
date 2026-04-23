from dataclasses import dataclass


@dataclass(slots=True)
class SignupDTO:
    email: str
    phone: str
    password: str


@dataclass(slots=True)
class SigninDTO:
    email: str
    password: str
