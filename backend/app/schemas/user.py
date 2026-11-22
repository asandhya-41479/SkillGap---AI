from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    target_role: str | None = Field(default=None, max_length=150)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    target_role: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_role: str | None = Field(default=None, max_length=150)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def _must_differ(self):
        if self.new_password == self.current_password:
            raise ValueError("The new password must be different from the current password.")
        return self


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"