"""
CRUD operations for User model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .base import CRUDBase
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User instance or None if not found
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            db: Database session
            obj_in: User creation data
            
        Returns:
            Created user instance
        """
        # Hash the password
        hashed_password = get_password_hash(obj_in.password)
        
        # Create user object
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_password(
        self, 
        db: AsyncSession, 
        *, 
        user: User, 
        new_password: str
    ) -> User:
        """
        Update user password.
        
        Args:
            db: Database session
            user: User instance
            new_password: New plain text password
            
        Returns:
            Updated user instance
        """
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def update_last_login(self, db: AsyncSession, *, user_id: int) -> None:
        """
        Update user's last login timestamp.
        
        Args:
            db: Database session
            user_id: User ID
        """
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await db.flush()
    
    async def activate_user(self, db: AsyncSession, *, user: User) -> User:
        """
        Activate a user account.
        
        Args:
            db: Database session
            user: User instance
            
        Returns:
            Updated user instance
        """
        user.is_active = True
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def deactivate_user(self, db: AsyncSession, *, user: User) -> User:
        """
        Deactivate a user account.
        
        Args:
            db: Database session
            user: User instance
            
        Returns:
            Updated user instance
        """
        user.is_active = False
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def verify_user(self, db: AsyncSession, *, user: User) -> User:
        """
        Mark user as verified.
        
        Args:
            db: Database session
            user: User instance
            
        Returns:
            Updated user instance
        """
        user.is_verified = True
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def get_active_users(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[User]:
        """
        Get all active users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active users
        """
        result = await db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


# Create instance of user CRUD
user_crud = CRUDUser(User)