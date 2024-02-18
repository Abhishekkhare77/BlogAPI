from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from pydantic import BaseModel, Extra
from passlib.context import CryptContext
from typing import Optional
from fastapi import status
from jose import JWTError,jwt
from datetime import datetime, timedelta
from db import get_database

# Create an APIRouter instance
router = APIRouter(
    prefix="/auth",
    tags=["User Authentication"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    id: Optional[str] = None
    username: str 
    password: str

    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "secret",
            }
        }

@router.post("/register")
async def register(user: User,db=Depends(get_database)):
    hashed_password = pwd_context.hash(user.password)
    user_in_db = await db.users.find_one({"username": user.username})
    if user_in_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    await db.users.insert_one({"username": user.username, "password": hashed_password})
    return {"username": user.username, "message": "User registered successfully"}


SECRET_KEY = "a very secret key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def authenticate_user(username: str, password: str,db=Depends(get_database)):
    user = await db.users.find_one({"username": username})
    if not user:
        return False
    if not pwd_context.verify(password, user["password"]):
        return False
    return user

@router.post("/login")
async def login_user_with_JWT(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_database)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Assuming user["_id"] or some unique identifier exists
    user_id = str(user["_id"])  # Convert ObjectId to string if using MongoDB
    access_token = create_access_token(
        data={"sub": user["username"]}, user_id=user_id, expires_delta=access_token_expires
    )
    return {"access_token": access_token}


def create_access_token(data: dict,user_id: str, expires_delta: timedelta = None):
    to_encode = data.copy()
    to_encode.update({"user_id": user_id}) 
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_database)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        user_doc = await db.users.find_one({"username": username})
        if user_doc is None:
            raise credentials_exception
        # Convert the ObjectId to a string and include it in the User instance
        user_id = str(user_doc["_id"])
        user = User(id=user_id, **user_doc)
        return user
    except JWTError:
        raise credentials_exception
    
@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user