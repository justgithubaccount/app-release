from pydantic import BaseModel, Field

class CreateProjectRequest(BaseModel):
    name: str = Field(..., examples=["My Project"])

class ProjectInfo(BaseModel):
    id: str = Field(..., examples=["project-123"])
    name: str = Field(..., examples=["Demo Project"])