from pydantic import BaseModel


class GitHubOAuthStartResponse(BaseModel):
    authorization_url: str
    state: str


class GitHubOAuthCallbackResponse(BaseModel):
    access_token: str
    token_type: str


class GitHubRepositoryResponse(BaseModel):
    full_name: str


class GitHubRefsResponse(BaseModel):
    branches: list[str]
    tags: list[str]
