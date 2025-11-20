"""
Database Schemas for the Learning App (Computer Networks)

Each Pydantic model name maps to a MongoDB collection using the lowercase of the
class name (e.g., Worksheet -> "worksheet").
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ---- Core Domain Schemas ----

class WorksheetAnswer(BaseModel):
    question_id: str = Field(..., description="Identifier for the worksheet question")
    answer_text: str = Field(..., description="Student's answer in free text")

class Worksheet(BaseModel):
    student_name: str = Field(..., description="Student full name")
    class_name: str = Field(..., description="Class / Grade / Group")
    topic: str = Field("Computer Network Topologies", description="Worksheet topic")
    answers: List[WorksheetAnswer] = Field(default_factory=list, description="List of answers")

class Reflection(BaseModel):
    worksheet_id: str = Field(..., description="Related worksheet document id")
    student_name: str = Field(..., description="Student full name")
    understanding_level: int = Field(..., ge=1, le=5, description="Self-assessed understanding 1-5")
    feelings: Optional[str] = Field(None, description="How do you feel about the topic?")
    challenges: Optional[str] = Field(None, description="What was challenging?")
    questions: Optional[str] = Field(None, description="What questions remain?")

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]

class QuizSubmission(BaseModel):
    student_name: Optional[str] = Field(None, description="Student full name")
    quiz_key: str = Field(..., description="Quiz identifier, e.g., 'network-topologies'")
    # Map of question id to selected option index
    answers: Dict[str, int] = Field(default_factory=dict)
    score: Optional[int] = None
    total: Optional[int] = None
    details: Optional[List[Dict[str, Any]]] = None
