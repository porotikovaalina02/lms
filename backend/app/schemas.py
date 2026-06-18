from pydantic import BaseModel


class AnswerPick(BaseModel):
    question_id: int
    answer_id: int


class AttemptIn(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    answers: list[AnswerPick]
