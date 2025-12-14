from pydantic import BaseModel, Field
from schema.synthetic_data import TrainingType

class PlanningResponse(BaseModel):
    topic: str = Field(..., description="The topic of the data to be generated")
    training_type: TrainingType = Field(..., description="The training that the user requires")
    research_plan: str = Field(..., description="The research plan to be used")
    data_structure_specification: str = Field(..., description="The data structure specification to be used")
    execution_plan: str = Field(..., description="The execution plan to be used")
    reasoning: str = Field(..., description="The reasoning to be used")

class Questions(BaseModel):
    topic: str = Field(..., description="The topic of the data to be generated")
    sub_topic: str = Field(..., description="The sub topic of the data to be generated")
    questions: list[str] = Field(..., description="The questions to be asked")
