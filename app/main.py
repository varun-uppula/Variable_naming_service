from fastapi import FastAPI
from app.api import routes
from app.models.database import init_db

app = FastAPI(title="Variable Naming Service")

init_db()  # creates tables if they don't exist

app.include_router(routes.router)






