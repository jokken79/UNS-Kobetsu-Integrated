#!/usr/bin/env python3
"""
Create Admin User Script

Creates an admin user for the UNS Kobetsu system.
Can be run with: docker exec uns-kobetsu-backend python scripts/create_admin.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User


def create_admin_user(
    email: str = "admin@local.dev",
    password: str = "admin123",
    full_name: str = "Admin User",
    role: str = "admin"
) -> User:
    """
    Create an admin user in the database.
    
    Args:
        email: Email address for the admin user
        password: Plain text password (will be hashed)
        full_name: Full name of the admin user
        role: User role (admin, manager, user)
    
    Returns:
        Created User object
    """
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"❌ User with email '{email}' already exists!")
            
            # Ask if we should update the password
            response = input("Do you want to update the password? (y/n): ").lower().strip()
            if response == 'y':
                existing_user.hashed_password = get_password_hash(password)
                existing_user.role = role
                existing_user.full_name = full_name
                existing_user.is_active = True
                existing_user.updated_at = datetime.now()
                db.commit()
                print(f"✅ Password updated for user '{email}'")
                return existing_user
            else:
                print("No changes made.")
                return existing_user
        
        # Create new user
        hashed_password = get_password_hash(password)
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Role: {role}")
        print(f"   ID: {user.id}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function to run when script is executed directly."""
    print("\n" + "="*50)
    print("UNS Kobetsu - Admin User Creation")
    print("="*50 + "\n")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created")
    
    # Default values for local development
    email = "admin@local.dev"
    password = "admin123"
    full_name = "Admin User"
    role = "admin"
    
    # Ask if user wants to customize
    print("\nDefault admin credentials:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  Role: {role}\n")
    
    customize = input("Use default values? (y/n): ").lower().strip()
    
    if customize == 'n':
        email_input = input(f"Enter email [{email}]: ").strip()
        if email_input:
            email = email_input
            
        password_input = input(f"Enter password [{password}]: ").strip()
        if password_input:
            password = password_input
            
        full_name_input = input(f"Enter full name [{full_name}]: ").strip()
        if full_name_input:
            full_name = full_name_input
            
        role_input = input(f"Enter role (admin/manager/user) [{role}]: ").strip()
        if role_input in ['admin', 'manager', 'user']:
            role = role_input
    
    # Create the admin user
    create_admin_user(
        email=email,
        password=password,
        full_name=full_name,
        role=role
    )
    
    print("\n" + "="*50)
    print("Admin user setup complete!")
    print("You can now login to the system.")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
