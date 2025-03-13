from fastapi import FastAPI,Depends,HTTPException,Body
from sqlalchemy import select, and_,cast, String
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import shutil,os,json,time
import subprocess,logging
from alembic.config import Config
from alembic import command



from Models.Acad import (
    Course,
    Resource,
    CourseCreate,
    CourseResponse,
    UpdateCourse,
    ResourceCreate,
    ResourceResponse,
    UpdateResource,
)
from Models.database import SessionLocal


app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/add-courses",response_model=CourseCreate)
async def add_course(course:CourseCreate,db:Session = Depends(get_db)):
    try:
        new_course = Course(
            course_code = course.course_code
        )
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        return new_course
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code = 400, detail = "Course code must be unique")



@app.get("/get-courses",response_model=list[CourseResponse])
async def return_courses(db:Session=Depends(get_db)):
    courses = db.execute(select(Course)).scalars().all()
    return courses 


@app.get("/get-resources",response_model=list[ResourceResponse])
async def return_resources(db:Session=Depends(get_db)):
    resources = db.execute(select(Resource)).scalars().all()
    return resources

@app.get("/get-resources/{course_id}/{resource_type}", response_model=list[ResourceResponse])
async def get_resource(resource_type: str, course_id: str, db: Session = Depends(get_db)):
    resources = db.execute(
        select(Resource).filter(
            and_(
                Resource.course_code == course_id,
                Resource.resource_type == resource_type
            )
        )
    ).scalars().all()

    if not resources:
        raise HTTPException(status_code=404, detail="Resources not found")

    # Convert resource_data from JSON strings to actual values
    for resource in resources:
        try:
            resource.resource_data = json.loads(resource.resource_data)
        except json.JSONDecodeError:
            resource.resource_data = None

    return resources

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

# def run_migrations():
#     alembic_cfg = Config("alembic.ini")  # Ensure this path is correct
#     command.upgrade(alembic_cfg, "head")

# run_migrations()


@app.post("/add-resources/{course_code}/{resource_type}/upload", response_model=ResourceResponse)
async def add_resource(
    course_code: str,
    resource_type: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    print("Received request body:", data)
    resource_data = data.get( 'resource_data')
    print("Received file_id:", resource_data)
    
    # Check if course exists
    course = db.execute(select(Course).filter(Course.course_code == course_code)).scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course does not exist")

    # Check if the file_id already exists for the same course_code and resource_type
    existing_resource = db.execute(
        select(Resource).filter(
            and_(Resource.course_code == course_code, 
                 Resource.resource_type == resource_type, 
                 cast(Resource.resource_data, String) == json.dumps([resource_data]))
        )
    ).scalars().first()

    if existing_resource:
        raise HTTPException(status_code=400, detail="This file already exists in the database.")

    # Create a new row for this resource
    new_resource = Resource(course_code=course_code, 
                            resource_type=resource_type, 
                            resource_data=json.dumps([resource_data])
                     )
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)

    return {
        "id": new_resource.id,
        "course_code": new_resource.course_code,
        "resource_type": new_resource.resource_type,
        "resource_data": json.loads(new_resource.resource_data),   
    }


