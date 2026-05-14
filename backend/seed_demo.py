"""Seed demo data for the imobiliária system."""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / '.env')

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

DEMO_EMAIL = "demo@imobiliaria.com"
DEMO_PASS = "demo1234"


async def seed():
    # Remove old demo user data
    user = await db.users.find_one({"email": DEMO_EMAIL})
    if user:
        uid = user['id']
        await db.clients.delete_many({"user_id": uid})
        await db.properties.delete_many({"user_id": uid})
        await db.contracts.delete_many({"user_id": uid})
        await db.receipts.delete_many({"user_id": uid})
        await db.users.delete_one({"id": uid})
        print(f"Removed existing demo user data ({uid})")

    # Create user
    uid = str(uuid.uuid4())
    hashed = bcrypt.hashpw(DEMO_PASS.encode(), bcrypt.gensalt()).decode()
    await db.users.insert_one({
        "id": uid,
        "email": DEMO_EMAIL,
        "password": hashed,
        "full_name": "Maria Silva",
        "company": "Silva & Associados Imobiliária",
        "creci": "12345-F/SP",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    print(f"Created demo user: {DEMO_EMAIL} / {DEMO_PASS}")

    # Clients
    clients_data = [
        {"name": "João Pereira", "cpf_cnpj": "123.456.789-00", "phone": "(11) 98765-4321", "email": "joao@email.com", "type": "proprietario", "address": "Av. Paulista, 1500, São Paulo/SP"},
        {"name": "Ana Costa", "cpf_cnpj": "987.654.321-00", "phone": "(11) 91234-5678", "email": "ana@email.com", "type": "inquilino", "address": "Rua Augusta, 200, São Paulo/SP"},
        {"name": "Carlos Mendes", "cpf_cnpj": "456.789.123-00", "phone": "(11) 99876-5432", "email": "carlos@email.com", "type": "comprador", "address": "Rua Oscar Freire, 500, São Paulo/SP"},
    ]
    client_ids = {}
    for c in clients_data:
        cid = str(uuid.uuid4())
        await db.clients.insert_one({
            "id": cid, **c, "notes": "", "user_id": uid,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        client_ids[c["type"]] = cid
    print(f"Created {len(clients_data)} clients")

    # Properties
    properties_data = [
        {
            "title": "Apartamento Vila Mariana - 3 Dormitórios",
            "type": "apartamento", "operation": "locacao", "price": 4500.0,
            "address": "Rua Domingos de Morais, 800, Apt 102",
            "city": "São Paulo", "state": "SP",
            "bedrooms": 3, "bathrooms": 2, "area": 85, "garage": 1,
            "description": "Apartamento reformado, prédio com lazer completo, próximo ao metrô.",
            "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800",
        },
        {
            "title": "Casa Térrea Jardins - Alto Padrão",
            "type": "casa", "operation": "venda", "price": 1850000.0,
            "address": "Rua Bela Cintra, 1200",
            "city": "São Paulo", "state": "SP",
            "bedrooms": 4, "bathrooms": 4, "area": 280, "garage": 3,
            "description": "Casa em condomínio fechado, piscina, área gourmet, segurança 24h.",
            "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800",
        },
        {
            "title": "Sala Comercial Faria Lima",
            "type": "comercial", "operation": "locacao", "price": 6800.0,
            "address": "Av. Brigadeiro Faria Lima, 3500, Sala 1502",
            "city": "São Paulo", "state": "SP",
            "bedrooms": 0, "bathrooms": 2, "area": 65, "garage": 2,
            "description": "Sala comercial em prédio AAA, vista panorâmica, totalmente mobiliada.",
            "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800",
        },
    ]
    property_ids = []
    for p in properties_data:
        pid = str(uuid.uuid4())
        property_ids.append(pid)
        await db.properties.insert_one({
            "id": pid, **p, "status": "ativo", "owner_id": client_ids["proprietario"], "user_id": uid,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    print(f"Created {len(properties_data)} properties")

    # Contract (locação)
    contract_id = str(uuid.uuid4())
    await db.contracts.insert_one({
        "id": contract_id,
        "type": "locacao",
        "property_id": property_ids[0],
        "landlord_id": client_ids["proprietario"],
        "tenant_id": client_ids["inquilino"],
        "value": 4500.0,
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=365 * 2)).strftime("%Y-%m-%d"),
        "payment_day": 5,
        "index": "IGPM",
        "commission_pct": 100.0,
        "deposit_value": 13500.0,
        "status": "ativo",
        "extra_terms": "Imóvel entregue mobiliado. IPTU e condomínio por conta do locatário.",
        "user_id": uid,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    print("Created 1 contract")

    # Receipts
    receipts_data = [
        {
            "type": "aluguel",
            "payer_id": client_ids["inquilino"],
            "receiver_id": client_ids["proprietario"],
            "value": 4500.0,
            "reference": f"Aluguel ref. {datetime.now().strftime('%m/%Y')}",
            "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "payment_method": "PIX",
            "notes": "Pagamento em dia.",
        },
        {
            "type": "comissao",
            "payer_id": client_ids["proprietario"],
            "receiver_id": client_ids["proprietario"],  # demo: imobiliária recebe
            "value": 4500.0,
            "reference": "Comissão de intermediação - locação Vila Mariana",
            "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "payment_method": "Transferência",
            "notes": "1 aluguel - taxa padrão",
        },
    ]
    for r in receipts_data:
        rid = str(uuid.uuid4())
        await db.receipts.insert_one({
            "id": rid,
            "receipt_number": f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            **r, "contract_id": contract_id, "user_id": uid,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    print(f"Created {len(receipts_data)} receipts")
    print("\nSEED COMPLETE!")
    print(f"Login: {DEMO_EMAIL} / {DEMO_PASS}")


asyncio.run(seed())
