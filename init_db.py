"""
Database initialization script.

This script initializes the database by:
1. Creating all tables from SQLAlchemy models
2. Creating an initial admin user for system administration

Run this script once after setting up the database:
    python init_db.py
"""
from datetime import datetime
from database import Base, engine, SessionLocal, init_db
from models import User, UserRole, UserStatus
from auth import hash_password


def seed_admin_user():
    """
    Create initial admin user if it doesn't exist.

    Default credentials:
    - Email: admin@personalblog.com
    - Password: admin123
    - Role: ADMIN
    - Status: ACTIVE (with verified email)

    IMPORTANT: Change this password immediately after first login!
    """
    db = SessionLocal()

    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "admin@personalblog.com").first()

        if existing_admin:
            print("✓ Admin user already exists")
            print(f"  Email: {existing_admin.email}")
            print(f"  Username: {existing_admin.username}")
            print(f"  Role: {existing_admin.role.value}")
            return

        # Create admin user
        admin = User(
            email="admin@personalblog.com",
            username="admin",
            hashed_password=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(admin)
        db.commit()

        print("✓ Admin user created successfully!")
        print("")
        print("=" * 60)
        print("ADMIN USER CREDENTIALS")
        print("=" * 60)
        print("Email: admin@personalblog.com")
        print("Password: admin123")
        print("")
        print("⚠️  IMPORTANT: Change this password immediately after first login!")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main initialization function."""
    print("")
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    print("")

    print("Step 1: Initializing database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Error creating database tables: {str(e)}")
        return

    print("")
    print("Step 2: Creating admin user...")
    seed_admin_user()

    print("")
    print("=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("1. Update your .env file with database and SMTP credentials")
    print("2. Change the admin password after first login")
    print("3. Start the FastAPI server: uvicorn main:app --reload")
    print("")


if __name__ == "__main__":
    main()
