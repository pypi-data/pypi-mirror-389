"""
Full application example for WebClone Backend
"""
from fastapi import File, UploadFile, Request
from webclone_backend import WebCloneBackend, Database
from webclone_backend.database.models import BaseModel
from sqlalchemy import Column, String, Integer
import os

# Define a sample model
class User(BaseModel):
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))

# Create app instance
app = WebCloneBackend(title="WebClone Example App")

# Setup database
db = Database('sqlite:///./test.db')

# Create tables
db.create_all()

@app.app.get("/")
async def home():
    return {"message": "Welcome to WebClone Backend!"}

@app.app.get("/users")
async def get_users():
    users = db.query(User).all()
    return {"users": [user.to_dict() for user in users]}

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)