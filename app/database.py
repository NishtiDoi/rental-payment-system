from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# This file sets up the database connection and session management for SQLAlchemy. 
# It defines the Base class for models to inherit from, and a get_db function that can be used in FastAPI endpoints to get a database session. 
# The database URL is constructed using settings from the config file, which allows for easy configuration across different environments (development, testing, production).
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)# connection string, tells sqlalchemy which db type -> postgresql, which driver -> psycopg2, and the credentials to connect to the database

print(SQLALCHEMY_DATABASE_URL) 

engine = create_engine(SQLALCHEMY_DATABASE_URL) # engine is the connection manager , bridge between python app and postgresql
SessionLocal = sessionmaker(
    autocommit=False, # nothing is saved automaticaally, you have to call db.commit() to save changes to the database. This gives you more control and allows you to roll back if something goes wrong.
    autoflush=False, # sending changes to database before commit
    bind=engine
    )

Base = declarative_base() # this class represents a db table

def get_db():
    db = SessionLocal() # each request to the API will get its own database session, which is created here.
    try:
        yield db
    finally:
        db.close()

"""
This file does 4 things:
    Builds database connection string
    Creates engine (bridge to DB)
    Creates session factory (working connection per request)
    Provides Base for models
"""