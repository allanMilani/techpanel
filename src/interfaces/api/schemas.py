from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str


class StartExecutionRequest(BaseModel):
    pipeline_id: str
    branch_or_tag: str


class ExecutionResponse(BaseModel):
    id: str
    pipeline_id: str
    branch_or_tag: str
    status: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
