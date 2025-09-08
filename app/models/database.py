from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./variables.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class VariableName(Base):
    __tablename__ = "variables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    # Add component fields
    module_key = Column(String)
    dtype_key = Column(String)
    dsize_key = Column(String)
    unit_key = Column(String)
    standard = Column(String)  # Optional, but useful if you support multiple naming standards


def init_db():
    # This will create all tables for all models derived from Base
    Base.metadata.create_all(bind=engine)
