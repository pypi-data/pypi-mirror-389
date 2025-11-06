from sqlalchemy import Column, Integer, String, Text, DateTime, text, UniqueConstraint, Boolean, func, Float, Double
from sqlalchemy.orm import declarative_base
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, timedelta


Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="待办", nullable=False) # 例如："待办", "进行中", "已完成", "已取消"
    priority = Column(String(20), default="中", nullable=False) # 例如："低", "中", "高", "紧急"
    created_at = Column(DateTime, default=datetime.now)
    # 预算时间
    # 以损耗时间
    # 剩余时间
    # 任务结束 ? 任务超时?
    
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_completed = Column(Boolean, default=False)
