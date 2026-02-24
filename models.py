from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    icon_path = Column(String(200), nullable=True)
    is_completed = Column(Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'icon_path': self.icon_path,
            'is_completed': self.is_completed
        }

class AACCategory(Base):
    __tablename__ = 'aac_category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    color = Column(String(20), default='#E0F7FA')
    buttons = relationship('AACButton', back_populates='category', lazy=True)

class AACButton(Base):
    __tablename__ = 'aac_button'
    id = Column(Integer, primary_key=True)
    label = Column(String(50), nullable=False)
    image_path = Column(String(200), nullable=True)
    speech_text = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey('aac_category.id'), nullable=False)
    category = relationship('AACCategory', back_populates='buttons')

def init_db(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
