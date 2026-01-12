"""
Pydantic Models for API Request/Response
"""

from pydantic import BaseModel, Field, field_validator, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# ==========================================
# Authentication Models
# ==========================================

class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """User registration model"""
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """User response model"""
    id: int
    role: str
    is_active: bool
    is_verified: bool
    request_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in = int = 1800

class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    scopes: List[str] = []

class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr

class PasswordChange(BaseModel):
    """Password change request"""
    old_password: str
    new_password: str = Field(..., min_length=8)

# ==========================================
# API Key Models
# ==========================================

class APICreate(BaseModel):
    """API key creation request"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class APIKeyResponse(BaseModel):
    """API key response"""
    key: str
    name: str
    created_at: datetime

class PredictionRequest(BaseModel):
    """Request model for single prediction"""
    customer_id: str = Field(
        ...,
        examples=["C12345"]
    )
    gender: str = Field(
        ...,
        examples=["Male"]
    )
    tenure: int = Field(
        ...,
        ge=0,
        le=72,
        examples=[24]
    )
    monthly_charges: float = Field(
        ...,
        ge=0,
        examples=[70.5]
    )
    total_charges: float = Field(
        ...,
        ge=0,
        examples=[1500.75]
    )
    contract: str = Field(
        ...,
        examples=["One year"]
    )
    payment_method: str = Field(
        ...,
        examples=["Bank transfer"]
    )
    internet_service: str = Field(
        ...,
        examples=["Fiber optic"]
    )

    @field_validator('gender')
    def validate_gender(cls, v):
        allowed = ['Male', 'Female']
        if v not in allowed:
            raise ValueError(f"Gender must be one of {allowed}")
        return v
    
    @field_validator('contract')
    def validate_contract(cls, v):
        allowed = ['Month-to-month', 'One year', 'Two year']
        if v not in allowed:
            raise ValueError(f"Contract must be one of {allowed}")
        return v
    
    @field_validator('internet_service')
    def validate_internet_service(cls, v):
        allowed = ['DSL', 'Fiber optic', 'No']
        if v not in allowed:
            raise ValueError(f"Internet service must be one of {allowed}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "C12345",
                "gender": "Male",
                "tenure": 24,
                "monthly_charges": 75.5,
                "total_charges": 1810.0,
                "contract": "One year",
                "payment_method": "Bank transfer",
                "internet_service": "Fiber optic"
            }
        }

class PredictionResponse(BaseModel):
    """Response model for prediction"""
    customer_id: str
    prediction: int = Field(..., description="0: No churn, 1: Churn")
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    no_churn_probability: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime

    class Config:
        json_schema_extra ={
            "example":{
                "customer_id": "C12345",
                "prediction": 1,
                "churn_probability": 0.75,
                "no_churn_probability": 0.25,
                "timestamp": "2024-01-15T10:30:00"
            }
        }

class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""
    customers: List[PredictionRequest]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str 
    model_loaded: bool
    timestamp: datetime
    error: Optional[str] = None

class ModelInfoResponse(BaseModel):
    """Model information response"""
    model_type: str
    model_version: str
    features: Optional[List[str]] = []
    trained_at: Optional[str] = None
    accuracy: Optional[float] = None

class PredictionHistoryResponse(BaseModel):
    """Prediction history response"""
    id: int
    customer_id: str
    prediction: int
    probability: float
    created_at: datetime

    class Config:
        from_attributes = True 
