from pydantic import BaseModel, EmailStr


class NoteCreate(BaseModel):
    content: str


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str
