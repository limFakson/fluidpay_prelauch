from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
DATABASE_URL = "sqlite:///db/data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define the database model
class UserWallet(Base):
    __tablename__ = "user_wallets"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    wallet = Column(String, nullable=False)


# Create the database tables
Base.metadata.create_all(bind=engine)

# FastAPI app instance
app = FastAPI()


# Request model
class WalletRequest(BaseModel):
    email: EmailStr
    wallet: str


# Response model
class WalletResponse(BaseModel):
    email: EmailStr
    wallet: str


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Store wallet data
@app.post("/store_wallet/", response_model=WalletResponse)
def store_wallet(request: WalletRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = (
        db.query(UserWallet).filter(UserWallet.email == request.email).scalar()
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already exists")

    # Store the new record
    new_entry = UserWallet(email=request.email, wallet=request.wallet)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


# Get all stored wallets
@app.get("/wallets/", response_model=list[WalletResponse])
def get_all_wallets(db: Session = Depends(get_db)):
    wallets = db.query(UserWallet).all()
    return wallets


# Get wallet by email
@app.get("/wallet/{email}", response_model=WalletResponse)
def get_wallet_by_email(email: str, db: Session = Depends(get_db)):
    wallet = db.query(UserWallet).filter(UserWallet.email == email).scalar()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet
