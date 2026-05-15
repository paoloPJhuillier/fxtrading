from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import uuid
import csv
import io
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database is initialized asynchronously in startup event
db = None

JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Object Storage (switchable via STORAGE_TYPE env var) ---
from services.storage import get_storage
# --- Database (switchable via DB_TYPE env var: mongodb | couchbase) ---
from services.database import get_database

APP_NAME = os.environ.get("APP_NAME", "fx-trading-tracker")


# --- Pydantic Models ---
class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

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
    to_type: Optional[str] = "bank"  # "bank" or "crypto"
    to_company: Optional[str] = ""
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

class BankAccountCreate(BaseModel):
    account_number: str
    account_name: Optional[str] = ""

class BankAccountUpdate(BaseModel):
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    is_active: Optional[bool] = None

class DealEdit(BaseModel):
    transaction_type: Optional[str] = None
    value_date: Optional[str] = None
    deal_date: Optional[str] = None
    transfer_type: Optional[str] = None
    client_name: Optional[str] = None
    from_type: Optional[str] = None
    from_company: Optional[str] = None
    from_bank: Optional[str] = None
    from_account_num: Optional[str] = None
    from_wallet_address: Optional[str] = None
    to_type: Optional[str] = None
    to_company: Optional[str] = None
    to_bank: Optional[str] = None
    to_account_num: Optional[str] = None
    to_wallet_address: Optional[str] = None
    ours_type: Optional[str] = None
    ours_bank: Optional[str] = None
    ours_account_num: Optional[str] = None
    ours_wallet_address: Optional[str] = None
    buy_currency: Optional[str] = None
    sell_currency: Optional[str] = None
    currency_amount: Optional[float] = None
    amount: Optional[float] = None
    rate: Optional[float] = None
    remarks: Optional[str] = None


# --- Auth Helpers ---
def user_full_name(user: dict) -> str:
    fn = user.get("first_name", "")
    ln = user.get("last_name", "")
    if fn or ln:
        return f"{fn} {ln}".strip()
    return user.get("name", "")

def create_token(user_id: str, email: str, role: str, first_name: str, last_name: str):
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "first_name": first_name,
        "last_name": last_name,
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
        # Ensure first_name/last_name exist (backward compat with legacy 'name' field)
        if "first_name" not in user:
            parts = (user.get("name", "")).split(" ", 1)
            user["first_name"] = parts[0] if parts else ""
            user["last_name"] = parts[1] if len(parts) > 1 else ""
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
        return_document=True
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
        "user_name": user_full_name(user),
        "user_role": user["role"],
        "details": details,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(entry)

async def record_deal_history(deal_id: str, action: str, user: dict, changes: list = None, remarks: str = ""):
    entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "user_name": user_full_name(user),
        "user_role": user["role"],
        "changes": changes or [],
        "remarks": remarks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.update_one({"id": deal_id}, {"$push": {"history": entry}})

def compute_changes(old_deal: dict, new_fields: dict) -> list:
    changes = []
    skip = {"_id", "id", "history", "settlement_proofs", "updated_at", "created_at"}
    for k, v in new_fields.items():
        if k in skip:
            continue
        old_val = old_deal.get(k)
        if old_val != v and v is not None:
            changes.append({"field": k, "old_value": str(old_val) if old_val is not None else "", "new_value": str(v)})
    return changes


# --- Auth Endpoints ---
@api_router.post("/auth/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email}, {"_id": 0})
    if not user or not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account disabled")
    fn = user.get("first_name", "")
    ln = user.get("last_name", "")
    token = create_token(user["id"], user["email"], user["role"], fn, ln)
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "first_name": fn, "last_name": ln, "role": user["role"]}
    }

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {"id": user.get("id"), "email": user.get("email"), "first_name": user.get("first_name", ""), "last_name": user.get("last_name", ""), "role": user.get("role")}

@api_router.put("/auth/change-password")
async def change_password(req: ChangePasswordRequest, user=Depends(get_current_user)):
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user or not pwd_context.verify(req.current_password, full_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": pwd_context.hash(req.new_password)}})
    await log_audit("password_changed", user, "user", user["id"], user.get("email", ""), "User changed their password")
    return {"message": "Password changed successfully"}


# --- User Management (Admin) ---
@api_router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    await require_role(user, ["admin"])
    query = {}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    total = await db.users.count_documents(query)
    skip = (page - 1) * limit
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).skip(skip).limit(limit).to_list(limit)
    return {"users": users, "total": total, "page": page, "pages": (total + limit - 1) // limit if total > 0 else 1}

@api_router.post("/users")
async def create_user(req: UserCreate, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "first_name": req.first_name,
        "last_name": req.last_name,
        "password_hash": pwd_context.hash(req.password),
        "role": req.role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    full_name = f"{req.first_name} {req.last_name}".strip()
    await log_audit("user_created", user, "user", new_user["id"], new_user["email"], f"Created user {full_name} ({new_user['role']})")
    return {"id": new_user["id"], "email": new_user["email"], "first_name": new_user["first_name"], "last_name": new_user["last_name"], "role": new_user["role"], "is_active": True}

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
    deals = await db.deals.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
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
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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
    total = await db.deals.count_documents(query)
    skip = (page - 1) * limit
    list_projection = {"_id": 0, "id": 1, "reference_number": 1, "client_name": 1, "transaction_type": 1, "transfer_type": 1, "buy_currency": 1, "sell_currency": 1, "currency_amount": 1, "amount": 1, "rate": 1, "deal_date": 1, "value_date": 1, "status": 1, "created_at": 1, "created_by_name": 1, "from_type": 1, "from_company": 1, "from_bank": 1, "from_account_num": 1, "from_wallet_address": 1, "to_type": 1, "to_company": 1, "to_bank": 1, "to_account_num": 1, "to_wallet_address": 1, "ours_type": 1, "ours_bank": 1, "ours_account_num": 1, "ours_wallet_address": 1, "remarks": 1, "treasury_remarks": 1, "cancellation_reason": 1, "processed_by_name": 1, "processed_at": 1, "settlement_proofs": 1, "history": 1}
    deals = await db.deals.find(query, list_projection).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"deals": deals, "total": total, "page": page, "pages": (total + limit - 1) // limit if total > 0 else 1}

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
        "history": [],
        "created_by": user["id"],
        "created_by_name": user_full_name(user),
        "processed_by": None,
        "processed_by_name": None,
        "processed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.insert_one(deal)
    deal.pop("_id", None)
    await record_deal_history(deal["id"], "created", user, remarks=f"Deal ticket created — {req.buy_currency}/{req.sell_currency} {req.currency_amount}")
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
async def upload_settlement_proof(deal_id: str, file: UploadFile = File(...), proof_type: str = Query("client", regex="^(client|processor)$"), user=Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    allowed = ["image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG, WebP, GIF) and PDF are allowed")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/deals/{deal_id}/{uuid.uuid4().hex}.{ext}"
    try:
        get_storage().put_object(path, data, file.content_type)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")
    proof = {"id": str(uuid.uuid4()), "path": path, "filename": file.filename, "content_type": file.content_type, "proof_type": proof_type, "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": user_full_name(user)}
    await db.deals.update_one({"id": deal_id}, {"$push": {"settlement_proofs": proof}})
    await record_deal_history(deal_id, "proof_uploaded", user, remarks=f"Uploaded {proof_type} settlement proof: {file.filename}")
    await log_audit("proof_uploaded", user, "deal", deal_id, deal.get("reference_number", ""), f"Uploaded {proof_type} settlement proof: {file.filename}")
    return proof

@api_router.get("/files/{path:path}")
async def get_file(path: str):
    try:
        data, ct = get_storage().get_object(path)
        return Response(content=data, media_type=ct)
    except Exception as e:
        logger.error(f"File fetch failed: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@api_router.delete("/deals/{deal_id}/proofs/{proof_id}")
async def delete_settlement_proof(deal_id: str, proof_id: str, user=Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    # Find the proof to get its storage path before removing
    proof_to_delete = next((p for p in deal.get("settlement_proofs", []) if p["id"] == proof_id), None)
    if proof_to_delete and proof_to_delete.get("path"):
        get_storage().delete_object(proof_to_delete["path"])
    await db.deals.update_one({"id": deal_id}, {"$pull": {"settlement_proofs": {"id": proof_id}}})
    await log_audit("proof_deleted", user, "deal", deal_id, deal.get("reference_number", ""), f"Deleted settlement proof")
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
        "processed_by_name": user_full_name(user),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.update_one({"id": deal_id}, {"$set": update})
    changes = [{"field": "status", "old_value": "pending", "new_value": req.status}]
    await record_deal_history(deal_id, f"deal_{req.status}", user, changes, req.treasury_remarks)
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
    changes = [{"field": "status", "old_value": "pending", "new_value": "cancelled"}]
    await record_deal_history(deal_id, "deal_cancelled", user, changes, req.cancellation_reason)
    updated = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    await log_audit("deal_cancelled", user, "deal", deal_id, deal.get("reference_number", ""), f"Deal cancelled — {req.cancellation_reason}")
    return updated

@api_router.put("/deals/{deal_id}/resubmit")
async def resubmit_deal(deal_id: str, user=Depends(get_current_user)):
    await require_role(user, ["trader"])
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if deal["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only resubmit your own deals")
    if deal["status"] != "returned":
        raise HTTPException(status_code=400, detail="Only returned deals can be resubmitted")
    update = {
        "status": "pending",
        "treasury_remarks": "",
        "processed_by": None,
        "processed_by_name": None,
        "processed_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.update_one({"id": deal_id}, {"$set": update})
    changes = [{"field": "status", "old_value": "returned", "new_value": "pending"}]
    await record_deal_history(deal_id, "deal_resubmitted", user, changes, "Deal resubmitted after return")
    updated = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    await log_audit("deal_resubmitted", user, "deal", deal_id, deal.get("reference_number", ""), f"Deal resubmitted after return")
    return updated

@api_router.put("/deals/{deal_id}/edit")
async def edit_deal(deal_id: str, req: DealEdit, user=Depends(get_current_user)):
    await require_role(user, ["trader"])
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if deal["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own deals")
    if deal["status"] != "returned":
        raise HTTPException(status_code=400, detail="Only returned deals can be edited")
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    changes = compute_changes(deal, update_data)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.deals.update_one({"id": deal_id}, {"$set": update_data})
    if changes:
        change_summary = ", ".join([f"{c['field']}: {c['old_value']} → {c['new_value']}" for c in changes[:5]])
        await record_deal_history(deal_id, "deal_edited", user, changes, f"Fields updated: {change_summary}")
        await log_audit("deal_edited", user, "deal", deal_id, deal.get("reference_number", ""), f"Deal edited — {change_summary}")
    updated = await db.deals.find_one({"id": deal_id}, {"_id": 0})
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
    items = await db[col].find({}, {"_id": 0}).to_list(1000)
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

# --- Bank Accounts ---
@api_router.get("/reference/banks/{bank_id}/accounts")
async def list_bank_accounts(bank_id: str, user=Depends(get_current_user)):
    accounts = await db.bank_accounts.find({"bank_id": bank_id}, {"_id": 0}).to_list(500)
    return accounts

@api_router.post("/reference/banks/{bank_id}/accounts")
async def create_bank_account(bank_id: str, req: BankAccountCreate, user=Depends(get_current_user)):
    bank = await db.banks.find_one({"id": bank_id}, {"_id": 0})
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    account = {
        "id": str(uuid.uuid4()),
        "bank_id": bank_id,
        "account_number": req.account_number,
        "account_name": req.account_name or "",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.bank_accounts.insert_one(account)
    account.pop("_id", None)
    await log_audit("bank_account_created", user, "bank_account", account["id"], req.account_number, f"Added account {req.account_number} to bank {bank['name']}")
    return account

@api_router.put("/reference/banks/{bank_id}/accounts/{account_id}")
async def update_bank_account(bank_id: str, account_id: str, req: BankAccountUpdate, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.bank_accounts.update_one({"id": account_id, "bank_id": bank_id}, {"$set": update_data})
    updated = await db.bank_accounts.find_one({"id": account_id}, {"_id": 0})
    return updated

@api_router.delete("/reference/banks/{bank_id}/accounts/{account_id}")
async def delete_bank_account(bank_id: str, account_id: str, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    result = await db.bank_accounts.delete_one({"id": account_id, "bank_id": bank_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted"}


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
    if date_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif date_range == "yesterday":
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif date_range == "7d":
        start_date = (now - timedelta(days=7)).isoformat()
    elif date_range == "30d":
        start_date = (now - timedelta(days=30)).isoformat()
    elif date_range == "ytd":
        start_date = datetime(now.year, 1, 1, tzinfo=timezone.utc).isoformat()

    match = {}
    if start_date:
        match["created_at"] = {"$gte": start_date}
    if date_range == "yesterday":
        match.setdefault("created_at", {})["$lt"] = end_date
    if user["role"] == "trader":
        match["created_by"] = user["id"]

    pipeline = [
        {"$match": match},
        {"$facet": {
            "counts": [{"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "volume": {"$sum": {"$toDouble": {"$ifNull": ["$amount", "0"]}}}
            }}],
            "by_date": [{"$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},
                "count": {"$sum": 1},
                "volume": {"$sum": {"$toDouble": {"$ifNull": ["$amount", "0"]}}}
            }}, {"$sort": {"_id": 1}}],
            "recent": [{"$sort": {"created_at": -1}}, {"$limit": 10}, {"$project": {"_id": 0}}]
        }}
    ]

    result = await db.deals.aggregate(pipeline).to_list(1)
    facets = result[0] if result else {"counts": [], "by_date": [], "recent": []}

    status_map = {}
    total_volume = 0
    total_deals = 0
    for c in facets["counts"]:
        status_map[c["_id"]] = c["count"]
        total_volume += c["volume"]
        total_deals += c["count"]

    deals_by_date = [{"date": d["_id"], "count": d["count"], "volume": d["volume"]} for d in facets["by_date"]]

    stats = {
        "total_deals": total_deals,
        "pending_deals": status_map.get("pending", 0),
        "confirmed_deals": status_map.get("confirmed", 0),
        "returned_deals": status_map.get("returned", 0),
        "cancelled_deals": status_map.get("cancelled", 0),
        "total_volume": total_volume,
        "deals_by_date": deals_by_date,
        "deals_by_currency": [],
        "recent_deals": facets["recent"]
    }

    if user["role"] == "admin":
        stats["total_users"] = await db.users.count_documents({})

    return stats


# --- Seed Data ---
async def seed_data():
    # Migrate existing users: split name → first_name + last_name
    async for u in db.users.find({"name": {"$exists": True}, "first_name": {"$exists": False}}, {"_id": 0, "id": 1, "name": 1}):
        parts = (u.get("name", "")).split(" ", 1)
        fn = parts[0] if parts else ""
        ln = parts[1] if len(parts) > 1 else ""
        await db.users.update_one({"id": u["id"]}, {"$set": {"first_name": fn, "last_name": ln}, "$unset": {"name": ""}})
    logger.info("Migration: user name → first_name/last_name complete")

    # Default users
    if not await db.users.find_one({"role": "admin"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "admin@fxtracker.com", "first_name": "System", "last_name": "Admin",
            "password_hash": pwd_context.hash("Admin@123"), "role": "admin",
            "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Created default admin user")

    if not await db.users.find_one({"role": "trader"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "trader@fxtracker.com", "first_name": "John", "last_name": "Trader",
            "password_hash": pwd_context.hash("Trader@123"), "role": "trader",
            "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
        })

    if not await db.users.find_one({"role": "treasury"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "treasury@fxtracker.com", "first_name": "Jane", "last_name": "Treasury",
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
    existing_fxbd = await db.transfer_types.find_one({"name": "FX Bank Deal"})
    if not existing_tf or not existing_fxbd:
        await db.transfer_types.delete_many({})
        types = [("FX Crypto Conversion", "FX_CRYPTO"), ("FX Local", "FX_LOCAL"), ("PDAX Withdrawal", "PDAX_WD"), ("FX Bank Deal", "FX_BANK")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c in types]
        await db.transfer_types.insert_many(docs)
        logger.info("Reseeded transfer types (with FX Bank Deal)")

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
    global db
    db = await get_database()
    logger.info("Database backend: %s", type(db).__name__)
    await seed_data()
    # Backfill: Add empty history array to old deals
    await db.deals.update_many({"history": {"$exists": False}}, {"$set": {"history": []}})
    # Backfill: Add proof_type='client' to old proofs without it
    await db.deals.update_many(
        {"settlement_proofs": {"$elemMatch": {"proof_type": {"$exists": False}}}},
        {"$set": {"settlement_proofs.$[elem].proof_type": "client"}},
        array_filters=[{"elem.proof_type": {"$exists": False}}]
    )

@api_router.get("/")
async def root():
    return {"message": "FX Trading Tracker API"}


# --- Report Permissions ---
DEFAULT_REPORT_PERMISSIONS = {
    "deal-blotter": {"trader": True, "treasury": True, "admin": True},
    "settlement": {"trader": True, "treasury": True, "admin": True},
    "open-positions": {"trader": True, "treasury": True, "admin": True},
    "audit-trail": {"trader": False, "treasury": False, "admin": True},
    "user-activity": {"trader": False, "treasury": False, "admin": True},
    "volume-summary": {"trader": True, "treasury": True, "admin": True},
    "client-activity": {"trader": True, "treasury": True, "admin": True},
}

async def _get_report_permissions():
    """Get report permissions from DB, falling back to defaults."""
    doc = await db.report_permissions.find_one({"id": "global"}, {"_id": 0})
    if doc and "permissions" in doc:
        return doc["permissions"]
    return DEFAULT_REPORT_PERMISSIONS

async def _check_report_access(report_id: str, user: dict):
    """Check if user's role has access to a specific report."""
    perms = await _get_report_permissions()
    report_perms = perms.get(report_id, {})
    if not report_perms.get(user["role"], False):
        raise HTTPException(status_code=403, detail=f"Report '{report_id}' is not enabled for your role")

@api_router.get("/reports/permissions")
async def get_report_permissions(user=Depends(get_current_user)):
    """Get report permissions for the current user's role (or all if admin)."""
    perms = await _get_report_permissions()
    if user["role"] == "admin":
        return {"permissions": perms}
    # Non-admin: return only their own enabled reports
    role = user["role"]
    enabled = {rid: rp.get(role, False) for rid, rp in perms.items()}
    return {"permissions": {rid: {role: v} for rid, v in enabled.items()}}

@api_router.put("/reports/permissions")
async def update_report_permissions(req: dict, user=Depends(get_current_user)):
    """Admin updates report permissions. Body: {permissions: {report_id: {role: bool}}}"""
    await require_role(user, ["admin"])
    new_perms = req.get("permissions", {})
    if not new_perms:
        raise HTTPException(status_code=400, detail="No permissions provided")
    # Merge with existing
    current = await _get_report_permissions()
    for report_id, roles in new_perms.items():
        if report_id in current:
            for role, enabled in roles.items():
                if role in ("trader", "treasury", "admin"):
                    current[report_id][role] = bool(enabled)
    await db.report_permissions.update_one(
        {"id": "global"},
        {"$set": {"permissions": current, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user_full_name(user)}},
        upsert=True
    )
    await log_audit("report_permissions_updated", user, "settings", "global", "", f"Updated report permissions")
    return {"permissions": current}


# --- Reports ---
from services import reports as rpt

@api_router.get("/reports/filter-options")
async def report_filter_options(user=Depends(get_current_user)):
    """Return distinct values for all report filter fields. Cached per request."""
    deal_query = {}
    if user["role"] == "trader":
        deal_query["created_by"] = user["id"]

    # Fetch minimal projections for distinct values
    deals = await db.deals.find(deal_query, {
        "_id": 0, "client_name": 1, "buy_currency": 1, "sell_currency": 1,
        "from_bank": 1, "to_bank": 1, "status": 1
    }).to_list(100000)

    clients = sorted({d.get("client_name", "") for d in deals if d.get("client_name")})
    currencies = sorted({c for d in deals for c in [d.get("buy_currency", ""), d.get("sell_currency", "")] if c})
    from_banks = sorted({d.get("from_bank", "") for d in deals if d.get("from_bank")})
    to_banks = sorted({d.get("to_bank", "") for d in deals if d.get("to_bank")})
    statuses = sorted({d.get("status", "") for d in deals if d.get("status")})

    # Users from audit logs (for audit-trail filter)
    users = []
    if user["role"] == "admin":
        logs = await db.audit_logs.find({}, {"_id": 0, "user_name": 1}).to_list(100000)
        users = sorted({l.get("user_name", "") for l in logs if l.get("user_name")})

    return {
        "clients": clients,
        "currencies": currencies,
        "from_banks": from_banks,
        "to_banks": to_banks,
        "statuses": statuses,
        "users": users,
    }

async def _get_deals_for_report(query, user, sort_field="created_at", sort_dir=-1, page=None, limit=None):
    """Shared query builder for report endpoints. Supports pagination."""
    if user["role"] == "trader":
        query["created_by"] = user["id"]
    if page and limit:
        total = await db.deals.count_documents(query)
        skip = (page - 1) * limit
        rows = await db.deals.find(query, {"_id": 0}).sort(sort_field, sort_dir).skip(skip).limit(limit).to_list(limit)
        return rows, total
    return await db.deals.find(query, {"_id": 0}).sort(sort_field, sort_dir).to_list(100000), None

async def _get_logs_for_report(query, sort_field="created_at", sort_dir=-1, page=None, limit=None):
    """Shared query builder for audit log reports. Supports pagination."""
    if page and limit:
        total = await db.audit_logs.count_documents(query)
        skip = (page - 1) * limit
        rows = await db.audit_logs.find(query, {"_id": 0}).sort(sort_field, sort_dir).skip(skip).limit(limit).to_list(limit)
        return rows, total
    return await db.audit_logs.find(query, {"_id": 0}).sort(sort_field, sort_dir).to_list(100000), None

def _date_range_label(date_from, date_to):
    f = date_from or "All"
    t = date_to or "Present"
    return f"{f} to {t}"

@api_router.get("/reports/deal-blotter")
async def report_deal_blotter(
    fmt: str = Query("csv", alias="format"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    client: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    await _check_report_access("deal-blotter", user)
    query = {}
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
    sf = sort_by or "created_at"
    sd = -1 if (sort_dir or "desc") == "desc" else 1
    dr = _date_range_label(date_from, date_to)
    if fmt == "json":
        deals, total = await _get_deals_for_report(dict(query), user, sf, sd, page, limit)
        rows = []
        for d in deals:
            rows.append({
                "reference_number": d.get("reference_number", ""), "deal_date": (d.get("deal_date") or "")[:10],
                "value_date": (d.get("value_date") or "")[:10], "client_name": d.get("client_name", ""),
                "transaction_type": d.get("transaction_type", ""), "transfer_type": d.get("transfer_type", ""),
                "buy_currency": d.get("buy_currency", ""), "sell_currency": d.get("sell_currency", ""),
                "currency_amount": d.get("currency_amount"), "rate": d.get("rate"),
                "amount": d.get("amount"), "status": d.get("status", ""),
                "created_by_name": d.get("created_by_name", ""), "processed_by_name": d.get("processed_by_name", ""),
                "remarks": d.get("remarks", ""),
            })
        return {"rows": rows, "total": total, "page": page, "pages": (total + limit - 1) // limit if total > 0 else 1}
    # CSV/PDF: fetch all (no pagination)
    deals, _ = await _get_deals_for_report(dict(query), user, sf, sd)
    if fmt == "pdf":
        buf = rpt.deal_blotter_pdf(deals, dr)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=deal_blotter_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"})
    csv_data = rpt.deal_blotter_csv(deals)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=deal_blotter_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"})

@api_router.get("/reports/settlement")
async def report_settlement(
    fmt: str = Query("csv", alias="format"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    from_bank: Optional[str] = Query(None),
    to_bank: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    await _check_report_access("settlement", user)
    query = {"$or": [{"status": "confirmed"}, {"status": "pending"}]}
    if date_from:
        query.setdefault("value_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("value_date", {})["$lte"] = date_to
    if from_bank:
        query["from_bank"] = {"$regex": from_bank, "$options": "i"}
    if to_bank:
        query["to_bank"] = {"$regex": to_bank, "$options": "i"}
    sf = sort_by or "value_date"
    sd = 1 if (sort_dir or "asc") == "asc" else -1
    dr = _date_range_label(date_from, date_to)
    if fmt == "json":
        deals, total = await _get_deals_for_report(dict(query), user, sf, sd, page, limit)
        rows = []
        for d in deals:
            rows.append({
                "value_date": (d.get("value_date") or "")[:10], "reference_number": d.get("reference_number", ""),
                "client_name": d.get("client_name", ""), "buy_currency": d.get("buy_currency", ""),
                "sell_currency": d.get("sell_currency", ""), "currency_amount": d.get("currency_amount"),
                "amount": d.get("amount"), "from_bank": d.get("from_bank", ""),
                "from_account_num": d.get("from_account_num", ""), "to_bank": d.get("to_bank", ""),
                "to_account_num": d.get("to_account_num", ""),
                "proofs": len(d.get("settlement_proofs", [])), "status": d.get("status", ""),
            })
        return {"rows": rows, "total": total, "page": page, "pages": (total + limit - 1) // limit if total > 0 else 1}
    deals, _ = await _get_deals_for_report(dict(query), user, sf, sd)
    if fmt == "pdf":
        buf = rpt.settlement_pdf(deals, dr)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=settlement_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"})
    csv_data = rpt.settlement_csv(deals)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=settlement_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"})

@api_router.get("/reports/open-positions")
async def report_open_positions(
    fmt: str = Query("csv", alias="format"),
    user=Depends(get_current_user)
):
    await _check_report_access("open-positions", user)
    query = {"status": "pending"}
    deals, _ = await _get_deals_for_report(query, user)
    # Group by currency pair
    pairs = {}
    for d in deals:
        pair = f"{d.get('buy_currency','')}/{d.get('sell_currency','')}"
        if pair not in pairs:
            pairs[pair] = {"pair": pair, "count": 0, "buy_total": 0, "sell_total": 0}
        pairs[pair]["count"] += 1
        pairs[pair]["buy_total"] += float(d.get("currency_amount", 0) or 0)
        pairs[pair]["sell_total"] += float(d.get("amount", 0) or 0)
    positions = []
    for p in sorted(pairs.values(), key=lambda x: -x["buy_total"]):
        p["net"] = p["buy_total"] - p["sell_total"]
        positions.append(p)
    dr = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if fmt == "json":
        return {"rows": positions, "total": len(positions)}
    if fmt == "pdf":
        buf = rpt.open_positions_pdf(positions, dr)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=open_positions_{dr}.pdf"})
    csv_data = rpt.open_positions_csv(positions)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=open_positions_{dr}.csv"})

@api_router.get("/reports/audit-trail")
async def report_audit_trail(
    fmt: str = Query("csv", alias="format"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    await _check_report_access("audit-trail", user)
    query = {}
    if date_from:
        query.setdefault("created_at", {})["$gte"] = date_from
    if date_to:
        query.setdefault("created_at", {})["$lte"] = date_to + "T23:59:59"
    if user_name:
        query["user_name"] = {"$regex": user_name, "$options": "i"}
    sf = sort_by or "created_at"
    sd = -1 if (sort_dir or "desc") == "desc" else 1
    dr = _date_range_label(date_from, date_to)
    if fmt == "json":
        logs, total = await _get_logs_for_report(dict(query), sf, sd, page, limit)
        rows = []
        for l in logs:
            rows.append({
                "timestamp": (l.get("created_at") or "")[:19], "action": l.get("action", ""),
                "entity_type": l.get("entity_type", ""), "entity_ref": l.get("entity_ref", ""),
                "user_name": l.get("user_name", ""), "user_role": l.get("user_role", ""),
                "details": l.get("details", ""),
            })
        return {"rows": rows, "total": total, "page": page, "pages": (total + limit - 1) // limit if total > 0 else 1}
    logs, _ = await _get_logs_for_report(dict(query), sf, sd)
    if fmt == "pdf":
        buf = rpt.audit_trail_pdf(logs, dr)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=audit_trail_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"})
    csv_data = rpt.audit_trail_csv(logs)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=audit_trail_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"})

@api_router.get("/reports/user-activity")
async def report_user_activity(
    fmt: str = Query("csv", alias="format"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    await _check_report_access("user-activity", user)
    query = {}
    if date_from:
        query.setdefault("created_at", {})["$gte"] = date_from
    if date_to:
        query.setdefault("created_at", {})["$lte"] = date_to + "T23:59:59"
    logs = await db.audit_logs.find(query, {"_id": 0}).to_list(50000)
    # Aggregate by user
    user_map = {}
    for l in logs:
        uid = l.get("user_id", "unknown")
        if uid not in user_map:
            user_map[uid] = {"user_name": l.get("user_name", ""), "role": l.get("user_role", ""),
                             "created": 0, "processed": 0, "returned": 0, "proofs": 0, "total": 0}
        u = user_map[uid]
        u["total"] += 1
        action = l.get("action", "")
        if action == "deal_created":
            u["created"] += 1
        elif action in ("deal_confirmed",):
            u["processed"] += 1
        elif action == "deal_returned":
            u["returned"] += 1
        elif action == "proof_uploaded":
            u["proofs"] += 1
    activities = sorted(user_map.values(), key=lambda x: -x["total"])
    dr = _date_range_label(date_from, date_to)
    if fmt == "json":
        return {"rows": activities, "total": len(activities)}
    if fmt == "pdf":
        buf = rpt.user_activity_pdf(activities, dr)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=user_activity_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"})
    csv_data = rpt.user_activity_csv(activities)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=user_activity_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"})

@api_router.get("/reports/volume-summary")
async def report_volume_summary(
    fmt: str = Query("csv", alias="format"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_by: str = Query("daily"),
    user=Depends(get_current_user)
):
    await _check_report_access("volume-summary", user)
    query = {}
    if user["role"] == "trader":
        query["created_by"] = user["id"]
    if date_from:
        query.setdefault("deal_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("deal_date", {})["$lte"] = date_to
    deals = await db.deals.find(query, {"_id": 0}).sort("deal_date", 1).to_list(50000)
    # Group
    groups = {}
    for d in deals:
        dd = d.get("deal_date", "")[:10]
        if group_by == "weekly":
            try:
                dt = datetime.strptime(dd, "%Y-%m-%d")
                period = f"{dt.strftime('%Y-W%V')}"
            except ValueError:
                period = dd
        elif group_by == "monthly":
            period = dd[:7]
        else:
            period = dd
        if period not in groups:
            groups[period] = {"period": period, "count": 0, "volume": 0, "confirmed": 0, "pending": 0, "returned": 0, "cancelled": 0}
        g = groups[period]
        g["count"] += 1
        g["volume"] += float(d.get("amount", 0) or 0)
        s = d.get("status", "")
        if s in g:
            g[s] += 1
    summary = []
    for g in sorted(groups.values(), key=lambda x: x["period"]):
        g["avg"] = g["volume"] / g["count"] if g["count"] > 0 else 0
        summary.append(g)
    dr = _date_range_label(date_from, date_to)
    if fmt == "json":
        return {"rows": summary, "total": len(summary)}
    if fmt == "pdf":
        buf = rpt.volume_summary_pdf(summary, dr, group_by)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=volume_summary_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"})
    csv_data = rpt.volume_summary_csv(summary)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=volume_summary_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"})

@api_router.get("/reports/client-activity")
async def report_client_activity(
    fmt: str = Query("csv", alias="format"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    client: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    await _check_report_access("client-activity", user)
    query = {}
    if user["role"] == "trader":
        query["created_by"] = user["id"]
    if date_from:
        query.setdefault("deal_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("deal_date", {})["$lte"] = date_to
    if client:
        query["client_name"] = {"$regex": client, "$options": "i"}
    deals = await db.deals.find(query, {"_id": 0}).to_list(50000)
    # Group by client
    clients = {}
    for d in deals:
        cn = d.get("client_name", "Unknown")
        if cn not in clients:
            clients[cn] = {"client": cn, "count": 0, "volume": 0, "pairs_set": set(), "last_deal": ""}
        c = clients[cn]
        c["count"] += 1
        c["volume"] += float(d.get("amount", 0) or 0)
        pair = f"{d.get('buy_currency','')}/{d.get('sell_currency','')}"
        c["pairs_set"].add(pair)
        dd = d.get("deal_date", "")
        if dd > c["last_deal"]:
            c["last_deal"] = dd
    result = []
    for c in sorted(clients.values(), key=lambda x: -x["volume"]):
        c["avg"] = c["volume"] / c["count"] if c["count"] > 0 else 0
        c["pairs"] = ", ".join(sorted(c["pairs_set"]))
        del c["pairs_set"]
        result.append(c)
    dr = _date_range_label(date_from, date_to)
    if fmt == "json":
        return {"rows": result, "total": len(result)}
    if fmt == "pdf":
        buf = rpt.client_activity_pdf(result, dr)
        return Response(content=buf.read(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=client_activity_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"})
    csv_data = rpt.client_activity_csv(result)
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=client_activity_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"})

@api_router.get("/storage/status")
async def storage_status(user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    storage = get_storage()
    backend_type = os.environ.get("STORAGE_TYPE", "emergent").lower()
    info = {"backend": backend_type, "class": type(storage).__name__}
    if backend_type == "s3":
        info["endpoint"] = os.environ.get("S3_ENDPOINT_URL", "default")
        info["bucket"] = os.environ.get("S3_BUCKET_NAME", "")
        info["region"] = os.environ.get("S3_REGION", "")
    return info

@api_router.get("/database/status")
async def database_status(user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    db_type = os.environ.get("DB_TYPE", "mongodb").lower()
    info = {"backend": db_type, "class": type(db).__name__}
    if db_type == "couchbase":
        info["connection"] = os.environ.get("CB_CONNECTION_STRING", "")
        info["bucket"] = os.environ.get("CB_BUCKET_NAME", "")
        from services.database import SCOPE_MAP
        info["scopes"] = sorted(set(s for s, _ in SCOPE_MAP.values()))
    return info

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
    pass  # Connection cleanup handled by database backend
