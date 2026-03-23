from app.db.session import engine
from app.db.models import Base

# create all tables
Base.metadata.create_all(bind=engine)

print("Database and tables created.")