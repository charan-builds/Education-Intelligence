from pydantic import BaseModel


class TopicPracticeQuestion(BaseModel):
    id: int
    difficulty: int
    question_text: str


class TopicDetailResponse(BaseModel):
    id: int
    name: str
    description: str
    examples: list[str]
    practice_questions: list[TopicPracticeQuestion]
