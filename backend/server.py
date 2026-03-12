from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
import os
import logging
import uuid
import csv
import io
import requests as http_requests
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Object Storage ---
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "fx-trading-tracker"
storage_key = None

def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    resp = http_requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = http_requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    key = init_storage()
    resp = http_requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


# --- Pydantic Models ---
class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class DealCreate(BaseModel):
    transaction_type: str
    value_date: str
    deal_date: str
    transfer_type: str
    client_name: str
    from_type: str  # "bank" or "crypto"
    from_company: str
    from_bank: Optional[str] = ""
    from_account_num: Optional[str] = ""
    from_wallet_address: Optional[str] = ""
    to_type: str  # "bank" or "crypto"
    to_company: str
    to_bank: Optional[str] = ""
    to_account_num: Optional[str] = ""
    to_wallet_address: Optional[str] = ""
    ours_type: str  # "bank" or "crypto"
    ours_bank: Optional[str] = ""
    ours_account_num: Optional[str] = ""
    ours_wallet_address: Optional[str] = ""
    buy_currency: str
    sell_currency: str
    currency_amount: float
    amount: float
    rate: float
    remarks: Optional[str] = ""

class DealProcess(BaseModel):
    status: str
    treasury_remarks: str

class DealCancel(BaseModel):
    cancellation_reason: str

class ReferenceItemCreate(BaseModel):
    name: str
    code: str
    swift_code: Optional[str] = None
    type: Optional[str] = None
    symbol: Optional[str] = None

class ReferenceItemUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    swift_code: Optional[str] = None
    type: Optional[str] = None
    symbol: Optional[str] = None
    is_active: Optional[bool] = None


# --- Auth Helpers ---
def create_token(user_id: str, email: str, role: str, name: str):
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_role(user, roles):
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user

async def generate_deal_reference():
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    counter = await db.counters.find_one_and_update(
        {"name": "deal_ref", "date": today},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return f"FX-{today}-{counter['seq']:04d}"


# --- Audit Log Helper ---
async def log_audit(action: str, user: dict, entity_type: str, entity_id: str, entity_ref: str = "", details: str = "", metadata: dict = None):
    entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_ref": entity_ref,
        "user_id": user["id"],
        "user_name": user["name"],
        "user_role": user["role"],
        "details": details,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(entry)


# --- Auth Endpoints ---
@api_router.post("/auth/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email}, {"_id": 0})
    if not user or not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account disabled")
    token = create_token(user["id"], user["email"], user["role"], user["name"])
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    }

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return user


# --- User Management (Admin) ---
@api_router.get("/users")
async def list_users(user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.post("/users")
async def create_user(req: UserCreate, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "name": req.name,
        "password_hash": pwd_context.hash(req.password),
        "role": req.role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    await log_audit("user_created", user, "user", new_user["id"], new_user["email"], f"Created user {new_user['name']} ({new_user['role']})")
    return {"id": new_user["id"], "email": new_user["email"], "name": new_user["name"], "role": new_user["role"], "is_active": True}

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, req: UserUpdate, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if "password" in update_data:
        update_data["password_hash"] = pwd_context.hash(update_data.pop("password"))
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    await log_audit("user_updated", user, "user", user_id, updated.get("email", ""), f"Updated user fields: {', '.join(update_data.keys())}")
    return updated

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit("user_deleted", user, "user", user_id, target.get("email", "") if target else "", f"Deleted user")
    return {"message": "User deleted"}


# --- Deal Endpoints ---
@api_router.get("/deals/export")
async def export_deals_csv(
    status_filter: Optional[str] = Query(None, alias="status"),
    client: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    query = {}
    if user["role"] == "trader":
        query["created_by"] = user["id"]
    if status_filter:
        query["status"] = status_filter
    if client:
        query["client_name"] = {"$regex": client, "$options": "i"}
    if currency:
        query["$or"] = [{"buy_currency": currency}, {"sell_currency": currency}]
    if date_from:
        query.setdefault("deal_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("deal_date", {})["$lte"] = date_to
    deals = await db.deals.find(query, {"_id": 0}).sort("created_at", -1).to_list(100000)
    output = io.StringIO()
    fields = ["reference_number", "client_name", "transaction_type", "transfer_type", "deal_date", "value_date",
              "buy_currency", "sell_currency", "currency_amount", "rate", "amount",
              "from_type", "from_company", "from_bank", "from_account_num", "from_wallet_address",
              "to_type", "to_company", "to_bank", "to_account_num", "to_wallet_address",
              "ours_type", "ours_bank", "ours_account_num", "ours_wallet_address",
              "status", "remarks", "treasury_remarks", "cancellation_reason",
              "created_by_name", "processed_by_name", "processed_at", "created_at"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for d in deals:
        writer.writerow({f: d.get(f, "") for f in fields})
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=deals_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@api_router.get("/deals")
async def list_deals(
    status_filter: Optional[str] = Query(None, alias="status"),
    client: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    query = {}
    if user["role"] == "trader":
        query["created_by"] = user["id"]
    if status_filter:
        query["status"] = status_filter
    if client:
        query["client_name"] = {"$regex": client, "$options": "i"}
    if currency:
        query["$or"] = [{"buy_currency": currency}, {"sell_currency": currency}]
    if date_from:
        query.setdefault("deal_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("deal_date", {})["$lte"] = date_to
    deals = await db.deals.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    return deals

@api_router.post("/deals")
async def create_deal(req: DealCreate, user=Depends(get_current_user)):
    await require_role(user, ["trader"])
    ref = await generate_deal_reference()
    deal = {
        "id": str(uuid.uuid4()),
        "reference_number": ref,
        **req.model_dump(),
        "status": "pending",
        "treasury_remarks": "",
        "settlement_proofs": [],
        "created_by": user["id"],
        "created_by_name": user["name"],
        "processed_by": None,
        "processed_by_name": None,
        "processed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.insert_one(deal)
    deal.pop("_id", None)
    await log_audit("deal_created", user, "deal", deal["id"], ref, f"Created deal {ref} for {req.client_name} — {req.buy_currency}/{req.sell_currency} {req.currency_amount}")
    return deal

@api_router.get("/deals/{deal_id}")
async def get_deal(deal_id: str, user=Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if user["role"] == "trader" and deal["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return deal

@api_router.post("/deals/{deal_id}/upload")
async def upload_settlement_proof(deal_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG, WebP, GIF) are allowed")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/deals/{deal_id}/{uuid.uuid4().hex}.{ext}"
    try:
        put_object(path, data, file.content_type)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")
    proof = {"id": str(uuid.uuid4()), "path": path, "filename": file.filename, "content_type": file.content_type, "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": user["name"]}
    await db.deals.update_one({"id": deal_id}, {"$push": {"settlement_proofs": proof}})
    await log_audit("proof_uploaded", user, "deal", deal_id, deal.get("reference_number", ""), f"Uploaded settlement proof: {file.filename}")
    return proof

@api_router.get("/files/{path:path}")
async def get_file(path: str, user=Depends(get_current_user)):
    try:
        data, ct = get_object(path)
        return Response(content=data, media_type=ct)
    except Exception as e:
        logger.error(f"File fetch failed: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@api_router.delete("/deals/{deal_id}/proofs/{proof_id}")
async def delete_settlement_proof(deal_id: str, proof_id: str, user=Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    await db.deals.update_one({"id": deal_id}, {"$pull": {"settlement_proofs": {"id": proof_id}}})
    await log_audit("proof_deleted", user, "deal", deal_id, deal.get("reference_number", "") if deal else "", f"Deleted settlement proof")
    return {"message": "Proof deleted"}

@api_router.put("/deals/{deal_id}/process")
async def process_deal(deal_id: str, req: DealProcess, user=Depends(get_current_user)):
    await require_role(user, ["treasury"])
    if req.status not in ["confirmed", "returned"]:
        raise HTTPException(status_code=400, detail="Status must be 'confirmed' or 'returned'")
    if not req.treasury_remarks.strip():
        raise HTTPException(status_code=400, detail="Treasury remarks are required")
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if deal["status"] != "pending":
        raise HTTPException(status_code=400, detail="Deal already processed")
    update = {
        "status": req.status,
        "treasury_remarks": req.treasury_remarks,
        "processed_by": user["id"],
        "processed_by_name": user["name"],
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.update_one({"id": deal_id}, {"$set": update})
    updated = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    await log_audit(f"deal_{req.status}", user, "deal", deal_id, deal.get("reference_number", ""), f"Deal {req.status} — {req.treasury_remarks}")
    return updated

@api_router.put("/deals/{deal_id}/cancel")
async def cancel_deal(deal_id: str, req: DealCancel, user=Depends(get_current_user)):
    await require_role(user, ["trader"])
    if not req.cancellation_reason.strip():
        raise HTTPException(status_code=400, detail="Cancellation reason is required")
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if deal["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only cancel your own deals")
    if deal["status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending deals can be cancelled")
    update = {
        "status": "cancelled",
        "cancellation_reason": req.cancellation_reason,
        "cancelled_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.update_one({"id": deal_id}, {"$set": update})
    updated = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    await log_audit("deal_cancelled", user, "deal", deal_id, deal.get("reference_number", ""), f"Deal cancelled — {req.cancellation_reason}")
    return updated


# --- Reference Data ---
COLLECTION_MAP = {
    "companies": "companies",
    "banks": "banks",
    "transaction-types": "transaction_types",
    "transfer-types": "transfer_types",
    "currencies": "currencies"
}

def get_col(entity_type: str):
    if entity_type not in COLLECTION_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")
    return COLLECTION_MAP[entity_type]

@api_router.get("/reference/{entity_type}")
async def list_reference(entity_type: str, user=Depends(get_current_user)):
    col = get_col(entity_type)
    items = await db[col].find({}, {"_id": 0}).to_list(10000)
    return items

@api_router.post("/reference/{entity_type}")
async def create_reference(entity_type: str, req: ReferenceItemCreate, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    col = get_col(entity_type)
    item = {
        "id": str(uuid.uuid4()),
        "name": req.name,
        "code": req.code,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    if entity_type == "banks" and req.swift_code:
        item["swift_code"] = req.swift_code
    if entity_type == "currencies":
        item["type"] = req.type or "fiat"
        item["symbol"] = req.symbol or ""
    await db[col].insert_one(item)
    item.pop("_id", None)
    return item

@api_router.put("/reference/{entity_type}/{item_id}")
async def update_reference(entity_type: str, item_id: str, req: ReferenceItemUpdate, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    col = get_col(entity_type)
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db[col].update_one({"id": item_id}, {"$set": update_data})
    updated = await db[col].find_one({"id": item_id}, {"_id": 0})
    return updated

@api_router.delete("/reference/{entity_type}/{item_id}")
async def delete_reference(entity_type: str, item_id: str, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    col = get_col(entity_type)
    result = await db[col].delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}


# --- Audit Logs ---
@api_router.get("/audit-logs")
async def list_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user)
):
    await require_role(user, ["admin"])
    query = {}
    if action:
        query["action"] = action
    if entity_type:
        query["entity_type"] = entity_type
    if user_name:
        query["user_name"] = {"$regex": user_name, "$options": "i"}
    if date_from:
        query.setdefault("created_at", {})["$gte"] = date_from
    if date_to:
        query.setdefault("created_at", {})["$lte"] = date_to + "T23:59:59"
    total = await db.audit_logs.count_documents(query)
    skip = (page - 1) * limit
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"logs": logs, "total": total, "page": page, "pages": (total + limit - 1) // limit if total > 0 else 1}


# --- Dashboard ---
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(date_range: str = Query("30d", alias="range"), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    start_date = None
    if date_range == "7d":
        start_date = (now - timedelta(days=7)).isoformat()
    elif date_range == "30d":
        start_date = (now - timedelta(days=30)).isoformat()
    elif date_range == "ytd":
        start_date = datetime(now.year, 1, 1, tzinfo=timezone.utc).isoformat()

    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if user["role"] == "trader":
        query["created_by"] = user["id"]

    deals = await db.deals.find(query, {"_id": 0}).to_list(100000)

    total = len(deals)
    pending = sum(1 for d in deals if d["status"] == "pending")
    confirmed = sum(1 for d in deals if d["status"] == "confirmed")
    returned = sum(1 for d in deals if d["status"] == "returned")
    cancelled = sum(1 for d in deals if d["status"] == "cancelled")
    total_volume = sum(float(d.get("amount", 0)) for d in deals)

    deals_by_date = {}
    for d in deals:
        date_key = d["created_at"][:10]
        if date_key not in deals_by_date:
            deals_by_date[date_key] = {"date": date_key, "count": 0, "volume": 0}
        deals_by_date[date_key]["count"] += 1
        deals_by_date[date_key]["volume"] += float(d.get("amount", 0))

    deals_by_currency = {}
    for d in deals:
        pair = f"{d.get('buy_currency', '')}/{d.get('sell_currency', '')}"
        if pair not in deals_by_currency:
            deals_by_currency[pair] = {"pair": pair, "count": 0, "volume": 0}
        deals_by_currency[pair]["count"] += 1
        deals_by_currency[pair]["volume"] += float(d.get("amount", 0))

    recent = sorted(deals, key=lambda x: x["created_at"], reverse=True)[:10]

    stats = {
        "total_deals": total,
        "pending_deals": pending,
        "confirmed_deals": confirmed,
        "returned_deals": returned,
        "cancelled_deals": cancelled,
        "total_volume": total_volume,
        "deals_by_date": sorted(deals_by_date.values(), key=lambda x: x["date"]),
        "deals_by_currency": sorted(deals_by_currency.values(), key=lambda x: x["volume"], reverse=True)[:10],
        "recent_deals": recent
    }

    if user["role"] == "admin":
        stats["total_users"] = await db.users.count_documents({})

    return stats


# --- Seed Data ---
async def seed_data():
    # Default users
    if not await db.users.find_one({"role": "admin"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "admin@fxtracker.com", "name": "System Admin",
            "password_hash": pwd_context.hash("Admin@123"), "role": "admin",
            "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Created default admin user")

    if not await db.users.find_one({"role": "trader"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "trader@fxtracker.com", "name": "John Trader",
            "password_hash": pwd_context.hash("Trader@123"), "role": "trader",
            "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
        })

    if not await db.users.find_one({"role": "treasury"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "treasury@fxtracker.com", "name": "Jane Treasury",
            "password_hash": pwd_context.hash("Treasury@123"), "role": "treasury",
            "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
        })

    # Currencies
    if await db.currencies.count_documents({}) == 0:
        fiat = [
            ("USD", "US Dollar", "$"), ("EUR", "Euro", "E"), ("GBP", "British Pound", "L"),
            ("JPY", "Japanese Yen", "Y"), ("CHF", "Swiss Franc", "CHF"), ("AUD", "Australian Dollar", "A$"),
            ("CAD", "Canadian Dollar", "C$"), ("NZD", "New Zealand Dollar", "NZ$"),
            ("SEK", "Swedish Krona", "kr"), ("NOK", "Norwegian Krone", "kr"),
            ("DKK", "Danish Krone", "kr"), ("SGD", "Singapore Dollar", "S$"),
            ("HKD", "Hong Kong Dollar", "HK$"), ("KRW", "South Korean Won", "W"),
            ("CNY", "Chinese Yuan", "Y"), ("INR", "Indian Rupee", "Rs"),
            ("MXN", "Mexican Peso", "$"), ("BRL", "Brazilian Real", "R$"),
            ("ZAR", "South African Rand", "R"), ("THB", "Thai Baht", "B"),
            ("PHP", "Philippine Peso", "P"), ("IDR", "Indonesian Rupiah", "Rp"),
            ("MYR", "Malaysian Ringgit", "RM"), ("TWD", "Taiwan Dollar", "NT$"),
            ("AED", "UAE Dirham", "AED"), ("SAR", "Saudi Riyal", "SAR"),
            ("TRY", "Turkish Lira", "TL"), ("PLN", "Polish Zloty", "zl"),
            ("CZK", "Czech Koruna", "CZK"), ("HUF", "Hungarian Forint", "Ft"),
            ("RUB", "Russian Ruble", "RUB")
        ]
        stablecoin = [
            ("USDT", "Tether", "USDT"), ("USDC", "USD Coin", "USDC"),
            ("DAI", "Dai", "DAI"), ("BUSD", "Binance USD", "BUSD"),
            ("TUSD", "TrueUSD", "TUSD"), ("FRAX", "Frax", "FRAX"),
            ("LUSD", "Liquity USD", "LUSD"), ("GUSD", "Gemini Dollar", "GUSD"),
            ("USDP", "Pax Dollar", "USDP"), ("PYUSD", "PayPal USD", "PYUSD"),
            ("FDUSD", "First Digital USD", "FDUSD"), ("USDD", "USDD", "USDD"),
            ("cUSD", "Celo Dollar", "cUSD"), ("sUSD", "Synthetix USD", "sUSD"),
            ("EURT", "Tether Euro", "EURT"), ("XSGD", "StraitsX SGD", "XSGD")
        ]
        crypto = [
            ("BTC", "Bitcoin", "BTC"), ("ETH", "Ethereum", "ETH"),
            ("BNB", "Binance Coin", "BNB"), ("XRP", "Ripple", "XRP"),
            ("ADA", "Cardano", "ADA"), ("SOL", "Solana", "SOL"),
            ("DOGE", "Dogecoin", "DOGE"), ("DOT", "Polkadot", "DOT"),
            ("AVAX", "Avalanche", "AVAX"), ("MATIC", "Polygon", "MATIC"),
            ("LINK", "Chainlink", "LINK"), ("UNI", "Uniswap", "UNI"),
            ("LTC", "Litecoin", "LTC"), ("ATOM", "Cosmos", "ATOM"),
            ("NEAR", "NEAR Protocol", "NEAR"), ("APT", "Aptos", "APT"),
            ("ARB", "Arbitrum", "ARB"), ("OP", "Optimism", "OP")
        ]
        currencies = []
        for code, name, symbol in fiat:
            currencies.append({"id": str(uuid.uuid4()), "code": code, "name": name, "type": "fiat", "symbol": symbol, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()})
        for code, name, symbol in stablecoin:
            currencies.append({"id": str(uuid.uuid4()), "code": code, "name": name, "type": "stablecoin", "symbol": symbol, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()})
        for code, name, symbol in crypto:
            currencies.append({"id": str(uuid.uuid4()), "code": code, "name": name, "type": "crypto", "symbol": symbol, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()})
        await db.currencies.insert_many(currencies)
        logger.info(f"Seeded {len(currencies)} currencies")

    # Transaction types - always reseed with correct values
    existing_tx = await db.transaction_types.find_one({"name": "Today"})
    if not existing_tx:
        await db.transaction_types.delete_many({})
        types = [("Today", "TODAY"), ("Tomorrow", "TOM"), ("Spot", "SPOT")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c in types]
        await db.transaction_types.insert_many(docs)
        logger.info("Reseeded transaction types")

    # Transfer types - always reseed with correct values
    existing_tf = await db.transfer_types.find_one({"name": "FX Crypto Conversion"})
    if not existing_tf:
        await db.transfer_types.delete_many({})
        types = [("FX Crypto Conversion", "FX_CRYPTO"), ("FX Local", "FX_LOCAL"), ("PDAX Withdrawal", "PDAX_WD")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c in types]
        await db.transfer_types.insert_many(docs)
        logger.info("Reseeded transfer types")

    # Companies
    if await db.companies.count_documents({}) == 0:
        companies = [("Acme Corporation", "ACME"), ("GlobalTech Inc", "GTECH"), ("Pacific Trading Co", "PACIFIC"), ("Sterling Enterprises", "STERL"), ("Atlantic Financial Group", "AFG")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c in companies]
        await db.companies.insert_many(docs)

    # Banks
    if await db.banks.count_documents({}) == 0:
        banks = [("JP Morgan Chase", "JPMC", "CHASUS33"), ("Citibank", "CITI", "CITIUS33"), ("HSBC", "HSBC", "HSBCGB2L"), ("Deutsche Bank", "DB", "DEUTDEFF"), ("Standard Chartered", "SCB", "SCBLSGSG"), ("Bank of America", "BAC", "BOFAUS3N")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "swift_code": s, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c, s in banks]
        await db.banks.insert_many(docs)

    logger.info("Seed data complete")


@app.on_event("startup")
async def startup():
    await seed_data()

@api_router.get("/")
async def root():
    return {"message": "FX Trading Tracker API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
