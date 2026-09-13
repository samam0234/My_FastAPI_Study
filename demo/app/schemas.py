from pydantic import BaseModel, ConfigDict


class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True


class PostResponse(PostCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
