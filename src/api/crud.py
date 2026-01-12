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

"""
CRUD Operations for Database
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.api import schemas
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import password hashing from auth module
from src.api.auth import get_password_hash

# ==========================================
# User CRUD Operations
# ==========================================

def create_user(
    db: Session, 
    username: str, 
    email: str, 
    password: str, 
    **kwargs
) -> schemas.User:
    """
    Create new user with hashed password
    
    Args:
        db: Database session
        username: Username
        email: Email address
        password: Plain text password (will be hashed)
        **kwargs: Additional user fields (full_name, role, etc.)
        
    Returns:
        Created user object
    """
    # Hash password with bcrypt (automatically handles 72 byte limit)
    hashed_password = get_password_hash(password)
    
    db_user = schemas.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=kwargs.get('full_name'),
        role=kwargs.get('role', 'user')
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[schemas.User]:
    """Get user by username"""
    return db.query(schemas.User).filter(schemas.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[schemas.User]:
    """Get user by email"""
    return db.query(schemas.User).filter(schemas.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[schemas.User]:
    """Get user by ID"""
    return db.query(schemas.User).filter(schemas.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
    """Get all users with pagination"""
    return db.query(schemas.User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, **kwargs) -> Optional[schemas.User]:
    """
    Update user
    
    Args:
        db: Database session
        user_id: User ID
        **kwargs: Fields to update
        
    Returns:
        Updated user object or None if not found
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Handle password update separately
    if 'password' in kwargs and kwargs['password'] is not None:
        kwargs['hashed_password'] = get_password_hash(kwargs.pop('password'))
    
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete user"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True

def increment_user_request_count(db: Session, user_id: int):
    """Increment user's request count"""
    user = get_user_by_id(db, user_id)
    if user:
        user.request_count += 1
        user.last_request_at = datetime.utcnow()
        db.commit()

# ==========================================
# Updated Prediction CRUD with User Tracking
# ==========================================

def create_prediction_log(
    db: Session,
    customer_id: str,
    prediction: int,
    probability: float,
    input_data: Dict[str, Any],
    user_id: Optional[int] = None
) -> schemas.PredictionLog:
    """Create prediction log with optional user tracking"""
    db_prediction = schemas.PredictionLog(
        customer_id=customer_id,
        prediction=prediction,
        probability=probability,
        input_data=input_data,
        user_id=user_id
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)

    if user_id:
        increment_user_request_count(db, user_id)
    
    return db_prediction

def get_user_predictions(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[schemas.PredictionLog]:
    """Get all predictions by user"""
    return db.query(schemas.PredictionLog)\
        .filter(schemas.PredictionLog.user_id == user_id)\
        .order_by(desc(schemas.PredictionLog.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_prediction(
    db: Session,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[schemas.PredictionLog]:
    """
    Get prediction logs with pagination
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of prediction logs
    """
    query = db.query(schemas.PredictionLog)
    
    if user_id is not None:
        query = query.filter(schemas.PredictionLog.user_id == user_id)
    
    return query\
        .order_by(desc(schemas.PredictionLog.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_customer_predictions(
    db: Session,
    customer_id: str
) -> List[schemas.PredictionLog]:
    """Get all predictions for a specific customer"""
    return db.query(schemas.PredictionLog)\
        .filter(schemas.PredictionLog.customer_id == customer_id)\
        .order_by(desc(schemas.PredictionLog.created_at))\
        .all()

def get_prediction_statistics(db: Session) -> Dict[str, Any]:
    """Get prediction statistics"""
    total_predictions = db.query(func.count(schemas.PredictionLog.id)).scalar()

    churn_predictions = db.query(func.count(schemas.PredictionLog.id))\
        .filter(schemas.PredictionLog.prediction == 1)\
        .scalar()
    
    avg_churn_probability = db.query(func.avg(schemas.PredictionLog.probability))\
        .filter(schemas.PredictionLog.prediction == 1)\
        .scalar()
    
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_predictions = db.query(func.count(schemas.PredictionLog.id))\
        .filter(schemas.PredictionLog.created_at >= yesterday)\
        .scalar()
    
    return {
        "total_predictions": total_predictions or 0,
        "churn_predictions": churn_predictions or 0,
        "no_churn_predictions": (total_predictions or 0) - (churn_predictions or 0),
        "churn_rate": (churn_predictions / total_predictions) * 100 if total_predictions else 0,
        "avg_churn_probability": float(avg_churn_probability) if avg_churn_probability else 0.0,
        "recent_predictions": recent_predictions or 0
    }

# ==========================================
# Customer CRUD Operations
# ==========================================

def create_customer(
    db: Session,
    customer_data: Dict[str, Any]
) -> schemas.Customer:
    """Create or update customer"""
    existing = db.query(schemas.Customer)\
        .filter(schemas.Customer.customer_id == customer_data['customer_id'])\
        .first()
    
    if existing:
        for key, value in customer_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_customer = schemas.Customer(**customer_data)
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer

def get_customer(db: Session, customer_id: str) -> Optional[schemas.Customer]:
    """Get customer by ID"""
    return db.query(schemas.Customer)\
        .filter(schemas.Customer.customer_id == customer_id)\
        .first()

# ==========================================
# Model Metrics CRUD Operations
# ==========================================

def save_model_metrics(
    db: Session,
    model_version: str,
    metrics: Dict[str, Any]
) -> schemas.ModelMetrics:
    """Save model performance metrics"""
    db_metrics = schemas.ModelMetrics(
        model_version=model_version,
        accuracy=metrics.get("accuracy"),
        precision=metrics.get("precision"),
        recall=metrics.get('recall'),
        f1_score=metrics.get("f1_score"),
        roc_auc=metrics.get("roc_auc"),
        confusion_matrix=metrics.get("confusion_matrix")
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def get_latest_model_metrics(db: Session) -> Optional[schemas.ModelMetrics]:
    """Get latest model metrics"""
    return db.query(schemas.ModelMetrics)\
        .order_by(desc(schemas.ModelMetrics.created_at))\
        .first()