"""
Sample API for demonstrating APIDocForge capabilities.

This is a sample FastAPI-style application showing how APIDocForge
extracts documentation from code.
"""

from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    """User model."""
    id: int
    name: str
    email: str
    is_active: bool = True


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    name: str
    email: str


class UpdateUserRequest(BaseModel):
    """Request model for updating a user."""
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


# Simulated FastAPI-style routes for demonstration

@app.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
):
    """
    Get all users.
    
    Retrieve a list of users with optional filtering.
    
    :param skip: Number of users to skip (pagination)
    :param limit: Maximum number of users to return
    :param is_active: Filter by active status
    :return: List of users
    """
    return {"users": [], "total": 0}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get a specific user by ID.
    
    :param user_id: The user's unique identifier
    :return: User details
    """
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}


@app.post("/users")
def create_user(request: CreateUserRequest):
    """
    Create a new user.
    
    Creates a user with the provided information.
    
    :param request: User creation data
    :return: Created user with ID
    """
    return {"id": 1, **request.dict()}


@app.put("/users/{user_id}")
def update_user(user_id: int, request: UpdateUserRequest):
    """
    Update an existing user.
    
    Updates user information. Only provided fields are modified.
    
    :param user_id: The user's unique identifier
    :param request: User update data
    :return: Updated user
    """
    return {"id": user_id, "name": "Updated Name", "email": "updated@example.com"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """
    Delete a user.
    
    Permanently removes a user from the system.
    
    :param user_id: The user's unique identifier
    :return: Deletion confirmation
    """
    return {"message": "User deleted successfully"}


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the API.
    """
    return {"status": "healthy", "version": "1.0.0"}
