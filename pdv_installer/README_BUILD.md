# 📦 PDV Supermercado — Build Multi-Arquitetura (32 + 64 bits)

Guia para gerar **UM ÚNICO instalador** que funciona tanto em Windows 32-bit quanto 64-bit (detecta automaticamente).

---

## ✅ Pré-requisitos

| Item | Versão | Onde baixar |
|------|--------|-------------|
| Python 64-bit | 3.12 | https://python.org → **MARQUE "Add to PATH"** |
| Python 32-bit | 3.9.13 | https://python.org → versão "Windows installer (32-bit)" |
| Inno Setup | 6 | https://jrsoftware.org/isinfo.php |

### Instalação recomendada
- Python 3.12 (64-bit): instalar normalmente, **com PATH**
- Python 3.9.13 (32-bit): instalar em pasta separada, por exemplo `C:\Python39-32\`, **sem adicionar ao PATH** (para não conflitar)

---

## 🚀 Build automatizado (recomendado)

### Etapa 1 — Prepare a pasta
1. Crie `C:\Build_PDV\`
2. Copie TODOS os arquivos do pacote pra dentro
3. Adicione um arquivo `icone.ico` (256x256) — converter PNG: https://convertio.co/png-ico

### Etapa 2 — Ajuste o build_32.bat (se necessário)
Abra `build_32.bat` no Bloco de Notas e confirme a linha:
```bat
set PY32="C:\Python39-32\python.exe"
```
Se seu Python 3.9.13 32-bit estiver em **outro lugar**, ajuste essa linha. O script já tenta vários caminhos comuns automaticamente.

### Etapa 3 — Execute o build completo
Duplo clique em **`build_all.bat`** OU no cmd:
```bash
cd C:\Build_PDV
build_all.bat
```

Em ~10 minutos você terá:
- ✅ `dist\PDV_Supermercado_x64.exe` (executável Windows 64-bit)
- ✅ `dist\PDV_Supermercado_x86.exe` (executável Windows 32-bit)
- ✅ `output\setup_PDV_Supermercado_v1.0.0.exe` ← **instalador único pra distribuir**

---

## 🧪 Build de cada arquitetura separadamente

Se preferir gerar uma por vez:

```bash
build_64.bat   :: só 64-bit
build_32.bat   :: só 32-bit
```

---

## 🎯 Como o instalador único funciona

Quando o cliente roda `setup_PDV_Supermercado_v1.0.0.exe`:

1. Inno Setup detecta a arquitetura do Windows
2. **Se Windows 64-bit**: extrai e instala `PDV_Supermercado_x64.exe`
3. **Se Windows 32-bit**: extrai e instala `PDV_Supermercado_x86.exe`
4. Em ambos os casos, o arquivo instalado se chama `PDV_Supermercado.exe`
5. Atalhos no Menu Iniciar e Área de Trabalho apontam pra `PDV_Supermercado.exe`

**Resultado**: o cliente nem percebe que existem duas versões — apenas o programa funciona perfeitamente no PC dele.

---

## 📊 Tamanhos esperados

| Arquivo | Tamanho aprox. |
|---------|----------------|
| `PDV_Supermercado_x64.exe` | 25-35 MB |
| `PDV_Supermercado_x86.exe` | 22-30 MB |
| `setup_PDV_Supermercado_v1.0.0.exe` | 35-50 MB (LZMA2 ultra comprime os dois exes) |

---

## ⚠️ Avisos importantes

### Pillow no Python 3.9 32-bit
A versão mais recente do Pillow pode não ter wheels para Python 3.9 32-bit. Se der erro:
```bash
C:\Python39-32\python.exe -m pip install "pillow<10.4" "qrcode[pil]"
```

### Antivírus pode bloquear o .exe
PyInstaller gera arquivos que alguns antivírus detectam como falso positivo. Soluções:
- Adicione a pasta `C:\Build_PDV\dist\` na exceção do antivírus
- **Solução profissional**: assine digitalmente os .exe com certificado de assinatura de código (custo: ~R$300/ano via Certisign, Valid, etc.)

### Tela "Aviso de Segurança do Windows SmartScreen"
Como o instalador não tem assinatura digital ainda, o Windows pode mostrar uma tela azul ao abrir. O cliente clica em **"Mais informações"** → **"Executar assim mesmo"**. Solução definitiva: certificado de assinatura.

---

## 🔄 Atualização de versão futura

Quando lançar v1.1.0:
1. Edite `pdv_installer.iss` → mude `AppVersion "1.0.0"` para `"1.1.0"`
2. Edite `version_info.txt` → mude `filevers=(1, 0, 0, 0)` para `(1, 1, 0, 0)`
3. Rode `build_all.bat`
4. Distribua o novo `setup_PDV_Supermercado_v1.1.0.exe`

O instalador automaticamente:
- ✅ Fecha o PDV se estiver aberto
- ✅ Substitui o .exe pela nova versão
- ✅ **Mantém o banco de dados** do cliente intacto
- ✅ Mantém configurações e backups

---

## 📁 Estrutura final no PC do cliente

```
C:\Program Files\PDV Supermercado\          (Program Files (x86)\... se 32-bit)
├── PDV_Supermercado.exe       ← versão correta da arquitetura
├── icone.ico
├── README.txt
└── unins000.exe               ← desinstalador

C:\ProgramData\PDV Supermercado\            (dados do usuário)
├── dados_pdv.db               ← banco SQLite
├── backups\
├── qrcodes\
└── etiquetas\
```

---

## 🆘 Problemas comuns

| Erro | Solução |
|------|---------|
| `'python' não é reconhecido como comando` | Reinstale Python 3.12 marcando "Add to PATH" |
| `Nao encontrei o Python 3.9.13 32-bit` | Edite `build_32.bat`, ajuste a variável `PY32` |
| `dist\PDV_Supermercado_x86.exe nao encontrado` | Build 32-bit falhou. Rode `build_32.bat` separado para ver o erro |
| Erro de Pillow no Python 32-bit | `C:\Python39-32\python.exe -m pip install "pillow<10.4"` |
| Inno Setup não compila | Confirme instalação em `C:\Program Files (x86)\Inno Setup 6\` |
| `.exe` muito grande (>100MB) | Já incluímos `upx=True` no spec. Para comprimir mais, baixe UPX |
| `msvcp140.dll missing` no cliente | Distribua Microsoft Visual C++ Redistributable junto |

---

## 📞 Suporte

Em caso de erro, copie a mensagem do cmd e abra novamente o Emergent para ajuda.
