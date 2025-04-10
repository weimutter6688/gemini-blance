"""
数据库模型模块
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.database.connection import Base


class Settings(Base):
    """
    设置表，对应.env中的配置项
    """
    __tablename__ = "t_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, comment="配置项键名")
    value = Column(Text, nullable=True, comment="配置项值")
    description = Column(String(255), nullable=True, comment="配置项描述")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="更新时间")
    
    def __repr__(self):
        return f"<Settings(key='{self.key}', value='{self.value}')>"


class ErrorLog(Base):
    """
    错误日志表
    """
    __tablename__ = "t_error_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gemini_key = Column(String(100), nullable=True, comment="Gemini API密钥")
    model_name = Column(String(100), nullable=True, comment="模型名称")
    error_type = Column(String(50), nullable=True, comment="错误类型")
    error_log = Column(Text, nullable=True, comment="错误日志")
    error_code = Column(Integer, nullable=True, comment="错误代码")
    request_msg = Column(JSON, nullable=True, comment="请求消息")
    request_time = Column(DateTime, default=datetime.datetime.now, comment="请求时间")
    
    def __repr__(self):
        return f"<ErrorLog(id='{self.id}', gemini_key='{self.gemini_key}')>"
