"""
Database connection manager for WebClone Backend
"""
from typing import Any, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Database:
    """Database connection manager"""
    
    def __init__(self, database_url: str):
        """Initialize database connection"""
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def create_all(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all(self):
        """Drop all tables"""
        Base.metadata.drop_all(bind=self.engine)
    
    def add(self, obj: Any) -> Any:
        """Add an object to the database"""
        with self.get_session() as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
    
    def query(self, model: Any) -> Any:
        """Create a query for a model"""
        with self.get_session() as session:
            return session.query(model)