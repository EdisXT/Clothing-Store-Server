from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas, oauth2, utils
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED
)
def register_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(models.User)
        .filter(
            or_(
                models.User.email == data.email.lower(),
                models.User.username == data.username,
            )
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    hashed_password = utils.hash_password(data.password)

    new_user = models.User(
        email=data.email.lower(),
        username=data.username,
        hashed_password=hashed_password,
        first_name=data.first_name,
        last_name=data.last_name,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=schemas.Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(
            or_(
                models.User.email == form_data.username.lower(),
                models.User.username == form_data.username,
            )
        )
        .first()
    )

    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user=Depends(oauth2.get_current_user)):
    return current_user
