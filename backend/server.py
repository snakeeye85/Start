from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import requests
import os
from typing import Optional, List
import asyncio
from contextlib import asynccontextmanager

# Pydantic models
class UserCreate(BaseModel):
    email: str
    name: str

class StakeCreate(BaseModel):
    user_id: str
    amount: float

class PaymentCreate(BaseModel):
    user_id: str
    amount: float

class User(BaseModel):
    id: str
    email: str
    name: str
    balance: float
    staked_amount: float
    total_rewards: float
    created_at: datetime

class StakeRecord(BaseModel):
    id: str
    user_id: str
    amount: float
    daily_rate: float
    start_date: datetime
    is_active: bool
    total_earned: float

class Transaction(BaseModel):
    id: str
    user_id: str
    type: str  # "deposit", "stake", "unstake", "reward"
    amount: float
    status: str
    created_at: datetime
    payment_id: Optional[str] = None

# Background task for calculating daily rewards
async def calculate_daily_rewards():
    """Calculate and distribute daily rewards for all active stakes"""
    while True:
        try:
            # Get all active stakes
            stakes = list(db.stakes.find({"is_active": True}))
            
            for stake in stakes:
                # Calculate time since last reward
                last_reward = stake.get('last_reward_date', stake['start_date'])
                now = datetime.utcnow()
                
                # Check if 24 hours have passed
                if now - last_reward >= timedelta(hours=24):
                    # Calculate reward (30% daily)
                    daily_reward = stake['amount'] * 0.30
                    
                    # Update user balance
                    db.users.update_one(
                        {"id": stake['user_id']},
                        {
                            "$inc": {
                                "balance": daily_reward,
                                "total_rewards": daily_reward
                            }
                        }
                    )
                    
                    # Update stake record
                    db.stakes.update_one(
                        {"id": stake['id']},
                        {
                            "$inc": {"total_earned": daily_reward},
                            "$set": {"last_reward_date": now}
                        }
                    )
                    
                    # Create transaction record
                    transaction = {
                        "id": str(uuid.uuid4()),
                        "user_id": stake['user_id'],
                        "type": "reward",
                        "amount": daily_reward,
                        "status": "completed",
                        "created_at": now
                    }
                    db.transactions.insert_one(transaction)
                    
                    print(f"Distributed {daily_reward} USDT reward to user {stake['user_id']}")
                    
        except Exception as e:
            print(f"Error calculating rewards: {e}")
            
        # Wait 1 hour before next check
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task
    task = asyncio.create_task(calculate_daily_rewards())
    yield
    # Cleanup
    task.cancel()

app = FastAPI(lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(mongo_url)
db = client.usdt_staking_db

# NOWPayments configuration
NOWPAYMENTS_API_KEY = "9P6G10G-HKS4CD5-NK7R625-AH7JCKC"
NOWPAYMENTS_BASE_URL = "https://api-sandbox.nowpayments.io/v1"

@app.get("/")
async def root():
    return {"message": "USDT Staking API is running!"}

@app.post("/api/users")
async def create_user(user: UserCreate):
    """Create a new user"""
    # Check if user already exists
    existing_user = db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "name": user.name,
        "balance": 0.0,
        "staked_amount": 0.0,
        "total_rewards": 0.0,
        "created_at": datetime.utcnow()
    }
    
    db.users.insert_one(new_user)
    return {"message": "User created successfully", "user_id": new_user["id"]}

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user information"""
    user = db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["_id"] = str(user["_id"])
    return user

@app.post("/api/payments/create")
async def create_payment(payment: PaymentCreate):
    """Create a NOWPayments payment for USDT deposit"""
    try:
        # Create payment with NOWPayments
        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY,
            "Content-Type": "application/json"
        }
        
        payment_data = {
            "price_amount": payment.amount,
            "price_currency": "usd",
            "pay_currency": "usdt",
            "order_id": str(uuid.uuid4()),
            "order_description": f"USDT deposit for staking - User: {payment.user_id}",
            "ipn_callback_url": f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api/payments/callback",
            "success_url": f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/dashboard?payment=success",
            "cancel_url": f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/dashboard?payment=cancelled"
        }
        
        response = requests.post(
            f"{NOWPAYMENTS_BASE_URL}/payment",
            json=payment_data,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Payment creation failed: {response.text}")
        
        payment_response = response.json()
        
        # Store pending transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": payment.user_id,
            "type": "deposit",
            "amount": payment.amount,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "payment_id": payment_response.get("payment_id")
        }
        db.transactions.insert_one(transaction)
        
        return {
            "payment_url": payment_response.get("invoice_url"),
            "payment_id": payment_response.get("payment_id"),
            "transaction_id": transaction["id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payment: {str(e)}")

@app.post("/api/payments/callback")
async def payment_callback(callback_data: dict):
    """Handle NOWPayments callback"""
    try:
        payment_id = callback_data.get("payment_id")
        payment_status = callback_data.get("payment_status")
        
        if payment_status == "finished":
            # Find the transaction
            transaction = db.transactions.find_one({"payment_id": payment_id})
            if transaction:
                # Update user balance
                db.users.update_one(
                    {"id": transaction["user_id"]},
                    {"$inc": {"balance": transaction["amount"]}}
                )
                
                # Update transaction status
                db.transactions.update_one(
                    {"payment_id": payment_id},
                    {"$set": {"status": "completed"}}
                )
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error processing callback: {e}")
        return {"status": "error"}

@app.post("/api/stake")
async def create_stake(stake: StakeCreate):
    """Create a new stake"""
    # Check user balance
    user = db.users.find_one({"id": stake.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["balance"] < stake.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create stake record
    new_stake = {
        "id": str(uuid.uuid4()),
        "user_id": stake.user_id,
        "amount": stake.amount,
        "daily_rate": 0.30,  # 30% daily return
        "start_date": datetime.utcnow(),
        "last_reward_date": datetime.utcnow(),
        "is_active": True,
        "total_earned": 0.0
    }
    
    db.stakes.insert_one(new_stake)
    
    # Update user balance and staked amount
    db.users.update_one(
        {"id": stake.user_id},
        {
            "$inc": {
                "balance": -stake.amount,
                "staked_amount": stake.amount
            }
        }
    )
    
    # Create transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": stake.user_id,
        "type": "stake",
        "amount": stake.amount,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    db.transactions.insert_one(transaction)
    
    return {"message": "Stake created successfully", "stake_id": new_stake["id"]}

@app.post("/api/unstake/{stake_id}")
async def unstake(stake_id: str):
    """Unstake funds"""
    # Find the stake
    stake = db.stakes.find_one({"id": stake_id, "is_active": True})
    if not stake:
        raise HTTPException(status_code=404, detail="Active stake not found")
    
    # Calculate final reward if any time has passed
    now = datetime.utcnow()
    last_reward = stake.get('last_reward_date', stake['start_date'])
    
    # If less than 24 hours, calculate partial reward
    hours_since_reward = (now - last_reward).total_seconds() / 3600
    if hours_since_reward > 0:
        partial_reward = stake['amount'] * 0.30 * (hours_since_reward / 24)
        
        # Add partial reward
        db.users.update_one(
            {"id": stake["user_id"]},
            {
                "$inc": {
                    "balance": partial_reward,
                    "total_rewards": partial_reward
                }
            }
        )
        
        db.stakes.update_one(
            {"id": stake_id},
            {"$inc": {"total_earned": partial_reward}}
        )
    
    # Return staked amount to user balance
    db.users.update_one(
        {"id": stake["user_id"]},
        {
            "$inc": {
                "balance": stake["amount"],
                "staked_amount": -stake["amount"]
            }
        }
    )
    
    # Mark stake as inactive
    db.stakes.update_one(
        {"id": stake_id},
        {"$set": {"is_active": False, "end_date": now}}
    )
    
    # Create transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": stake["user_id"],
        "type": "unstake",
        "amount": stake["amount"],
        "status": "completed",
        "created_at": now
    }
    db.transactions.insert_one(transaction)
    
    return {"message": "Unstaked successfully"}

@app.get("/api/users/{user_id}/stakes")
async def get_user_stakes(user_id: str):
    """Get all stakes for a user"""
    stakes = list(db.stakes.find({"user_id": user_id}))
    for stake in stakes:
        stake["_id"] = str(stake["_id"])
    return stakes

@app.get("/api/users/{user_id}/transactions")
async def get_user_transactions(user_id: str):
    """Get all transactions for a user"""
    transactions = list(db.transactions.find({"user_id": user_id}).sort("created_at", -1))
    for transaction in transactions:
        transaction["_id"] = str(transaction["_id"])
    return transactions

@app.get("/api/stats")
async def get_stats():
    """Get platform statistics"""
    total_users = db.users.count_documents({})
    total_staked = db.users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$staked_amount"}}}
    ])
    total_staked = list(total_staked)
    total_staked_amount = total_staked[0]["total"] if total_staked else 0
    
    total_rewards = db.users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_rewards"}}}
    ])
    total_rewards = list(total_rewards)
    total_rewards_amount = total_rewards[0]["total"] if total_rewards else 0
    
    return {
        "total_users": total_users,
        "total_staked": total_staked_amount,
        "total_rewards_distributed": total_rewards_amount,
        "daily_apy": "30%"
    }
