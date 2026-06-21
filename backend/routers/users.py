import hashlib
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random
import re
from models.firebase_admin import get_db
import firebase_admin.auth

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    idToken: str


# Password hashing utilities using PBKDF2
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    db_password = salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return db_password.hex()

def verify_password(stored_password_hex: str, password: str) -> bool:
    try:
        stored_bytes = bytes.fromhex(stored_password_hex)
        salt = stored_bytes[:16]
        stored_hash = stored_bytes[16:]
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return new_hash == stored_hash
    except Exception:
        return False

# In-memory database fallback when Firestore is not available
MOCK_USERS = {
    "demo-user-123": {
        "uid": "demo-user-123",
        "displayName": "Alex Rivera",
        "email": "alex@ecotrace.org",
        "eco_level": 24,
        "eco_title": "Eco-Warrior",
        "total_co2_saved_kg": 420.5,
        "current_streak_days": 15,
        "avatar_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuBTKipwUhnqDPmF0sg8cjq3Pt1GuNLxIewKESrdlF0otVZ-Upx1c28DDSCht2dbkhgQl-1KVFLOEIG1EUV_swxFj89a9VGDYGpkbwTsQVoI2lYdff0e6YaW8e5WNaK7BbyninFsx8DT9eGK-BHs8aeu_R-RPZHsTm7coJm8kDUSwdj035iHYw4-CSDXdnpWodVnQdWQWyy0kIshYWUltWhnTR-1Y85XO8FFAWQp1cMPE-OgaqZtD1Re_dWYBGukDTBN-0vwVNsZtGJO",
        "badges_earned": [1, 2, 3, 4, 5, 6, 7, 8],
        "impact_id": "#ET-8829-XR",
        "trace_balance": 4850,
        "password_hash": "" # Dynamic init below
    }
}

# Deterministic hash for demo user so they can log in using password: demo123
demo_salt = b'\x00' * 16
demo_hash = demo_salt + hashlib.pbkdf2_hmac('sha256', b"demo123", demo_salt, 100000)
MOCK_USERS["demo-user-123"]["password_hash"] = demo_hash.hex()

DEFAULT_AVATAR = "https://lh3.googleusercontent.com/aida-public/AB6AXuAmbxBDuQgQ_juwISAMZ3VKBA0Ul3r4KzOGEnkY9NvCW3R-C-Yrc69icQvwjYdEPmqsP1oH69e35PqH_pl9wqZmeGyTEwtOMYQx_5yjAu2J7pid98PJcc_A9PjwSxhRH_0GBvsoGw89CFlTx0Q-b52Y-HcBHFL_mjyTP2vU-R0-WenWvVliiuq5g36wJZYSeFhEfg43-cOnmL0u-1inxvHwHiEEbRf5NeIuip7EjKMEQcRc0EwtA8zjnDXZKtGw-YGq32S_zLDZS71t"

class LoginRequest(BaseModel):
    email: str
    password: str
    fullName: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    displayName: str
    email: str
    avatar_url: Optional[str] = None

class RedeemRequest(BaseModel):
    cost: int
    rewardName: str

class AddTraceRequest(BaseModel):
    amount: int

def _db_available() -> bool:
    return get_db() is not None

def clean_uid(email: str) -> str:
    # Clean email to make a valid document ID
    uid = re.sub(r'[^a-zA-Z0-9-]', '-', email.lower())
    return uid.strip("-")

def generate_impact_id(name: str) -> str:
    # e.g., #ET-8829-XR
    prefix = "".join([c.upper() for c in name if c.isalpha()][:2])
    if len(prefix) < 2:
        prefix = "XX"
    num = random.randint(1000, 9999)
    return f"#ET-{num}-{prefix}"

@router.post("/signup")
async def signup_user(req: LoginRequest):
    uid = clean_uid(req.email)
    hashed = hash_password(req.password)
    name = req.fullName if req.fullName else req.email.split("@")[0].capitalize()
    
    user_data = {
        "uid": uid,
        "displayName": name,
        "email": req.email.lower(),
        "password_hash": hashed,
        "eco_level": 1,
        "eco_title": "Eco Enthusiast",
        "total_co2_saved_kg": 0.0,
        "current_streak_days": 1,
        "avatar_url": DEFAULT_AVATAR,
        "badges_earned": [1],
        "impact_id": generate_impact_id(name),
        "trace_balance": 4850
    }
    
    if _db_available():
        db = get_db()
        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            raise HTTPException(status_code=400, detail="Account already exists. Please log in.")
        doc_ref.set(user_data)
    else:
        if uid in MOCK_USERS:
            raise HTTPException(status_code=400, detail="Account already exists. Please log in.")
        MOCK_USERS[uid] = user_data
        
    ret = user_data.copy()
    ret.pop("password_hash", None)
    return ret

@router.post("/login")
async def login_user(req: LoginRequest):
    uid = clean_uid(req.email)
    
    user_data = None
    if _db_available():
        db = get_db()
        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
    else:
        if uid in MOCK_USERS:
            user_data = MOCK_USERS[uid]
            
    if not user_data:
        # Check if demo-user-123 needs auto-initialization in database
        if uid == "demo-user-123":
            demo_data = MOCK_USERS["demo-user-123"].copy()
            if _db_available():
                db = get_db()
                db.collection("users").document(uid).set(demo_data)
            user_data = demo_data
        elif req.password == "google-oauth-mock-pass":
            # Auto-register google user
            name = req.fullName if req.fullName else req.email.split("@")[0].capitalize()
            user_data = {
                "uid": uid,
                "displayName": name,
                "email": req.email.lower(),
                "password_hash": hash_password(req.password),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": 0.0,
                "current_streak_days": 1,
                "avatar_url": DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(name),
                "trace_balance": 4850
            }
            if _db_available():
                db = get_db()
                db.collection("users").document(uid).set(user_data)
            else:
                MOCK_USERS[uid] = user_data
        else:
            raise HTTPException(status_code=404, detail="No account found with this email. Please register first.")
            
    # Verify password
    stored_hash = user_data.get("password_hash")
    if not stored_hash:
        # If user exists but has no password (e.g. from Google or legacy), set this password
        stored_hash = hash_password(req.password)
        if _db_available():
            db = get_db()
            db.collection("users").document(uid).update({"password_hash": stored_hash})
        else:
            MOCK_USERS[uid]["password_hash"] = stored_hash
    elif not verify_password(stored_hash, req.password):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
        
    ret = user_data.copy()
    ret.pop("password_hash", None)
    return ret

@router.post("/google-login")
async def google_login(req: GoogleLoginRequest):
    try:
        decoded_token = firebase_admin.auth.verify_id_token(req.idToken)
        
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Token does not contain an email address.")
            
        name = decoded_token.get("name") or email.split("@")[0].capitalize()
        avatar_url = decoded_token.get("picture") or DEFAULT_AVATAR
        uid = clean_uid(email)
        
        user_data = None
        if _db_available():
            db = get_db()
            doc_ref = db.collection("users").document(uid)
            doc = doc_ref.get()
            if doc.exists:
                user_data = doc.to_dict()
        else:
            if uid in MOCK_USERS:
                user_data = MOCK_USERS[uid]
                
        if not user_data:
            # Auto-register google user
            user_data = {
                "uid": uid,
                "displayName": name,
                "email": email.lower(),
                "password_hash": "", # Google login has no local password hash
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": 0.0,
                "current_streak_days": 1,
                "avatar_url": avatar_url,
                "badges_earned": [1],
                "impact_id": generate_impact_id(name),
                "trace_balance": 4850
            }
            if _db_available():
                db = get_db()
                db.collection("users").document(uid).set(user_data)
            else:
                MOCK_USERS[uid] = user_data
        else:
            # Update user profile picture if changed
            if avatar_url and user_data.get("avatar_url") == DEFAULT_AVATAR:
                user_data["avatar_url"] = avatar_url
                if _db_available():
                    db = get_db()
                    db.collection("users").document(uid).update({"avatar_url": avatar_url})
                else:
                    MOCK_USERS[uid]["avatar_url"] = avatar_url
                
        ret = user_data.copy()
        ret.pop("password_hash", None)
        return ret
        
    except (firebase_admin.auth.InvalidIdTokenError, firebase_admin.auth.ExpiredIdTokenError,
            firebase_admin.auth.RevokedIdTokenError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid Firebase ID Token: {str(e)}")

@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    if _db_available():
        db = get_db()
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            name = user_id.split("-")[0].capitalize()
            email = user_id.replace("-", "@")
            if "@" not in email:
                email = f"{user_id}@ecotrace.org"
            
            user_data = {
                "uid": user_id,
                "displayName": name,
                "email": email.lower(),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": 0.0,
                "current_streak_days": 1,
                "avatar_url": DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(name),
                "trace_balance": 4850
            }
            doc_ref.set(user_data)
            return user_data
    else:
        if user_id in MOCK_USERS:
            return MOCK_USERS[user_id]
        else:
            name = user_id.split("-")[0].capitalize()
            email = user_id.replace("-", "@")
            if "@" not in email:
                email = f"{user_id}@ecotrace.org"
                
            user_data = {
                "uid": user_id,
                "displayName": name,
                "email": email.lower(),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": 0.0,
                "current_streak_days": 1,
                "avatar_url": DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(name),
                "trace_balance": 4850
            }
            MOCK_USERS[user_id] = user_data
            return user_data

@router.put("/profile/{user_id}")
async def update_profile(user_id: str, req: ProfileUpdateRequest):
    if _db_available():
        db = get_db()
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        
        update_data = {
            "displayName": req.displayName,
            "email": req.email.lower()
        }
        if req.avatar_url:
            update_data["avatar_url"] = req.avatar_url
            
        if not doc.exists:
            user_data = {
                "uid": user_id,
                "displayName": req.displayName,
                "email": req.email.lower(),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": 0.0,
                "current_streak_days": 1,
                "avatar_url": req.avatar_url if req.avatar_url else DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(req.displayName),
                "trace_balance": 4850
            }
            doc_ref.set(user_data)
            return {"status": "success", "user": user_data}
            
        doc_ref.update(update_data)
        return {"status": "success", "user": {**doc.to_dict(), **update_data}}
    else:
        if user_id not in MOCK_USERS:
            MOCK_USERS[user_id] = {
                "uid": user_id,
                "displayName": req.displayName,
                "email": req.email.lower(),
                "eco_level": 1,
                "eco_title": "Eco Enthusiast",
                "total_co2_saved_kg": 0.0,
                "current_streak_days": 1,
                "avatar_url": req.avatar_url if req.avatar_url else DEFAULT_AVATAR,
                "badges_earned": [1],
                "impact_id": generate_impact_id(req.displayName),
                "trace_balance": 4850
            }
        else:
            MOCK_USERS[user_id]["displayName"] = req.displayName
            MOCK_USERS[user_id]["email"] = req.email.lower()
            if req.avatar_url:
                MOCK_USERS[user_id]["avatar_url"] = req.avatar_url
            
        return {"status": "success", "user": MOCK_USERS[user_id]}

@router.post("/profile/{user_id}/redeem")
async def redeem_reward(user_id: str, req: RedeemRequest):
    if _db_available():
        db = get_db()
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = doc.to_dict()
        current_balance = user_data.get("trace_balance", 4850)
        
        if current_balance < req.cost:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. You need {req.cost - current_balance} more $TRACE.")
            
        new_balance = current_balance - req.cost
        doc_ref.update({"trace_balance": new_balance})
        return {"status": "success", "new_balance": new_balance, "message": f"Successfully redeemed: {req.rewardName}!"}
    else:
        if user_id not in MOCK_USERS:
            if user_id == "demo-user-123":
                MOCK_USERS[user_id] = MOCK_USERS["demo-user-123"].copy()
            else:
                raise HTTPException(status_code=404, detail="User not found")
                
        user_data = MOCK_USERS[user_id]
        current_balance = user_data.get("trace_balance", 4850)
        
        if current_balance < req.cost:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. You need {req.cost - current_balance} more $TRACE.")
            
        new_balance = current_balance - req.cost
        MOCK_USERS[user_id]["trace_balance"] = new_balance
        return {"status": "success", "new_balance": new_balance, "message": f"Successfully redeemed: {req.rewardName}!"}

@router.post("/profile/{user_id}/add_trace")
async def add_trace_balance(user_id: str, req: AddTraceRequest):
    if _db_available():
        db = get_db()
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = doc.to_dict()
        current_balance = user_data.get("trace_balance", 4850)
        new_balance = current_balance + req.amount
        doc_ref.update({"trace_balance": new_balance})
        return {"status": "success", "new_balance": new_balance, "message": f"Successfully credited {req.amount} $TRACE!"}
    else:
        if user_id not in MOCK_USERS:
            raise HTTPException(status_code=404, detail="User not found")
        current_balance = MOCK_USERS[user_id].get("trace_balance", 4850)
        new_balance = current_balance + req.amount
        MOCK_USERS[user_id]["trace_balance"] = new_balance
        return {"status": "success", "new_balance": new_balance, "message": f"Successfully credited {req.amount} $TRACE!"}
