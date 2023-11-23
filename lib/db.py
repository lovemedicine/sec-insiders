from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import Session
from models import Base

def create_engine(echo=False):
    return sqlalchemy_create_engine("sqlite:///../data/sec-insiders.db", echo=echo, future=True)

def create_session(engine=None, echo=False):
    if engine == None:
        engine = create_engine(echo=echo)
    return Session(engine)

def create_tables(engine=None, echo=False):
    if engine == None:
        engine = create_engine(echo=echo)
    Base.metadata.create_all(engine)

