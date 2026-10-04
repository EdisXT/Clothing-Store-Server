from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from .. import models, schemas
from ..security import hash_password, verify_password, create_access_token
from ..dependencies import get_current_user
router=APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(data:schemas.UserCreate, db:Session=Depends(get_db)):
    exists=db.query(models.User).filter(or_(models.User.email==data.email.lower(),models.User.username==data.username)).first()
    if exists: raise HTTPException(409,"Email or username already registered")
    user=models.User(email=data.email.lower(),username=data.username,hashed_password=hash_password(data.password),first_name=data.first_name,last_name=data.last_name)
    db.add(user); db.commit(); db.refresh(user); return user

@router.post("/login", response_model=schemas.Token)
def login(form:OAuth2PasswordRequestForm=Depends(), db:Session=Depends(get_db)):
    user=db.query(models.User).filter(or_(models.User.email==form.username.lower(),models.User.username==form.username)).first()
    if not user or not verify_password(form.password,user.hashed_password): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid credentials")
    return {"access_token":create_access_token(user.id),"token_type":"bearer"}

@router.get("/me",response_model=schemas.UserOut)
def me(user=Depends(get_current_user)): return user
