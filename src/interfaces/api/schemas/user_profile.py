from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    email: str
    display_name: str | None = None
    has_github_token: bool = False


class ProfilePatchBody(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    github_token: str | None = None
