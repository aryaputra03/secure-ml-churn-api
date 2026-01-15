# """
# CRUD Operations for Database
# """
# from sqlalchemy.orm import Session
# from sqlalchemy import func, desc
# from src.api import schemas
# from typing import List, Dict, Any, Optional
# from datetime import datetime, timedelta
# from src.api.auth import get_password_hash

# # ==========================================
# # User CRUD Operations
# # ==========================================

# def create_user(db: Session, username: str, email: str, password: str, **kwargs) -> schemas.User:
#     """Create new user"""
#     hashed_password = get_password_hash(password)
#     db_user = schemas.User(
#         username=username,
#         email=email,
#         hashed_password=hashed_password,
#         full_name=kwargs.get('full_name'),
#         role=kwargs.get('role', 'user')
#     )

#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def get_user_by_username(db: Session, username: str) -> Optional[schemas.User]:
#     """Get user by username"""
#     return db.query(schemas.User).filter(schemas.User.username == username).first()

# def get_user_by_email(db: Session, email: str) -> Optional[schemas.User]:
#     """Get user by email"""
#     return db.query(schemas.User).filter(schemas.User.email == email).first()

# def get_user_by_id(db: Session, user_id: int) -> Optional[schemas.User]:
#     """Get user by ID"""
#     return db.query(schemas.User).filter(schemas.User.id == user_id).first()

# def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
#     """Get all users with pagination"""
#     return db.query(schemas.User).offset(skip).limit(limit).all()

# def update_user(db: Session, user_id: int, **kwargs) -> Optional[schemas.User]:
#     """Update user"""
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return None
    
#     for key, value in kwargs.items():
#         if hasattr(user, key) and value is not None:
#             setattr(user, key, value)

#     db.commit()
#     db.refresh(user)
#     return user

# def delete_user(db: Session, user_id: int) -> bool:
#     """Delete user"""
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return False
    
#     db.delete(user)
#     db.commit()
#     return True

# def increment_user_request_count(db: Session, user_id: int):
#     """Increment user's request count"""
#     user = get_user_by_id(db, user_id)
#     if user:
#         user.request_count += 1
#         user.last_request_at = datetime.utcnow()
#         db.commit()

# # ==========================================
# # Updated Prediction CRUD with User Tracking
# # ==========================================

# def create_prediction_log(
#         db: Session,
#         customer_id: str,
#         prediction: int,
#         probability: float,
#         input_data: Dict[str, Any],
#         user_id: Optional[int] = None
# ) -> schemas.PredictionLog:
#     """Create prediction log with optional user tracking"""
#     db_prediction = schemas.PredictionLog(
#         customer_id=customer_id,
#         prediction=prediction,
#         probability=probability,
#         input_data=input_data,
#         user_id=user_id
#     )
#     db.add(db_prediction)
#     db.commit()
#     db.refresh(db_prediction)

#     if user_id:
#         increment_user_request_count(db, user_id)
    
#     return db_prediction

# def get_user_predictions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
#     """Get all predictions by user"""
#     return db.query(schemas.PredictionLog)\
#         .filter(schemas.PredictionLog.user_id == user_id)\
#         .order_by(desc(schemas.PredictionLog.created_at))\
#         .offset(skip)\
#         .limit(limit)\
#         .all()

# def get_prediction(
#         db: Session,
#         skip: int = 0,
#         limit: int = 100
# ) -> List[schemas.PredictionLog]:
#     """Get prediction logs with pagination"""
#     return db.query(schemas.PredictionLog)\
#         .order_by(desc(schemas.PredictionLog.created_at))\
#         .offset(skip)\
#         .limit(limit)\
#         .all()

# def get_customer_predictions(
#         db: Session,
#         customer_id: str
# ) -> List[schemas.PredictionLog]:
#     """Get all predictions for a specific customer"""
#     return db.query(schemas.PredictionLog)\
#         .filter(schemas.PredictionLog.customer_id == customer_id)\
#         .order_by(desc(schemas.PredictionLog.created_at))\
#         .all()

# def get_prediction_statistics(db: Session) -> Dict[str, Any]:
#     """Get prediction statistics"""
#     total_predictions = db.query(func.count(schemas.PredictionLog.id)).scalar()

#     churn_predictions = db.query(func.count(schemas.PredictionLog.id))\
#         .filter(schemas.PredictionLog.prediction == 1)\
#         .scalar()
    
#     avg_churn_probability = db.query(func.avg(schemas.PredictionLog.probability))\
#         .filter(schemas.PredictionLog.prediction == 1)\
#         .scalar()
    
#     yesterday = datetime.utcnow() - timedelta(days=1)
#     recent_predictions = db.query(func.count(schemas.PredictionLog.id))\
#         .filter(schemas.PredictionLog.created_at >= yesterday)\
#         .scalar()
#     return{
#      "total_predictions": total_predictions or 0,
#      "Churn_Predictions" : churn_predictions or 0,
#      "No_Churn_Predictions": (total_predictions or 0) - (churn_predictions or 0),
#      "Churn_rate" : (churn_predictions / total_predictions) * 100 if total_predictions else 0,
#      "avg_Churn_Probability" : float(avg_churn_probability) if avg_churn_probability else 0.0,
#      "recent_predictions": recent_predictions or 0
#     }

# def create_customer(
#         db: Session,
#         customer_data: Dict[str, Any]
# ) -> schemas.Customer:
#     """Create or update customer"""
#     existing = db.query(schemas.Customer)\
#         .filter(schemas.Customer.customer_id == customer_data['customer_id'])\
#         .first()
    
#     if existing:
#         for key, value in customer_data.items():
#             setattr(existing, key, value)
#         db.commit()
#         db.refresh(existing)
#         return existing
#     else:
#         db_customer = schemas.Customer(**customer_data)
#         db.add(db_customer)
#         db.commit()
#         db.refresh(db_customer)
#         return db_customer

# def get_customer(db: Session, customer_id: str) -> schemas.Customer:
#     """Get customer by ID"""
#     return db.query(schemas.Customer)\
#         .filter(schemas.Customer.customer_id == customer_id)\
#         .first()

# def save_model_metrics(
#         db: Session,
#         model_version: str,
#         metrics: Dict[str, Any]
# ) -> schemas.ModelMetrics:
#     """Save model performance metrics"""
#     db_metrics = schemas.ModelMetrics(
#         model_version=model_version,
#         accuracy=metrics.get("accuracy"),
#         precision=metrics.get("precision"),
#         recall=metrics.get('recall'),
#         f1_score=metrics.get("f1_score"),
#         roc_auc=metrics.get("roc_auc"),
#         confusion_matrix=metrics.get("confusion_matrix")
#     )
#     db.add(db_metrics)
#     db.commit()
#     db.refresh(db_metrics)
#     return db_metrics

# def get_latest_model_metrics(db: Session) -> schemas.ModelMetrics:
#     """Get latest model metrics"""
#     return db.query(schemas.ModelMetrics)\
#         .order_by(desc(schemas.ModelMetrics.created_at))\
#         .first()

# """
# CRUD Operations for Database - FIXED
# """
# from sqlalchemy.orm import Session
# from sqlalchemy import func, desc
# from src.api import schemas
# from typing import List, Dict, Any, Optional
# from datetime import datetime, timedelta

# # Import password hashing from auth module
# from src.api.auth import get_password_hash

# # ==========================================
# # User CRUD Operations - FIXED
# # ==========================================

# def create_user(
#     db: Session, 
#     username: str, 
#     email: str, 
#     password: str, 
#     **kwargs
# ) -> schemas.User:
#     """
#     Create new user with hashed password
    
#     Password is automatically truncated to 72 bytes if necessary
#     for bcrypt compatibility.
    
#     Args:
#         db: Database session
#         username: Username
#         email: Email address
#         password: Plain text password (will be hashed and truncated if needed)
#         **kwargs: Additional user fields (full_name, role, etc.)
        
#     Returns:
#         Created user object
#     """
#     # Hash password (get_password_hash automatically handles truncation)
#     hashed_password = get_password_hash(password)
    
#     db_user = schemas.User(
#         username=username,
#         email=email,
#         hashed_password=hashed_password,
#         full_name=kwargs.get('full_name'),
#         role=kwargs.get('role', 'user')
#     )

#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def get_user_by_username(db: Session, username: str) -> Optional[schemas.User]:
#     """Get user by username"""
#     return db.query(schemas.User).filter(schemas.User.username == username).first()

# def get_user_by_email(db: Session, email: str) -> Optional[schemas.User]:
#     """Get user by email"""
#     return db.query(schemas.User).filter(schemas.User.email == email).first()

# def get_user_by_id(db: Session, user_id: int) -> Optional[schemas.User]:
#     """Get user by ID"""
#     return db.query(schemas.User).filter(schemas.User.id == user_id).first()

# def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
#     """Get all users with pagination"""
#     return db.query(schemas.User).offset(skip).limit(limit).all()

# def update_user(db: Session, user_id: int, **kwargs) -> Optional[schemas.User]:
#     """
#     Update user
    
#     Args:
#         db: Database session
#         user_id: User ID
#         **kwargs: Fields to update
        
#     Returns:
#         Updated user object or None if not found
#     """
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return None
    
#     # Handle password update separately
#     if 'password' in kwargs and kwargs['password'] is not None:
#         # Hash new password (automatically handles truncation)
#         kwargs['hashed_password'] = get_password_hash(kwargs.pop('password'))
    
#     for key, value in kwargs.items():
#         if hasattr(user, key) and value is not None:
#             setattr(user, key, value)

#     db.commit()
#     db.refresh(user)
#     return user

# def delete_user(db: Session, user_id: int) -> bool:
#     """Delete user"""
#     user = get_user_by_id(db, user_id)
#     if not user:
#         return False
    
#     db.delete(user)
#     db.commit()
#     return True

# def increment_user_request_count(db: Session, user_id: int):
#     """Increment user's request count"""
#     user = get_user_by_id(db, user_id)
#     if user:
#         user.request_count += 1
#         user.last_request_at = datetime.utcnow()
#         db.commit()

# # ==========================================
# # Updated Prediction CRUD with User Tracking
# # ==========================================

# def create_prediction_log(
#     db: Session,
#     customer_id: str,
#     prediction: int,
#     probability: float,
#     input_data: Dict[str, Any],
#     user_id: Optional[int] = None
# ) -> schemas.PredictionLog:
#     """Create prediction log with optional user tracking"""
#     db_prediction = schemas.PredictionLog(
#         customer_id=customer_id,
#         prediction=prediction,
#         probability=probability,
#         input_data=input_data,
#         user_id=user_id
#     )
#     db.add(db_prediction)
#     db.commit()
#     db.refresh(db_prediction)

#     if user_id:
#         increment_user_request_count(db, user_id)
    
#     return db_prediction

# def get_user_predictions(
#     db: Session, 
#     user_id: int, 
#     skip: int = 0, 
#     limit: int = 100
# ) -> List[schemas.PredictionLog]:
#     """Get all predictions by user"""
#     return db.query(schemas.PredictionLog)\
#         .filter(schemas.PredictionLog.user_id == user_id)\
#         .order_by(desc(schemas.PredictionLog.created_at))\
#         .offset(skip)\
#         .limit(limit)\
#         .all()

# def get_prediction(
#     db: Session,
#     user_id: Optional[int] = None,
#     skip: int = 0,
#     limit: int = 100
# ) -> List[schemas.PredictionLog]:
#     """
#     Get prediction logs with pagination
    
#     Args:
#         db: Database session
#         user_id: Optional user ID to filter by
#         skip: Number of records to skip
#         limit: Maximum number of records to return
        
#     Returns:
#         List of prediction logs
#     """
#     query = db.query(schemas.PredictionLog)
    
#     if user_id is not None:
#         query = query.filter(schemas.PredictionLog.user_id == user_id)
    
#     return query\
#         .order_by(desc(schemas.PredictionLog.created_at))\
#         .offset(skip)\
#         .limit(limit)\
#         .all()

# def get_customer_predictions(
#     db: Session,
#     customer_id: str
# ) -> List[schemas.PredictionLog]:
#     """Get all predictions for a specific customer"""
#     return db.query(schemas.PredictionLog)\
#         .filter(schemas.PredictionLog.customer_id == customer_id)\
#         .order_by(desc(schemas.PredictionLog.created_at))\
#         .all()

# def get_prediction_statistics(db: Session) -> Dict[str, Any]:
#     """Get prediction statistics"""
#     total_predictions = db.query(func.count(schemas.PredictionLog.id)).scalar()

#     churn_predictions = db.query(func.count(schemas.PredictionLog.id))\
#         .filter(schemas.PredictionLog.prediction == 1)\
#         .scalar()
    
#     avg_churn_probability = db.query(func.avg(schemas.PredictionLog.probability))\
#         .filter(schemas.PredictionLog.prediction == 1)\
#         .scalar()
    
#     yesterday = datetime.utcnow() - timedelta(days=1)
#     recent_predictions = db.query(func.count(schemas.PredictionLog.id))\
#         .filter(schemas.PredictionLog.created_at >= yesterday)\
#         .scalar()
    
#     return {
#         "total_predictions": total_predictions or 0,
#         "churn_predictions": churn_predictions or 0,
#         "no_churn_predictions": (total_predictions or 0) - (churn_predictions or 0),
#         "churn_rate": (churn_predictions / total_predictions) * 100 if total_predictions else 0,
#         "avg_churn_probability": float(avg_churn_probability) if avg_churn_probability else 0.0,
#         "recent_predictions": recent_predictions or 0
#     }

# # ==========================================
# # Customer CRUD Operations
# # ==========================================

# def create_customer(
#     db: Session,
#     customer_data: Dict[str, Any]
# ) -> schemas.Customer:
#     """Create or update customer"""
#     existing = db.query(schemas.Customer)\
#         .filter(schemas.Customer.customer_id == customer_data['customer_id'])\
#         .first()
    
#     if existing:
#         for key, value in customer_data.items():
#             setattr(existing, key, value)
#         db.commit()
#         db.refresh(existing)
#         return existing
#     else:
#         db_customer = schemas.Customer(**customer_data)
#         db.add(db_customer)
#         db.commit()
#         db.refresh(db_customer)
#         return db_customer

# def get_customer(db: Session, customer_id: str) -> Optional[schemas.Customer]:
#     """Get customer by ID"""
#     return db.query(schemas.Customer)\
#         .filter(schemas.Customer.customer_id == customer_id)\
#         .first()

# # ==========================================
# # Model Metrics CRUD Operations
# # ==========================================

# def save_model_metrics(
#     db: Session,
#     model_version: str,
#     metrics: Dict[str, Any]
# ) -> schemas.ModelMetrics:
#     """Save model performance metrics"""
#     db_metrics = schemas.ModelMetrics(
#         model_version=model_version,
#         accuracy=metrics.get("accuracy"),
#         precision=metrics.get("precision"),
#         recall=metrics.get('recall'),
#         f1_score=metrics.get("f1_score"),
#         roc_auc=metrics.get("roc_auc"),
#         confusion_matrix=metrics.get("confusion_matrix")
#     )
#     db.add(db_metrics)
#     db.commit()
#     db.refresh(db_metrics)
#     return db_metrics

# def get_latest_model_metrics(db: Session) -> Optional[schemas.ModelMetrics]:
#     """Get latest model metrics"""
#     return db.query(schemas.ModelMetrics)\
#         .order_by(desc(schemas.ModelMetrics.created_at))\
#         .first()

"""
CRUD Operations for Database

Handles database operations for users, predictions, etc.
ULTIMATE FIX: Use bcrypt directly to avoid passlib backend detection bug
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import datetime
import bcrypt

from src.api import schemas
from src.utils import logger


# ==========================================
# Password Utilities - Direct bcrypt usage
# ==========================================

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt directly
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    # Ensure password is bytes
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password
    
    # Bcrypt max 72 bytes - truncate if necessary
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        logger.warning("Password truncated to 72 bytes for bcrypt")
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash using bcrypt directly
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches
    """
    try:
        # Ensure password is bytes
        if isinstance(plain_password, str):
            password_bytes = plain_password.encode('utf-8')
        else:
            password_bytes = plain_password
        
        # Truncate to 72 bytes if necessary
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Ensure hash is bytes
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        # Verify
        return bcrypt.checkpw(password_bytes, hashed_password)
    
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ==========================================
# User CRUD Operations
# ==========================================

def get_user(db: Session, user_id: int) -> Optional[schemas.User]:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object or None
    """
    return db.query(schemas.User).filter(schemas.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[schemas.User]:
    """
    Get user by username
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User object or None
    """
    return db.query(schemas.User).filter(schemas.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[schemas.User]:
    """
    Get user by email
    
    Args:
        db: Database session
        email: Email address
        
    Returns:
        User object or None
    """
    return db.query(schemas.User).filter(schemas.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
    """
    Get list of users
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    return db.query(schemas.User).offset(skip).limit(limit).all()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role: str = "user"
) -> schemas.User:
    """
    Create new user with hashed password
    
    Args:
        db: Database session
        username: Username
        email: Email
        password: Plain text password
        full_name: Full name (optional)
        role: User role
        
    Returns:
        Created user object
    """
    # Hash the password using bcrypt directly
    hashed_password = get_password_hash(password)
    
    # Create user object
    db_user = schemas.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=False,
        request_count=0
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User created: {username} (role: {role})")
    return db_user


def update_user(
    db: Session,
    user_id: int,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    password: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[schemas.User]:
    """
    Update user information
    
    Args:
        db: Database session
        user_id: User ID
        email: New email (optional)
        full_name: New full name (optional)
        password: New password (optional)
        is_active: Active status (optional)
        
    Returns:
        Updated user object or None
    """
    user = get_user(db, user_id)
    if not user:
        return None
    
    if email is not None:
        user.email = email
    if full_name is not None:
        user.full_name = full_name
    if password is not None:
        user.hashed_password = get_password_hash(password)
    if is_active is not None:
        user.is_active = is_active
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated: {user.username}")
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    user = get_user(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    
    logger.info(f"User deleted: {user.username}")
    return True


def increment_request_count(db: Session, user_id: int) -> None:
    """
    Increment user's request count
    
    Args:
        db: Database session
        user_id: User ID
    """
    user = get_user(db, user_id)
    if user:
        user.request_count += 1
        user.last_request_at = datetime.utcnow()
        db.commit()


# ==========================================
# Prediction Log CRUD Operations
# ==========================================

def create_prediction_log(
    db: Session,
    customer_id: str,
    prediction: int,
    probability: float,
    input_data: dict,
    user_id: Optional[int] = None
) -> schemas.PredictionLog:
    """
    Create prediction log entry
    
    Args:
        db: Database session
        customer_id: Customer ID
        prediction: Prediction result
        probability: Prediction probability
        input_data: Input data dictionary
        user_id: User ID (optional)
        
    Returns:
        Created prediction log
    """
    log = schemas.PredictionLog(
        customer_id=customer_id,
        prediction=prediction,
        probability=probability,
        input_data=input_data,
        user_id=user_id
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # Increment user request count if user_id provided
    if user_id:
        increment_request_count(db, user_id)
    
    return log


def get_prediction(
    db: Session,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[schemas.PredictionLog]:
    """
    Get prediction logs
    
    Args:
        db: Database session
        user_id: Filter by user ID (optional)
        skip: Number of records to skip
        limit: Maximum records to return
        
    Returns:
        List of prediction logs
    """
    query = db.query(schemas.PredictionLog)
    
    if user_id:
        query = query.filter(schemas.PredictionLog.user_id == user_id)
    
    return query.order_by(desc(schemas.PredictionLog.created_at)).offset(skip).limit(limit).all()


def get_customer_predictions(
    db: Session,
    customer_id: str
) -> List[schemas.PredictionLog]:
    """
    Get all predictions for a specific customer
    
    Args:
        db: Database session
        customer_id: Customer ID
        
    Returns:
        List of predictions for the customer
    """
    return db.query(schemas.PredictionLog).filter(
        schemas.PredictionLog.customer_id == customer_id
    ).order_by(desc(schemas.PredictionLog.created_at)).all()


def get_prediction_statistics(db: Session) -> dict:
    """
    Get prediction statistics
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with statistics
    """
    total_predictions = db.query(func.count(schemas.PredictionLog.id)).scalar()
    
    churn_predictions = db.query(func.count(schemas.PredictionLog.id)).filter(
        schemas.PredictionLog.prediction == 1
    ).scalar()
    
    avg_probability = db.query(func.avg(schemas.PredictionLog.probability)).scalar()
    
    # Get predictions in last 24 hours
    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_predictions = db.query(func.count(schemas.PredictionLog.id)).filter(
        schemas.PredictionLog.created_at >= yesterday
    ).scalar()
    
    return {
        "total_predictions": total_predictions or 0,
        "churn_predictions": churn_predictions or 0,
        "no_churn_predictions": (total_predictions or 0) - (churn_predictions or 0),
        "average_probability": float(avg_probability) if avg_probability else 0.0,
        "predictions_last_24h": recent_predictions or 0
    }


# ==========================================
# Model Metrics CRUD Operations
# ==========================================

def create_model_metrics(
    db: Session,
    model_version: str,
    accuracy: float,
    precision: float,
    recall: float,
    f1_score: float,
    roc_auc: Optional[float] = None,
    confusion_matrix: Optional[dict] = None
) -> schemas.ModelMetrics:
    """
    Create model metrics entry
    
    Args:
        db: Database session
        model_version: Model version
        accuracy: Accuracy score
        precision: Precision score
        recall: Recall score
        f1_score: F1 score
        roc_auc: ROC AUC score (optional)
        confusion_matrix: Confusion matrix (optional)
        
    Returns:
        Created metrics object
    """
    metrics = schemas.ModelMetrics(
        model_version=model_version,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        roc_auc=roc_auc,
        confusion_matrix=confusion_matrix
    )
    
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    
    logger.info(f"Model metrics saved: {model_version}")
    return metrics


def get_latest_model_metrics(db: Session) -> Optional[schemas.ModelMetrics]:
    """
    Get latest model metrics
    
    Args:
        db: Database session
        
    Returns:
        Latest model metrics or None
    """
    return db.query(schemas.ModelMetrics).order_by(
        desc(schemas.ModelMetrics.created_at)
    ).first()