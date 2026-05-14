# 📦 PDV Supermercado — Gerar Instalador Profissional para Windows

Este guia te leva passo a passo para transformar o `pdv_supermercado.py` em um instalador `.exe` profissional para Windows 10/11 (32 e 64 bits), sem dependência de Python no PC do cliente.

---

## ✅ Pré-requisitos (instale uma única vez no seu PC de desenvolvimento)

### 1. Python 3.10+ (64 bits — para gerar exe 64-bit)
- Baixe em: https://www.python.org/downloads/
- ⚠️ **MARQUE** a opção "Add Python to PATH" durante a instalação

### 2. Inno Setup (gratuito)
- Baixe em: https://jrsoftware.org/isinfo.php
- Instale a versão "Stable" (Inno Setup 6 ou superior)

### 3. (Opcional) Python 3.10 32-bit
- Apenas se você precisa de instalador para Windows 32-bit
- Baixe a versão "Windows installer (32-bit)" no python.org
- Instale em pasta separada (ex: `C:\Python310-32\`)

---

## 🚀 Passo a passo — Build 64-bit (padrão)

### Etapa 1 — Preparar a pasta
1. Crie uma pasta no PC: `C:\Build_PDV\`
2. Copie para dentro dela:
   - `pdv_supermercado.py` (seu código)
   - `pdv_supermercado.spec` (deste pacote)
   - `version_info.txt` (deste pacote)
   - `pdv_installer.iss` (deste pacote)
   - `icone.ico` — **crie ou baixe um ícone 256x256** (pode usar https://convertio.co/png-ico para converter PNG)
   - `README.txt` — copie o conteúdo deste arquivo ou crie um manual do usuário

### Etapa 2 — Instalar dependências Python
Abra o **Prompt de Comando (cmd)** dentro da pasta `C:\Build_PDV\` e rode:

```bash
pip install pyinstaller pillow qrcode[pil]
```

### Etapa 3 — Gerar o executável (.exe)
Na mesma pasta, no cmd:

```bash
pyinstaller pdv_supermercado.spec --clean
```

Aguarde 2-5 minutos. Resultado:
- `C:\Build_PDV\dist\PDV_Supermercado.exe` ← **executável standalone, sem Python**

### Etapa 4 — Teste o .exe
Dê duplo clique em `dist\PDV_Supermercado.exe` para validar que abre normalmente. Teste o login, cadastros, etc.

### Etapa 5 — Compilar o instalador com Inno Setup
1. Abra o **Inno Setup Compiler** (atalho instalado no Menu Iniciar)
2. Menu **File → Open** → selecione `C:\Build_PDV\pdv_installer.iss`
3. Menu **Build → Compile** (ou aperte `F9`)
4. Aguarde ~1 minuto. Resultado:
   - `C:\Build_PDV\output\setup_PDV_Supermercado_v1.0.0.exe` ← **instalador profissional**

### Etapa 6 — Distribuir
- Envie o arquivo `setup_PDV_Supermercado_v1.0.0.exe` por:
  - Pendrive
  - Email (se < 25MB)
  - Google Drive / WeTransfer
  - Site da sua empresa
- O cliente apenas executa, aceita os termos, escolhe a pasta e clica em **Instalar**
- Atalho criado no **Menu Iniciar** e na **Área de Trabalho**

---

## 🖥️ Build 32-bit (opcional — só se precisar)

Se algum cliente ainda usa Windows 10 32-bit (raro em 2026):

1. Instale **Python 3.10 32-bit** num caminho separado: `C:\Python310-32\`
2. Crie outra pasta: `C:\Build_PDV_32\` e copie os mesmos arquivos
3. Use o pip do Python 32-bit:
   ```bash
   C:\Python310-32\Scripts\pip.exe install pyinstaller pillow qrcode[pil]
   C:\Python310-32\Scripts\pyinstaller.exe pdv_supermercado.spec --clean
   ```
4. Renomeie o resultado: `dist\PDV_Supermercado.exe` → `dist\PDV_Supermercado_32.exe`
5. Edite `pdv_installer.iss` para apontar pro novo arquivo e mude `ArchitecturesAllowed=x86` e remova `x64`
6. Compile no Inno Setup → vai gerar `setup_PDV_Supermercado_v1.0.0_32bits.exe`

---

## 📁 Onde ficam os dados após instalado

O instalador cria automaticamente esta estrutura:

```
C:\Program Files\PDV Supermercado\
├── PDV_Supermercado.exe         ← executável
├── icone.ico
└── README.txt

C:\ProgramData\PDV Supermercado\  ← dados do usuário (banco, backups, logs)
├── pdv.db                        ← banco SQLite (criado no 1º uso)
├── backups\
└── logs\
```

> ⚠️ **Importante**: ajuste seu código Python para criar o banco em `%PROGRAMDATA%\PDV Supermercado\pdv.db` em vez da pasta do .exe. Caminho recomendado:
> ```python
> import os
> DATA_DIR = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'PDV Supermercado')
> os.makedirs(DATA_DIR, exist_ok=True)
> DB_PATH = os.path.join(DATA_DIR, 'pdv.db')
> ```

---

## 🔄 Atualizar versão futura

Quando lançar v1.1.0:
1. Mude `AppVersion "1.0.0"` → `"1.1.0"` em `pdv_installer.iss`
2. Mude `filevers=(1, 0, 0, 0)` → `(1, 1, 0, 0)` em `version_info.txt`
3. Recompile o .exe e o instalador
4. O instalador atualiza automaticamente sobre a versão antiga, **mantendo o banco de dados** do cliente

O script Inno Setup já mata o processo do PDV antes de atualizar e pergunta se quer remover o banco ao desinstalar.

---

## ❓ Problemas comuns

| Erro | Solução |
|------|---------|
| `pyinstaller` não é reconhecido | Reinstale Python marcando "Add to PATH" |
| `.exe` muito grande (>100MB) | Já incluímos `upx=True`. Baixe UPX e adicione ao PATH para comprimir mais |
| Falha ao abrir Pillow/qrcode | Confirme `pip install pillow qrcode[pil]` no Python correto |
| Antivírus bloqueia o .exe | Comum com PyInstaller. Assine digitalmente o .exe com certificado (custo: ~R$300/ano) |
| Erro "msvcp140.dll missing" | Instale o **Microsoft Visual C++ Redistributable** no PC do cliente |

---

## 📞 Suporte

Em caso de dúvida no build, abra novamente o Emergent e descreva o erro exato (mensagem completa do cmd).
