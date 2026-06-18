from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.db import get_db

router = APIRouter()


def _load_test(db, test_id):
    return (
        db.query(models.Test)
        .options(joinedload(models.Test.questions).joinedload(models.Question.answers))
        .filter(models.Test.id == test_id)
        .first()
    )


def _get_user(db, tg_id, username=None, first_name=None):
    u = db.query(models.User).filter(models.User.telegram_id == tg_id).first()
    if u:
        if username:
            u.username = username
        if first_name:
            u.first_name = first_name
        db.commit()
        return u
    u = models.User(telegram_id=tg_id, username=username, first_name=first_name)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/tests")
def tests_list(db: Session = Depends(get_db)):
    rows = db.query(models.Test).filter(models.Test.is_active == True).order_by(models.Test.id).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "questions_count": len(t.questions),
        }
        for t in rows
    ]


@router.get("/tests/{test_id}/public")
def test_public(test_id: int, db: Session = Depends(get_db)):
    test = _load_test(db, test_id)
    if not test or not test.is_active:
        raise HTTPException(404, "не найден")

    questions = []
    for q in test.questions:
        questions.append({
            "id": q.id,
            "text": q.text,
            "answers": [{"id": a.id, "text": a.text} for a in q.answers],
        })

    return {"id": test.id, "title": test.title, "questions": questions}


@router.post("/tests/{test_id}/submit")
def test_submit(test_id: int, body: schemas.AttemptIn, db: Session = Depends(get_db)):
    test = _load_test(db, test_id)
    if not test or not test.is_active:
        raise HTTPException(404, "не найден")

    user = _get_user(db, body.telegram_id, body.username, body.first_name)

    qmap = {q.id: q for q in test.questions}
    amap = {a.id: a for q in test.questions for a in q.answers}

    attempt = models.TestAttempt(user_id=user.id, test_id=test.id, total=len(test.questions))
    db.add(attempt)
    db.flush()

    score = 0
    for pick in body.answers:
        q = qmap.get(pick.question_id)
        a = amap.get(pick.answer_id)
        if not q or not a or a.question_id != q.id:
            continue
        if a.is_correct:
            score += 1
        db.add(models.UserAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            answer_id=a.id,
            is_correct=a.is_correct,
        ))

    attempt.score = score
    db.commit()

    total = attempt.total or 1
    return {
        "score": score,
        "total": attempt.total,
        "percentage": round(score / total * 100, 1),
    }


@router.get("/users/{telegram_id}/attempts")
def user_attempts(telegram_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.TestAttempt)
        .join(models.User)
        .options(joinedload(models.TestAttempt.test))
        .filter(models.User.telegram_id == telegram_id)
        .order_by(models.TestAttempt.completed_at.desc())
        .all()
    )
    out = []
    for a in rows:
        pct = round(a.score / a.total * 100, 1) if a.total else 0
        out.append({
            "test_title": a.test.title,
            "score": a.score,
            "total": a.total,
            "percentage": pct,
        })
    return out
