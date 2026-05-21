from sqlmodel import create_engine, SQLModel, Session
from app.core.config import settings

DATABASE_URL = "postgresql://postgres:shina@localhost:5432/parcial_prog_4"

engine = create_engine(settings.DATABASE_URL, echo=True)

'''
engine = create_engine(
    DATABASE_URL, 
    echo= True
)'''

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session