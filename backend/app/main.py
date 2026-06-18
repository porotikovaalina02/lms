import time

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.db import Base, engine
from app.routes import router
from app.seed import seed

app = FastAPI()
app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    for n in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            seed()
            break
        except OperationalError:
            if n == 9:
                raise
            time.sleep(2)
