from pydantic import BaseModel, ConfigDict


class SignupDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    phone: str
    password: str


class SigninDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
