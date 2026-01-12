"""
FastAPI Main Application

REST API for customer churn prediction with database logging.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List
import pandas as pd
from datetime import datetime
import io
from fastapi.security import OAuth2PasswordRequestForm
from slowapi.errors import RateLimitExceeded
from datetime import timedelta

from src.api.models import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    HealthResponse,
    ModelInfoResponse,
    PredictionHistoryResponse,
    UserCreate,
    UserResponse,
    Token,
    UserUpdate
)

from src.api.database import get_db, engine
from src.api import crud, schemas

from src.api.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    require_role,
    ACCESS_TOKEN_EXPIRE_MINUTES

)

from src.api.rate_limit import limiter, _rate_limit_exceeded_handler
from src.api.ml_service import MLService
from src.utils import logger
from sqlalchemy.orm import Session

from src.api.database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Churn Prediciton API",
    description="ML API for customer churn prediction with tracking",
    version="1.0.0",
    docs_url="/docs",
    redocs_url="/redocs",        
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ml_service = MLService()

# ==========================================
# Authentication Endpoints
# ==========================================
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register new user
    
    Rate limited to 5 registrations per hour per IP
    """

    if crud.get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = crud.create_user(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password,
        full_name=user.full_name
    )

    logger.info(f"New user registered: {user.username}")
    return db_user

@app.post("/auth/token", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token
    
    OAuth2 compatible token login, get an access token for future requests
    
    Rate limited to 10 attempts per minute
    """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    logger.info(f"User logged in: {user.username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expire_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.get("/auth/me", response_model=UserResponse)
async def read_users_me(
    current_user: schemas.User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Requires authentication
    """
    return current_user

@app.put("/auth/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information
    
    Requires authentication
    """
    update_user = crud.update_user(
        db=db,
        user_id=current_user.id,
        **user_update.dict(exclude_unset=True)
    )
    return update_user

@app.get("/auth/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)
    
    Requires admin role
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# ==========================================
# Protected Prediction Endpoints
# ==========================================
@app.post("/predict", response_model=PredictionResponse)
@limiter.limit("30/minute")
async def predict_single(
    request: Request,
    pred_request: PredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Predict churn for a single customer (Protected)
    
    Requires authentication. Rate limited to 30 requests per minute.
    """
    try:
        input_data = pd.DataFrame([pred_request.dict()])
        
        prediction, probability = ml_service.predict(input_data)

        response = PredictionResponse(
            customer_id=pred_request.customer_id,
            prediction=int(prediction[0]),
            churn_probability=float(probability[0][1]),
            no_churn_probability=float(probability[0][0]),
            timestamp=datetime.utcnow()
        )

        background_tasks.add_task(
            crud.create_prediction_log,
            db=db,
            customer_id=pred_request.customer_id,
            prediction=response.prediction,
            probability=response.churn_probability,
            input_data=pred_request.dict(),
            user_id=current_user.id
        )
        return response
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )




# ==========================================
# Health & Info Endpoints
# ==========================================
@app.get("/", response_model=dict)
# @limiter.limit("60/minute")
@limiter.limit("2/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Churn Prediction API v2.0",
        "features": ["Authentication", "Rate Limiting", "ML Predictions"],
        "docs": "/docs",
        "auth": "/auth/token"
    }

@app.get("/health", response_model=HealthResponse)
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    try:
        model_loaded = ml_service.is_model_loaded()

        return HealthResponse(
            status='health' if model_loaded else 'unhealthy',
            model_loaded=model_loaded,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            timestamp=datetime.utcnow(),
            error=str(e)
        )

@app.get("/model/info", response_model=ModelInfoResponse)
async def model_info():
    """Get model information"""
    try:
        info = ml_service.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        logger.error(e)
        return ModelInfoResponse(
            model_type="unknown",
            model_version="unknown",
            features=[],
            trained_at=None,
            accuracy=None
        )

# ==========================================
# Prediction Endpoints
# ==========================================
    
@app.post("/predict/batch", response_model=List[PredictionResponse])
@limiter.limit("10/hour")
async def predict_batch(
    request: Request,
    batch_request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Predict churn for multiple customers
    
    Example request:
    ```json
    {
        "customers": [
            {
                "customer_id": "C001",
                "gender": "Male",
                "tenure": 24,
                ...
            },
            {
                "customer_id": "C002",
                "gender": "Female",
                "tenure": 12,
                ...
            }
        ]
    }
    ```
    """
    try:
        customer_data = [customer.dict() for customer in request.customers]
        input_data = pd.DataFrame(customer_data)

        prediction, probabilities = ml_service.predict(input_data)

        responses = []
        for i, customer in enumerate(request.customers):
            response = PredictionResponse(
                customer_id=customer.customer_id,
                prediction=int(prediction[i]),
                churn_probability=float(probabilities[i][1]),
                no_churn_probability=float(probabilities[i][0]),
                timestamp=datetime.utcnow()
            )
            responses.append(response)

            background_tasks.add_task(
                crud.create_prediction_log,
                db=db,
                customer_id=customer.customer_id,
                prediction=response.prediction,
                probability=response.churn_probability,
                input_data=customer.dict()
            )

        return responses
    
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/predict/csv")
async def predict_csv(
    file: UploadFile = File(...),
    background_task: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Predict churn from CSV file upload
    
    CSV should contain columns:
    - customer_id, gender, tenure, monthly_charges, total_charges,
      contract, payment_method, internet_service
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        required_col = [
            'customer_id', 'gender', 'tenure', 'monthly_charges',
            'total_charges', 'contract', 'payment_method', 'internet_service'
        ]
        missing_cols = set(required_col) - set(df.columns)
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_cols}"
            )
        
        predictions, probabilities = ml_service.predict(df)

        df['prediction'] = predictions
        df['churn_probability'] = probabilities[:, 1]
        df['no_churn_probability'] = probabilities[:, 0]

        results = df.to_dict('records')

        return JSONResponse(content={
            "total_predictions": len(results),
            "predictions": results
        })
    
    except Exception as e:
        logger.error(f"CSV prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# History & Analytics Endpoints
# ==========================================
@app.get("/predictions/history", response_model=List[PredictionHistoryResponse])
async def get_prediction_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000, ge=1),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Get prediction history from database"""
    try:
        predictions = crud.get_prediction(db,current_user.id , skip=skip, limit=limit)
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/predictions/customer/{customer_id}", response_model=List[PredictionHistoryResponse])
async def get_customer_prediction(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get prediction history for specific customer"""
    try:
        predictions = crud.get_customer_predictions(db, customer_id)
        if not predictions:
            raise HTTPException(status_code=404, detail="Customer not found")
        return predictions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db)
):
    """Get prediction analytics summary"""
    try:
        stats = crud.get_prediction_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# Model Management Endpoints
# ==========================================
@app.post("/model/reload")
async def reload_model():
    try:
        ml_service.load_model()
        return {"message":"Model Reload Sucessfuly", "timestamp":datetime.utcnow()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")

# ==========================================
# Startup & Shutdown Events
# ==========================================
@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    logger.info("Starting Churn Prediction API...")
    Base.metadata.create_all(bind=engine)
    logger.info("Starting Churn Prediction API v2.0...")
    logger.info("Authentication enabled")
    logger.info("Rate limiting enabled")
    try:
        ml_service.load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Churn Prediction API...")

# ==========================================
# Main Entry Point
# ==========================================
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level='info'
    )
