"""Pytest suite for Sistema Imobiliária backend (FastAPI + JWT + MongoDB)."""
import os
import uuid
import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

BASE_URL = "https://contract-calc-system.preview.emergentagent.com"
API = f"{BASE_URL}/api"

DEMO_EMAIL = "demo@imobiliaria.com"
DEMO_PASS = "demo1234"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def demo_token(session):
    r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASS}, timeout=30)
    assert r.status_code == 200, f"Demo login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(demo_token):
    return {"Authorization": f"Bearer {demo_token}", "Content-Type": "application/json"}


# ---------- Public ----------
class TestPublic:
    def test_indices_endpoint(self, session):
        r = session.get(f"{API}/indices", timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert "indices" in body
        assert body["indices"]["IGPM"] == 4.5
        assert body["indices"]["IPCA"] == 4.62


# ---------- Auth ----------
class TestAuth:
    def test_register_new_user_and_login(self, session):
        email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        r = session.post(f"{API}/auth/register", json={
            "email": email, "password": "secret123", "full_name": "TEST User"
        }, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == email.lower()
        # login
        r2 = session.post(f"{API}/auth/login", json={"email": email, "password": "secret123"}, timeout=30)
        assert r2.status_code == 200
        assert "access_token" in r2.json()

    def test_duplicate_register_rejected(self, session):
        r = session.post(f"{API}/auth/register", json={
            "email": DEMO_EMAIL, "password": "demo1234", "full_name": "Dup"
        }, timeout=30)
        assert r.status_code == 400

    def test_login_invalid_credentials(self, session):
        r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": "wrong"}, timeout=30)
        assert r.status_code == 401

    def test_me_with_token(self, session, auth_headers):
        r = session.get(f"{API}/auth/me", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == DEMO_EMAIL
        assert "password" not in body

    def test_me_without_token_rejected(self, session):
        r = session.get(f"{API}/auth/me", timeout=20)
        assert r.status_code in (401, 403)


# ---------- Calculations ----------
class TestCalculations:
    def test_reajuste_igpm_default(self, session):
        r = session.post(f"{API}/calc/reajuste", json={"valor_atual": 1000.0, "indice": "IGPM"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["percentual_aplicado"] == 4.5
        assert d["novo_valor"] == 1045.0
        assert d["diferenca"] == 45.0

    def test_reajuste_ipca_default(self, session):
        r = session.post(f"{API}/calc/reajuste", json={"valor_atual": 1000.0, "indice": "IPCA"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["percentual_aplicado"] == 4.62
        assert d["novo_valor"] == 1046.2

    def test_reajuste_custom_pct(self, session):
        r = session.post(f"{API}/calc/reajuste",
                         json={"valor_atual": 2000.0, "indice": "IGPM", "percentual_anual": 10.0}, timeout=20)
        assert r.status_code == 200
        assert r.json()["novo_valor"] == 2200.0

    def test_multa_juros_default(self, session):
        # valor 1000, 30 dias atraso => multa 10% = 100; juros 1% a.m. simples
        # juros = 1000 * (1/30/100) * 30 = 10
        r = session.post(f"{API}/calc/multa-juros",
                         json={"valor_devido": 1000.0, "dias_atraso": 30}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["multa"] == 100.0
        assert d["juros"] == 10.0
        assert d["total"] == 1110.0

    def test_comissao_venda_default(self, session):
        r = session.post(f"{API}/calc/comissao",
                         json={"valor_transacao": 100000.0, "tipo": "venda"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["percentual"] == 6.0
        assert d["comissao"] == 6000.0

    def test_comissao_locacao_default(self, session):
        # 100% de 1 aluguel
        r = session.post(f"{API}/calc/comissao",
                         json={"valor_transacao": 4500.0, "tipo": "locacao"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["percentual"] == 100.0
        assert d["comissao"] == 4500.0


# ---------- Properties / Clients / Contracts / Receipts (Demo data) ----------
class TestSeededData:
    def test_dashboard_stats(self, session, auth_headers):
        r = session.get(f"{API}/dashboard/stats", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["total_properties", "total_clients", "total_contracts",
                  "receipts_month", "commission_month", "sale_portfolio", "rent_portfolio"]:
            assert k in d
        assert d["total_properties"] >= 3
        assert d["total_clients"] >= 3
        assert d["total_contracts"] >= 1

    def test_list_properties_seeded(self, session, auth_headers):
        r = session.get(f"{API}/properties", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 3
        ops = {i["operation"] for i in items}
        assert "venda" in ops and "locacao" in ops

    def test_list_clients_seeded(self, session, auth_headers):
        r = session.get(f"{API}/clients", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 3

    def test_list_contracts_and_enrichment(self, session, auth_headers):
        r = session.get(f"{API}/contracts", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        cid = items[0]["id"]
        r2 = session.get(f"{API}/contracts/{cid}", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        d = r2.json()
        assert d.get("property") is not None
        assert d.get("landlord") is not None
        assert d.get("tenant") is not None

    def test_list_receipts_and_enrichment(self, session, auth_headers):
        r = session.get(f"{API}/receipts", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 2
        rid = items[0]["id"]
        r2 = session.get(f"{API}/receipts/{rid}", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        d = r2.json()
        assert d.get("payer") is not None
        assert d.get("receiver") is not None
        assert d.get("receipt_number", "").startswith("REC-")


# ---------- CRUD with cleanup ----------
class TestPropertyCRUD:
    created_id = None

    def test_create_get_update_delete_property(self, session, auth_headers):
        payload = {
            "title": "TEST_Apt Pinheiros", "type": "apartamento", "operation": "locacao",
            "price": 3500.0, "address": "TEST Rua X 1", "city": "São Paulo", "state": "SP",
            "bedrooms": 2, "bathrooms": 1, "area": 60, "garage": 1, "description": "TEST",
        }
        r = session.post(f"{API}/properties", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code == 200, r.text
        prop = r.json()
        pid = prop["id"]
        assert prop["title"].startswith("TEST_")

        # GET verify persistence
        r2 = session.get(f"{API}/properties/{pid}", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["price"] == 3500.0

        # UPDATE
        payload["price"] = 3700.0
        r3 = session.put(f"{API}/properties/{pid}", headers=auth_headers, json=payload, timeout=20)
        assert r3.status_code == 200
        assert r3.json()["price"] == 3700.0

        # DELETE
        r4 = session.delete(f"{API}/properties/{pid}", headers=auth_headers, timeout=20)
        assert r4.status_code == 200

        # Verify deletion
        r5 = session.get(f"{API}/properties/{pid}", headers=auth_headers, timeout=20)
        assert r5.status_code == 404


class TestClientCRUD:
    def test_create_and_delete_client(self, session, auth_headers):
        payload = {
            "name": "TEST_Client", "cpf_cnpj": "000.000.000-00",
            "phone": "(11) 90000-0000", "type": "inquilino",
            "email": "test@x.com", "address": "TEST", "notes": "",
        }
        r = session.post(f"{API}/clients", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code == 200
        cid = r.json()["id"]
        # Verify persistence via list
        r2 = session.get(f"{API}/clients/{cid}", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["name"] == "TEST_Client"
        # cleanup
        r3 = session.delete(f"{API}/clients/{cid}", headers=auth_headers, timeout=20)
        assert r3.status_code == 200


class TestReceiptCRUD:
    def test_create_receipt_generates_number(self, session, auth_headers):
        # need real client ids
        r = session.get(f"{API}/clients", headers=auth_headers, timeout=20)
        clients = r.json()
        assert len(clients) >= 2
        payer = clients[0]["id"]
        receiver = clients[1]["id"]
        payload = {
            "type": "aluguel", "payer_id": payer, "receiver_id": receiver,
            "value": 1000.0, "reference": "TEST_REF",
            "payment_date": "2026-01-15", "payment_method": "PIX", "notes": "TEST",
        }
        r2 = session.post(f"{API}/receipts", headers=auth_headers, json=payload, timeout=20)
        assert r2.status_code == 200, r2.text
        rec = r2.json()
        assert rec["receipt_number"].startswith("REC-")
        rid = rec["id"]
        # cleanup
        r3 = session.delete(f"{API}/receipts/{rid}", headers=auth_headers, timeout=20)
        assert r3.status_code == 200
