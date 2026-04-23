from pydantic import BaseModel


class ServerCreateRequest(BaseModel):
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str


class ServerUpdateRequest(BaseModel):
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str | None = None


class ServerResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    ssh_user: str
    created_by: str


class TestConnectionResponse(BaseModel):
    ok: bool
