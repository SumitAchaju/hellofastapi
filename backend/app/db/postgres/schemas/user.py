from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    table_name = "users"
    id: int
    uid: str
    first_name: str
    last_name: str
    email: EmailStr
    address: str = ""
    profile: str | None = None
    contact_number_country_code: int
    contact_number: int
    is_superuser: bool
    is_active: bool = True
    username: str
    hashed_password: str

    blocked_user: list["UserSchema"] | None = None

    friend: list["UserSchema"] | None = None

    requested_user: list["UserSchema"] | None = None
