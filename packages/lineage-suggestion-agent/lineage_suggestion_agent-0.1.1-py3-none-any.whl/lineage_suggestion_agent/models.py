from pydantic import BaseModel, Field
from typing import Dict

class LineageSuggestion(BaseModel):
    answer: str = Field(..., description="The suggestion text ")
