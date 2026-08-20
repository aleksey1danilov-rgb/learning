from app.core.database import engine, Base
from app.models import user, course, lesson, course_assignment

Base.metadata.create_all(bind=engine)
print("Database created!")