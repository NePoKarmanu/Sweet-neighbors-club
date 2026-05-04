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


class UpdateProfileDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str
    email: str | None = None
    phone: str | None = None
    password: str | None = None

class RefreshDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str