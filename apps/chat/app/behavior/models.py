from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class TaskSchema(BaseModel):
    """Single task definition executed by an agent."""
    
    description: str = Field(..., examples=["Collect articles about AI"])
    expected_output: Optional[str] = Field(
        None,
        alias="expected_output", 
        examples=["List of article URLs"]
    )
    context: Optional[List[str]] = Field(
        default_factory=list,
        examples=[["Use only academic sources"]]
    )
    agent: Optional[str] = Field(None, examples=["researcher"])
    
    model_config = ConfigDict(populate_by_name=True)

class AgentSchema(BaseModel):
    """CrewAI-style agent configuration."""
    
    role: str = Field(..., examples=["researcher"])
    goal: Optional[str] = Field(None, examples=["Provide an overview of AI trends"])
    backstory: Optional[str] = Field(None, examples=["PhD in computer science"])
    tools: List[str] = Field(default_factory=list, examples=[["browser"]])
    allow_delegation: bool = Field(False, alias="allow_delegation", examples=[True])
    tasks: List[TaskSchema] = Field(default_factory=list)
    
    model_config = ConfigDict(populate_by_name=True)

class BehaviorDefinition(BaseModel):
    """Root object describing agent behaviors loaded from Notion."""
    
    agents: List[AgentSchema] = Field(
        default_factory=list,
        examples=[[{"role": "researcher", "goal": "Find info"}]]
    )
    tasks: List[TaskSchema] = Field(default_factory=list)
    process: Optional[str] = Field("sequential", examples=["sequential"])
    
    model_config = ConfigDict(populate_by_name=True)