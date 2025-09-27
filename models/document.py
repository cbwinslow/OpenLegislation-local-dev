import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, validator
from typing import Optional

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String)
    description = Column(String)
    pub_date = Column(DateTime)
    content = Column(String)
    doc_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now, nullable=False)

    def __repr__(self):
        return f"<Document(id={self.id}, source='{self.source}', url='{self.url}', title='{self.title}', pub_date={self.pub_date}, created_at={self.created_at})>"

@event.listens_for(Document, 'init')
def init_created_at(target, args, kwargs):
    if 'created_at' not in kwargs:
        target.created_at = datetime.datetime.now()

class DocumentModel(BaseModel):
    id: Optional[int] = None
    source: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    pub_date: Optional[datetime.datetime] = None
    content: Optional[str] = None
    doc_metadata: Optional[dict] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True