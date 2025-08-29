#!/usr/bin/env python3
"""
Database migration: Add profile_customized column to users table
Run this after updating the User model to add the profile_customized field
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add profile_customized column to users table"""
    
    try:
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            
            try:
                # Check if column already exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='profile_customized'
                """))
                
                if result.fetchone():
                    logger.info("Column 'profile_customized' already exists. Skipping migration.")
                    trans.rollback()
                    return
                
                # Add the new column
                logger.info("Adding 'profile_customized' column to users table...")
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN profile_customized BOOLEAN DEFAULT FALSE
                """))
                
                # Update existing users to have profile_customized = FALSE
                logger.info("Setting default values for existing users...")
                result = connection.execute(text("""
                    UPDATE users 
                    SET profile_customized = FALSE 
                    WHERE profile_customized IS NULL
                """))
                
                logger.info(f"Updated {result.rowcount} existing users with default profile_customized = FALSE")
                
                # Commit the transaction
                trans.commit()
                logger.info("Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Migration failed: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting database migration: add_profile_customized")
    run_migration()
    logger.info("Migration completed")
