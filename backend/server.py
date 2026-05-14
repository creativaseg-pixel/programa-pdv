from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'imobiliaria-secret-key-change-in-prod-2026')
JWT_ALG = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 7

app = FastAPI(title="Sistema Imobiliária API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ============ MODELS ============
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    company: Optional[str] = None
    creci: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str
    type: str  # casa, apartamento, terreno, comercial
    operation: str  # venda, locacao
    price: float
    address: str
    city: str
    state: str
    bedrooms: int = 0
    bathrooms: int = 0
    area: float = 0
    garage: int = 0
    description: str = ""
    image_url: Optional[str] = None
    status: str = "ativo"  # ativo, vendido, alugado, inativo
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: Optional[str] = None

class PropertyCreate(BaseModel):
    title: str
    type: str
    operation: str
    price: float
    address: str
    city: str
    state: str
    bedrooms: int = 0
    bathrooms: int = 0
    area: float = 0
    garage: int = 0
    description: str = ""
    image_url: Optional[str] = None
    owner_id: Optional[str] = None
    status: str = "ativo"

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    cpf_cnpj: str
    email: Optional[str] = None
    phone: str
    type: str  # proprietario, inquilino, comprador
    address: str = ""
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: Optional[str] = None

class ClientCreate(BaseModel):
    name: str
    cpf_cnpj: str
    email: Optional[str] = None
    phone: str
    type: str
    address: str = ""
    notes: str = ""

class Contract(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # locacao, compra_venda
    property_id: str
    landlord_id: str  # proprietário/vendedor
    tenant_id: str  # inquilino/comprador
    value: float
    start_date: str
    end_date: Optional[str] = None
    payment_day: int = 5
    index: str = "IGPM"  # IGPM ou IPCA
    commission_pct: float = 6.0
    deposit_value: float = 0
    status: str = "ativo"
    extra_terms: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: Optional[str] = None

class ContractCreate(BaseModel):
    type: str
    property_id: str
    landlord_id: str
    tenant_id: str
    value: float
    start_date: str
    end_date: Optional[str] = None
    payment_day: int = 5
    index: str = "IGPM"
    commission_pct: float = 6.0
    deposit_value: float = 0
    extra_terms: str = ""

class Receipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    receipt_number: str
    type: str  # aluguel, sinal, comissao
    contract_id: Optional[str] = None
    payer_id: str
    receiver_id: str
    value: float
    reference: str  # ex: "Aluguel ref. Jan/2026"
    payment_date: str
    payment_method: str = "PIX"
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: Optional[str] = None

class ReceiptCreate(BaseModel):
    type: str
    contract_id: Optional[str] = None
    payer_id: str
    receiver_id: str
    value: float
    reference: str
    payment_date: str
    payment_method: str = "PIX"
    notes: str = ""

class ReajusteCalc(BaseModel):
    valor_atual: float
    indice: str = "IGPM"  # IGPM ou IPCA
    percentual_anual: Optional[float] = None  # se nulo, usa padrão

class MultaJurosCalc(BaseModel):
    valor_devido: float
    dias_atraso: int
    multa_pct: float = 10.0
    juros_mes_pct: float = 1.0

class ComissaoCalc(BaseModel):
    valor_transacao: float
    tipo: str = "venda"  # venda ou locacao
    percentual: Optional[float] = None

# ============ AUTH HELPERS ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============ AUTH ROUTES ============
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": data.email.lower(),
        "password": hash_password(data.password),
        "full_name": data.full_name,
        "company": data.company or "",
        "creci": data.creci or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, data.email.lower())
    user_resp = {k: v for k, v in user_doc.items() if k not in ("password", "_id")}
    return TokenResponse(access_token=token, user=user_resp)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email.lower()})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    token = create_token(user["id"], user["email"])
    user_resp = {k: v for k, v in user.items() if k not in ("password", "_id")}
    return TokenResponse(access_token=token, user=user_resp)

@api_router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user

# ============ PROPERTIES ============
@api_router.post("/properties", response_model=Property)
async def create_property(data: PropertyCreate, current_user: dict = Depends(get_current_user)):
    payload = data.dict()
    payload["owner_id"] = data.owner_id or ""
    prop = Property(**payload, user_id=current_user["id"])
    await db.properties.insert_one(prop.dict())
    return prop

@api_router.get("/properties", response_model=List[Property])
async def list_properties(current_user: dict = Depends(get_current_user)):
    items = await db.properties.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return items

@api_router.get("/properties/{prop_id}", response_model=Property)
async def get_property(prop_id: str, current_user: dict = Depends(get_current_user)):
    item = await db.properties.find_one({"id": prop_id, "user_id": current_user["id"]}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Imóvel não encontrado")
    return item

@api_router.put("/properties/{prop_id}", response_model=Property)
async def update_property(prop_id: str, data: PropertyCreate, current_user: dict = Depends(get_current_user)):
    update_data = data.dict()
    update_data["owner_id"] = data.owner_id or ""
    result = await db.properties.update_one(
        {"id": prop_id, "user_id": current_user["id"]}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Imóvel não encontrado")
    item = await db.properties.find_one({"id": prop_id}, {"_id": 0})
    return item

@api_router.delete("/properties/{prop_id}")
async def delete_property(prop_id: str, current_user: dict = Depends(get_current_user)):
    await db.properties.delete_one({"id": prop_id, "user_id": current_user["id"]})
    return {"ok": True}

# ============ CLIENTS ============
@api_router.post("/clients", response_model=Client)
async def create_client(data: ClientCreate, current_user: dict = Depends(get_current_user)):
    c = Client(**data.dict(), user_id=current_user["id"])
    await db.clients.insert_one(c.dict())
    return c

@api_router.get("/clients", response_model=List[Client])
async def list_clients(current_user: dict = Depends(get_current_user)):
    items = await db.clients.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return items

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    item = await db.clients.find_one({"id": client_id, "user_id": current_user["id"]}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Cliente não encontrado")
    return item

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, data: ClientCreate, current_user: dict = Depends(get_current_user)):
    result = await db.clients.update_one(
        {"id": client_id, "user_id": current_user["id"]}, {"$set": data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Cliente não encontrado")
    item = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return item

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    await db.clients.delete_one({"id": client_id, "user_id": current_user["id"]})
    return {"ok": True}

# ============ CONTRACTS ============
@api_router.post("/contracts", response_model=Contract)
async def create_contract(data: ContractCreate, current_user: dict = Depends(get_current_user)):
    c = Contract(**data.dict(), user_id=current_user["id"])
    await db.contracts.insert_one(c.dict())
    return c

@api_router.get("/contracts", response_model=List[Contract])
async def list_contracts(current_user: dict = Depends(get_current_user)):
    items = await db.contracts.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return items

@api_router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, current_user: dict = Depends(get_current_user)):
    item = await db.contracts.find_one({"id": contract_id, "user_id": current_user["id"]}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Contrato não encontrado")
    # enrich
    prop = await db.properties.find_one({"id": item["property_id"]}, {"_id": 0})
    landlord = await db.clients.find_one({"id": item["landlord_id"]}, {"_id": 0})
    tenant = await db.clients.find_one({"id": item["tenant_id"]}, {"_id": 0})
    item["property"] = prop
    item["landlord"] = landlord
    item["tenant"] = tenant
    return item

@api_router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str, current_user: dict = Depends(get_current_user)):
    await db.contracts.delete_one({"id": contract_id, "user_id": current_user["id"]})
    return {"ok": True}

# ============ RECEIPTS ============
def generate_receipt_number():
    return f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

@api_router.post("/receipts", response_model=Receipt)
async def create_receipt(data: ReceiptCreate, current_user: dict = Depends(get_current_user)):
    r = Receipt(**data.dict(), receipt_number=generate_receipt_number(), user_id=current_user["id"])
    await db.receipts.insert_one(r.dict())
    return r

@api_router.get("/receipts", response_model=List[Receipt])
async def list_receipts(current_user: dict = Depends(get_current_user)):
    items = await db.receipts.find({"user_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return items

@api_router.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str, current_user: dict = Depends(get_current_user)):
    item = await db.receipts.find_one({"id": receipt_id, "user_id": current_user["id"]}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Recibo não encontrado")
    payer = await db.clients.find_one({"id": item["payer_id"]}, {"_id": 0})
    receiver = await db.clients.find_one({"id": item["receiver_id"]}, {"_id": 0})
    item["payer"] = payer
    item["receiver"] = receiver
    return item

@api_router.delete("/receipts/{receipt_id}")
async def delete_receipt(receipt_id: str, current_user: dict = Depends(get_current_user)):
    await db.receipts.delete_one({"id": receipt_id, "user_id": current_user["id"]})
    return {"ok": True}

# ============ CALCULATIONS ============
# Índices padrão mercado brasileiro 2026 (atualizáveis)
DEFAULT_INDICES = {
    "IGPM": 4.5,  # IGPM acumulado 12 meses (referência mercado)
    "IPCA": 4.62,  # IPCA acumulado 12 meses
}

@api_router.get("/indices")
async def get_indices():
    return {
        "indices": DEFAULT_INDICES,
        "reference": "Acumulado 12 meses - referência de mercado",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

@api_router.post("/calc/reajuste")
async def calc_reajuste(data: ReajusteCalc):
    pct = data.percentual_anual if data.percentual_anual is not None else DEFAULT_INDICES.get(data.indice, 4.5)
    novo_valor = data.valor_atual * (1 + pct / 100)
    diferenca = novo_valor - data.valor_atual
    return {
        "valor_atual": round(data.valor_atual, 2),
        "indice": data.indice,
        "percentual_aplicado": round(pct, 4),
        "novo_valor": round(novo_valor, 2),
        "diferenca": round(diferenca, 2),
    }

@api_router.post("/calc/multa-juros")
async def calc_multa_juros(data: MultaJurosCalc):
    multa = data.valor_devido * (data.multa_pct / 100)
    # juros simples por dia (juros_mes_pct/30 por dia)
    juros_dia_pct = data.juros_mes_pct / 30
    juros = data.valor_devido * (juros_dia_pct / 100) * data.dias_atraso
    total = data.valor_devido + multa + juros
    return {
        "valor_devido": round(data.valor_devido, 2),
        "dias_atraso": data.dias_atraso,
        "multa": round(multa, 2),
        "juros": round(juros, 2),
        "total": round(total, 2),
    }

@api_router.post("/calc/comissao")
async def calc_comissao(data: ComissaoCalc):
    if data.percentual is not None:
        pct = data.percentual
    else:
        # padrões de mercado COFECI/CRECI
        pct = 6.0 if data.tipo == "venda" else 100.0  # locação = 1 aluguel = 100%
    comissao = data.valor_transacao * (pct / 100)
    return {
        "valor_transacao": round(data.valor_transacao, 2),
        "tipo": data.tipo,
        "percentual": round(pct, 2),
        "comissao": round(comissao, 2),
    }

# ============ DASHBOARD ============
@api_router.get("/dashboard/stats")
async def dashboard_stats(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    total_properties = await db.properties.count_documents({"user_id": uid, "status": "ativo"})
    total_clients = await db.clients.count_documents({"user_id": uid})
    total_contracts = await db.contracts.count_documents({"user_id": uid, "status": "ativo"})

    # current month receipts
    now = datetime.now(timezone.utc)
    month_prefix = now.strftime("%Y-%m")
    receipts = await db.receipts.find({"user_id": uid}, {"_id": 0}).to_list(1000)
    receipts_month = [r for r in receipts if r.get("payment_date", "").startswith(month_prefix)]
    total_month = sum(r["value"] for r in receipts_month)
    total_commission = sum(r["value"] for r in receipts_month if r.get("type") == "comissao")

    # property sums
    properties = await db.properties.find({"user_id": uid}, {"_id": 0}).to_list(1000)
    sale_value = sum(p["price"] for p in properties if p.get("operation") == "venda" and p.get("status") == "ativo")
    rent_value = sum(p["price"] for p in properties if p.get("operation") == "locacao" and p.get("status") == "ativo")

    return {
        "total_properties": total_properties,
        "total_clients": total_clients,
        "total_contracts": total_contracts,
        "receipts_month": round(total_month, 2),
        "commission_month": round(total_commission, 2),
        "sale_portfolio": round(sale_value, 2),
        "rent_portfolio": round(rent_value, 2),
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
