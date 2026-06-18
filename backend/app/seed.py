from app.db import SessionLocal
from app import models


def seed():
    db = SessionLocal()
    try:
        if db.query(models.Test).count():
            return

        t1 = models.Test(title="Основы Python", description="для новичков")
        db.add(t1)
        db.flush()

        q1 = models.Question(test_id=t1.id, text="Тип для целых чисел?", order=1)
        db.add(q1)
        db.flush()
        db.add_all([
            models.Answer(question_id=q1.id, text="int", is_correct=True),
            models.Answer(question_id=q1.id, text="float"),
            models.Answer(question_id=q1.id, text="str"),
        ])

        q2 = models.Question(test_id=t1.id, text="Как сделать список?", order=2)
        db.add(q2)
        db.flush()
        db.add_all([
            models.Answer(question_id=q2.id, text="list()", is_correct=True),
            models.Answer(question_id=q2.id, text="dict()"),
        ])

        t2 = models.Test(title="SQL основы")
        db.add(t2)
        db.flush()

        q3 = models.Question(test_id=t2.id, text="Команда для выборки?", order=1)
        db.add(q3)
        db.flush()
        db.add_all([
            models.Answer(question_id=q3.id, text="SELECT", is_correct=True),
            models.Answer(question_id=q3.id, text="INSERT"),
        ])

        db.commit()
    finally:
        db.close()
