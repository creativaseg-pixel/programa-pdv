# Sistema Imobiliária - PRD

## Visão geral
Sistema completo de gestão imobiliária mobile (Expo React Native) + FastAPI + MongoDB para corretores e gestores no Brasil. Cobre toda a operação: cadastro, contratos, recibos e cálculos automáticos baseados em padrões de mercado brasileiro 2026.

## Tela / Funcionalidades

### Autenticação (JWT)
- Cadastro: nome, email, senha, empresa (opcional), CRECI
- Login com persistência (AsyncStorage)
- Token JWT 7 dias; logout limpa o token

### Painel (Dashboard)
- KPIs: imóveis ativos, clientes, contratos vigentes, recebimentos do mês, comissão do mês
- Hero card: receita do mês destacada
- Índices de mercado atualizados (IGPM/IPCA)
- Portfólio: valor total venda e valor mensal locação

### Imóveis
- Lista filtrável (todos / venda / locação)
- Cadastro completo: título, tipo (casa/apto/terreno/comercial), operação, preço, endereço, quartos, banheiros, vagas, área, descrição, imagem, proprietário
- Editar e excluir (long press)

### Clientes
- Filtros por tipo (proprietário, inquilino, comprador)
- Avatar colorido por tipo
- Campos: nome, CPF/CNPJ, telefone, email, endereço, observações

### Calculadora (cálculos automáticos)
- **Reajuste**: aplica IGPM (4.5%) ou IPCA (4.62%) com percentual customizável
- **Multa/Juros**: padrão Lei do Inquilinato (10% multa + 1% a.m.)
- **Comissão**: 6% venda (COFECI) / 100% (1 aluguel) locação

### Documentos
- **Contratos**: Locação (Lei 8.245/91) e Compra e Venda (Código Civil)
  - Cláusulas de reajuste IGPM/IPCA, multa e juros, caução
  - Modelo profissional com partes, imóvel, condições, vigência, assinaturas
- **Recibos**: numerados (REC-AAAAMMDD-XXXXXX) com valor por extenso
- Exportação via Share API (WhatsApp, email, etc.)

## API endpoints
- `POST /api/auth/register` `/login` `GET /me`
- CRUD `/api/properties` `/api/clients` `/api/contracts` `/api/receipts`
- `POST /api/calc/reajuste` `/multa-juros` `/comissao`
- `GET /api/dashboard/stats` `/indices`

## Stack
- Frontend: Expo Router, React Native, AsyncStorage, @expo/vector-icons
- Backend: FastAPI, Motor (async MongoDB), bcrypt, PyJWT
- Database: MongoDB

## Conta Demo
- email: demo@imobiliaria.com
- senha: demo1234
- Re-seed: `cd /app/backend && python seed_demo.py`
