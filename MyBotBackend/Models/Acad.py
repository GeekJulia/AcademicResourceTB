from sqlalchemy import String,Integer,Column,ForeignKey
from sqlalchemy.orm import DeclarativeBase,relationship
from pydantic import BaseModel,field_validator
from typing import Optional,List
from sqlalchemy.dialects.postgresql import JSON

class Base(DeclarativeBase):
    pass

class Course(Base):
    __tablename__ = "courses"
    id = Column (Integer,primary_key = True,autoincrement=True)
    course_code = Column(String, nullable = False,unique=True)

    resources = relationship("Resource", back_populates="course")

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String, ForeignKey("courses.course_code"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_data = Column(JSON, nullable=False,default="[]")
    
    course = relationship("Course", back_populates="resources")
    
class CourseResponse(BaseModel):
    id:int
    course_code:str
    
    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    course_code:str

class UpdateCourse(BaseModel):
    course_code:str

class ResourceResponse(BaseModel):
    id:int
    course_code:str
    resource_type:str
    resource_data: List[str]
    course: Optional[CourseResponse] = None
    
    @field_validator("resource_data", mode="before")
    @classmethod
    def validate_resource_data(cls, value):
        if isinstance(value, str):  # If it's a string, convert it to a list
            import json
            return json.loads(value)
        return value
    class Config:
        from_attributes = True

class ResourceCreate(BaseModel):
    course_code:str
    resource_type:str
    resource_data:str

class UpdateResource(BaseModel):
    resource_type:Optional[str] = None
    resource_data:Optional[str] = None

    class Config:
        from_attributes = True