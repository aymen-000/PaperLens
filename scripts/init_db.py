from backend.app.database import engine , Base 

from backend.app.models import * 

Base.metadata.create_all(bind=engine)