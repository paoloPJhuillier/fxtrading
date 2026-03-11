from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
import os
import logging
import uuid
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
    from_company: str
    from_bank: str
    from_account_num: str
    to_company: str
    to_bank: str
    to_account_num: str
    buy_currency: str
    sell_currency: str
    currency_amount: float
    amount: float
    rate: float
    remarks: Optional[str] = ""

class DealProcess(BaseModel):
    status: str
    treasury_remarks: Optional[str] = ""

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
    return updated

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, user=Depends(get_current_user)):
    await require_role(user, ["admin"])
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


# --- Deal Endpoints ---
@api_router.get("/deals")
async def list_deals(
    status_filter: Optional[str] = Query(None, alias="status"),
    user=Depends(get_current_user)
):
    query = {}
    if user["role"] == "trader":
        query["created_by"] = user["id"]
    if status_filter:
        query["status"] = status_filter
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
    return deal

@api_router.get("/deals/{deal_id}")
async def get_deal(deal_id: str, user=Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if user["role"] == "trader" and deal["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return deal

@api_router.put("/deals/{deal_id}/process")
async def process_deal(deal_id: str, req: DealProcess, user=Depends(get_current_user)):
    await require_role(user, ["treasury"])
    if req.status not in ["confirmed", "returned"]:
        raise HTTPException(status_code=400, detail="Status must be 'confirmed' or 'returned'")
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

    # Transaction types
    if await db.transaction_types.count_documents({}) == 0:
        types = [("Spot", "SPOT"), ("Forward", "FWD"), ("Swap", "SWAP"), ("NDF", "NDF"), ("Option", "OPT")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c in types]
        await db.transaction_types.insert_many(docs)

    # Transfer types
    if await db.transfer_types.count_documents({}) == 0:
        types = [("Wire Transfer", "WIRE"), ("SWIFT", "SWIFT"), ("Internal Transfer", "INT"), ("ACH", "ACH"), ("RTGS", "RTGS")]
        docs = [{"id": str(uuid.uuid4()), "name": n, "code": c, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()} for n, c in types]
        await db.transfer_types.insert_many(docs)

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
