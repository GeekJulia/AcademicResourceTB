from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_url="postgresql://Julia Esele:julia7105@localhost/Academic Resource"

engine = create_engine(database_url)
SessionLocal = sessionmaker(bind = engine)