import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import datetime
from datetime import timezone, timedelta
import random
import os
import sys
import gc
import json
import shutil
from tkinter import filedialog
# =============================================================================
# IMPORTAÇÃO SEGURA DE BIBLIOTECAS OPCIONAIS
# =============================================================================

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    PIL_DISPONIVEL = True
except ImportError:
    PIL_DISPONIVEL = False
    # Stubs para evitar NameError quando PIL não está instalado
    class _ImageStub:
        class Resampling:
            LANCZOS = None
        @staticmethod
        def new(*args, **kwargs):
            return None
        @staticmethod
        def open(*args, **kwargs):
            return None
    class _ImageDrawStub:
        @staticmethod
        def Draw(*args, **kwargs):
            return None
    class _ImageFontStub:
        @staticmethod
        def truetype(*args, **kwargs):
            return None
        @staticmethod
        def load_default(*args, **kwargs):
            return None
    class _ImageTkStub:
        @staticmethod
        def PhotoImage(*args, **kwargs):
            return None
    Image = _ImageStub()
    ImageDraw = _ImageDrawStub()
    ImageFont = _ImageFontStub()
    ImageTk = _ImageTkStub()

try:
    import qrcode
    QRCODE_DISPONIVEL = True
except ImportError:
    QRCODE_DISPONIVEL = False

# Compatibilidade Pillow < 9.1
if PIL_DISPONIVEL:
    try:
        if not hasattr(Image, 'Resampling') or Image.Resampling.LANCZOS is None:
            class _Resampling:
                LANCZOS = Image.LANCZOS if hasattr(Image, 'LANCZOS') else (Image.ANTIALIAS if hasattr(Image, 'ANTIALIAS') else None)
            Image.Resampling = _Resampling()
    except:
        pass

import re
import getpass  # Para identificar usuário no log administrativo

# =============================================================================
# CONFIGURAÇÃO DE FUSO HORÁRIO - BRASIL (UTC-3)
# =============================================================================

# Força o timezone do Brasil independente do servidor
BRASIL_TZ = timezone(timedelta(hours=-3))

# =============================================================================
# CONFIGURAÇÃO DE FUSO HORÁRIO - BRASIL (UTC-3) - VERSÃO ROBUSTA
# =============================================================================

def get_brasil_now():
    """Retorna datetime com hora atual do servidor (horário local)"""
    return datetime.datetime.now()

def get_brasil_today():
    """Retorna date com data atual do servidor"""
    return datetime.date.today()

def get_brasil_strftime(formato='%Y-%m-%d %H:%M:%S'):
    """Retorna string formatada do horário local"""
    return datetime.datetime.now().strftime(formato)

def get_brasil_strftime_iso():
    """Retorna string ISO formatada do horário local para SQLite"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Constante BRASIL_TZ mantida para compatibilidade
BRASIL_TZ = datetime.timezone(datetime.timedelta(hours=-3))
gc.enable()


def get_app_path():
    """
    Retorna a pasta de DADOS do aplicativo (banco, backups, etc).

    Quando o programa é executado a partir do instalador Inno Setup, os dados
    devem ficar em C:\\ProgramData\\PDV Supermercado\\ — pasta compartilhada
    entre todos os usuários do Windows e gravável sem precisar de admin.

    Em modo de desenvolvimento (rodando direto o .py) usa a pasta do script.
    """
    if getattr(sys, 'frozen', False):
        # Executável (PyInstaller): usa C:\ProgramData\PDV Supermercado
        base = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
        data_dir = os.path.join(base, 'PDV Supermercado')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        return data_dir
    else:
        # Desenvolvimento: pasta do .py
        return os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    return os.path.join(get_app_path(), "dados_pdv.db")

def get_backup_path():
    backup_dir = os.path.join(get_app_path(), "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def get_qrcode_path():
    qrcode_dir = os.path.join(get_app_path(), "qrcodes")
    if not os.path.exists(qrcode_dir):
        os.makedirs(qrcode_dir)
    return qrcode_dir

def get_etiquetas_path():
    etiquetas_dir = os.path.join(get_app_path(), "etiquetas")
    if not os.path.exists(etiquetas_dir):
        os.makedirs(etiquetas_dir)
    return etiquetas_dir


# =============================================================================
# CONFIGURACOES DE ESTILO WINDOWS 95
# =============================================================================

class Win95Style:
    """Estilo visual retro Windows 95 para o sistema"""

    BG_GRAY = "#c0c0c0"
    DARK_GRAY = "#808080"
    LIGHT_GRAY = "#dfdfdf"
    WHITE = "#ffffff"
    BLACK = "#000000"
    NAVY = "#000080"

    SUCCESS = "#2e7d32"
    WARNING = "#ed6c02"
    DANGER = "#d32f2f"
    INFO = "#0288d1"

    @staticmethod
    def create_button(parent, text, command, bg_color=None, fg_color="black", 
                     font=('MS Sans Serif', 9), width=None, height=None, **kwargs):
        """Cria botao estilo Windows 95 com borda 3D"""
        if bg_color is None:
            bg_color = Win95Style.BG_GRAY

        btn = tk.Button(parent, text=text, command=command,
                       bg=bg_color, fg=fg_color,
                       font=font, width=width, height=height,
                       relief='raised', bd=2,
                       cursor="hand2",
                       **kwargs)

        def on_press(event):
            btn.config(relief='sunken')

        def on_release(event):
            btn.config(relief='raised')

        btn.bind('<Button-1>', on_press)
        btn.bind('<ButtonRelease-1>', on_release)

        return btn


# =============================================================================
# TELA DE CADASTRO DE CLIENTES - ESTILO WIN95
# =============================================================================

class CadastroClientes:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Clientes")
        self.janela.geometry("900x650")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db

        self.create_interface()
        self.carregar_clientes()

        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="CADASTRO DE CLIENTES", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Formulário
        form = tk.LabelFrame(self.janela, text=" NOVO CLIENTE ", 
                            font=('MS Sans Serif', 9, 'bold'),
                            bg=Win95Style.BG_GRAY)
        form.pack(fill='x', padx=10, pady=10)

        # Linha 1
        tk.Label(form, text="Nome:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.nome_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nome_var, width=40,
                font=('MS Sans Serif', 10)).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(form, text="CPF:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.cpf_var = tk.StringVar()
        tk.Entry(form, textvariable=self.cpf_var, width=15,
                font=('MS Sans Serif', 10)).grid(row=0, column=3, padx=5, pady=5)

        # Linha 2
        tk.Label(form, text="Telefone:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.telefone_var = tk.StringVar()
        tk.Entry(form, textvariable=self.telefone_var, width=15,
                font=('MS Sans Serif', 10)).grid(row=1, column=1, padx=5, pady=5, sticky='w')

        tk.Label(form, text="Email:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.email_var = tk.StringVar()
        tk.Entry(form, textvariable=self.email_var, width=25,
                font=('MS Sans Serif', 10)).grid(row=1, column=3, padx=5, pady=5)

        # Linha 3
        tk.Label(form, text="Endereço:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.endereco_var = tk.StringVar()
        tk.Entry(form, textvariable=self.endereco_var, width=60,
                font=('MS Sans Serif', 10)).grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='w')

        # Botões
        btn_frame = tk.Frame(form, bg=Win95Style.BG_GRAY)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)

        Win95Style.create_button(btn_frame, "💾 SALVAR (F2)", self.salvar,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🔍 CONSULTAR HISTÓRICO (F3)", self.consultar_historico,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=22).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🔄 LIMPAR", self.limpar,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=12).pack(side='left', padx=5)

        # Lista
        lista_frame = tk.LabelFrame(self.janela, text=" CLIENTES CADASTRADOS ", 
                                   font=('MS Sans Serif', 9, 'bold'),
                                   bg=Win95Style.BG_GRAY)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'nome', 'cpf', 'telefone', 'email', 'total_gasto')
        self.tree = ttk.Treeview(lista_frame, columns=cols, show='headings', height=12)

        for c in cols:
            self.tree.heading(c, text=c.upper())
            if c == 'nome':
                self.tree.column(c, width=200)
            elif c == 'email':
                self.tree.column(c, width=150)
            elif c == 'total_gasto':
                self.tree.column(c, width=100, anchor='e')
            else:
                self.tree.column(c, width=100, anchor='center')

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        # Resumo
        resumo_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        resumo_frame.pack(fill='x', padx=10, pady=5)

        self.total_clientes_label = tk.Label(resumo_frame, text="Total de Clientes: 0", 
                                            font=('MS Sans Serif', 10, 'bold'),
                                            bg=Win95Style.NAVY, fg="white", padx=10, pady=5)
        self.total_clientes_label.pack(side='left', padx=5)

        Win95Style.create_button(resumo_frame, "❌ FECHAR (ESC)", self.fechar,
                                font=('MS Sans Serif', 9, 'bold'), width=12).pack(side='right', padx=5)

        # Atalhos
        self.janela.bind('<F2>', lambda e: self.salvar())
        self.janela.bind('<F3>', lambda e: self.consultar_historico())
        self.janela.bind('<Escape>', lambda e: self.fechar())

    def salvar(self):
        nome = self.nome_var.get().strip()
        cpf = self.cpf_var.get().strip()

        if not nome:
            messagebox.showerror("Erro", "Informe o nome do cliente!")
            return

        if not cpf:
            messagebox.showerror("Erro", "Informe o CPF!")
            return

        try:
            cliente_id = self.db.cadastrar_cliente(
                nome, 
                cpf,
                self.telefone_var.get(),
                self.email_var.get(),
                self.endereco_var.get()
            )

            if cliente_id:
                messagebox.showinfo("Sucesso", f"Cliente cadastrado com sucesso!\nID: {cliente_id}")
                self.limpar()
                self.carregar_clientes()
            else:
                # Verificar se é CPF duplicado ou outro erro
                cliente_existente = self.db.buscar_cliente_por_cpf(cpf)
                if cliente_existente:
                    messagebox.showerror("Erro", f"CPF já cadastrado!\nCliente: {cliente_existente[1]}")
                else:
                    messagebox.showerror("Erro", "Erro ao cadastrar cliente. Verifique o console para mais detalhes.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")

    def consultar_historico(self):
        selecionado = self.tree.selection()
        if not selecionado:
            # Tenta pelo CPF digitado
            cpf = self.cpf_var.get().strip()
            if not cpf:
                messagebox.showwarning("Aviso", "Selecione um cliente ou digite o CPF!")
                return
        else:
            valores = self.tree.item(selecionado[0])['values']
            cpf = valores[2]

        historico = self.db.get_historico_cliente(cpf)

        if not historico:
            messagebox.showinfo("Histórico", "Nenhuma compra encontrada para este cliente.")
            return

        # Mostra janela com histórico
        janela = tk.Toplevel(self.janela)
        janela.title(f"Histórico de Compras - CPF: {cpf}")
        janela.geometry("700x500")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.resizable(False, False)

        header = tk.Frame(janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="HISTÓRICO DE COMPRAS", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        cols = ('cupom', 'data', 'valor', 'pagamento', 'parcelas')
        tree = ttk.Treeview(janela, columns=cols, show='headings', height=15)

        for c in cols:
            tree.heading(c, text=c.upper())

        tree.column('cupom', width=120, anchor='center')
        tree.column('data', width=150, anchor='center')
        tree.column('valor', width=100, anchor='e')
        tree.column('pagamento', width=100, anchor='center')
        tree.column('parcelas', width=80, anchor='center')

        scroll = ttk.Scrollbar(janela, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scroll.pack(side='right', fill='y', pady=10)

        for h in historico:
            data = datetime.datetime.strptime(h[1], '%Y-%m-%d %H:%M:%S')
            tree.insert('', 'end', values=(
                h[0],
                data.strftime('%d/%m/%Y %H:%M'),
                f"R$ {h[2]:.2f}",
                h[3].upper(),
                h[4]
            ))

        Win95Style.create_button(janela, "Fechar", janela.destroy, width=15).pack(pady=10)

    def carregar_clientes(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        clientes = self.db.get_all_clientes()

        for c in clientes:
            self.tree.insert('', 'end', values=(
                c[0], c[1], c[2], c[3], c[4], f"R$ {c[5]:.2f}"
            ))

        self.total_clientes_label.config(text=f"Total de Clientes: {len(clientes)}")

    def limpar(self):
        self.nome_var.set('')
        self.cpf_var.set('')
        self.telefone_var.set('')
        self.email_var.set('')
        self.endereco_var.set('')

    def fechar(self):
        self.janela.destroy()

# =============================================================================
# TELA DE CADASTRO DE FIADOS E PARCELADOS - ESTILO WIN95
# =============================================================================

class CadastroFiados:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Fiados e Parcelados")
        self.janela.geometry("900x650")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db

        self.create_interface()
        self.carregar_fiados()

        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="CADASTRO DE FIADOS / PARCELADOS", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Formulário
        form = tk.LabelFrame(self.janela, text=" NOVO REGISTRO ", 
                            font=('MS Sans Serif', 9, 'bold'),
                            bg=Win95Style.BG_GRAY)
        form.pack(fill='x', padx=10, pady=10)

        # Linha 1
        tk.Label(form, text="Cliente:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.cliente_var = tk.StringVar()
        tk.Entry(form, textvariable=self.cliente_var, width=40,
                font=('MS Sans Serif', 10)).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(form, text="Telefone:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.telefone_var = tk.StringVar()
        tk.Entry(form, textvariable=self.telefone_var, width=15,
                font=('MS Sans Serif', 10)).grid(row=0, column=3, padx=5, pady=5)

        # CPF
        tk.Label(form, text="CPF:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=4, padx=5, pady=5, sticky='e')
        self.cpf_fiado_var = tk.StringVar()
        tk.Entry(form, textvariable=self.cpf_fiado_var, width=15,
                font=('MS Sans Serif', 10)).grid(row=0, column=5, padx=5, pady=5)

        # Linha 2
        tk.Label(form, text="Valor Total R$:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.valor_var = tk.StringVar()
        tk.Entry(form, textvariable=self.valor_var, width=15,
                font=('MS Sans Serif', 10)).grid(row=1, column=1, padx=5, pady=5, sticky='w')

        tk.Label(form, text="Tipo:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.tipo_var = tk.StringVar(value="Fiado")
        combo_tipo = ttk.Combobox(form, textvariable=self.tipo_var, 
                                 values=["Fiado", "Parcelado"], width=15)
        combo_tipo.grid(row=1, column=3, padx=5, pady=5)

        # Linha 3
        tk.Label(form, text="Descrição:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.desc_var = tk.StringVar()
        tk.Entry(form, textvariable=self.desc_var, width=60,
                font=('MS Sans Serif', 10)).grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='w')

        # Linha 4 - Parcelas (se for parcelado)
        tk.Label(form, text="Nº Parcelas:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.parcelas_var = tk.StringVar(value="1")
        tk.Entry(form, textvariable=self.parcelas_var, width=10,
                font=('MS Sans Serif', 10)).grid(row=3, column=1, padx=5, pady=5, sticky='w')

        tk.Label(form, text="Vencimento:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=3, column=2, padx=5, pady=5, sticky='e')
        self.vencimento_var = tk.StringVar(value=get_brasil_today().strftime('%d/%m/%Y'))
        tk.Entry(form, textvariable=self.vencimento_var, width=15,
                font=('MS Sans Serif', 10)).grid(row=3, column=3, padx=5, pady=5)

        # Botões
        btn_frame = tk.Frame(form, bg=Win95Style.BG_GRAY)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=15)

        Win95Style.create_button(btn_frame, "💾 SALVAR (F2)", self.salvar,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "💰 REGISTRAR PAGAMENTO (F3)", self.registrar_pagamento,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=22).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🔄 LIMPAR", self.limpar,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=12).pack(side='left', padx=5)

        # Lista
        lista_frame = tk.LabelFrame(self.janela, text=" REGISTROS CADASTRADOS ", 
                                   font=('MS Sans Serif', 9, 'bold'),
                                   bg=Win95Style.BG_GRAY)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'cliente', 'telefone', 'valor', 'tipo', 'parcelas', 'vencimento', 'status')
        self.tree = ttk.Treeview(lista_frame, columns=cols, show='headings', height=12)

        for c in cols:
            self.tree.heading(c, text=c.upper())
            if c == 'cliente':
                self.tree.column(c, width=200)
            elif c == 'valor':
                self.tree.column(c, width=80, anchor='e')
            elif c in ['id', 'parcelas']:
                self.tree.column(c, width=60, anchor='center')
            else:
                self.tree.column(c, width=100, anchor='center')

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        # Resumo
        resumo_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        resumo_frame.pack(fill='x', padx=10, pady=5)

        self.total_fiado_label = tk.Label(resumo_frame, text="Total Fiado: R$ 0,00", 
                                         font=('MS Sans Serif', 10, 'bold'),
                                         bg=Win95Style.DANGER, fg="white", padx=10, pady=5)
        self.total_fiado_label.pack(side='left', padx=5)

        self.total_parcelado_label = tk.Label(resumo_frame, text="Total Parcelado: R$ 0,00", 
                                             font=('MS Sans Serif', 10, 'bold'),
                                             bg=Win95Style.WARNING, fg="white", padx=10, pady=5)
        self.total_parcelado_label.pack(side='left', padx=5)

        Win95Style.create_button(resumo_frame, "📄 IMPRIMIR RESUMO (F4)", self.imprimir_resumo,
                                bg_color="#9C27B0", fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='right', padx=5)

        Win95Style.create_button(resumo_frame, "❌ FECHAR (ESC)", self.fechar,
                                font=('MS Sans Serif', 9, 'bold'), width=12).pack(side='right', padx=5)

        # Atalhos
        self.janela.bind('<F2>', lambda e: self.salvar())
        self.janela.bind('<F3>', lambda e: self.registrar_pagamento())
        self.janela.bind('<F4>', lambda e: self.imprimir_resumo())
        self.janela.bind('<Escape>', lambda e: self.fechar())

    def salvar(self):
        cliente = self.cliente_var.get().strip()
        if not cliente:
            messagebox.showerror("Erro", "Informe o nome do cliente!")
            return

        try:
            valor = float(self.valor_var.get().replace(',', '.'))
            parcelas = int(self.parcelas_var.get())
        except:
            messagebox.showerror("Erro", "Valor ou parcelas inválidos!")
            return

        # Busca ou cadastra cliente pelo CPF
        cpf = self.cpf_fiado_var.get().strip()
        cliente_id = None
        if cpf:
            cliente_db = self.db.buscar_cliente_por_cpf(cpf)
            if cliente_db:
                cliente_id = cliente_db[0]

        # Salva no banco de dados
        fiado_id = self.db.add_fiado(
            cliente_id,
            cliente, 
            self.telefone_var.get(),
            valor,
            self.tipo_var.get(),
            self.desc_var.get(),
            parcelas,
            self.vencimento_var.get(),
            cpf
        )

        if fiado_id:
            messagebox.showinfo("Sucesso", f"Registro salvo!\nCliente: {cliente}\nValor: R$ {valor:.2f}")
            self.limpar()
            self.carregar_fiados()
        else:
            messagebox.showerror("Erro", "Não foi possível salvar o registro!")

    def registrar_pagamento(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um registro!")
            return

        valores = self.tree.item(selecionado[0])['values']
        fiado_id = valores[0]

        janela_pg = tk.Toplevel(self.janela)
        janela_pg.title("Registrar Pagamento")
        janela_pg.geometry("400x300")
        janela_pg.configure(bg=Win95Style.BG_GRAY)
        janela_pg.resizable(False, False)
        janela_pg.transient(self.janela)
        janela_pg.grab_set()

        tk.Label(janela_pg, text=f"Cliente: {valores[1]}", 
                font=('MS Sans Serif', 11, 'bold'), bg=Win95Style.BG_GRAY).pack(pady=10)
        tk.Label(janela_pg, text=f"Valor Restante: {valores[3]}", 
                font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack()

        tk.Label(janela_pg, text="Valor Pago R$:", 
                font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(pady=(20, 5))

        pg_var = tk.StringVar(value="0")
        tk.Entry(janela_pg, textvariable=pg_var, font=('MS Sans Serif', 14), 
                width=15, justify='center').pack()

        def confirmar():
            try:
                val = float(pg_var.get().replace(',', '.'))
                if val <= 0:
                    messagebox.showerror("Erro", "Valor deve ser maior que zero!", parent=janela_pg)
                    return

                if self.db.registrar_pagamento_fiado(fiado_id, val):
                    messagebox.showinfo("Sucesso", f"Pagamento de R$ {val:.2f} registrado!", parent=janela_pg)
                    janela_pg.destroy()
                    self.carregar_fiados()
                else:
                    messagebox.showerror("Erro", "Não foi possível registrar o pagamento!", parent=janela_pg)
            except:
                messagebox.showerror("Erro", "Valor inválido!", parent=janela_pg)

        Win95Style.create_button(janela_pg, "CONFIRMAR PAGAMENTO", confirmar,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 11, 'bold'), width=20).pack(pady=20)

    def carregar_fiados(self):
        # Limpa a lista
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Carrega do banco de dados
        fiados = self.db.get_all_fiados()

        for f in fiados:
            valor_restante = f[3] - f[4]
            self.tree.insert('', 'end', values=(
                f[0], f[1], f[2], f"R$ {valor_restante:.2f}", 
                f[5], f"{f[7]}/{f[6]}", f[8], f[9]
            ))

        # Atualiza totais
        totais = self.db.get_totais_fiados()
        total_fiado = totais[0] if totais and totais[0] else 0
        total_parcelado = totais[1] if totais and totais[1] else 0

        self.total_fiado_label.config(text=f"Total Fiado: R$ {total_fiado:.2f}")
        self.total_parcelado_label.config(text=f"Total Parcelado: R$ {total_parcelado:.2f}")

    def imprimir_resumo(self):
        """Imprime resumo de fiados e parcelados na impressora térmica"""
        try:
            linhas = []
            linhas.append("RESUMO DE FIADOS/PARCELADOS")
            linhas.append("=" * 35)
            linhas.append(f"Data: {get_brasil_now().strftime('%d/%m/%Y %H:%M')}")
            linhas.append("")

            # Cabeçalho
            linhas.append("CLIENTE              VALOR    TIPO")
            linhas.append("-" * 35)

            # Dados (aqui você pegaria do banco)
            for item in self.tree.get_children():
                vals = self.tree.item(item)['values']
                cliente = vals[1][:15].ljust(15)
                valor = str(vals[3]).rjust(8)
                tipo = vals[4][:8].ljust(8)
                linhas.append(f"{cliente} {valor} {tipo}")

            linhas.append("-" * 35)
            linhas.append(f"Total Fiado:    {self.total_fiado_label.cget('text').split(': ')[1].rjust(20)}")
            linhas.append(f"Total Parcelado: {self.total_parcelado_label.cget('text').split(': ')[1].rjust(19)}")
            linhas.append("=" * 35)
            linhas.append("")

            texto = "\n".join(linhas)

            with open("resumo_fiados_temp.txt", "w", encoding="utf-8") as f:
                f.write(texto)

            os.system(f'notepad /p "resumo_fiados_temp.txt"')
            messagebox.showinfo("Sucesso", "Resumo enviado para impressão!")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao imprimir: {str(e)}")

    def limpar(self):
        self.cliente_var.set('')
        self.telefone_var.set('')
        self.valor_var.set('')
        self.desc_var.set('')
        self.parcelas_var.set('1')
        self.vencimento_var.set(get_brasil_today().strftime('%d/%m/%Y'))

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# LOGGER ADMINISTRATIVO - ARQUIVO OCULTO
# =============================================================================

class LoggerAdministrativo:
    """Sistema de log em arquivo oculto para administradores
    Registra todas as vendas, aberturas e fechamentos de caixa do mês"""

    def __init__(self):
        self.arquivo_oculto = self._get_arquivo_oculto()
        self._garantir_arquivo_existe()

    def _get_arquivo_oculto(self):
        """Retorna o caminho do arquivo oculto na pasta do sistema"""
        app_path = get_app_path()
        # Nome discreto na pasta do sistema
        arquivo = os.path.join(app_path, ".sysdata_pdv.dat")
        return arquivo

    def _garantir_arquivo_existe(self):
        """Garante que o arquivo existe, cria cabeçalho se necessário"""
        if not os.path.exists(self.arquivo_oculto):
            with open(self.arquivo_oculto, 'w', encoding='utf-8') as f:
                f.write("=== LOG ADMINISTRATIVO PDV ===\n")
                f.write(f"Criado em: {get_brasil_now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("Acesso restrito ao administrador\n")
                f.write("=" * 50 + "\n\n")
            # Tornar arquivo oculto no Windows
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.arquivo_oculto, 2)  # 2 = FILE_ATTRIBUTE_HIDDEN
            except:
                pass

    def registrar_venda(self, numero_cupom, valor, forma_pagamento, operador, itens):
        """Registra uma venda no log"""
        with open(self.arquivo_oculto, 'a', encoding='utf-8') as f:
            f.write(f"\n[VENDA] {get_brasil_now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Cupom: {numero_cupom}\n")
            f.write(f"Valor: R$ {valor:.2f}\n")
            f.write(f"Forma: {forma_pagamento}\n")
            f.write(f"Operador: {operador}\n")
            f.write(f"Itens: {len(itens)}\n")
            f.write("-" * 40 + "\n")

    def registrar_abertura_caixa(self, operador, valor_abertura):
        """Registra abertura de caixa"""
        with open(self.arquivo_oculto, 'a', encoding='utf-8') as f:
            f.write(f"\n[ABERTURA CAIXA] {get_brasil_now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Operador: {operador}\n")
            f.write(f"Valor Abertura: R$ {valor_abertura:.2f}\n")
            f.write("-" * 40 + "\n")

    def registrar_fechamento_caixa(self, operador, valor_fechamento, totais):
        """Registra fechamento de caixa com todos os totais"""
        with open(self.arquivo_oculto, 'a', encoding='utf-8') as f:
            f.write(f"\n[FECHAMENTO CAIXA] {get_brasil_now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Operador: {operador}\n")
            f.write(f"Valor Fechamento: R$ {valor_fechamento:.2f}\n")
            f.write(f"Total Dinheiro: R$ {totais.get('dinheiro', 0):.2f}\n")
            f.write(f"Total Crédito: R$ {totais.get('credito', 0):.2f}\n")
            f.write(f"Total Débito: R$ {totais.get('debito', 0):.2f}\n")
            f.write(f"Total PIX: R$ {totais.get('pix', 0):.2f}\n")
            f.write(f"Total Fiado: R$ {totais.get('fiado', 0):.2f}\n")
            f.write(f"Total Parcelado: R$ {totais.get('parcelado', 0):.2f}\n")
            f.write("=" * 40 + "\n")

    def ler_log(self):
        """Lê todo o conteúdo do log (apenas para admin)"""
        try:
            with open(self.arquivo_oculto, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "Erro ao ler log administrativo"

    def exportar_para_txt(self, caminho):
        """Exporta o log para um arquivo TXT visível"""
        try:
            conteudo = self.ler_log()
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            return True
        except:
            return False

# =============================================================================
# GERADOR DE QR CODE PIX - PADRAO BANCO CENTRAL (EMVCo) - CORRIGIDO V2
# =============================================================================

class QRCodeGenerator:
    """Gerador de QR Code PIX seguindo padrao oficial do Banco Central"""

    def __init__(self):
        self.version = 2
        self.error_correction = 'M'

    def _calcular_crc16(self, payload):
        """Calcula CRC16-CCITT (0xFFFF) conforme especificacao EMVCo"""
        crc = 0xFFFF
        for char in payload:
            crc ^= ord(char) << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            crc &= 0xFFFF
        return f"{crc:04X}"

    def _criar_payload_pix(self, chave_pix, valor, descricao="Pagamento"):
        """Cria payload PIX seguindo padrao BRCode do Banco Central"""
        chave_pix = chave_pix.strip()

        # Valida e formata a chave
        chave_pix = self._formatar_chave_pix(chave_pix)

        # Dados do merchant (limitados por especificacao)
        merchant_name = "SUPERMERCADO"[:25]
        merchant_city = "BRASILIA"[:15]
        txid = "***"  # QR Estático usa TXID fixo

        payload = ""

        # 00: Payload Format Indicator (obrigatorio) - valor fixo "01"
        payload += "000201"

        # 01: Point of Initiation Method - "11" = QR estatico
        payload += "010211"

        # 26: Merchant Account Information (obrigatorio)
        gui = "br.gov.bcb.pix"
        campo_26 = f"00{len(gui):02d}{gui}01{len(chave_pix):02d}{chave_pix}"
        payload += f"26{len(campo_26):02d}{campo_26}"

        # 52: Merchant Category Code - "0000" para nao listado
        payload += "52040000"

        # 53: Transaction Currency - "986" = BRL (Real)
        payload += "5303986"

        # 54: Transaction Amount (condicional)
        if valor and valor > 0:
            valor_str = f"{valor:.2f}"
            payload += f"54{len(valor_str):02d}{valor_str}"

        # 58: Country Code - "BR"
        payload += "5802BR"

        # 59: Merchant Name (max 25 chars)
        merchant_name = merchant_name[:25]
        payload += f"59{len(merchant_name):02d}{merchant_name}"

        # 60: Merchant City (max 15 chars)
        merchant_city = merchant_city[:15]
        payload += f"60{len(merchant_city):02d}{merchant_city}"

        # 62: Additional Data Field Template (TXID)
        campo_62 = f"05{len(txid):02d}{txid}"
        payload += f"62{len(campo_62):02d}{campo_62}"

        # 63: CRC16
        payload_com_crc = payload + "6304"
        crc = self._calcular_crc16(payload_com_crc)
        payload_final = payload_com_crc + crc

        return payload_final

    def _formatar_chave_pix(self, chave):
        """Formata a chave PIX conforme tipo"""
        chave = chave.strip()

        # Remove espacos
        chave = chave.replace(" ", "")

        # Se for CPF/CNPJ, remove pontuacao
        if chave.replace(".", "").replace("-", "").replace("/", "").isdigit():
            chave = re.sub(r'[^0-9]', '', chave)

        # Se for email, converte para minusculo
        if "@" in chave:
            chave = chave.lower()

        # Se for telefone, garante formato internacional
        if chave.startswith("+"):
            chave = chave.replace("-", "").replace(" ", "")
        elif len(chave) == 11 and chave.isdigit():  # Celular brasileiro sem +
            chave = "+55" + chave

        return chave

    def gerar_pix_qrcode(self, chave_pix, valor, descricao="Pagamento"):
        """Gera payload PIX e imagem QR Code valida usando biblioteca qrcode"""
        payload = self._criar_payload_pix(chave_pix, valor, descricao)

        if not PIL_DISPONIVEL:
            return None, payload

        if QRCODE_DISPONIVEL:
            # Usa biblioteca qrcode (gera imagem 100% valida)
            qr = qrcode.QRCode(
                version=None,  # Auto-detecta versao
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # 15% recuperacao
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)

            # Cria imagem
            img = qr.make_image(fill_color="black", back_color="white")

            # Converte para RGB se necessario
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Redimensiona para tamanho padrao
            img = img.resize((400, 400), Image.Resampling.LANCZOS)

        else:
            # Fallback: gera imagem com instrucoes
            img = Image.new('RGB', (400, 400), 'white')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            draw.text((20, 150), "INSTALE A BIBLIOTECA QRCODE:", fill='red', font=font)
            draw.text((20, 180), "pip install qrcode[pil]", fill='black', font=font)
            draw.text((20, 220), "Payload gerado (copie para gerador online):", fill='black', font=font)

            # Quebra payload em linhas
            y = 250
            for i in range(0, len(payload), 50):
                draw.text((20, y), payload[i:i+50], fill='black', font=font)
                y += 20

        return img, payload


# =============================================================================
# GERADOR DE CODIGO DE BARRAS EAN-13
# =============================================================================

class EAN13Generator:
    def __init__(self):
        self.l_code = {
            '0': '0001101', '1': '0011001', '2': '0010011', '3': '0111101',
            '4': '0100011', '5': '0110001', '6': '0101111', '7': '0111011',
            '8': '0110111', '9': '0001011'
        }
        self.r_code = {
            '0': '1110010', '1': '1100110', '2': '1101100', '3': '1000010',
            '4': '1011100', '5': '1001110', '6': '1010000', '7': '1000100',
            '8': '1001000', '9': '1110100'
        }
        self.g_code = {
            '0': '0100111', '1': '0110011', '2': '0011011', '3': '0100001',
            '4': '0011101', '5': '0111001', '6': '0000101', '7': '0010001',
            '8': '0001001', '9': '0010111'
        }
        self.parity = {
            '0': 'LLLLLL', '1': 'LLGLGG', '2': 'LLGGLG', '3': 'LLGGGL',
            '4': 'LGLLGG', '5': 'LGGLLG', '6': 'LGGGLL', '7': 'LGLGLG',
            '8': 'LGLGGL', '9': 'LGGLGL'
        }

    def validar_ean13(self, codigo):
        codigo = re.sub(r'[^0-9]', '', codigo)
        if len(codigo) == 12:
            soma = 0
            for i, digito in enumerate(codigo):
                if i % 2 == 0:
                    soma += int(digito)
                else:
                    soma += int(digito) * 3
            dv = (10 - (soma % 10)) % 10
            codigo += str(dv)
        return codigo if len(codigo) == 13 else None

    def gerar_imagem(self, codigo, altura=150, largura_scale=3, mostrar_texto=True):
        if not PIL_DISPONIVEL:
            return None, self.validar_ean13(codigo)
        codigo = self.validar_ean13(codigo)
        if not codigo:
            return None

        padrao = '101'
        primeiro = codigo[0]
        parity_pattern = self.parity[primeiro]

        for i in range(6):
            digito = codigo[i + 1]
            if parity_pattern[i] == 'L':
                padrao += self.l_code[digito]
            else:
                padrao += self.g_code[digito]

        padrao += '01010'

        for i in range(6):
            digito = codigo[i + 7]
            padrao += self.r_code[digito]

        padrao += '101'

        largura = len(padrao) * largura_scale
        img = Image.new('RGB', (largura, altura), 'white')
        draw = ImageDraw.Draw(img)

        for i, bit in enumerate(padrao):
            if bit == '1':
                x = i * largura_scale
                if mostrar_texto and ((12 <= i <= 46) or (50 <= i <= 84)):
                    draw.rectangle([x, 0, x + largura_scale - 1, altura - 25], fill='black')
                else:
                    draw.rectangle([x, 0, x + largura_scale - 1, altura], fill='black')

        if mostrar_texto:
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()

            draw.text((5, altura - 22), codigo[0], fill='black', font=font)
            for i in range(6):
                x = 20 + i * 22
                draw.text((x, altura - 22), codigo[i + 1], fill='black', font=font)
            for i in range(6):
                x = 160 + i * 22
                draw.text((x, altura - 22), codigo[i + 7], fill='black', font=font)

        return img, codigo

# =============================================================================
# BANCO DE DADOS - ATUALIZADO COM TABELA DE CAIXA
# =============================================================================

class Database:
    def __init__(self):
        db_path = get_db_path()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=NORMAL')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_default_data()

    def create_tables(self):
        # Tabela de usuarios
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nome TEXT NOT NULL,
                cargo TEXT NOT NULL,
                ativo INTEGER DEFAULT 1
            )
        """)

        # Tabela de produtos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                preco_venda REAL NOT NULL,
                estoque REAL DEFAULT 0,
                unidade TEXT DEFAULT 'UN',
                tipo_peso INTEGER DEFAULT 0,
                ativo INTEGER DEFAULT 1
            )
        """)

        # Tabela de vendas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_cupom TEXT UNIQUE NOT NULL,
                data_hora TIMESTAMP,
                usuario_id INTEGER,
                total REAL,
                forma_pagamento TEXT
            )
        """)

        # Tabela de itens de venda
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                produto_id INTEGER,
                quantidade REAL,
                preco_unitario REAL
            )
        """)

        # Tabela de configuracoes
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY,
                nome_empresa TEXT DEFAULT 'SUPERMERCADO CENTRAL',
                cnpj TEXT DEFAULT '00.000.000/0001-00',
                endereco TEXT DEFAULT 'Rua Principal, 100',
                telefone TEXT DEFAULT '(00) 0000-0000',
                mensagem_cupom TEXT DEFAULT 'Obrigado pela preferencia! Volte sempre!',
                chave_pix TEXT DEFAULT '',
                nome_recebedor_pix TEXT DEFAULT ''
            )
        """)

        # TABELA DE CLIENTES
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                data_cadastro TIMESTAMP,
                total_gasto REAL DEFAULT 0
            )
        """)

        # TABELA DE HISTORICO DE COMPRAS
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_cliente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                cpf TEXT,
                numero_cupom TEXT,
                data_compra TIMESTAMP,
                valor_total REAL,
                forma_pagamento TEXT,
                parcelas INTEGER DEFAULT 1,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)

        # NOVA TABELA: Controle de Caixa por Forma de Pagamento
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS caixa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_abertura TIMESTAMP,
                data_fechamento TIMESTAMP,
                usuario_id INTEGER,
                usuario_nome TEXT,
                status TEXT DEFAULT 'ABERTO',

                total_dinheiro REAL DEFAULT 0,
                total_credito REAL DEFAULT 0,
                total_debito REAL DEFAULT 0,
                total_pix REAL DEFAULT 0,
                total_fiado REAL DEFAULT 0,
                total_parcelado REAL DEFAULT 0,

                valor_abertura REAL DEFAULT 0,
                valor_fechamento REAL DEFAULT 0,

                observacoes TEXT
            )
        """)

        # TABELA DE HISTÓRICO DE VENDAS (arquivamento ao fechar caixa)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas_historico (
                id INTEGER,
                numero_cupom TEXT,
                data_hora TIMESTAMP,
                usuario_id INTEGER,
                total REAL,
                forma_pagamento TEXT,
                data_arquivamento TIMESTAMP,
                caixa_id INTEGER
            )
        """)

        self.conn.commit()

        # Criar tabela de fiados se não existir
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS fiados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente TEXT NOT NULL,
                    telefone TEXT,
                    valor_total REAL NOT NULL,
                    valor_pago REAL DEFAULT 0,
                    tipo TEXT DEFAULT 'Fiado',
                    descricao TEXT,
                    parcelas INTEGER DEFAULT 1,
                    parcelas_pagas INTEGER DEFAULT 0,
                    vencimento TEXT,
                    cpf TEXT,
                    data_cadastro TIMESTAMP,
                    status TEXT DEFAULT 'PENDENTE'
                )
            ''')
            self.conn.commit()

            # Adicionar coluna cpf se a tabela já existir (upgrade de versão)
            try:
                self.cursor.execute("ALTER TABLE fiados ADD COLUMN cpf TEXT")
                self.conn.commit()
            except sqlite3.OperationalError:
                # Coluna já existe, ignorar erro
                pass
        except:
            pass

    def insert_default_data(self):
        try:
            # Usuario admin padrao
            self.cursor.execute("""
                INSERT OR IGNORE INTO usuarios (id, username, password, nome, cargo)
                VALUES (1, 'admin', ?, 'Administrador', 'Gerente')
            """, (hashlib.sha256('admin123'.encode()).hexdigest(),))

            self.cursor.execute("""
                INSERT OR IGNORE INTO usuarios (id, username, password, nome, cargo)
                VALUES (2, 'caixa', ?, 'Operador', 'Caixa')
            """, (hashlib.sha256('caixa123'.encode()).hexdigest(),))

            self.cursor.execute("INSERT OR IGNORE INTO configuracoes (id) VALUES (1)")

            # Produtos padrao
            produtos = [
                ('7891000315507', 'Leite Integral 1L', 5.99, 50, 'UN', 0),
                ('7891000100103', 'Arroz 5kg', 22.90, 30, 'UN', 0),
                ('7896002300103', 'Feijao 1kg', 8.99, 40, 'UN', 0),
                ('7891000053508', 'Cafe 500g', 14.99, 25, 'UN', 0),
                ('7891000123456', 'Pao de Forma', 6.49, 20, 'UN', 0),
                ('7891000234567', 'Manteiga 200g', 9.99, 35, 'UN', 0),
                ('7891000345678', 'Ovos 30un', 18.90, 15, 'CX', 0),
                ('7891000456789', 'Acucar 1kg', 4.99, 60, 'UN', 0),
                ('7891000567890', 'Oleo 900ml', 7.99, 45, 'UN', 0),
                ('7891000678901', 'Sabao em Po', 12.99, 30, 'UN', 0),
                ('2000000000011', 'Banana Prata (KG)', 5.99, 100, 'KG', 1),
                ('2000000000028', 'Maca Fuji (KG)', 7.99, 80, 'KG', 1),
                ('2000000000035', 'Tomate (KG)', 6.49, 60, 'KG', 1),
            ]

            for p in produtos:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO produtos (codigo_barras, nome, preco_venda, estoque, unidade, tipo_peso)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, p)

            self.conn.commit()
        except Exception as e:
            print(f"Erro: {e}")

    # ============ METODOS DO CAIXA ============

    def abrir_caixa(self, usuario_id, usuario_nome, valor_abertura=0):
        """Abre um novo caixa"""
        try:
            self.cursor.execute("SELECT id FROM caixa WHERE status = 'ABERTO'")
            if self.cursor.fetchone():
                return None

            self.cursor.execute("""
                INSERT INTO caixa (data_abertura, usuario_id, usuario_nome, valor_abertura, status)
                VALUES (?, ?, ?, ?, 'ABERTO')
            """, (get_brasil_strftime('%Y-%m-%d %H:%M:%S'), usuario_id, usuario_nome, valor_abertura))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Erro ao abrir caixa: {e}")
            return None

    def get_caixa_aberto(self):
        """Retorna o caixa atualmente aberto"""
        self.cursor.execute("""
            SELECT * FROM caixa WHERE status = 'ABERTO' ORDER BY id DESC LIMIT 1
        """)
        return self.cursor.fetchone()

    def atualizar_totais_caixa(self, forma_pagamento, valor):
        """Atualiza os totais do caixa aberto conforme a forma de pagamento"""
        caixa = self.get_caixa_aberto()
        if not caixa:
            return False

        colunas = {
            'dinheiro': 'total_dinheiro',
            'credito': 'total_credito',
            'debito': 'total_debito',
            'pix': 'total_pix',
            'fiado': 'total_fiado',
            'parcelado': 'total_parcelado'
        }

        coluna = colunas.get(forma_pagamento.lower())
        if coluna:
            self.cursor.execute(f"""
                UPDATE caixa SET {coluna} = {coluna} + ? WHERE id = ?
            """, (valor, caixa[0]))
            self.conn.commit()
            return True
        return False

    def fechar_caixa(self, valor_fechamento=0, observacoes=""):
        """Fecha o caixa atual, arquiva vendas do dia e zera para o proximo"""
        caixa = self.get_caixa_aberto()
        if not caixa:
            return None

        data_fechamento = get_brasil_now().strftime('%Y-%m-%d %H:%M:%S')

        # Arquiva as vendas do dia na tabela de histórico
        self.cursor.execute("""
            INSERT INTO vendas_historico 
            SELECT id, numero_cupom, data_hora, usuario_id, total, forma_pagamento, ? as data_arquivamento, ? as caixa_id 
            FROM vendas 
            WHERE strftime('%Y-%m-%d', data_hora) = strftime('%Y-%m-%d', ?)
        """, (get_brasil_strftime('%Y-%m-%d %H:%M:%S'), caixa[0], data_fechamento))

        # Remove as vendas do dia atual (zera o relatório do dia)
        self.cursor.execute("""
            DELETE FROM vendas 
            WHERE strftime('%Y-%m-%d', data_hora) = strftime('%Y-%m-%d', ?)
        """, (data_fechamento,))

        data_fechamento = get_brasil_strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("""
            UPDATE caixa 
            SET data_fechamento = ?,
                status = 'FECHADO',
                valor_fechamento = ?,
                observacoes = ?
            WHERE id = ?
        """, (data_fechamento, valor_fechamento, observacoes, caixa[0]))

        self.conn.commit()
        return caixa[0]

    def get_vendas_arquivadas(self, data_ini, data_fim):
        """Retorna vendas arquivadas do histórico"""
        self.cursor.execute("""
            SELECT numero_cupom, data_hora, total, forma_pagamento, data_arquivamento 
            FROM vendas_historico 
            WHERE date(data_arquivamento) BETWEEN ? AND ?
            ORDER BY data_arquivamento DESC
        """, (data_ini, data_fim))
        return self.cursor.fetchall()

    def get_resumo_caixa(self, caixa_id):
        """Retorna resumo completo do caixa"""
        self.cursor.execute("""
            SELECT 
                total_dinheiro, total_credito, total_debito, 
                total_pix, total_fiado, total_parcelado,
                valor_abertura, data_abertura, usuario_nome
            FROM caixa WHERE id = ?
        """, (caixa_id,))
        return self.cursor.fetchone()

    def get_historico_caixas(self, limite=10):
        """Retorna historico de caixas fechados"""
        self.cursor.execute("""
            SELECT id, data_abertura, data_fechamento, usuario_nome, 
                   total_dinheiro + total_credito + total_debito + total_pix + total_fiado + total_parcelado as total,
                   status
            FROM caixa 
            ORDER BY id DESC LIMIT ?
        """, (limite,))
        return self.cursor.fetchall()

    # ============ METODOS EXISTENTES ============

    def verify_login(self, username, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ? AND ativo = 1', 
                          (username, hashed))
        return self.cursor.fetchone()

    def get_produto_by_codigo(self, codigo):
        self.cursor.execute('SELECT * FROM produtos WHERE codigo_barras = ? AND ativo = 1', (codigo,))
        return self.cursor.fetchone()

    def get_all_produtos(self):
        self.cursor.execute('SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome')
        return self.cursor.fetchall()

    def update_estoque(self, produto_id, quantidade):
        self.cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', 
                          (quantidade, produto_id))
        self.conn.commit()

    def save_venda(self, venda_data):
        try:
            numero_cupom = f"CF{get_brasil_now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"

            self.cursor.execute("""
                INSERT INTO vendas (numero_cupom, data_hora, usuario_id, total, forma_pagamento)
                VALUES (?, ?, ?, ?, ?)
            """, (numero_cupom, get_brasil_strftime('%Y-%m-%d %H:%M:%S'), 
                   venda_data['usuario_id'], 
                   venda_data['total'], venda_data['forma_pagamento']))

            venda_id = self.cursor.lastrowid

            for item in venda_data['itens']:
                self.cursor.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                    VALUES (?, ?, ?, ?)
                """, (venda_id, item['produto_id'], item['quantidade'], item['preco']))
                self.update_estoque(item['produto_id'], item['quantidade'])

            # Atualiza totais do caixa
            self.atualizar_totais_caixa(venda_data['forma_pagamento'], venda_data['total'])

            self.conn.commit()
            return venda_id, numero_cupom
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_produto(self, codigo, nome, preco, estoque, unidade, tipo_peso=0):
        try:
            self.cursor.execute("""
                INSERT INTO produtos (codigo_barras, nome, preco_venda, estoque, unidade, tipo_peso)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (codigo, nome, preco, estoque, unidade, tipo_peso))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Erro ao adicionar: {e}")
            return False

    def update_produto(self, produto_id, nome, preco, estoque, unidade, tipo_peso=0):
        try:
            self.cursor.execute("""
                UPDATE produtos SET nome=?, preco_venda=?, estoque=?, unidade=?, tipo_peso=?
                WHERE id=?
            """, (nome, preco, estoque, unidade, tipo_peso, produto_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar: {e}")
            return False

    def delete_produto(self, produto_id):
        try:
            self.cursor.execute("UPDATE produtos SET ativo=0 WHERE id=?", (produto_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao excluir: {e}")
            return False

    def get_config(self):
        self.cursor.execute('SELECT * FROM configuracoes WHERE id = 1')
        return self.cursor.fetchone()

    def add_usuario(self, username, password, nome, cargo):
        try:
            hash_pass = hashlib.sha256(password.encode()).hexdigest()
            self.cursor.execute("INSERT INTO usuarios (username, password, nome, cargo) VALUES (?, ?, ?, ?)",
                              (username, hash_pass, nome, cargo))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_usuario_senha(self, user_id, nova_senha):
        try:
            hash_pass = hashlib.sha256(nova_senha.encode()).hexdigest()
            self.cursor.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def desativar_usuario(self, user_id):
        try:
            self.cursor.execute("UPDATE usuarios SET ativo=0 WHERE id=?", (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def get_all_usuarios(self):
        self.cursor.execute("SELECT id, nome, username, cargo, CASE WHEN ativo=1 THEN 'Ativo' ELSE 'Inativo' END FROM usuarios")
        return self.cursor.fetchall()

    def update_config(self, nome, cnpj, endereco, telefone, mensagem, chave_pix='', nome_recebedor=''):
        try:
            self.cursor.execute("""
                UPDATE configuracoes SET nome_empresa=?, cnpj=?, endereco=?, telefone=?, mensagem_cupom=?, chave_pix=?, nome_recebedor_pix=?
                WHERE id=1
            """, (nome, cnpj, endereco, telefone, mensagem, chave_pix, nome_recebedor))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def get_vendas_periodo(self, data_ini, data_fim, forma_pagamento=None):
        if forma_pagamento:
            self.cursor.execute("""
                SELECT numero_cupom, data_hora, total, forma_pagamento 
                FROM vendas 
                WHERE strftime('%Y-%m-%d', data_hora) BETWEEN ? AND ? AND forma_pagamento = ?
                ORDER BY data_hora DESC
            """, (data_ini, data_fim, forma_pagamento))
        else:
            self.cursor.execute("""
                SELECT numero_cupom, data_hora, total, forma_pagamento 
                FROM vendas 
                WHERE strftime('%Y-%m-%d', data_hora) BETWEEN ? AND ?
                ORDER BY data_hora DESC
            """, (data_ini, data_fim))
        return self.cursor.fetchall()

    def get_vendas_por_forma_pagamento(self, data_ini, data_fim):
        self.cursor.execute("""
            SELECT forma_pagamento, COUNT(*) as qtd, SUM(total) as total
            FROM vendas 
            WHERE strftime('%Y-%m-%d', data_hora) BETWEEN ? AND ?
            GROUP BY forma_pagamento
        """, (data_ini, data_fim))
        return self.cursor.fetchall()

    def add_estoque(self, codigo, quantidade):
        self.cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE codigo_barras = ?", 
                          (quantidade, codigo))
        self.conn.commit()
        return self.cursor.rowcount

    def gerar_codigo_barras_avulso(self):
        prefixo = "200"
        numero = str(random.randint(10000000, 99999999))
        codigo_sem_dv = prefixo + numero
        soma = 0
        for i, digito in enumerate(codigo_sem_dv):
            if i % 2 == 0:
                soma += int(digito)
            else:
                soma += int(digito) * 3
        dv = (10 - (soma % 10)) % 10
        return codigo_sem_dv + str(dv)

    # ============ METODOS DE FIADOS ============

    def add_fiado(self, cliente_id, cliente, telefone, valor, tipo, descricao, parcelas, vencimento, cpf=''):
        """Adiciona novo registro de fiado/parcelado"""
        try:
            self.cursor.execute("""
                INSERT INTO fiados (cliente, telefone, valor_total, tipo, descricao, parcelas, vencimento, cpf, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cliente, telefone, valor, tipo, descricao, parcelas, vencimento, cpf, get_brasil_strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Erro ao adicionar fiado: {e}")
            return None

    def get_all_fiados(self):
        """Retorna todos os registros de fiados pendentes"""
        self.cursor.execute("""
            SELECT id, cliente, telefone, valor_total, valor_pago, tipo, 
                   parcelas, parcelas_pagas, vencimento, status 
            FROM fiados 
            WHERE status = 'PENDENTE'
            ORDER BY data_cadastro DESC
        """)
        return self.cursor.fetchall()

    def registrar_pagamento_fiado(self, fiado_id, valor):
        """Registra pagamento parcial ou total de um fiado"""
        try:
            self.cursor.execute("""
                UPDATE fiados 
                SET valor_pago = valor_pago + ?,
                    parcelas_pagas = parcelas_pagas + 1,
                    status = CASE 
                        WHEN (valor_pago + ?) >= valor_total THEN 'QUITADO' 
                        ELSE 'PENDENTE' 
                    END
                WHERE id = ?
            """, (valor, valor, fiado_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao registrar pagamento: {e}")
            return False

    def get_totais_fiados(self):
        """Retorna totais de fiados e parcelados pendentes"""
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN tipo = 'Fiado' AND status = 'PENDENTE' THEN (valor_total - valor_pago) ELSE 0 END) as total_fiado,
                SUM(CASE WHEN tipo = 'Parcelado' AND status = 'PENDENTE' THEN (valor_total - valor_pago) ELSE 0 END) as total_parcelado
            FROM fiados
        """)
        return self.cursor.fetchone()

    # ============ METODOS DE CLIENTES ============

    def buscar_cliente_por_cpf(self, cpf):
        """Busca cliente pelo CPF"""
        cpf = re.sub(r'[^0-9]', '', cpf)
        self.cursor.execute("SELECT * FROM clientes WHERE cpf = ?", (cpf,))
        return self.cursor.fetchone()

    def cadastrar_cliente(self, nome, cpf, telefone='', email='', endereco=''):
        """Cadastra novo cliente"""
        try:
            cpf_limpo = re.sub(r'[^0-9]', '', cpf)
            if not cpf_limpo:
                print("Erro: CPF vazio após limpeza")
                return None

            self.cursor.execute("""
                INSERT INTO clientes (nome, cpf, telefone, email, endereco)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, cpf_limpo, telefone, email, endereco))
            self.conn.commit()
            print(f"Cliente cadastrado: ID={self.cursor.lastrowid}, Nome={nome}, CPF={cpf_limpo}")
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"Erro de integridade (CPF duplicado): {e}")
            return None
        except Exception as e:
            print(f"Erro ao cadastrar cliente: {e}")
            return None

    def atualizar_total_gasto_cliente(self, cliente_id, valor):
        """Atualiza o total gasto pelo cliente"""
        try:
            self.cursor.execute("""
                UPDATE clientes SET total_gasto = total_gasto + ? WHERE id = ?
            """, (valor, cliente_id))
            self.conn.commit()
            return True
        except:
            return False

    def registrar_historico_compra(self, cliente_id, cpf, numero_cupom, valor, forma_pagamento, parcelas=1):
        """Registra compra no histórico do cliente"""
        try:
            self.cursor.execute("""
                INSERT INTO historico_cliente (cliente_id, cpf, numero_cupom, data_compra, valor_total, forma_pagamento, parcelas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, cpf, numero_cupom, get_brasil_strftime('%Y-%m-%d %H:%M:%S'), valor, forma_pagamento, parcelas))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao registrar histórico: {e}")
            return False

    def get_historico_cliente(self, cpf):
        """Retorna histórico de compras do cliente pelo CPF"""
        cpf = re.sub(r'[^0-9]', '', cpf)
        self.cursor.execute("""
            SELECT numero_cupom, data_compra, valor_total, forma_pagamento, parcelas
            FROM historico_cliente
            WHERE cpf = ?
            ORDER BY data_compra DESC
        """, (cpf,))
        return self.cursor.fetchall()

    def consulta_geral_por_cpf(self, cpf):
        """Consulta geral por CPF em todas as tabelas (vendas, fiados, historico)"""
        cpf = re.sub(r'[^0-9]', '', cpf)
        resultados = []

        # 1. Buscar no histórico_cliente (vendas registradas)
        self.cursor.execute("""
            SELECT h.numero_cupom, h.data_compra, h.valor_total, h.forma_pagamento, h.parcelas, c.nome
            FROM historico_cliente h
            LEFT JOIN clientes c ON h.cliente_id = c.id
            WHERE h.cpf = ?
            ORDER BY h.data_compra DESC
        """, (cpf,))
        for row in self.cursor.fetchall():
            resultados.append({
                'tipo': 'VENDA',
                'cupom': row[0],
                'data': row[1],
                'valor': row[2],
                'forma': row[3],
                'parcelas': row[4],
                'cliente': row[5] or 'N/A',
                'status': 'CONCLUÍDA'
            })

        # 2. Buscar no fiados (contas pendentes)
        self.cursor.execute("""
            SELECT f.id, f.cliente, f.valor_total, f.valor_pago, f.tipo, f.parcelas, f.parcelas_pagas, f.vencimento, f.status
            FROM fiados f
            WHERE f.cpf = ?
            ORDER BY f.data_cadastro DESC
        """, (cpf,))
        for row in self.cursor.fetchall():
            resultados.append({
                'tipo': row[4].upper(),  # FIADO ou PARCELADO
                'id': row[0],
                'cliente': row[1],
                'valor_total': row[2],
                'valor_pago': row[3],
                'parcelas': f"{row[6]}/{row[5]}",
                'vencimento': row[7],
                'status': row[8],
                'data': None
            })

        # 3. Buscar cliente cadastrado
        self.cursor.execute("""
            SELECT nome, telefone, email, endereco, data_cadastro, total_gasto
            FROM clientes
            WHERE cpf = ?
        """, (cpf,))
        cliente_info = self.cursor.fetchone()

        return {
            'cliente': cliente_info,
            'transacoes': resultados
        }

    def get_all_clientes(self):
        """Retorna todos os clientes"""
        self.cursor.execute("""
            SELECT id, nome, cpf, telefone, email, total_gasto 
            FROM clientes 
            ORDER BY nome
        """)
        return self.cursor.fetchall()


# =============================================================================
# BACKUP E RESTAURACAO
# =============================================================================

class BackupManager:
    def __init__(self, db):
        self.db = db

    def criar_backup(self):
        try:
            timestamp = get_brasil_now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(get_backup_path(), f"backup_{timestamp}.db")
            self.db.conn.commit()
            shutil.copy2(get_db_path(), backup_file)
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                return backup_file
            return None
        except Exception as e:
            print(f"Erro backup: {e}")
            return None

    def listar_backups(self):
        backup_dir = get_backup_path()
        if not os.path.exists(backup_dir):
            return []
        arquivos = [f for f in os.listdir(backup_dir) if f.endswith('.db') or f.endswith('.zip')]
        return sorted(arquivos, reverse=True)

    def restaurar_backup(self, arquivo):
        try:
            backup_path = os.path.join(get_backup_path(), arquivo)
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                self.db.conn.close()
                timestamp = get_brasil_now().strftime('%Y%m%d_%H%M%S')
                seguranca = os.path.join(get_backup_path(), f"auto_seguranca_{timestamp}.db")
                try:
                    shutil.copy2(get_db_path(), seguranca)
                except:
                    pass
                shutil.copy2(backup_path, get_db_path())
                self.db.__init__()
                return True
            return False
        except Exception as e:
            print(f"Erro restauracao: {e}")
            try:
                self.db.__init__()
            except:
                pass
            return False

    def exportar_dados(self):
        try:
            dados = {
                'produtos': self.db.get_all_produtos(),
                'usuarios': self.db.get_all_usuarios(),
                'config': self.db.get_config(),
                'data_exportacao': get_brasil_now().isoformat(),
                'versao': '2.0'
            }
            arquivo = os.path.join(get_app_path(), f"export_{get_brasil_now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2, default=str)
            return arquivo
        except Exception as e:
            print(f"Erro exportacao: {e}")
            return None

    def importar_dados(self, arquivo_json):
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if 'produtos' in dados:
                for p in dados['produtos']:
                    try:
                        self.db.add_produto(p[1], p[2], p[3], p[4], p[5], p[6] if len(p) > 6 else 0)
                    except:
                        pass
            return True
        except Exception as e:
            print(f"Erro importacao: {e}")
            return False

# =============================================================================
# TELA DE BACKUP E RESTAURACAO - ESTILO WIN95
# =============================================================================

class TelaBackup:
    def __init__(self, parent, db, backup_manager):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Backup e Restauracao do Sistema")
        self.janela.geometry("700x600")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db
        self.backup_manager = backup_manager

        self.create_interface()
        self.carregar_backups()

        # Botao fechar
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        # Header
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="BACKUP E RESTAURACAO", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Botoes de acao
        acoes = tk.LabelFrame(self.janela, text=" ACOES ", 
                             font=('MS Sans Serif', 9, 'bold'), 
                             bg=Win95Style.BG_GRAY)
        acoes.pack(fill='x', padx=10, pady=10)

        btn_frame = tk.Frame(acoes, bg=Win95Style.BG_GRAY)
        btn_frame.pack(pady=15)

        Win95Style.create_button(btn_frame, "💾 CRIAR BACKUP (F2)", self.criar_backup,
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 9, 'bold'), width=20).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "📤 EXPORTAR JSON (F3)", self.exportar_dados,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=20).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "📥 IMPORTAR JSON (F4)", self.importar_dados,
                                bg_color=Win95Style.WARNING, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=20).pack(side='left', padx=5)

        # Lista de backups
        lista_frame = tk.LabelFrame(self.janela, text=" BACKUPS DISPONIVEIS ", 
                                   font=('MS Sans Serif', 9, 'bold'), 
                                   bg=Win95Style.BG_GRAY)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Label(lista_frame, text="Selecione um backup e clique em RESTAURAR:", 
                bg=Win95Style.BG_GRAY, font=('MS Sans Serif', 9), fg=Win95Style.DARK_GRAY).pack(anchor='w', padx=10, pady=5)

        cols = ('arquivo', 'data', 'tamanho')
        self.tree = ttk.Treeview(lista_frame, columns=cols, show='headings', height=12)

        self.tree.heading('arquivo', text='ARQUIVO')
        self.tree.heading('data', text='DATA CRIACAO')
        self.tree.heading('tamanho', text='TAMANHO')

        self.tree.column('arquivo', width=300)
        self.tree.column('data', width=150, anchor='center')
        self.tree.column('tamanho', width=100, anchor='center')

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y', pady=5)

        # Botoes de acao na lista
        acao_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        acao_frame.pack(fill='x', padx=10, pady=5)

        Win95Style.create_button(acao_frame, "🔄 RESTAURAR SELECIONADO (F5)", self.restaurar_backup,
                                bg_color="#9C27B0", fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=25).pack(side='left', padx=5)

        Win95Style.create_button(acao_frame, "🗑️ EXCLUIR (F6)", self.excluir_backup,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(acao_frame, "🔄 ATUALIZAR (F7)", self.carregar_backups,
                                bg_color=Win95Style.DARK_GRAY, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=18).pack(side='right', padx=5)

        # Status
        self.status_label = tk.Label(self.janela, text="Pronto", 
                                    font=('MS Sans Serif', 9), bg=Win95Style.BG_GRAY, fg=Win95Style.DARK_GRAY)
        self.status_label.pack(pady=10)

        # Botao fechar
        Win95Style.create_button(self.janela, "❌ FECHAR (ESC)", self.fechar,
                                width=15).pack(pady=5)

        # Atalhos
        self.janela.bind('<F2>', lambda e: self.criar_backup())
        self.janela.bind('<F3>', lambda e: self.exportar_dados())
        self.janela.bind('<F4>', lambda e: self.importar_dados())
        self.janela.bind('<F5>', lambda e: self.restaurar_backup())
        self.janela.bind('<F6>', lambda e: self.excluir_backup())
        self.janela.bind('<F7>', lambda e: self.carregar_backups())
        self.janela.bind('<Escape>', lambda e: self.fechar())

    def carregar_backups(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        backups = self.backup_manager.listar_backups()

        for arquivo in backups:
            try:
                caminho = os.path.join(get_backup_path(), arquivo)
                stat = os.stat(caminho)
                data = datetime.datetime.fromtimestamp(stat.st_mtime)
                data_str = data.strftime('%d/%m/%Y %H:%M')

                tamanho = stat.st_size
                if tamanho < 1024:
                    tam_str = f"{tamanho} B"
                elif tamanho < 1024*1024:
                    tam_str = f"{tamanho/1024:.1f} KB"
                else:
                    tam_str = f"{tamanho/(1024*1024):.1f} MB"

                self.tree.insert('', 'end', values=(arquivo, data_str, tam_str))
            except:
                self.tree.insert('', 'end', values=(arquivo, "-", "-"))

        self.status_label.config(text=f"{len(backups)} backup(s) encontrado(s)")

    def criar_backup(self):
        self.status_label.config(text="Criando backup...", fg=Win95Style.INFO)
        self.janela.update()

        arquivo = self.backup_manager.criar_backup()
        if arquivo:
            self.carregar_backups()
            messagebox.showinfo("Sucesso", f"Backup criado com sucesso!\n\n{os.path.basename(arquivo)}")
            self.status_label.config(text=f"Backup criado: {os.path.basename(arquivo)}", fg=Win95Style.SUCCESS)
        else:
            messagebox.showerror("Erro", "Nao foi possivel criar o backup!")
            self.status_label.config(text="Erro ao criar backup", fg=Win95Style.DANGER)

    def restaurar_backup(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um backup para restaurar!")
            return

        arquivo = self.tree.item(selecionado[0])['values'][0]

        if messagebox.askyesno("CONFIRMAR RESTAURACAO", 
                              f"Deseja restaurar o backup:\n\n{arquivo}\n\n" +
                              "ATENCAO: Os dados atuais serao substituidos!\n" +
                              "O sistema sera reiniciado apos a restauracao."):

            self.status_label.config(text="Restaurando backup...", fg=Win95Style.WARNING)
            self.janela.update()

            if self.backup_manager.restaurar_backup(arquivo):
                messagebox.showinfo("Sucesso", "Backup restaurado!\nO sistema sera reiniciado.")
                self.janela.destroy()
                python = sys.executable
                os.execl(python, python, *sys.argv)
            else:
                messagebox.showerror("Erro", "Nao foi possivel restaurar o backup!")
                self.status_label.config(text="Erro na restauracao", fg=Win95Style.DANGER)

    def excluir_backup(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um backup para excluir!")
            return

        arquivo = self.tree.item(selecionado[0])['values'][0]

        if messagebox.askyesno("Confirmar", f"Excluir backup:\n{arquivo}?"):
            try:
                caminho = os.path.join(get_backup_path(), arquivo)
                os.remove(caminho)
                self.carregar_backups()
                messagebox.showinfo("Sucesso", "Backup excluido!")
            except Exception as e:
                messagebox.showerror("Erro", f"Nao foi possivel excluir:\n{str(e)}")

    def exportar_dados(self):
        self.status_label.config(text="Exportando dados...", fg=Win95Style.INFO)
        self.janela.update()

        arquivo = self.backup_manager.exportar_dados()
        if arquivo:
            messagebox.showinfo("Sucesso", f"Dados exportados!\n\n{arquivo}")
            self.status_label.config(text=f"Exportado: {os.path.basename(arquivo)}", fg=Win95Style.SUCCESS)
        else:
            messagebox.showerror("Erro", "Nao foi possivel exportar!")
            self.status_label.config(text="Erro na exportacao", fg=Win95Style.DANGER)

    def importar_dados(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar arquivo JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=get_app_path()
        )

        if arquivo:
            if messagebox.askyesno("Confirmar", f"Importar dados de:\n{os.path.basename(arquivo)}?"):
                if self.backup_manager.importar_dados(arquivo):
                    messagebox.showinfo("Sucesso", "Dados importados!")
                    self.carregar_backups()
                else:
                    messagebox.showerror("Erro", "Erro na importacao!")

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE GERACAO DE ETIQUETAS - ESTILO WIN95
# =============================================================================

class TelaEtiquetas:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Geracao de Etiquetas - Codigo de Barras")
        self.janela.geometry("900x700")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db
        self.ean_generator = EAN13Generator()

        self.create_interface()
        self.carregar_produtos()

        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="GERACAO DE ETIQUETAS", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        main_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame esquerdo
        left_frame = tk.Frame(main_frame, bg=Win95Style.BG_GRAY)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)

        # Busca
        busca_frame = tk.Frame(left_frame, bg=Win95Style.BG_GRAY)
        busca_frame.pack(fill='x', pady=5)

        tk.Label(busca_frame, text="Buscar:", bg=Win95Style.BG_GRAY, 
                font=('MS Sans Serif', 9)).pack(side='left')
        self.busca_var = tk.StringVar()
        tk.Entry(busca_frame, textvariable=self.busca_var, 
                font=('MS Sans Serif', 10), width=30).pack(side='left', padx=5)
        Win95Style.create_button(busca_frame, "🔍", self.filtrar_produtos, width=5).pack(side='left')

        # Lista
        lista_frame = tk.LabelFrame(left_frame, text=" PRODUTOS ", 
                                   font=('MS Sans Serif', 9, 'bold'),
                                   bg=Win95Style.BG_GRAY)
        lista_frame.pack(fill='both', expand=True, pady=5)

        cols = ('codigo', 'nome', 'preco', 'selecionar')
        self.tree = ttk.Treeview(lista_frame, columns=cols, show='headings', height=15)

        self.tree.heading('codigo', text='CODIGO')
        self.tree.heading('nome', text='NOME')
        self.tree.heading('preco', text='PRECO')
        self.tree.heading('selecionar', text='IMPRIMIR')

        self.tree.column('codigo', width=120, anchor='center')
        self.tree.column('nome', width=200)
        self.tree.column('preco', width=80, anchor='e')
        self.tree.column('selecionar', width=80, anchor='center')

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.gerar_etiqueta_selecionado)

        # Frame direito
        right_frame = tk.Frame(main_frame, bg=Win95Style.BG_GRAY, width=350)
        right_frame.pack(side='right', fill='y', padx=5)
        right_frame.pack_propagate(False)

        # Preview
        preview_frame = tk.LabelFrame(right_frame, text=" PREVIEW DA ETIQUETA ", 
                                     font=('MS Sans Serif', 9, 'bold'),
                                     bg=Win95Style.BG_GRAY)
        preview_frame.pack(fill='x', pady=5)

        self.preview_label = tk.Label(preview_frame, bg="white", height=10)
        self.preview_label.pack(padx=10, pady=10)

        # Configuracoes
        config_frame = tk.LabelFrame(right_frame, text=" CONFIGURACOES ", 
                                    font=('MS Sans Serif', 9, 'bold'),
                                    bg=Win95Style.BG_GRAY)
        config_frame.pack(fill='x', pady=10)

        tk.Label(config_frame, text="Quantidade de etiquetas:", 
                font=('MS Sans Serif', 9), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=5, pady=2)
        self.qtd_etiquetas = tk.Spinbox(config_frame, from_=1, to=100, width=10, 
                                       font=('MS Sans Serif', 10))
        self.qtd_etiquetas.pack(anchor='w', padx=5, pady=2)
        self.qtd_etiquetas.delete(0, tk.END)
        self.qtd_etiquetas.insert(0, "1")

        tk.Label(config_frame, text="Tamanho:", font=('MS Sans Serif', 9), 
                bg=Win95Style.BG_GRAY).pack(anchor='w', padx=5, pady=(10, 2))
        self.tamanho_var = tk.StringVar(value="padrao")
        tk.Radiobutton(config_frame, text="Padrao (40x30mm)", variable=self.tamanho_var, 
                      value="padrao", bg=Win95Style.BG_GRAY, 
                      font=('MS Sans Serif', 9)).pack(anchor='w', padx=5)
        tk.Radiobutton(config_frame, text="Grande (60x40mm)", variable=self.tamanho_var, 
                      value="grande", bg=Win95Style.BG_GRAY,
                      font=('MS Sans Serif', 9)).pack(anchor='w', padx=5)

        # Botoes
        btn_frame = tk.Frame(right_frame, bg=Win95Style.BG_GRAY)
        btn_frame.pack(fill='x', pady=20)

        Win95Style.create_button(btn_frame, "🖨️ IMPRIMIR SELECIONADO (F2)", self.imprimir_etiqueta,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(fill='x', pady=2)

        Win95Style.create_button(btn_frame, "📄 IMPRIMIR TODOS (F3)", self.imprimir_todos,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(fill='x', pady=2)

        Win95Style.create_button(btn_frame, "💾 SALVAR IMAGEM (F4)", self.salvar_imagem,
                                bg_color=Win95Style.WARNING, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(fill='x', pady=2)

        Win95Style.create_button(btn_frame, "❌ FECHAR (ESC)", self.fechar,
                                font=('MS Sans Serif', 9, 'bold')).pack(fill='x', pady=2)

        # Info
        info_frame = tk.Frame(right_frame, bg=Win95Style.BG_GRAY)
        info_frame.pack(fill='x', pady=10)

        tk.Label(info_frame, text="Dica: Duplo clique no produto\npara gerar preview", 
                font=('MS Sans Serif', 9), fg=Win95Style.DARK_GRAY, 
                bg=Win95Style.BG_GRAY, justify='center').pack()

        # Atalhos
        self.janela.bind('<F2>', lambda e: self.imprimir_etiqueta())
        self.janela.bind('<F3>', lambda e: self.imprimir_todos())
        self.janela.bind('<F4>', lambda e: self.salvar_imagem())
        self.janela.bind('<Escape>', lambda e: self.fechar())

        self.busca_var.trace('w', lambda *args: self.filtrar_produtos())

    def carregar_produtos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        produtos = self.db.get_all_produtos()
        for p in produtos:
            self.tree.insert('', 'end', values=(p[1], p[2], f"R$ {p[3]:.2f}", "📄"))

    def filtrar_produtos(self):
        termo = self.busca_var.get().lower()
        for item in self.tree.get_children():
            valores = self.tree.item(item)['values']
            if termo in valores[0].lower() or termo in valores[1].lower():
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

    def gerar_etiqueta_selecionado(self, event=None):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        try:
            item = None
            if event:
                item = self.tree.identify_row(event.y)
            if not item:
                selecionado = self.tree.selection()
                if selecionado:
                    item = selecionado[0]
            if not item:
                return

            self.tree.selection_set(item)
            valores = self.tree.item(item, 'values')
            if not valores or len(valores) < 3:
                return

            codigo = str(valores[0])
            nome = str(valores[1])
            preco = str(valores[2])

            resultado = self.ean_generator.gerar_imagem(codigo, altura=100, largura_scale=3)

            if resultado:
                img, codigo_validado = resultado
                largura, altura = img.size
                nova_altura = altura + 70
                img_final = Image.new('RGB', (largura, nova_altura), 'white')
                img_final.paste(img, (0, 0))

                draw = ImageDraw.Draw(img_final)
                try:
                    font_nome = ImageFont.truetype("arial.ttf", 14)
                    font_preco = ImageFont.truetype("arial.ttf", 18)
                    font_codigo = ImageFont.truetype("arial.ttf", 10)
                except:
                    font_nome = ImageFont.load_default()
                    font_preco = ImageFont.load_default()
                    font_codigo = ImageFont.load_default()

                draw.text((10, altura + 5), nome[:35], fill='black', font=font_nome)
                draw.text((10, altura + 28), preco, fill='red', font=font_preco)
                draw.text((10, altura + 52), f"Cod: {codigo_validado}", fill='gray', font=font_codigo)

                self.imagem_atual = img_final
                self.dados_atual = {'codigo': codigo_validado, 'nome': nome, 'preco': preco}

                img_preview = img_final.resize((300, 200))
                img_tk = ImageTk.PhotoImage(img_preview)
                self.preview_label.config(image=img_tk, text="")
                self.preview_label.image = img_tk

        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {str(e)}")

    def imprimir_etiqueta(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        if not hasattr(self, 'imagem_atual'):
            messagebox.showwarning("Aviso", "Selecione um produto primeiro!")
            return

        try:
            qtd = int(self.qtd_etiquetas.get())
        except:
            qtd = 1

        temp_file = os.path.join(get_etiquetas_path(), "temp_etiqueta.png")
        self.imagem_atual.save(temp_file, dpi=(300, 300))

        for i in range(qtd):
            os.system(f'start /min "" "{temp_file}"')

        messagebox.showinfo("Sucesso", f"{qtd} etiqueta(s) enviada(s) para impressao!")

    def imprimir_todos(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow nao instalada!\nInstale com: pip install pillow")
            return
        if not messagebox.askyesno("Confirmar", "Imprimir etiquetas de TODOS os produtos visiveis?"):
            return

        arquivos_gerados = []

        for item in self.tree.get_children():
            valores = self.tree.item(item)['values']
            codigo = valores[0]
            nome = valores[1]
            preco = valores[2]

            resultado = self.ean_generator.gerar_imagem(codigo, altura=120, largura_scale=2)
            if resultado:
                img, codigo_validado = resultado
                largura, altura = img.size
                nova_altura = altura + 60
                img_final = Image.new('RGB', (largura, nova_altura), 'white')
                img_final.paste(img, (0, 0))

                draw = ImageDraw.Draw(img_final)
                try:
                    font_nome = ImageFont.truetype("arial.ttf", 14)
                    font_preco = ImageFont.truetype("arial.ttf", 18)
                except:
                    font_nome = ImageFont.load_default()
                    font_preco = ImageFont.load_default()

                draw.text((10, altura + 5), nome[:30], fill='black', font=font_nome)
                draw.text((10, altura + 28), preco, fill='red', font=font_preco)

                arquivo = os.path.join(get_etiquetas_path(), f"etiqueta_{codigo}.png")
                img_final.save(arquivo, dpi=(300, 300))
                arquivos_gerados.append(arquivo)

        messagebox.showinfo("Sucesso", f"{len(arquivos_gerados)} etiquetas geradas!\n\nLocal: {get_etiquetas_path()}")

    def salvar_imagem(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        if not hasattr(self, 'imagem_atual'):
            messagebox.showwarning("Aviso", "Selecione um produto primeiro!")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialdir=get_etiquetas_path(),
            initialvalue=f"etiqueta_{self.dados_atual['codigo']}.png"
        )

        if arquivo:
            self.imagem_atual.save(arquivo, dpi=(300, 300))
            messagebox.showinfo("Sucesso", f"Etiqueta salva!\n{arquivo}")

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE CADASTRO DE PRODUTOS - ESTILO WIN95
# =============================================================================

class CadastroProdutos:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Produtos - Estoque")
        self.janela.geometry("900x600")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db
        self.ean_generator = EAN13Generator()

        self.create_interface()
        self.carregar_produtos()

        self.janela.after(100, lambda: self.codigo_entry.focus_set())
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="CADASTRO DE PRODUTOS / ESTOQUE", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        form_frame = tk.LabelFrame(self.janela, text=" NOVO PRODUTO ", 
                                  font=('MS Sans Serif', 9, 'bold'), 
                                  bg=Win95Style.BG_GRAY)
        form_frame.pack(fill='x', padx=10, pady=10)

        # Linha 1
        tk.Label(form_frame, text="Codigo de Barras:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.codigo_var = tk.StringVar()
        self.codigo_entry = tk.Entry(form_frame, textvariable=self.codigo_var, 
                                    font=('MS Sans Serif', 10), width=20)
        self.codigo_entry.grid(row=0, column=1, padx=5, pady=5)
        self.codigo_entry.bind('<Return>', lambda e: self.nome_entry.focus_set())

        Win95Style.create_button(form_frame, "🔢 Gerar Codigo (F9)", self.gerar_codigo,
                                bg_color="#9C27B0", fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(form_frame, text="Nome do Produto:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=3, padx=5, pady=5, sticky='e')
        self.nome_var = tk.StringVar()
        self.nome_entry = tk.Entry(form_frame, textvariable=self.nome_var, 
                                  font=('MS Sans Serif', 10), width=30)
        self.nome_entry.grid(row=0, column=4, padx=5, pady=5)
        self.nome_entry.bind('<Return>', lambda e: self.preco_entry.focus_set())

        # Linha 2
        tk.Label(form_frame, text="Preco (R$):", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.preco_var = tk.StringVar()
        self.preco_entry = tk.Entry(form_frame, textvariable=self.preco_var, 
                                   font=('MS Sans Serif', 10), width=15)
        self.preco_entry.grid(row=1, column=1, padx=5, pady=5)
        self.preco_entry.bind('<Return>', lambda e: self.estoque_entry.focus_set())

        tk.Label(form_frame, text="Estoque:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.estoque_var = tk.StringVar(value="0")
        self.estoque_entry = tk.Entry(form_frame, textvariable=self.estoque_var, 
                                     font=('MS Sans Serif', 10), width=10)
        self.estoque_entry.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        self.estoque_entry.bind('<Return>', lambda e: self.unidade_combo.focus_set())

        tk.Label(form_frame, text="Unidade:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=4, padx=5, pady=5, sticky='e')
        self.unidade_var = tk.StringVar(value="UN")
        self.unidade_combo = ttk.Combobox(form_frame, textvariable=self.unidade_var, 
                                         values=["UN", "CX", "KG", "LT", "PC", "GR"], width=8)
        self.unidade_combo.grid(row=1, column=5, padx=5, pady=5)

        # Tipo de produto
        self.tipo_peso_var = tk.IntVar(value=0)
        tk.Checkbutton(form_frame, text="Produto por Peso/Grama", variable=self.tipo_peso_var,
                      bg=Win95Style.BG_GRAY, font=('MS Sans Serif', 9)).grid(row=2, column=0, columnspan=2, pady=5)

        btn_frame = tk.Frame(form_frame, bg=Win95Style.BG_GRAY)
        btn_frame.grid(row=3, column=0, columnspan=6, pady=10)

        Win95Style.create_button(btn_frame, "💾 SALVAR (F2)", self.salvar_produto,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🖨️ IMPRIMIR ETIQUETA (F6)", self.imprimir_etiqueta,
                                bg_color=Win95Style.WARNING, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=20).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🔄 LIMPAR (ESC)", self.limpar_campos,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(side='left', padx=5)

        # Atalhos
        self.janela.bind('<F2>', lambda e: self.salvar_produto())
        self.janela.bind('<F6>', lambda e: self.imprimir_etiqueta())
        self.janela.bind('<F9>', lambda e: self.gerar_codigo())
        self.janela.bind('<Escape>', lambda e: self.limpar_campos())

        lista_frame = tk.LabelFrame(self.janela, text=" PRODUTOS CADASTRADOS ", 
                                   font=('MS Sans Serif', 9, 'bold'), 
                                   bg=Win95Style.BG_GRAY)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'codigo', 'nome', 'preco', 'estoque', 'unidade', 'tipo')
        self.tree = ttk.Treeview(lista_frame, columns=cols, show='headings', height=12)

        self.tree.heading('id', text='ID')
        self.tree.heading('codigo', text='CODIGO DE BARRAS')
        self.tree.heading('nome', text='NOME DO PRODUTO')
        self.tree.heading('preco', text='PRECO')
        self.tree.heading('estoque', text='ESTOQUE')
        self.tree.heading('unidade', text='UN')
        self.tree.heading('tipo', text='TIPO')

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('codigo', width=150, anchor='center')
        self.tree.column('nome', width=250)
        self.tree.column('preco', width=100, anchor='e')
        self.tree.column('estoque', width=80, anchor='center')
        self.tree.column('unidade', width=50, anchor='center')
        self.tree.column('tipo', width=80, anchor='center')

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        acao_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        acao_frame.pack(fill='x', padx=10, pady=5)

        Win95Style.create_button(acao_frame, "✏️ EDITAR (F3)", self.editar_produto,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(acao_frame, "🗑️ EXCLUIR (F4)", self.excluir_produto,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(acao_frame, "📄 ETIQUETA (F7)", self.imprimir_etiqueta_selecionado,
                                bg_color="#9C27B0", fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=15).pack(side='left', padx=5)

        Win95Style.create_button(acao_frame, "🔄 ATUALIZAR (F5)", self.carregar_produtos,
                                bg_color=Win95Style.DARK_GRAY, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold'), width=15).pack(side='right', padx=5)

        Win95Style.create_button(acao_frame, "❌ FECHAR", self.fechar,
                                font=('MS Sans Serif', 9, 'bold'), width=12).pack(side='right', padx=5)

        self.janela.bind('<F3>', lambda e: self.editar_produto())
        self.janela.bind('<F4>', lambda e: self.excluir_produto())
        self.janela.bind('<F5>', lambda e: self.carregar_produtos())
        self.janela.bind('<F7>', lambda e: self.imprimir_etiqueta_selecionado())

        self.status_label = tk.Label(self.janela, text="Pronto", 
                                    bg=Win95Style.BG_GRAY, fg=Win95Style.DARK_GRAY, 
                                    font=('MS Sans Serif', 9))
        self.status_label.pack(pady=5)

    def gerar_codigo(self):
        codigo = self.db.gerar_codigo_barras_avulso()
        self.codigo_var.set(codigo)
        self.nome_entry.focus_set()
        messagebox.showinfo("Codigo Gerado", f"Codigo EAN-13 gerado:\n{codigo}")

    def imprimir_etiqueta(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        codigo = self.codigo_var.get().strip()
        nome = self.nome_var.get().strip()
        preco_str = self.preco_var.get().strip()

        if not codigo or not nome:
            messagebox.showwarning("Aviso", "Preencha codigo e nome do produto!")
            return

        try:
            preco = float(preco_str.replace(',', '.'))
        except:
            preco = 0

        resultado = self.ean_generator.gerar_imagem(codigo, altura=120, largura_scale=2)
        if resultado:
            img, codigo_validado = resultado
            largura, altura = img.size
            nova_altura = altura + 60
            img_final = Image.new('RGB', (largura, nova_altura), 'white')
            img_final.paste(img, (0, 0))

            draw = ImageDraw.Draw(img_final)
            try:
                font_nome = ImageFont.truetype("arial.ttf", 14)
                font_preco = ImageFont.truetype("arial.ttf", 18)
            except:
                font_nome = ImageFont.load_default()
                font_preco = ImageFont.load_default()

            draw.text((10, altura + 5), nome[:30], fill='black', font=font_nome)
            draw.text((10, altura + 28), f"R$ {preco:.2f}", fill='red', font=font_preco)

            arquivo = os.path.join(get_etiquetas_path(), f"etiqueta_{codigo}.png")
            img_final.save(arquivo, dpi=(300, 300))

            os.system(f'start "" "{arquivo}"')
            messagebox.showinfo("Sucesso", f"Etiqueta gerada e enviada para impressao!\nSalva em: {arquivo}")

    def imprimir_etiqueta_selecionado(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto na lista!")
            return

        valores = self.tree.item(selecionado[0])['values']
        codigo = valores[1]
        nome = valores[2]
        preco_str = valores[3].replace('R$ ', '').replace(',', '.')

        try:
            preco = float(preco_str)
        except:
            preco = 0

        resultado = self.ean_generator.gerar_imagem(codigo, altura=120, largura_scale=2)
        if resultado:
            img, codigo_validado = resultado
            largura, altura = img.size
            nova_altura = altura + 60
            img_final = Image.new('RGB', (largura, nova_altura), 'white')
            img_final.paste(img, (0, 0))

            draw = ImageDraw.Draw(img_final)
            try:
                font_nome = ImageFont.truetype("arial.ttf", 14)
                font_preco = ImageFont.truetype("arial.ttf", 18)
            except:
                font_nome = ImageFont.load_default()
                font_preco = ImageFont.load_default()

            draw.text((10, altura + 5), nome[:30], fill='black', font=font_nome)
            draw.text((10, altura + 28), f"R$ {preco:.2f}", fill='red', font=font_preco)

            arquivo = os.path.join(get_etiquetas_path(), f"etiqueta_{codigo}.png")
            img_final.save(arquivo, dpi=(300, 300))

            os.system(f'start "" "{arquivo}"')
            messagebox.showinfo("Sucesso", "Etiqueta enviada para impressao!")

    def carregar_produtos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        produtos = self.db.get_all_produtos()
        for p in produtos:
            tipo = "PESO" if p[6] == 1 else "UNID"
            self.tree.insert('', 'end', values=(p[0], p[1], p[2], f"R$ {p[3]:.2f}", p[4], p[5], tipo))

        self.status_label.config(text=f"Total de produtos: {len(produtos)}")

    def salvar_produto(self):
        codigo = self.codigo_var.get().strip()
        nome = self.nome_var.get().strip()
        preco_str = self.preco_var.get().strip().replace(',', '.')
        estoque_str = self.estoque_var.get().strip()
        unidade = self.unidade_var.get()
        tipo_peso = self.tipo_peso_var.get()

        if not codigo or not nome or not preco_str:
            messagebox.showerror("Erro", "Preencha codigo, nome e preco!")
            return

        try:
            preco = float(preco_str)
            estoque = float(estoque_str) if estoque_str else 0
        except ValueError:
            messagebox.showerror("Erro", "Preco e estoque devem ser numeros!")
            return

        if preco <= 0:
            messagebox.showerror("Erro", "Preco deve ser maior que zero!")
            return

        if self.db.add_produto(codigo, nome, preco, estoque, unidade, tipo_peso):
            messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
            self.limpar_campos()
            self.carregar_produtos()
            self.codigo_entry.focus_set()
        else:
            messagebox.showerror("Erro", f"Codigo '{codigo}' ja existe!")

    def limpar_campos(self):
        self.codigo_var.set('')
        self.nome_var.set('')
        self.preco_var.set('')
        self.estoque_var.set('0')
        self.unidade_var.set('UN')
        self.tipo_peso_var.set(0)
        self.codigo_entry.focus_set()

    def editar_produto(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto para editar!")
            return

        valores = self.tree.item(selecionado[0])['values']
        produto_id = valores[0]

        edit_janela = tk.Toplevel(self.janela)
        edit_janela.title("Editar Produto")
        edit_janela.geometry("400x350")
        edit_janela.configure(bg=Win95Style.BG_GRAY)
        edit_janela.transient(self.janela)
        edit_janela.grab_set()
        edit_janela.resizable(False, False)

        tk.Label(edit_janela, text="Nome:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(pady=5)
        nome_edit = tk.StringVar(value=valores[2])
        nome_entry = tk.Entry(edit_janela, textvariable=nome_edit, 
                             font=('MS Sans Serif', 10), width=40)
        nome_entry.pack()
        nome_entry.focus_set()

        tk.Label(edit_janela, text="Preco (R$):", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(pady=5)
        preco_edit = tk.StringVar(value=str(valores[3]).replace('R$ ', ''))
        preco_entry = tk.Entry(edit_janela, textvariable=preco_edit, 
                              font=('MS Sans Serif', 10), width=15)
        preco_entry.pack()

        tk.Label(edit_janela, text="Estoque:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(pady=5)
        estoque_edit = tk.StringVar(value=valores[4])
        estoque_entry = tk.Entry(edit_janela, textvariable=estoque_edit, 
                                font=('MS Sans Serif', 10), width=10)
        estoque_entry.pack()

        tk.Label(edit_janela, text="Unidade:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(pady=5)
        unidade_edit = tk.StringVar(value=valores[5])
        unidade_combo = ttk.Combobox(edit_janela, textvariable=unidade_edit, 
                                    values=["UN", "CX", "KG", "LT", "PC", "GR"], width=8)
        unidade_combo.pack()

        tipo_peso_edit = tk.IntVar(value=1 if valores[6] == "PESO" else 0)
        tk.Checkbutton(edit_janela, text="Produto por Peso/Grama", variable=tipo_peso_edit,
                      bg=Win95Style.BG_GRAY, font=('MS Sans Serif', 9)).pack(pady=5)

        def salvar_edicao():
            try:
                novo_preco = float(preco_edit.get().replace(',', '.'))
                novo_estoque = float(estoque_edit.get())

                if self.db.update_produto(produto_id, nome_edit.get(), novo_preco, 
                                         novo_estoque, unidade_edit.get(), tipo_peso_edit.get()):
                    messagebox.showinfo("Sucesso", "Produto atualizado!")
                    edit_janela.destroy()
                    self.carregar_produtos()
                else:
                    messagebox.showerror("Erro", "Nao foi possivel atualizar!")
            except ValueError:
                messagebox.showerror("Erro", "Preco e estoque devem ser numeros!")

        nome_entry.bind('<Return>', lambda e: preco_entry.focus_set())
        preco_entry.bind('<Return>', lambda e: estoque_entry.focus_set())
        estoque_entry.bind('<Return>', lambda e: unidade_combo.focus_set())
        unidade_combo.bind('<Return>', lambda e: salvar_edicao())

        Win95Style.create_button(edit_janela, "SALVAR (ENTER)", salvar_edicao,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 11, 'bold'), width=20).pack(pady=20)

        Win95Style.create_button(edit_janela, "CANCELAR", edit_janela.destroy,
                                width=15).pack(pady=5)

    def excluir_produto(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto para excluir!")
            return

        valores = self.tree.item(selecionado[0])['values']
        produto_id = valores[0]
        nome = valores[2]

        if messagebox.askyesno("Confirmar", f"Deseja realmente excluir '{nome}'?"):
            if self.db.delete_produto(produto_id):
                messagebox.showinfo("Sucesso", f"Produto '{nome}' excluido!")
                self.carregar_produtos()
            else:
                messagebox.showerror("Erro", "Nao foi possivel excluir!")

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE CADASTRO DE USUARIOS - ESTILO WIN95
# =============================================================================

class CadastroUsuarios:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Usuarios")
        self.janela.geometry("700x500")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db

        self.create_interface()
        self.carregar_usuarios()

        self.janela.after(100, lambda: self.nome_entry.focus_set())
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="CADASTRO DE USUARIOS", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        form = tk.LabelFrame(self.janela, text=" NOVO USUARIO ", 
                            font=('MS Sans Serif', 9, 'bold'),
                            bg=Win95Style.BG_GRAY)
        form.pack(fill='x', padx=10, pady=10)

        tk.Label(form, text="Nome:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.nome_var = tk.StringVar()
        self.nome_entry = tk.Entry(form, textvariable=self.nome_var, width=30,
                                  font=('MS Sans Serif', 10))
        self.nome_entry.grid(row=0, column=1, padx=5)
        self.nome_entry.bind('<Return>', lambda e: self.user_entry.focus_set())

        tk.Label(form, text="Usuario:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.user_var = tk.StringVar()
        self.user_entry = tk.Entry(form, textvariable=self.user_var, width=20,
                                  font=('MS Sans Serif', 10))
        self.user_entry.grid(row=0, column=3, padx=5)
        self.user_entry.bind('<Return>', lambda e: self.senha_entry.focus_set())

        tk.Label(form, text="Senha:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.senha_var = tk.StringVar()
        self.senha_entry = tk.Entry(form, textvariable=self.senha_var, show="*", width=20,
                                   font=('MS Sans Serif', 10))
        self.senha_entry.grid(row=1, column=1, padx=5)
        self.senha_entry.bind('<Return>', lambda e: self.cargo_combo.focus_set())

        tk.Label(form, text="Cargo:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.cargo_var = tk.StringVar(value="Caixa")
        self.cargo_combo = ttk.Combobox(form, textvariable=self.cargo_var, 
                                       values=["Gerente", "Caixa"], width=15)
        self.cargo_combo.grid(row=1, column=3, padx=5)
        self.cargo_combo.bind('<Return>', lambda e: self.salvar_usuario())

        Win95Style.create_button(form, "💾 SALVAR (F2)", self.salvar_usuario,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold')).grid(row=2, column=0, columnspan=4, pady=10)

        self.janela.bind('<F2>', lambda e: self.salvar_usuario())

        lista = tk.LabelFrame(self.janela, text=" USUARIOS CADASTRADOS ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=Win95Style.BG_GRAY)
        lista.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'nome', 'usuario', 'cargo', 'status')
        self.tree = ttk.Treeview(lista, columns=cols, show='headings', height=10)

        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=100, anchor='center')

        self.tree.column('nome', width=200)

        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        btn_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        btn_frame.pack(fill='x', padx=10, pady=5)

        Win95Style.create_button(btn_frame, "🔄 Resetar Senha (123456) (F3)", self.resetar_senha,
                                bg_color=Win95Style.WARNING, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🗑️ Desativar Usuario (F4)", self.desativar_usuario,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🔄 Atualizar (F5)", self.carregar_usuarios,
                                bg_color=Win95Style.DARK_GRAY, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='right', padx=5)

        Win95Style.create_button(btn_frame, "❌ FECHAR", self.fechar,
                                font=('MS Sans Serif', 9, 'bold')).pack(side='right', padx=5)

        self.janela.bind('<F3>', lambda e: self.resetar_senha())
        self.janela.bind('<F4>', lambda e: self.desativar_usuario())
        self.janela.bind('<F5>', lambda e: self.carregar_usuarios())

    def carregar_usuarios(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for u in self.db.get_all_usuarios():
            self.tree.insert('', 'end', values=u)

    def salvar_usuario(self):
        nome = self.nome_var.get().strip()
        user = self.user_var.get().strip()
        senha = self.senha_var.get().strip()
        cargo = self.cargo_var.get()

        if not all([nome, user, senha]):
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return

        if self.db.add_usuario(user, senha, nome, cargo):
            messagebox.showinfo("Sucesso", f"Usuario '{nome}' cadastrado!")
            self.limpar()
            self.carregar_usuarios()
            self.nome_entry.focus_set()
        else:
            messagebox.showerror("Erro", "Nome de usuario ja existe!")

    def limpar(self):
        self.nome_var.set('')
        self.user_var.set('')
        self.senha_var.set('')
        self.cargo_var.set('Caixa')

    def resetar_senha(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um usuario!")
            return

        id_user = self.tree.item(sel[0])['values'][0]
        if self.db.update_usuario_senha(id_user, "123456"):
            messagebox.showinfo("Sucesso", "Senha resetada para: 123456")

    def desativar_usuario(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um usuario!")
            return

        id_user = self.tree.item(sel[0])['values'][0]
        nome = self.tree.item(sel[0])['values'][1]

        if messagebox.askyesno("Confirmar", f"Desativar usuario '{nome}'?"):
            if self.db.desativar_usuario(id_user):
                self.carregar_usuarios()

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE RELATORIO DE VENDAS - ESTILO WIN95
# =============================================================================

class RelatorioVendas:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Relatorio de Vendas")
        self.janela.geometry("1000x700")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db

        self.create_interface()
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="RELATORIO DE VENDAS", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        filtros = tk.LabelFrame(self.janela, text=" FILTROS ", 
                               font=('MS Sans Serif', 9, 'bold'),
                               bg=Win95Style.BG_GRAY)
        filtros.pack(fill='x', padx=10, pady=10)

        tk.Label(filtros, text="De:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.data_ini = tk.StringVar(value=get_brasil_today().strftime('%d/%m/%Y'))
        tk.Entry(filtros, textvariable=self.data_ini, width=12,
                font=('MS Sans Serif', 10)).pack(side='left', padx=5)

        tk.Label(filtros, text="Ate:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.data_fim = tk.StringVar(value=get_brasil_today().strftime('%d/%m/%Y'))
        tk.Entry(filtros, textvariable=self.data_fim, width=12,
                font=('MS Sans Serif', 10)).pack(side='left', padx=5)

        tk.Label(filtros, text="Forma:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.forma_var = tk.StringVar(value="TODAS")
        formas = ["TODAS", "dinheiro", "credito", "debito", "pix", "fiado", "parcelado"]
        ttk.Combobox(filtros, textvariable=self.forma_var, values=formas, width=12).pack(side='left', padx=5)

        Win95Style.create_button(filtros, "🔍 BUSCAR (F2)", self.buscar_vendas,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=20)

        Win95Style.create_button(filtros, "📊 HOJE (F3)", self.vendas_hoje,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        Win95Style.create_button(filtros, "📋 RESUMO (F4)", self.mostrar_resumo,
                                bg_color="#9C27B0", fg_color="white",
                                font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        self.janela.bind('<F2>', lambda e: self.buscar_vendas())
        self.janela.bind('<F3>', lambda e: self.vendas_hoje())
        self.janela.bind('<F4>', lambda e: self.mostrar_resumo())

        # Resumo por forma de pagamento
        self.resumo_frame = tk.LabelFrame(self.janela, text=" RESUMO POR FORMA DE PAGAMENTO ", 
                                         font=('MS Sans Serif', 9, 'bold'),
                                         bg=Win95Style.BG_GRAY)
        self.resumo_frame.pack(fill='x', padx=10, pady=5)

        self.resumo_labels = {}
        formas_pag = ['dinheiro', 'credito', 'debito', 'pix', 'fiado', 'parcelado']
        cores = [Win95Style.SUCCESS, Win95Style.INFO, Win95Style.WARNING, "#9C27B0", "#E91E63", "#FF5722"]

        for i, (forma, cor) in enumerate(zip(formas_pag, cores)):
            frame = tk.Frame(self.resumo_frame, bg=cor, padx=10, pady=5)
            frame.pack(side='left', padx=5, pady=5, fill='both', expand=True)
            tk.Label(frame, text=forma.upper(), font=('MS Sans Serif', 9, 'bold'), 
                    bg=cor, fg="white").pack()
            self.resumo_labels[forma] = tk.Label(frame, text="R$ 0,00 | 0 vendas", 
                                                font=('MS Sans Serif', 10, 'bold'), 
                                                bg=cor, fg="white")
            self.resumo_labels[forma].pack()

        self.total_frame = tk.Frame(self.resumo_frame, bg=Win95Style.NAVY, padx=10, pady=5)
        self.total_frame.pack(side='left', padx=5, pady=5, fill='both', expand=True)
        tk.Label(self.total_frame, text="TOTAL GERAL", font=('MS Sans Serif', 9, 'bold'), 
                bg=Win95Style.NAVY, fg="white").pack()
        self.total_geral_label = tk.Label(self.total_frame, text="R$ 0,00 | 0 vendas", 
                                         font=('MS Sans Serif', 11, 'bold'), 
                                         bg=Win95Style.NAVY, fg="white")
        self.total_geral_label.pack()

        lista = tk.LabelFrame(self.janela, text=" VENDAS ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=Win95Style.BG_GRAY)
        lista.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('cupom', 'data', 'hora', 'total', 'pagamento')
        self.tree = ttk.Treeview(lista, columns=cols, show='headings', height=15)

        self.tree.heading('cupom', text='CUPOM')
        self.tree.heading('data', text='DATA')
        self.tree.heading('hora', text='HORA')
        self.tree.heading('total', text='TOTAL')
        self.tree.heading('pagamento', text='PAGAMENTO')

        self.tree.column('cupom', width=150, anchor='center')
        self.tree.column('data', width=100, anchor='center')
        self.tree.column('hora', width=100, anchor='center')
        self.tree.column('total', width=100, anchor='e')
        self.tree.column('pagamento', width=100, anchor='center')

        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        btn_frame = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        btn_frame.pack(fill='x', padx=10, pady=5)

        Win95Style.create_button(btn_frame, "📄 EXPORTAR PARA TXT (F5)", self.exportar,
                                bg_color=Win95Style.WARNING, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "❌ FECHAR (ESC)", self.fechar,
                                font=('MS Sans Serif', 9, 'bold'), width=15).pack(side='right', padx=5)

        self.janela.bind('<F5>', lambda e: self.exportar())
        self.janela.bind('<Escape>', lambda e: self.fechar())

        self.vendas_hoje()

    def vendas_hoje(self):
        hoje = get_brasil_today().strftime('%Y-%m-%d')
        self.data_ini.set(get_brasil_today().strftime('%d/%m/%Y'))
        self.data_fim.set(get_brasil_today().strftime('%d/%m/%Y'))
        self.forma_var.set("TODAS")
        self.buscar_vendas(hoje, hoje)

    def buscar_vendas(self, ini=None, fim=None):
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            if ini is None:
                ini = datetime.datetime.strptime(self.data_ini.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
                fim = datetime.datetime.strptime(self.data_fim.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
        except:
            messagebox.showerror("Erro", "Datas invalidas! Use DD/MM/AAAA")
            return

        forma = self.forma_var.get()
        if forma == "TODAS":
            forma = None

        vendas = self.db.get_vendas_periodo(ini, fim, forma)
        total = 0
        qtd = 0

        for v in vendas:
            # Data já está em horário local do servidor
            data_brasil = datetime.datetime.strptime(v[1], '%Y-%m-%d %H:%M:%S')

            self.tree.insert('', 'end', values=(
                v[0],
                data_brasil.strftime('%d/%m/%Y'),
                data_brasil.strftime('%H:%M:%S'),
                f"R$ {v[2]:.2f}",
                v[3].upper()
            ))
            total += v[2]
            qtd += 1

        self.atualizar_resumo(ini, fim)

    def atualizar_resumo(self, ini, fim):
        resumo = self.db.get_vendas_por_forma_pagamento(ini, fim)

        total_geral = 0
        qtd_geral = 0

        for forma in self.resumo_labels:
            self.resumo_labels[forma].config(text="R$ 0,00 | 0 vendas")

        for forma, qtd, total in resumo:
            if forma in self.resumo_labels:
                self.resumo_labels[forma].config(text=f"R$ {total:.2f} | {qtd} vendas")
            total_geral += total
            qtd_geral += qtd

        self.total_geral_label.config(text=f"R$ {total_geral:.2f} | {qtd_geral} vendas")

    def mostrar_resumo(self):
        try:
            ini = datetime.datetime.strptime(self.data_ini.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
            fim = datetime.datetime.strptime(self.data_fim.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
        except:
            messagebox.showerror("Erro", "Datas invalidas!")
            return

        resumo = self.db.get_vendas_por_forma_pagamento(ini, fim)

        msg = "RESUMO DE VENDAS\n" + "="*40 + "\n\n"
        total = 0
        for forma, qtd, valor in resumo:
            msg += f"{forma.upper():<15} {qtd:>3} vendas = R$ {valor:>10.2f}\n"
            total += valor
        msg += "\n" + "="*40 + "\n"
        msg += f"TOTAL GERAL:     R$ {total:.2f}"

        messagebox.showinfo("Resumo de Vendas", msg)

    def exportar(self):
        try:
            ini = datetime.datetime.strptime(self.data_ini.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
            fim = datetime.datetime.strptime(self.data_fim.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
        except:
            messagebox.showerror("Erro", "Datas invalidas!")
            return

        arquivo = f"relatorio_vendas_{get_brasil_today().strftime('%Y%m%d')}.txt"

        resumo = self.db.get_vendas_por_forma_pagamento(ini, fim)

        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write("RELATORIO DE VENDAS\n")
            f.write("="*50 + "\n")
            f.write(f"Periodo: {self.data_ini.get()} a {self.data_fim.get()}\n\n")

            f.write("RESUMO POR FORMA DE PAGAMENTO\n")
            f.write("-"*50 + "\n")
            total = 0
            for forma, qtd, valor in resumo:
                f.write(f"{forma.upper():<15} {qtd:>3} vendas = R$ {valor:>10.2f}\n")
                total += valor
            f.write("-"*50 + "\n")
            f.write(f"{'TOTAL':<15} {'':>3}        = R$ {total:>10.2f}\n\n")

            f.write("DETALHAMENTO\n")
            f.write("="*50 + "\n\n")
            for item in self.tree.get_children():
                valores = self.tree.item(item)['values']
                f.write(f"Cupom: {valores[0]} | Data: {valores[1]} | Hora: {valores[2]} | Total: {valores[3]} | {valores[4]}\n")

        messagebox.showinfo("Sucesso", f"Relatorio salvo em:\n{os.path.abspath(arquivo)}")

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE CONFIGURACOES - ESTILO WIN95
# =============================================================================

class ConfiguracoesSistema:
    def __init__(self, parent, db, backup_manager):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Configuracoes do Sistema")
        self.janela.geometry("650x650")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db
        self.backup_manager = backup_manager
        self.qr_generator = QRCodeGenerator()

        self.create_interface()
        self.carregar_config()

        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="CONFIGURACOES", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Notebook para abas
        notebook = ttk.Notebook(self.janela)
        notebook.pack(fill='both', expand=True, padx=15, pady=15)

        # Aba Dados da Empresa
        tab_empresa = tk.Frame(notebook, bg=Win95Style.BG_GRAY)
        notebook.add(tab_empresa, text="Dados da Empresa")

        campos = [
            ("Nome da Empresa:", "nome", 50),
            ("CNPJ:", "cnpj", 30),
            ("Endereco:", "endereco", 50),
            ("Telefone:", "telefone", 30),
            ("Mensagem do Cupom:", "mensagem", 50),
            ("Chave PIX:", "chave_pix", 50),
            ("Nome do Recebedor PIX:", "nome_recebedor", 50)
        ]

        self.vars = {}
        for i, (label, campo, width) in enumerate(campos):
            tk.Label(tab_empresa, text=label, bg=Win95Style.BG_GRAY, 
                    font=('MS Sans Serif', 9, 'bold')).pack(anchor='w', pady=(15 if i==0 else 10, 0), padx=15)
            self.vars[campo] = tk.StringVar()
            entry = tk.Entry(tab_empresa, textvariable=self.vars[campo], 
                           font=('MS Sans Serif', 10), width=width)
            entry.pack(anchor='w', padx=15, pady=2, fill='x')

        Win95Style.create_button(tab_empresa, "💾 SALVAR DADOS (F2)", self.salvar,
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 10, 'bold'), width=20).pack(pady=20)

        # Aba QR Code PIX
        tab_pix = tk.Frame(notebook, bg=Win95Style.BG_GRAY)
        notebook.add(tab_pix, text="QR Code PIX")

        tk.Label(tab_pix, text="GERADOR DE QR CODE PIX", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.BG_GRAY).pack(pady=20)

        tk.Label(tab_pix, text="Valor (R$):", font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack()
        self.pix_valor = tk.StringVar(value="10.00")
        tk.Entry(tab_pix, textvariable=self.pix_valor, font=('MS Sans Serif', 12), width=15, justify='center').pack(pady=5)

        tk.Label(tab_pix, text="Descricao:", font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack()
        self.pix_desc = tk.StringVar(value="Pagamento")
        tk.Entry(tab_pix, textvariable=self.pix_desc, font=('MS Sans Serif', 10), width=40).pack(pady=5)

        Win95Style.create_button(tab_pix, "📱 GERAR QR CODE (F3)", self.gerar_qr_pix,
                                bg_color="#9C27B0", fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=25).pack(pady=15)

        # Frame para preview do QR Code
        self.qr_frame = tk.LabelFrame(tab_pix, text=" QR CODE GERADO ", 
                                     font=('MS Sans Serif', 9, 'bold'),
                                     bg=Win95Style.BG_GRAY)
        self.qr_frame.pack(pady=10, padx=20, fill='both', expand=True)

        self.qr_label = tk.Label(self.qr_frame, bg="white")
        self.qr_label.pack(padx=20, pady=20)

        Win95Style.create_button(tab_pix, "💾 SALVAR IMAGEM (F4)", self.salvar_qr,
                                bg_color=Win95Style.WARNING, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=20).pack(pady=10)

        # Botao fechar
        Win95Style.create_button(self.janela, "❌ FECHAR (ESC)", self.fechar,
                                width=15).pack(pady=10)

        # Atalhos
        self.janela.bind('<F2>', lambda e: self.salvar())
        self.janela.bind('<F3>', lambda e: self.gerar_qr_pix())
        self.janela.bind('<F4>', lambda e: self.salvar_qr())
        self.janela.bind('<Escape>', lambda e: self.fechar())

    def carregar_config(self):
        config = self.db.get_config()
        if config:
            self.vars['nome'].set(config[1] or '')
            self.vars['cnpj'].set(config[2] or '')
            self.vars['endereco'].set(config[3] or '')
            self.vars['telefone'].set(config[4] or '')
            self.vars['mensagem'].set(config[5] or '')
            if len(config) > 6:
                self.vars['chave_pix'].set(config[6] or '')
            if len(config) > 7:
                self.vars['nome_recebedor'].set(config[7] or '')

    def salvar(self):
        if self.db.update_config(
            self.vars['nome'].get(),
            self.vars['cnpj'].get(),
            self.vars['endereco'].get(),
            self.vars['telefone'].get(),
            self.vars['mensagem'].get(),
            self.vars['chave_pix'].get(),
            self.vars['nome_recebedor'].get()
        ):
            messagebox.showinfo("Sucesso", "Configuracoes salvas!")
        else:
            messagebox.showerror("Erro", "Nao foi possivel salvar!")

    def gerar_qr_pix(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        chave = self.vars['chave_pix'].get().strip()
        if not chave:
            messagebox.showwarning("Aviso", "Cadastre a chave PIX na aba 'Dados da Empresa'!")
            return

        try:
            valor = float(self.pix_valor.get().replace(',', '.'))
        except:
            valor = 0

        descricao = self.pix_desc.get() or "Pagamento"

        img, payload = self.qr_generator.gerar_pix_qrcode(chave, valor, descricao)

        img_display = img.resize((250, 250))
        img_tk = ImageTk.PhotoImage(img_display)

        self.qr_label.config(image=img_tk)
        self.qr_label.image = img_tk

        self.qr_imagem = img
        self.qr_payload = payload

        messagebox.showinfo("QR Code Gerado", 
                           f"Payload PIX:\n{payload[:50]}...\n\n" +
                           f"Valor: R$ {valor:.2f}\n" +
                           f"Chave: {chave}\n\n" +
                           "Escaneie com o app do seu banco!")

    def salvar_qr(self):
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        if not hasattr(self, 'qr_imagem'):
            messagebox.showwarning("Aviso", "Gere o QR Code primeiro!")
            return

        arquivo = os.path.join(get_qrcode_path(), 
                              f"pix_{get_brasil_now().strftime('%Y%m%d_%H%M%S')}.png")
        self.qr_imagem.save(arquivo)
        messagebox.showinfo("Sucesso", f"QR Code salvo!\n{arquivo}")

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE CONSULTA DE ESTOQUE - ESTILO WIN95
# =============================================================================

class ConsultaEstoque:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Consulta de Estoque")
        self.janela.geometry("900x600")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db

        self.create_interface()
        self.carregar_estoque()

        self.janela.after(100, lambda: self.busca_entry.focus_set())
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="CONSULTA DE ESTOQUE", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        filtros = tk.Frame(self.janela, bg=Win95Style.BG_GRAY)
        filtros.pack(fill='x', padx=10, pady=10)

        tk.Label(filtros, text="Buscar:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.busca_var = tk.StringVar()
        self.busca_entry = tk.Entry(filtros, textvariable=self.busca_var, width=30, font=('MS Sans Serif', 10))
        self.busca_entry.pack(side='left', padx=5)
        self.busca_entry.bind('<Return>', lambda e: self.filtrar())

        Win95Style.create_button(filtros, "🔍 BUSCAR (F2)", self.filtrar,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        Win95Style.create_button(filtros, "⚠️ Estoque Baixo (F3)", self.estoque_baixo,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='right', padx=5)

        Win95Style.create_button(filtros, "🔄 Atualizar (F4)", self.carregar_estoque,
                                bg_color=Win95Style.DARK_GRAY, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).pack(side='right', padx=5)

        self.janela.bind('<F2>', lambda e: self.filtrar())
        self.janela.bind('<F3>', lambda e: self.estoque_baixo())
        self.janela.bind('<F4>', lambda e: self.carregar_estoque())

        lista = tk.LabelFrame(self.janela, text=" PRODUTOS EM ESTOQUE ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=Win95Style.BG_GRAY)
        lista.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('codigo', 'nome', 'preco', 'estoque', 'unidade', 'status', 'tipo')
        self.tree = ttk.Treeview(lista, columns=cols, show='headings', height=12)

        for c in cols:
            self.tree.heading(c, text=c.upper())

        self.tree.column('codigo', width=120, anchor='center')
        self.tree.column('nome', width=250)
        self.tree.column('preco', width=80, anchor='e')
        self.tree.column('estoque', width=80, anchor='center')
        self.tree.column('unidade', width=50, anchor='center')
        self.tree.column('status', width=100, anchor='center')
        self.tree.column('tipo', width=80, anchor='center')

        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        entrada = tk.LabelFrame(self.janela, text=" ENTRADA DE ESTOQUE (NOTA FISCAL) ", 
                               font=('MS Sans Serif', 9, 'bold'),
                               bg=Win95Style.BG_GRAY)
        entrada.pack(fill='x', padx=10, pady=10)

        tk.Label(entrada, text="Codigo:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5)
        self.ent_codigo = tk.StringVar()
        ent_cod_entry = tk.Entry(entrada, textvariable=self.ent_codigo, width=15, font=('MS Sans Serif', 10))
        ent_cod_entry.grid(row=0, column=1, padx=5)

        tk.Label(entrada, text="Qtd a Adicionar:", bg=Win95Style.BG_GRAY,
                font=('MS Sans Serif', 9)).grid(row=0, column=2, padx=5, pady=5)
        self.ent_qtd = tk.StringVar()
        self.ent_qtd_entry = tk.Entry(entrada, textvariable=self.ent_qtd, width=10, font=('MS Sans Serif', 10))
        self.ent_qtd_entry.grid(row=0, column=3, padx=5)

        Win95Style.create_button(entrada, "➕ ADICIONAR ESTOQUE", self.entrada_estoque,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 9, 'bold')).grid(row=0, column=4, padx=20, pady=5)

        Win95Style.create_button(self.janela, "❌ FECHAR (ESC)", self.fechar,
                                width=15).pack(pady=5)

        self.janela.bind('<Escape>', lambda e: self.fechar())
        self.busca_var.trace('w', lambda *args: self.filtrar())

    def carregar_estoque(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for p in self.db.get_all_produtos():
            status = "OK" if p[4] > 10 else "BAIXO" if p[4] > 0 else "ZERADO"
            tipo = "PESO" if p[6] == 1 else "UNID"
            self.tree.insert('', 'end', values=(p[1], p[2], f"R$ {p[3]:.2f}", p[4], p[5], status, tipo))

    def filtrar(self):
        termo = self.busca_var.get().lower()
        for item in self.tree.get_children():
            valores = self.tree.item(item)['values']
            if termo in valores[0].lower() or termo in valores[1].lower():
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

    def estoque_baixo(self):
        for item in self.tree.get_children():
            valores = self.tree.item(item)['values']
            try:
                estoque = float(valores[3])
                if estoque <= 10:
                    self.tree.reattach(item, '', 'end')
                else:
                    self.tree.detach(item)
            except:
                pass

    def entrada_estoque(self):
        codigo = self.ent_codigo.get().strip()
        try:
            qtd = float(self.ent_qtd.get())
        except:
            messagebox.showerror("Erro", "Quantidade invalida!")
            return

        if qtd <= 0:
            messagebox.showerror("Erro", "Quantidade deve ser maior que zero!")
            return

        if self.db.add_estoque(codigo, qtd) > 0:
            messagebox.showinfo("Sucesso", f"Adicionado {qtd} unidades!")
            self.carregar_estoque()
            self.ent_codigo.set('')
            self.ent_qtd.set('')
        else:
            messagebox.showerror("Erro", "Produto nao encontrado!")

    def fechar(self):
        self.janela.destroy()


# =============================================================================
# TELA DE LOGIN - ESTILO WIN95
# =============================================================================

class LoginScreen:
    def __init__(self, root, db, on_login_success):
        self.root = root
        self.db = db
        self.on_login_success = on_login_success

        self.root.title("PDV MERCADO - Login")
        self.root.geometry("400x450")
        self.root.configure(bg=Win95Style.NAVY)
        self.root.resizable(False, False)

        self.center_window()
        self.create_widgets()

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 225
        self.root.geometry(f'+{x}+{y}')

    def create_widgets(self):
        frame = tk.Frame(self.root, bg=Win95Style.BG_GRAY, bd=2, relief='ridge')
        frame.place(relx=0.5, rely=0.5, anchor='center', width=350, height=380)

        tk.Label(frame, text="PDV SUPERMERCADO", 
                font=('MS Sans Serif', 18, 'bold'), fg=Win95Style.NAVY, bg=Win95Style.BG_GRAY).pack(pady=(25, 5))

        tk.Label(frame, text="Sistema de Caixa Offline", 
                font=('MS Sans Serif', 10), fg=Win95Style.DARK_GRAY, bg=Win95Style.BG_GRAY).pack()

        tk.Label(frame, text="Usuario:", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.BG_GRAY, fg=Win95Style.BLACK).pack(anchor='w', padx=30, pady=(15, 2))

        self.username_var = tk.StringVar(value="admin")
        self.user_entry = tk.Entry(frame, textvariable=self.username_var, 
                                  font=('MS Sans Serif', 10), width=25, bd=2, relief='groove')
        self.user_entry.pack()
        self.user_entry.bind('<Return>', lambda e: self.pass_entry.focus_set())

        tk.Label(frame, text="Senha:", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.BG_GRAY, fg=Win95Style.BLACK).pack(anchor='w', padx=30, pady=(15, 2))

        self.password_var = tk.StringVar()
        self.pass_entry = tk.Entry(frame, textvariable=self.password_var, 
                                  font=('MS Sans Serif', 10), width=25, bd=2, 
                                  relief='groove', show="*")
        self.pass_entry.pack()
        self.pass_entry.bind('<Return>', lambda e: self.login())

        Win95Style.create_button(frame, "ENTRAR", self.login,
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 11, 'bold'),
                                width=20, pady=8).pack(pady=25)

        tk.Label(frame, text="Padrao: admin/admin123", 
                font=('MS Sans Serif', 8), fg=Win95Style.DARK_GRAY, bg=Win95Style.BG_GRAY).pack(side='bottom', pady=8)

        self.user_entry.focus_set()

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return

        user = self.db.verify_login(username, password)

        if user:
            self.root.withdraw()
            # Verifica se existe caixa aberto, se nao, abre tela de abertura
            caixa = self.db.get_caixa_aberto()
            if not caixa:
                TelaAberturaCaixa(self.root, self.db, user, self.on_login_success)
            else:
                self.on_login_success(user)
        else:
            messagebox.showerror("Erro", "Usuario ou senha incorretos!")


# =============================================================================
# TELA DE ABERTURA DE CAIXA - ESTILO WIN95
# =============================================================================

class TelaAberturaCaixa:
    def __init__(self, parent, db, user, on_login_success):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Abertura de Caixa")
        self.janela.geometry("400x300")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db
        self.user = user
        self.on_login_success = on_login_success

        self.janela.grab_set()
        self.janela.focus_force()

        self.create_interface()

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.SUCCESS, height=50)
        header.pack(fill='x')
        tk.Label(header, text="ABERTURA DE CAIXA", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.SUCCESS, fg="white").pack(pady=10)

        tk.Label(self.janela, text=f"Operador: {self.user[3]}", 
                font=('MS Sans Serif', 11), bg=Win95Style.BG_GRAY).pack(pady=20)

        tk.Label(self.janela, text="Valor de Abertura (R$):", 
                font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack()

        self.valor_var = tk.StringVar(value="0.00")
        tk.Entry(self.janela, textvariable=self.valor_var, 
                font=('MS Sans Serif', 14), width=15, justify='center').pack(pady=10)

        Win95Style.create_button(self.janela, "✅ ABRIR CAIXA", self.abrir_caixa,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 12, 'bold'), width=20).pack(pady=20)

        self.janela.bind('<Return>', lambda e: self.abrir_caixa())

    def abrir_caixa(self):
        try:
            valor = float(self.valor_var.get().replace(',', '.'))
        except:
            valor = 0

        caixa_id = self.db.abrir_caixa(self.user[0], self.user[3], valor)
        if caixa_id:
            # Registra no log administrativo
            logger = LoggerAdministrativo()
            logger.registrar_abertura_caixa(self.user[3], valor)

            messagebox.showinfo("Sucesso", f"Caixa aberto com sucesso!\nValor: R$ {valor:.2f}")
            self.janela.destroy()
            self.on_login_success(self.user)
        else:
            messagebox.showerror("Erro", "Nao foi possivel abrir o caixa!")


# =============================================================================
# TELA DE FECHAMENTO DE CAIXA - ESTILO WIN95 COM BOTAO DESTACADO
# =============================================================================

class TelaFechamentoCaixa:
    def __init__(self, parent, db, user, on_fechar):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Fechamento de Caixa")
        self.janela.geometry("500x650")
        self.janela.configure(bg=Win95Style.BG_GRAY)
        self.janela.resizable(False, False)
        self.db = db
        self.user = user
        self.on_fechar = on_fechar

        self.janela.grab_set()
        self.janela.focus_force()

        self.create_interface()

    def create_interface(self):
        header = tk.Frame(self.janela, bg=Win95Style.BG_GRAY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="FECHAMENTO DE CAIXA", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Busca dados do caixa
        caixa = self.db.get_caixa_aberto()
        if caixa:
            resumo = self.db.get_resumo_caixa(caixa[0])
        else:
            resumo = (0, 0, 0, 0, 0, 0, 0, "", "")

        # Frame com os totais
        frame_totais = tk.LabelFrame(self.janela, text=" RESUMO DO DIA ", 
                                    font=('MS Sans Serif', 10, 'bold'),
                                    bg=Win95Style.BG_GRAY)
        frame_totais.pack(fill='x', padx=15, pady=10)

        # Valor de abertura
        caixa_info = self.db.get_caixa_aberto()
        valor_abertura = caixa[12] if caixa and len(caixa) > 12 else 0

        frame_abertura = tk.Frame(frame_totais, bg="#2196F3", padx=5, pady=3)
        frame_abertura.pack(fill='x', pady=2)
        tk.Label(frame_abertura, text="VALOR DE ABERTURA:", font=('MS Sans Serif', 10, 'bold'), 
                bg="#2196F3", fg="white", width=18, anchor='e').pack(side='left')
        tk.Label(frame_abertura, text=f"R$ {valor_abertura:.2f}", font=('MS Sans Serif', 10, 'bold'), 
                bg="#2196F3", fg="white", width=12, anchor='e').pack(side='right')

        # Formas de pagamento
        formas = [
            ('Dinheiro', resumo[0] if resumo else 0, Win95Style.SUCCESS),
            ('Cartao Credito', resumo[1] if resumo else 0, Win95Style.INFO),
            ('Cartao Debito', resumo[2] if resumo else 0, Win95Style.WARNING),
            ('PIX', resumo[3] if resumo else 0, "#9C27B0"),
            ('Fiado', resumo[4] if resumo else 0, "#E91E63"),
            ('Parcelado', resumo[5] if resumo else 0, "#FF5722")
        ]

        total_geral = 0
        for nome, valor, cor in formas:
            frame = tk.Frame(frame_totais, bg=cor, padx=5, pady=3)
            frame.pack(fill='x', pady=2)
            tk.Label(frame, text=f"{nome}:", font=('MS Sans Serif', 10, 'bold'), 
                    bg=cor, fg="white", width=15, anchor='e').pack(side='left')
            tk.Label(frame, text=f"R$ {valor:.2f}", font=('MS Sans Serif', 10, 'bold'), 
                    bg=cor, fg="white", width=12, anchor='e').pack(side='right')
            total_geral += valor

        # Total geral
        frame_total = tk.Frame(frame_totais, bg=Win95Style.NAVY, padx=5, pady=5)
        frame_total.pack(fill='x', pady=5)
        tk.Label(frame_total, text="TOTAL VENDAS (Sem Abertura):", font=('MS Sans Serif', 10, 'bold'), bg=Win95Style.NAVY, fg="white").pack(side='left')
        tk.Label(frame_total, text=f"R$ {total_geral:.2f}", font=('MS Sans Serif', 14, 'bold'), 
                bg=Win95Style.NAVY, fg="white").pack(side='right')

        # Total com abertura
        frame_total_com_abertura = tk.Frame(frame_totais, bg="#4CAF50", padx=5, pady=5)
        frame_total_com_abertura.pack(fill='x', pady=5)
        tk.Label(frame_total_com_abertura, text="TOTAL ESPERADO (Abertura + Vendas):", font=('MS Sans Serif', 12, 'bold'), bg="#4CAF50", fg="white").pack(side='left')
        tk.Label(frame_total_com_abertura, text=f"R$ {total_geral + valor_abertura:.2f}", font=('MS Sans Serif', 14, 'bold'), bg="#4CAF50", fg="white").pack(side='right')

        # Valor de fechamento
        tk.Label(self.janela, text="Valor de Fechamento (R$):", 
                font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(pady=(15, 5))

        self.valor_fechamento = tk.StringVar(value=f"{total_geral + valor_abertura:.2f}")
        tk.Entry(self.janela, textvariable=self.valor_fechamento, 
                font=('MS Sans Serif', 14), width=15, justify='center').pack()

        # Observacoes
        tk.Label(self.janela, text="Observacoes:", 
                font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(pady=(10, 5))

        self.observacoes = tk.Text(self.janela, height=4, width=40, font=('MS Sans Serif', 9))
        self.observacoes.pack()

        # BOTÃO FECHAR CAIXA - VERDE COM BORDA
        btn_container = tk.Frame(self.janela, bg="#006400", padx=4, pady=4)
        btn_container.pack(pady=20)

        btn_fechar_caixa = tk.Button(
            btn_container, 
            text="CONFIRMA FECHAR O CAIXA", 
            command=self.fechar_caixa,
            bg="#00FF00",
            fg="black",
            font=('MS Sans Serif', 12, 'bold'), 
            width=30,
            height=2,
            relief='raised',
            bd=3,
            cursor="hand2"
        )
        btn_fechar_caixa.pack()

        # Botão cancelar (menor e discreto)
        Win95Style.create_button(self.janela, "CANCELAR", self.janela.destroy,
                                font=('MS Sans Serif', 9), width=15).pack(pady=5)

    def fechar_caixa(self):
        try:
            valor = float(self.valor_fechamento.get().replace(',', '.'))
        except:
            valor = 0

        obs = self.observacoes.get("1.0", tk.END).strip()

        if messagebox.askyesno("⚠️ CONFIRMAR FECHAMENTO", 
                              "🔴 ATENÇÃO! 🔴\n\n" +
                              "Você está prestes a FECHAR O CAIXA e ZERAR todo o movimento do dia!\n\n" +
                              f"Valor de Fechamento: R$ {valor:.2f}\n\n" +
                              "✓ As vendas serão arquivadas no histórico\n" +
                              "✓ O relatório de vendas será zerado para amanhã\n" +
                              "✓ Esta ação não pode ser desfeita\n\n" +
                              "Deseja realmente continuar?"):

            # Pega os totais antes de fechar
            caixa = self.db.get_caixa_aberto()
            if caixa:
                resumo = self.db.get_resumo_caixa(caixa[0])
                totais = {
                    'dinheiro': resumo[0] if resumo else 0,
                    'credito': resumo[1] if resumo else 0,
                    'debito': resumo[2] if resumo else 0,
                    'pix': resumo[3] if resumo else 0,
                    'fiado': resumo[4] if resumo else 0,
                    'parcelado': resumo[5] if resumo else 0
                }
                # Registra no log administrativo
                logger = LoggerAdministrativo()
                logger.registrar_fechamento_caixa(self.user[3], valor, totais)

            caixa_id = self.db.fechar_caixa(valor, obs)
            if caixa_id:
                messagebox.showinfo("✅ Caixa Fechado", 
                                   "Caixa fechado com sucesso!\n\n" +
                                   "📊 O movimento do dia foi zerado.\n" +
                                   "📁 As vendas foram arquivadas no histórico.\n" +
                                   "🔄 O sistema será reiniciado para o próximo dia.")
                self.janela.destroy()
                # Reinicia o sistema
                import sys
                import os
                python = sys.executable
                os.execl(python, python, *sys.argv)
            else:
                messagebox.showerror("Erro", "Não foi possível fechar o caixa!")

class PDVSystem:
    def __init__(self, root, db, user):
        self.root = root
        self.db = db
        self.user = user
        self.carrinho = []
        self.total = 0.0

        # Inicializa logger administrativo
        self.logger_admin = LoggerAdministrativo()

        self.root.title(f"PDV - {user[3]} ({user[4]})")
        self.root.geometry("1300x800")
        self.root.configure(bg=Win95Style.BG_GRAY)
        self.root.state('zoomed')

        self.config = self.db.get_config()
        self.backup_manager = BackupManager(db)
        self.qr_generator = QRCodeGenerator()

        self.create_menu_bar()
        self.create_interface()
        self.atualizar_painel_caixa()
        self.codigo_entry.focus_set()

        # Atalhos globais
        self.root.bind('<F1>', lambda e: self.abrir_ajuda())
        self.root.bind('<F2>', lambda e: self.finalizar_venda())
        self.root.bind('<F3>', lambda e: self.editar_item_carrinho())
        self.root.bind('<Delete>', lambda e: self.cancelar_item())
        self.root.bind('<F4>', lambda e: self.cancelar_venda())
        self.root.bind('<F5>', lambda e: self.pesquisar())
        self.root.bind('<F6>', lambda e: self.abrir_cadastro_produtos())
        self.root.bind('<F7>', lambda e: self.abrir_consulta_estoque())
        self.root.bind('<F8>', lambda e: self.abrir_relatorio_vendas())
        self.root.bind('<F9>', lambda e: self.gerar_codigo_avulso())
        self.root.bind('<F10>', lambda e: self.abrir_backup())
        self.root.bind('<F11>', lambda e: self.abrir_etiquetas())
        self.root.bind('<F12>', lambda e: self.gerar_qr_pix_rapido())
        self.root.bind('<Control-f>', lambda e: self.abrir_fechamento_caixa())
        self.root.bind('<Escape>', lambda e: self.sair())

    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        oper = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Operacoes", menu=oper)
        oper.add_command(label="Finalizar Venda (F2)", command=self.finalizar_venda)
        oper.add_command(label="Editar Item (F3)", command=self.editar_item_carrinho)
        oper.add_command(label="Cancelar Item (Del)", command=self.cancelar_item)
        oper.add_command(label="Cancelar Venda (F4)", command=self.cancelar_venda)
        oper.add_separator()
        oper.add_command(label="Pesquisar (F5)", command=self.pesquisar)
        oper.add_command(label="Gerar Codigo Avulso (F9)", command=self.gerar_codigo_avulso)
        oper.add_separator()
        oper.add_command(label="Fechar Caixa (Ctrl+F)", command=self.abrir_fechamento_caixa)
        oper.add_separator()
        oper.add_command(label="Sair (ESC)", command=self.sair)

        cad = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Cadastros", menu=cad)
        cad.add_command(label="Produtos / Estoque (F6)", command=self.abrir_cadastro_produtos)
        cad.add_command(label="Usuarios", command=self.abrir_cadastro_usuarios)
        cad.add_command(label="Clientes", command=self.abrir_cadastro_clientes)
        cad.add_command(label="Fiados / Parcelados", command=self.abrir_cadastro_fiados)
        cad.add_command(label="Etiquetas (F11)", command=self.abrir_etiquetas)

        rel = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Relatorios", menu=rel)
        rel.add_command(label="Vendas (F8)", command=self.abrir_relatorio_vendas)
        rel.add_command(label="Consulta Estoque (F7)", command=self.abrir_consulta_estoque)
        rel.add_separator()
        rel.add_command(label="Consulta por CPF", command=self.abrir_consulta_cpf)
        rel.add_separator()
        rel.add_command(label="Reimprimir Cupom", command=self.reimprimir_cupom)

        ferr = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=ferr)
        ferr.add_command(label="Imprimir Resumo Diario", command=self.imprimir_resumo_diario)
        ferr.add_separator()
        ferr.add_command(label="Backup e Restauracao (F10)", command=self.abrir_backup)
        ferr.add_command(label="Gerar QR Code PIX (F12)", command=self.gerar_qr_pix_rapido)
        ferr.add_separator()
        ferr.add_command(label="Ajuda (F1)", command=self.abrir_ajuda)

        conf = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuracoes", menu=conf)
        conf.add_command(label="Dados da Empresa", command=self.abrir_configuracoes)
        conf.add_separator()
        conf.add_command(label="Log Administrativo (Oculto)", command=self.abrir_log_administrativo)

    def create_interface(self):
        # Header
        header = tk.Frame(self.root, bg=Win95Style.NAVY, height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=self.config[1], font=('MS Sans Serif', 16, 'bold'), 
                bg=Win95Style.NAVY, fg="white").pack(side='left', padx=15, pady=10)

        tk.Label(header, text=f"Operador: {self.user[3]} | {get_brasil_now().strftime('%d/%m/%Y %H:%M')}", 
                font=('MS Sans Serif', 10), bg=Win95Style.NAVY, fg="white").pack(side='right', padx=15, pady=15)

        # Container principal
        main_container = tk.Frame(self.root, bg=Win95Style.BG_GRAY)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # MENU LATERAL ESQUERDO - ESTILO WIN95
        menu_lateral = tk.Frame(main_container, bg=Win95Style.BG_GRAY, width=200)
        menu_lateral.pack(side='left', fill='y', padx=(0, 5))
        menu_lateral.pack_propagate(False)

        tk.Label(menu_lateral, text="MENU RAPIDO", font=('MS Sans Serif', 11, 'bold'), 
                bg=Win95Style.BG_GRAY, fg=Win95Style.BLACK).pack(pady=10)

        # Separador 3D
        tk.Frame(menu_lateral, bg=Win95Style.WHITE, height=2).pack(fill='x', padx=5)
        tk.Frame(menu_lateral, bg=Win95Style.DARK_GRAY, height=1).pack(fill='x', padx=5)

        # Botoes do menu
        botoes_menu = [
            ("💰 Finalizar (F2)", Win95Style.SUCCESS, self.finalizar_venda),
            ("✏️ Editar Item (F3)", "#FF9800", self.editar_item_carrinho),
            ("❌ Canc.Item (Del)", Win95Style.WARNING, self.cancelar_item),
            ("🗑️ Canc.Venda (F4)", Win95Style.DANGER, self.cancelar_venda),
            ("🔍 Pesquisar (F5)", Win95Style.INFO, self.pesquisar),
            ("📦 Produtos (F6)", "#009688", self.abrir_cadastro_produtos),
            ("📊 Estoque (F7)", "#795548", self.abrir_consulta_estoque),
            ("📈 Vendas (F8)", "#607D8B", self.abrir_relatorio_vendas),
            ("🔢 Gerar Codigo (F9)", "#9C27B0", self.gerar_codigo_avulso),
            ("💾 Backup (F10)", "#FF5722", self.abrir_backup),
            ("🏷️ Etiquetas (F11)", "#3F51B5", self.abrir_etiquetas),
            ("📱 QR PIX (F12)", "#E91E63", self.gerar_qr_pix_rapido),
        ]

        for texto, cor, comando in botoes_menu:
            btn = Win95Style.create_button(menu_lateral, texto, comando,
                                          bg_color=cor, fg_color="white", 
                                          font=('MS Sans Serif', 9, 'bold'),
                                          anchor='w', padx=10)
            btn.pack(fill='x', pady=2, padx=5)

        tk.Frame(menu_lateral, bg=Win95Style.BG_GRAY, height=10).pack()

        # Botao fechar caixa destacado
        tk.Frame(menu_lateral, bg=Win95Style.WHITE, height=2).pack(fill='x', padx=5)
        tk.Frame(menu_lateral, bg=Win95Style.DARK_GRAY, height=1).pack(fill='x', padx=5)

        Win95Style.create_button(menu_lateral, "🔒 FECHAR CAIXA (Ctrl+F)", self.abrir_fechamento_caixa,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), 
                                anchor='w', padx=10).pack(fill='x', pady=5, padx=5)

        tk.Frame(menu_lateral, bg=Win95Style.BG_GRAY, height=20).pack(fill='x')

        # Botao sair
        Win95Style.create_button(menu_lateral, "🚪 Sair (ESC)", self.sair,
                                bg_color=Win95Style.DARK_GRAY, fg_color="white", 
                                font=('MS Sans Serif', 10, 'bold'),
                                anchor='w', padx=10).pack(fill='x', pady=2, padx=5, side='bottom')

        # AREA CENTRAL
        center_area = tk.Frame(main_container, bg=Win95Style.BG_GRAY)
        center_area.pack(side='left', fill='both', expand=True)

        # Input frame
        input_frame = tk.Frame(center_area, bg=Win95Style.BG_GRAY, bd=2, relief='ridge')
        input_frame.pack(fill='x', pady=(0, 5), padx=5)

        # Codigo de barras
        tk.Label(input_frame, text="CODIGO:", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.BG_GRAY).pack(side='left', padx=5)

        self.codigo_var = tk.StringVar()
        self.codigo_entry = tk.Entry(input_frame, textvariable=self.codigo_var,
                                    font=('MS Sans Serif', 14), width=20, bd=2)
        self.codigo_entry.pack(side='left', padx=5, pady=5)
        self.codigo_entry.bind('<Return>', lambda e: self.adicionar())

        # Quantidade
        tk.Label(input_frame, text="QTD:", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.BG_GRAY, fg=Win95Style.DANGER).pack(side='left', padx=(20, 5))

        self.qtd_var = tk.StringVar(value="1")
        self.qtd_entry = tk.Entry(input_frame, textvariable=self.qtd_var,
                                 font=('MS Sans Serif', 14), width=8, bd=2, fg=Win95Style.DANGER)
        self.qtd_entry.pack(side='left', padx=5, pady=5)
        self.qtd_entry.bind('<Return>', lambda e: self.adicionar())

        Win95Style.create_button(input_frame, "🔢 GERAR CODIGO", self.gerar_codigo_avulso,
                                bg_color="#9C27B0", fg_color="white", 
                                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=10)

        Win95Style.create_button(input_frame, "➕ ADD", self.adicionar,
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 10, 'bold'), width=8).pack(side='left', padx=5)

        # Treeview de itens
        tree_frame = tk.Frame(center_area, bg=Win95Style.BG_GRAY, bd=2, relief='ridge')
        tree_frame.pack(fill='both', expand=True, pady=5, padx=5)

        columns = ('item', 'produto', 'qtd', 'preco', 'total', 'acoes')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        self.tree.heading('item', text='#')
        self.tree.heading('produto', text='PRODUTO')
        self.tree.heading('qtd', text='QTD')
        self.tree.heading('preco', text='UNIT')
        self.tree.heading('total', text='TOTAL')
        self.tree.heading('acoes', text='')

        self.tree.column('item', width=40, anchor='center')
        self.tree.column('produto', width=300)
        self.tree.column('qtd', width=80, anchor='center')
        self.tree.column('preco', width=90, anchor='e')
        self.tree.column('total', width=90, anchor='e')
        self.tree.column('acoes', width=60, anchor='center')

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.editar_item_carrinho)

        # PAINEL DIREITO - CAIXA E TOTAIS
        right_panel = tk.Frame(center_area, bg=Win95Style.BG_GRAY, width=320)
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        right_panel.pack_propagate(False)

        # PAINEL DE CAIXA - NOVO
        caixa_frame = tk.LabelFrame(right_panel, text=" PAINEL DE CAIXA ", 
                                   font=('MS Sans Serif', 10, 'bold'),
                                   bg=Win95Style.BG_GRAY)
        caixa_frame.pack(fill='x', pady=(0, 10))

        # Labels para cada forma de pagamento
        self.caixa_labels = {}
        formas_caixa = [
            ('dinheiro', '💵 Dinheiro', Win95Style.SUCCESS),
            ('credito', '💳 Cartao Credito', Win95Style.INFO),
            ('debito', '💳 Cartao Debito', Win95Style.WARNING),
            ('pix', '📱 PIX', "#9C27B0"),
            ('fiado', '📝 Fiado', "#E91E63"),
            ('parcelado', '💳 Parcelado', "#FF5722")
        ]

        for forma, texto, cor in formas_caixa:
            frame = tk.Frame(caixa_frame, bg=cor, padx=5, pady=3)
            frame.pack(fill='x', pady=1)
            tk.Label(frame, text=texto, font=('MS Sans Serif', 9, 'bold'), 
                    bg=cor, fg="white", width=18, anchor='w').pack(side='left')
            self.caixa_labels[forma] = tk.Label(frame, text="R$ 0,00", 
                                               font=('MS Sans Serif', 10, 'bold'), 
                                               bg=cor, fg="white", width=10, anchor='e')
            self.caixa_labels[forma].pack(side='right')

        # Total do caixa
        tk.Frame(caixa_frame, bg=Win95Style.WHITE, height=2).pack(fill='x', pady=5)
        tk.Frame(caixa_frame, bg=Win95Style.DARK_GRAY, height=1).pack(fill='x')

        total_caixa_frame = tk.Frame(caixa_frame, bg=Win95Style.NAVY, padx=5, pady=5)
        total_caixa_frame.pack(fill='x', pady=5)
        tk.Label(total_caixa_frame, text="TOTAL CAIXA:", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.NAVY, fg="white").pack(side='left')
        self.total_caixa_label = tk.Label(total_caixa_frame, text="R$ 0,00", 
                                         font=('MS Sans Serif', 12, 'bold'), 
                                         bg=Win95Style.NAVY, fg="white")
        self.total_caixa_label.pack(side='right')

        # Total da venda atual
        total_box = tk.Frame(right_panel, bg=Win95Style.DANGER)
        total_box.pack(fill='x', pady=(0, 10))

        tk.Label(total_box, text="TOTAL A PAGAR", font=('MS Sans Serif', 11, 'bold'), 
                bg=Win95Style.DANGER, fg="white").pack(pady=(10, 0))

        self.total_label = tk.Label(total_box, text="R$ 0,00", 
                                   font=('MS Sans Serif', 24, 'bold'), 
                                   bg=Win95Style.DANGER, fg="white")
        self.total_label.pack(pady=(0, 10))

        # Resumo
        resumo = tk.LabelFrame(right_panel, text=" RESUMO ", 
                              font=('MS Sans Serif', 9, 'bold'),
                              bg=Win95Style.BG_GRAY)
        resumo.pack(fill='x', pady=10)

        self.itens_label = tk.Label(resumo, text="Itens: 0", font=('MS Sans Serif', 10),
                                   bg=Win95Style.BG_GRAY)
        self.itens_label.pack(anchor='w', padx=5, pady=2)

        self.subtotal_label = tk.Label(resumo, text="Subtotal: R$ 0,00", font=('MS Sans Serif', 10),
                                      bg=Win95Style.BG_GRAY)
        self.subtotal_label.pack(anchor='w', padx=5, pady=2)

        # Atalhos visiveis
        atalhos = tk.LabelFrame(right_panel, text=" ATALHOS ", 
                               font=('MS Sans Serif', 9, 'bold'),
                               bg=Win95Style.BG_GRAY)
        atalhos.pack(fill='x', pady=10)

        atalhos_text = """F1-Ajuda  F2-Finalizar  F3-Canc.Item
F4-Canc.Venda  F5-Pesquisar
F6-Produtos  F7-Estoque
F8-Vendas  F9-Gerar Codigo
F10-Backup  F11-Etiquetas
F12-QR PIX  Ctrl+F-Fecha Caixa
ESC-Sair"""

        tk.Label(atalhos, text=atalhos_text, font=('Courier', 9), 
                justify='left', anchor='w', bg=Win95Style.BG_GRAY).pack(padx=5, pady=5, fill='x')

        # Status bar
        status = tk.Frame(self.root, bg=Win95Style.DARK_GRAY, height=25)
        status.pack(fill='x', side='bottom')
        tk.Label(status, text="Sistema Offline | F1=Ajuda | F2=Finalizar | F3=Editar Item | F4=Canc.Venda | F5=Pesquisar | F10=Backup | Ctrl+F=Fechar Caixa | ESC=Sair", 
                font=('MS Sans Serif', 8), bg=Win95Style.DARK_GRAY, fg="white").pack(side='left', padx=10)

    def atualizar_painel_caixa(self):
        """Atualiza o painel de caixa com os valores do banco"""
        caixa = self.db.get_caixa_aberto()
        if caixa:
            resumo = self.db.get_resumo_caixa(caixa[0])
            if resumo:
                valores = {
                    'dinheiro': resumo[0],
                    'credito': resumo[1],
                    'debito': resumo[2],
                    'pix': resumo[3],
                    'fiado': resumo[4],
                    'parcelado': resumo[5]
                }

                total = 0
                for forma, valor in valores.items():
                    if forma in self.caixa_labels:
                        self.caixa_labels[forma].config(text=f"R$ {valor:.2f}")
                        total += valor

                self.total_caixa_label.config(text=f"R$ {total:.2f}")

        # Agenda proxima atualizacao em 5 segundos
        self.root.after(5000, self.atualizar_painel_caixa)

    def abrir_fechamento_caixa(self):
        """Abre tela de fechamento de caixa"""
        if self.user[4] != 'Gerente':
            messagebox.showerror("Acesso Negado", "Apenas gerentes podem fechar o caixa!")
            return

        TelaFechamentoCaixa(self.root, self.db, self.user, self.on_caixa_fechado)

    def on_caixa_fechado(self):
        """Callback quando o caixa e fechado - volta para tela de login"""
        # Limpa o carrinho
        self.carrinho = []

        messagebox.showinfo("Caixa Fechado", "Caixa fechado com sucesso!\n\n" +
                           "O sistema será reiniciado para abertura do próximo dia.")

        # Destrói todos os widgets da janela principal
        for widget in self.root.winfo_children():
            widget.destroy()

        # Volta para tela de login
        self.show_login()

    def show_login(self):
        """Mostra tela de login novamente"""
        LoginScreen(self.root, self.db, self.on_login)

    def gerar_codigo_avulso(self):
        codigo = self.db.gerar_codigo_barras_avulso()
        self.codigo_var.set(codigo)
        self.qtd_entry.focus_set()
        messagebox.showinfo("Codigo Gerado", f"Codigo de barras EAN-13 gerado:\n{codigo}")


    def gerar_qr_pix_rapido(self):
        """Gera QR Code PIX rapidamente"""
        if not PIL_DISPONIVEL:
            messagebox.showwarning("Aviso", "Biblioteca Pillow não instalada!\nInstale com: pip install pillow")
            return
        config = self.db.get_config()
        chave = config[6] if len(config) > 6 else ""

        if not chave:
            messagebox.showwarning("Aviso", "Cadastre a chave PIX nas Configuracoes!")
            self.abrir_configuracoes()
            return

        valor_str = simpledialog.askstring("QR Code PIX", "Digite o valor (R$):", initialvalue="10.00")
        if not valor_str:
            return

        try:
            valor = float(valor_str.replace(',', '.'))
        except:
            valor = 0

        img, payload = self.qr_generator.gerar_pix_qrcode(chave, valor, "Pagamento PDV")

        janela = tk.Toplevel(self.root)
        janela.title("QR Code PIX")
        janela.geometry("400x500")
        janela.configure(bg="white")
        janela.resizable(False, False)

        tk.Label(janela, text="📱 ESCANEIE COM SEU BANCO", 
                font=('MS Sans Serif', 14, 'bold'), bg="#9C27B0", fg="white").pack(fill='x', ipady=10)

        tk.Label(janela, text=f"Valor: R$ {valor:.2f}", 
                font=('MS Sans Serif', 16, 'bold'), bg="white", fg=Win95Style.BLACK).pack(pady=10)

        img_tk = ImageTk.PhotoImage(img.resize((300, 300)))
        lbl = tk.Label(janela, image=img_tk, bg="white")
        lbl.image = img_tk
        lbl.pack(pady=10)

        tk.Label(janela, text=f"Chave: {chave}", 
                font=('MS Sans Serif', 9), bg="white", fg=Win95Style.DARK_GRAY, wraplength=350).pack()

        Win95Style.create_button(janela, "💾 Salvar Imagem", 
                                lambda: self.salvar_qr_pix(img),
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 10, 'bold'), width=20).pack(pady=10)

        Win95Style.create_button(janela, "Fechar", janela.destroy,
                                font=('MS Sans Serif', 10), width=15).pack(pady=5)

    def salvar_qr_pix(self, img):
        arquivo = os.path.join(get_qrcode_path(), 
                              f"pix_{get_brasil_now().strftime('%Y%m%d_%H%M%S')}.png")
        img.save(arquivo)
        messagebox.showinfo("Sucesso", f"QR Code salvo!\n{arquivo}")

    def editar_item_carrinho(self, event=None):
        """Edita quantidade e valor unitário do item no carrinho"""
        item = self.tree.selection()
        if not item:
            # Se não selecionou, tenta pelo duplo clique
            if event:
                item = self.tree.identify_row(event.y)
                if item:
                    self.tree.selection_set(item)
                    item = self.tree.selection()
            if not item:
                return

        idx = self.tree.index(item[0])
        if idx < 0 or idx >= len(self.carrinho):
            return

        produto = self.carrinho[idx]

        edit_win = tk.Toplevel(self.root)
        edit_win.title("EDITAR ITEM")
        edit_win.geometry("350x350")
        edit_win.configure(bg=Win95Style.BG_GRAY)
        edit_win.transient(self.root)
        edit_win.grab_set()
        edit_win.resizable(False, False)

        tk.Label(edit_win, text=f"Produto: {produto['nome']}", 
                font=('MS Sans Serif', 11, 'bold'), bg=Win95Style.BG_GRAY, 
                wraplength=320, fg=Win95Style.NAVY).pack(pady=10)

        # Quantidade
        tk.Label(edit_win, text="Quantidade:", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.BG_GRAY).pack(anchor='w', padx=30, pady=(10,0))

        qtd_var = tk.StringVar(value=str(produto['qtd']))
        qtd_entry = tk.Entry(edit_win, textvariable=qtd_var, font=('MS Sans Serif', 14), 
                            width=12, justify='center', bg="white")
        qtd_entry.pack(pady=5)
        qtd_entry.focus_set()
        qtd_entry.select_range(0, tk.END)

        # Valor Unitário
        tk.Label(edit_win, text="Valor Unitário (R$):", font=('MS Sans Serif', 10, 'bold'), 
                bg=Win95Style.BG_GRAY).pack(anchor='w', padx=30, pady=(15,0))

        val_var = tk.StringVar(value=f"{produto['preco']:.2f}")
        val_entry = tk.Entry(edit_win, textvariable=val_var, font=('MS Sans Serif', 14), 
                            width=12, justify='center', bg="#FFF9C4")
        val_entry.pack(pady=5)

        # Total calculado
        total_frame = tk.Frame(edit_win, bg=Win95Style.BG_GRAY)
        total_frame.pack(pady=10)

        tk.Label(total_frame, text="Total: R$", font=('MS Sans Serif', 12, 'bold'), 
                bg=Win95Style.BG_GRAY).pack(side='left')
        total_label = tk.Label(total_frame, text=f"{produto['preco'] * produto['qtd']:.2f}", 
                              font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.BG_GRAY, 
                              fg=Win95Style.DANGER)
        total_label.pack(side='left')

        def calcular_total(*args):
            try:
                q = float(qtd_var.get().replace(',', '.'))
                v = float(val_var.get().replace(',', '.'))
                total_label.config(text=f"{q * v:.2f}")
            except:
                pass

        qtd_var.trace('w', calcular_total)
        val_var.trace('w', calcular_total)

        def confirmar():
            try:
                nova_qtd = float(qtd_var.get().replace(',', '.'))
                novo_val = float(val_var.get().replace(',', '.'))

                if nova_qtd <= 0 or novo_val <= 0:
                    messagebox.showerror("Erro", "Valores devem ser maiores que zero!")
                    return

                # Verifica estoque se for aumentar quantidade
                if nova_qtd > produto['qtd']:
                    prod_db = self.db.get_produto_by_codigo(produto['codigo'])
                    if prod_db and prod_db[4] < nova_qtd:
                        messagebox.showerror("Erro", f"Estoque insuficiente! Disponível: {prod_db[4]}")
                        return

                self.carrinho[idx]['qtd'] = nova_qtd
                self.carrinho[idx]['preco'] = novo_val

                self.atualizar_tela()
                edit_win.destroy()
                self.codigo_entry.focus_set()

            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos!")

        def remover():
            self.carrinho.pop(idx)
            self.atualizar_tela()
            edit_win.destroy()
            self.codigo_entry.focus_set()

        btn_frame = tk.Frame(edit_win, bg=Win95Style.BG_GRAY)
        btn_frame.pack(pady=15)

        Win95Style.create_button(btn_frame, "💾 SALVAR (ENTER)", confirmar,
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 11, 'bold'), width=18).pack(side='left', padx=5)

        Win95Style.create_button(btn_frame, "🗑️ REMOVER", remover,
                                bg_color=Win95Style.DANGER, fg_color="white", 
                                font=('MS Sans Serif', 11, 'bold'), width=15).pack(side='left', padx=5)

        qtd_entry.bind('<Return>', lambda e: val_entry.focus_set())
        val_entry.bind('<Return>', lambda e: confirmar())
        edit_win.bind('<Escape>', lambda e: edit_win.destroy())

    def adicionar(self):
        codigo = self.codigo_var.get().strip()
        if not codigo:
            return

        if '*' in codigo:
            partes = codigo.split('*')
            if len(partes) == 2:
                try:
                    qtd = float(partes[0])
                    codigo = partes[1]
                    self.qtd_var.set(str(qtd))
                except:
                    pass

        try:
            qtd = float(self.qtd_var.get().replace(',', '.'))
        except:
            qtd = 1

        produto = self.db.get_produto_by_codigo(codigo)

        if produto:
            if produto[4] <= 0:
                messagebox.showwarning("Estoque", "Produto sem estoque!")
                return

            if produto[4] < qtd:
                messagebox.showwarning("Estoque", f"Estoque insuficiente!\nDisponivel: {produto[4]}")
                return

            for item in self.carrinho:
                if item['codigo'] == codigo:
                    item['qtd'] += qtd
                    break
            else:
                self.carrinho.append({
                    'id': produto[0],
                    'codigo': produto[1],
                    'nome': produto[2],
                    'preco': produto[3],
                    'qtd': qtd,
                    'tipo_peso': produto[6] if len(produto) > 6 else 0
                })

            self.atualizar_tela()
            self.codigo_var.set('')
            self.qtd_var.set('1')
            self.codigo_entry.focus_set()
        else:
            messagebox.showerror("Erro", f"Produto nao encontrado!\nCodigo: {codigo}")
            self.codigo_var.set('')

    def atualizar_tela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = 0.0
        for idx, item in enumerate(self.carrinho, 1):
            subtotal = item['preco'] * item['qtd']
            total += subtotal

            if item.get('tipo_peso') == 1:
                qtd_str = f"{item['qtd']:.3f}"
            else:
                qtd_str = f"{int(item['qtd'])}"

            self.tree.insert('', 'end', values=(
                idx,
                item['nome'][:30],
                qtd_str,
                f"R${item['preco']:.2f}",
                f"R${subtotal:.2f}",
                "✏️"
            ))

        self.total = total
        self.total_label.config(text=f"R$ {total:.2f}")
        self.subtotal_label.config(text=f"Subtotal: R$ {total:.2f}")
        self.itens_label.config(text=f"Itens: {len(self.carrinho)}")

        if self.tree.get_children():
            self.tree.see(self.tree.get_children()[-1])

    def cancelar_item(self):
        if not self.carrinho:
            return

        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            idx = int(item['values'][0]) - 1
            if 0 <= idx < len(self.carrinho):
                del self.carrinho[idx]
        else:
            self.carrinho.pop()

        self.atualizar_tela()

    def cancelar_venda(self):
        if not self.carrinho:
            return

        if messagebox.askyesno("Cancelar", "Cancelar toda a venda?"):
            self.carrinho = []
            self.atualizar_tela()

    def pesquisar(self):
        janela = tk.Toplevel(self.root)
        janela.title("Pesquisar Produto")
        janela.geometry("700x500")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.transient(self.root)
        janela.grab_set()
        janela.resizable(False, False)

        tk.Label(janela, text="PESQUISAR PRODUTO", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, 
                fg="white").pack(fill='x', ipady=10)

        busca_var = tk.StringVar()
        busca_entry = tk.Entry(janela, textvariable=busca_var, font=('MS Sans Serif', 12), width=40)
        busca_entry.pack(pady=10)
        busca_entry.focus_set()

        frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        frame.pack(fill='both', expand=True, padx=10, pady=5)

        cols = ('cod', 'nome', 'preco', 'estoque')
        lista = ttk.Treeview(frame, columns=cols, show='headings', height=15)
        lista.heading('cod', text='Codigo')
        lista.heading('nome', text='Nome')
        lista.heading('preco', text='Preco')
        lista.heading('estoque', text='Estoque')
        lista.column('cod', width=150)
        lista.column('nome', width=300)
        lista.column('preco', width=100, anchor='e')
        lista.column('estoque', width=80, anchor='center')

        scroll = ttk.Scrollbar(frame, orient="vertical", command=lista.yview)
        lista.configure(yscrollcommand=scroll.set)

        lista.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

        def carregar(filtro=""):
            for i in lista.get_children():
                lista.delete(i)
            for p in self.db.get_all_produtos():
                if filtro.lower() in p[2].lower() or filtro in p[1]:
                    lista.insert('', 'end', values=(p[1], p[2], f"R${p[3]:.2f}", p[4]))

        def selecionar(event=None):
            sel = lista.selection()
            if sel:
                cod = lista.item(sel[0])['values'][0]
                self.codigo_var.set(cod)
                janela.destroy()
                self.qtd_entry.focus_set()

        def selecionar_2x(event):
            sel = lista.selection()
            if sel:
                cod = lista.item(sel[0])['values'][0]
                self.codigo_var.set(cod)
                janela.destroy()
                self.adicionar()

        lista.bind('<Double-1>', selecionar_2x)
        lista.bind('<Return>', selecionar)
        busca_entry.bind('<Return>', lambda e: selecionar())
        busca_var.trace('w', lambda *args: carregar(busca_var.get()))

        tk.Label(janela, text="ENTER = Seleciona codigo | DUPLO CLIQUE = Adiciona direto", 
                font=('MS Sans Serif', 9), fg=Win95Style.DARK_GRAY, bg=Win95Style.BG_GRAY).pack(pady=5)

        Win95Style.create_button(janela, "Fechar (ESC)", janela.destroy, 
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(pady=10)

        janela.bind('<Escape>', lambda e: janela.destroy())

        carregar()


    def finalizar_venda(self):
        if not self.carrinho:
            messagebox.showwarning("Aviso", "Carrinho vazio!")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Finalizar Venda")
        janela.geometry("500x750")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.transient(self.root)
        janela.grab_set()
        janela.resizable(False, False)

        tk.Label(janela, text="FINALIZAR VENDA", 
                font=('MS Sans Serif', 16, 'bold'), bg=Win95Style.SUCCESS, 
                fg="white").pack(fill='x', ipady=15)

        tk.Label(janela, text=f"TOTAL: R$ {self.total:.2f}", 
                font=('MS Sans Serif', 24, 'bold'), fg=Win95Style.DANGER, bg=Win95Style.BG_GRAY).pack(pady=10)

        tk.Label(janela, text="Forma de Pagamento:", 
                font=('MS Sans Serif', 11), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=20, pady=(10, 5))

        pag_var = tk.StringVar(value="dinheiro")
        qr_window_open = [False]  # Flag para controlar se janela QR está aberta

        pag_frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        pag_frame.pack(fill='x', padx=20, pady=5)

        for val, texto, cor in [("dinheiro", "💵 Dinheiro", Win95Style.SUCCESS), 
                                ("credito", "💳 Cartao Credito", Win95Style.INFO),
                                ("debito", "💳 Cartao Debito", Win95Style.WARNING),
                                ("pix", "📱 PIX", "#9C27B0"),
                                ("fiado", "📝 Fiado", "#E91E63"),
                                ("parcelado", "💳 Parcelado (1-12x)", "#FF5722")]:
            tk.Radiobutton(pag_frame, text=texto, variable=pag_var, 
                          value=val, font=('MS Sans Serif', 11), bg=Win95Style.BG_GRAY,
                          selectcolor="white").pack(anchor='w', pady=2)

        # Frame para QR Code PIX (inicialmente oculto)
        qr_frame = tk.LabelFrame(janela, text=" QR CODE PIX ", 
                                font=('MS Sans Serif', 9, 'bold'),
                                bg=Win95Style.BG_GRAY)

        qr_label = tk.Label(qr_frame, bg="white")
        qr_label.pack(padx=10, pady=10)

        qr_payload_label = tk.Label(qr_frame, text="", font=('Courier', 8),
                                   bg=Win95Style.BG_GRAY, wraplength=350)
        qr_payload_label.pack(padx=5, pady=5)

        def gerar_qr_pix_venda():
            """Gera QR Code PIX com o valor da venda atual"""
            if not PIL_DISPONIVEL:
                messagebox.showwarning("Aviso", "Biblioteca Pillow nao instalada!\nInstale com: pip install pillow")
                return None
            config = self.db.get_config()
            chave = config[6] if len(config) > 6 else ""

            if not chave:
                messagebox.showwarning("Aviso", "Chave PIX nao configurada!\nConfigure em: Configuracoes > Dados da Empresa")
                return None

            try:
                desconto = float(desconto_var.get().replace(',', '.'))
            except:
                desconto = 0

            valor_final = self.total - desconto

            if valor_final <= 0:
                messagebox.showerror("Erro", "Valor invalido para pagamento!")
                return None

            # Gera QR Code
            img, payload = self.qr_generator.gerar_pix_qrcode(chave, valor_final, f"Venda PDV")

            # Atualiza imagem na tela
            img_tk = ImageTk.PhotoImage(img.resize((250, 250)))
            qr_label.config(image=img_tk)
            qr_label.image = img_tk

            # Mostra payload resumido
            qr_payload_label.config(text=f"Payload: {payload[:40]}...")

            return img, payload, valor_final

        def on_pagamento_change(*args):
            """Quando muda forma de pagamento"""
            if pag_var.get() == 'pix':
                # Mostra frame do QR Code
                qr_frame.pack(fill='x', padx=20, pady=10, before=btn_frame)
                # Gera QR Code automaticamente
                resultado = gerar_qr_pix_venda()
                if resultado:
                    img, payload, valor = resultado
                    # Abre janela grande com QR Code
                    abrir_janela_qr_pix(img, payload, valor, janela)
            else:
                qr_frame.pack_forget()

        def abrir_janela_qr_pix(img, payload, valor, parent_janela):
            """Abre janela dedicada para o QR Code PIX"""
            if not PIL_DISPONIVEL or img is None:
                messagebox.showwarning("Aviso", "QR Code nao pode ser gerado.\nInstale: pip install pillow qrcode")
                return
            nonlocal qr_window_open

            if qr_window_open[0]:
                return  # Ja esta aberta

            qr_janela = tk.Toplevel(parent_janela)
            qr_janela.title("PAGAMENTO PIX - Escaneie com seu banco")
            qr_janela.geometry("500x650")
            qr_janela.configure(bg="white")
            qr_janela.transient(parent_janela)
            qr_janela.resizable(False, False)
            qr_window_open[0] = True

            def on_close():
                qr_window_open[0] = False
                qr_janela.destroy()

            qr_janela.protocol("WM_DELETE_WINDOW", on_close)

            # Header
            tk.Label(qr_janela, text="📱 PAGAMENTO VIA PIX", 
                    font=('MS Sans Serif', 16, 'bold'), bg="#9C27B0", 
                    fg="white").pack(fill='x', ipady=15)

            # Valor
            tk.Label(qr_janela, text=f"VALOR: R$ {valor:.2f}", 
                    font=('MS Sans Serif', 20, 'bold'), bg="white", 
                    fg=Win95Style.DANGER).pack(pady=15)

            # Instrucoes
            tk.Label(qr_janela, text="1. Abra o app do seu banco\n2. Escaneie o QR Code abaixo\n3. Confirme o pagamento", 
                    font=('MS Sans Serif', 11), bg="white", justify='center').pack(pady=10)

            # QR Code em tamanho grande
            img_large = img.resize((350, 350), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img_large)

            lbl_qr = tk.Label(qr_janela, image=img_tk, bg="white", bd=2, relief='solid')
            lbl_qr.image = img_tk
            lbl_qr.pack(pady=15)

            # Chave PIX
            config = self.db.get_config()
            chave = config[6] if len(config) > 6 else ""
            tk.Label(qr_janela, text=f"Chave: {chave}", 
                    font=('MS Sans Serif', 9), bg="white", 
                    fg=Win95Style.DARK_GRAY).pack()

            # Botao confirmar pagamento
            tk.Frame(qr_janela, bg="white", height=20).pack()

            Win95Style.create_button(qr_janela, "✅ CONFIRMAR PAGAMENTO", 
                                    lambda: confirmar_pagamento_pix(qr_janela, valor),
                                    bg_color=Win95Style.SUCCESS, fg_color="white",
                                    font=('MS Sans Serif', 12, 'bold'), width=25, pady=10).pack(pady=10)

            Win95Style.create_button(qr_janela, "❌ Cancelar", on_close,
                                    bg_color=Win95Style.DANGER, fg_color="white",
                                    font=('MS Sans Serif', 10), width=15).pack(pady=5)

        def confirmar_pagamento_pix(qr_janela, valor):
            """Confirma pagamento PIX e finaliza venda"""
            qr_janela.destroy()
            qr_window_open[0] = False

            # Define forma de pagamento e finaliza
            pag_var.set('pix')

            # Confirma se deseja finalizar
            if messagebox.askyesno("Confirmar", f"Pagamento PIX de R$ {valor:.2f} confirmado?\n\nFinalizar venda e imprimir cupom?"):
                janela.destroy()
                processar_finalizacao('pix', valor, janela)

        def processar_finalizacao(forma, valor_final, janela_ref=None):
            """Processa a finalizacao da venda e imprime cupom"""

            try:
                desconto = float(desconto_var.get().replace(',', '.'))
            except:
                desconto = 0

            itens = [{'produto_id': i['id'], 'quantidade': i['qtd'], 
                     'preco': i['preco']} for i in self.carrinho]

            try:
                vid, cupom = self.db.save_venda({
                    'usuario_id': self.user[0],
                    'total': valor_final,
                    'forma_pagamento': forma,
                    'itens': itens
                })

                # Registra no log administrativo
                if hasattr(self, 'logger_admin'):
                    self.logger_admin.registrar_venda(
                        cupom, valor_final, forma, self.user[3], itens
                    )

                # Mostra cupom na tela
                self.mostrar_cupom(cupom, forma, desconto)

                # Imprime cupom automaticamente
                self.imprimir_cupom(cupom, forma, desconto)

                messagebox.showinfo("Sucesso", f"Venda finalizada!\nCupom: {cupom}\n\nPagamento: {forma.upper()}")

                # Limpa carrinho
                self.carrinho = []
                self.atualizar_tela()
                self.atualizar_painel_caixa()

                return vid, cupom

            except Exception as e:
                messagebox.showerror("Erro", str(e))
                return None, None

        pag_var.trace('w', on_pagamento_change)

        # Frame de parcelas (inicialmente oculto)
        parcelas_frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)

        tk.Label(parcelas_frame, text="Nº Parcelas:", 
                font=('MS Sans Serif', 11, 'bold'), bg=Win95Style.BG_GRAY).pack(side='left')
        parcelas_var = tk.StringVar(value="1")
        parcelas_combo = ttk.Combobox(parcelas_frame, textvariable=parcelas_var, 
                                     values=[str(i) for i in range(1, 13)], width=5, font=('MS Sans Serif', 11))
        parcelas_combo.pack(side='left', padx=5)
        tk.Label(parcelas_frame, text="x (máx 12)", font=('MS Sans Serif', 9), 
                bg=Win95Style.BG_GRAY, fg=Win95Style.DARK_GRAY).pack(side='left')

        # Desconto
        desc_frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        desc_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(desc_frame, text="Desconto R$:", font=('MS Sans Serif', 10), 
                bg=Win95Style.BG_GRAY).pack(side='left')
        desconto_var = tk.StringVar(value="0")
        tk.Entry(desc_frame, textvariable=desconto_var, font=('MS Sans Serif', 11), width=10).pack(side='left', padx=5)

        # Função para mostrar/esconder parcelas
        def mostrar_parcelas(*args):
            if pag_var.get() == 'parcelado':
                parcelas_frame.pack(fill='x', padx=20, pady=5, before=desc_frame)
            else:
                parcelas_frame.pack_forget()

        pag_var.trace('w', mostrar_parcelas)

        # Frame de botoes
        btn_frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        btn_frame.pack(fill='x', padx=20, pady=20)

        def confirmar_venda():
            """Confirma venda para formas de pagamento nao PIX"""
            forma = pag_var.get()

            try:
                desconto = float(desconto_var.get().replace(',', '.'))
            except:
                desconto = 0

            valor_final = self.total - desconto

            # Para fiado ou parcelado, informar dados do cliente na hora
            cliente_id = None
            cpf_cliente = ""
            if forma in ['fiado', 'parcelado']:
                # Solicita CPF do cliente
                cpf_cliente = simpledialog.askstring("Dados do Cliente", 
                                                      "Informe o CPF do cliente:")
                if not cpf_cliente:
                    messagebox.showerror("Erro", "CPF é obrigatório para Fiado/Parcelado!")
                    return

                # Busca ou cadastra cliente
                cliente = self.db.buscar_cliente_por_cpf(cpf_cliente)
                if not cliente:
                    # Cadastra cliente novo
                    nome_cliente = simpledialog.askstring("Cadastro de Cliente", 
                                                         f"Cliente não encontrado.\nInforme o nome para CPF {cpf_cliente}:")
                    if nome_cliente:
                        cliente_id = self.db.cadastrar_cliente(nome_cliente, cpf_cliente)
                        if cliente_id:
                            cliente = (cliente_id, nome_cliente, cpf_cliente, '', '', '', 0)
                        else:
                            messagebox.showerror("Erro", "Não foi possível cadastrar cliente!")
                            return
                    else:
                        return
                else:
                    cliente_id = cliente[0]

                # Para parcelado, pega número de parcelas
                num_parcelas = 1
                if forma == 'parcelado':
                    try:
                        num_parcelas = int(parcelas_var.get())
                        if num_parcelas < 1 or num_parcelas > 12:
                            messagebox.showerror("Erro", "Número de parcelas deve ser entre 1 e 12!")
                            return
                    except:
                        messagebox.showerror("Erro", "Número de parcelas inválido!")
                        return

                # Registra no fiados
                self.db.add_fiado(
                    cliente_id,
                    cliente[1],  # nome
                    cliente[3] if len(cliente) > 3 else '',  # telefone
                    valor_final,
                    forma.capitalize(),
                    f"Venda PDV",
                    num_parcelas,
                    (get_brasil_now() + datetime.timedelta(days=30)).strftime('%d/%m/%Y'),
                    cpf_cliente
                )

            if forma == "dinheiro":
                try:
                    r = float(recebido_var.get().replace(',', '.'))
                    if r < valor_final:
                        messagebox.showerror("Erro", "Valor insuficiente!")
                        return
                except:
                    messagebox.showerror("Erro", "Digite o valor recebido!")
                    return

            if forma == 'pix':
                # Se for PIX, deve usar o fluxo do QR Code
                messagebox.showinfo("PIX", "Selecione PIX na forma de pagamento para gerar o QR Code automaticamente.")
                return

            # Processa a venda
            vid, cupom = processar_finalizacao(forma, valor_final)

            # Fecha a janela de finalização após processar a venda
            try:
                janela.destroy()
            except:
                pass

            # Registra no histórico do cliente se for fiado/parcelado
            if cliente_id and vid:
                num_parcelas = int(parcelas_var.get()) if forma == 'parcelado' else 1
                self.db.registrar_historico_compra(
                    cliente_id, cpf_cliente, cupom, valor_final, forma, num_parcelas
                )
                self.db.atualizar_total_gasto_cliente(cliente_id, valor_final)

            # FECHA A JANELA SEMPRE NO FINAL
            try:
                if janela_ref and hasattr(janela_ref, 'destroy'):
                    janela_ref.destroy()
            except:
                pass

        # Frame para valor recebido e troco (apenas dinheiro)
        troco_frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        troco_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(troco_frame, text="Valor Recebido R$:", font=('MS Sans Serif', 11, 'bold'), 
                bg=Win95Style.BG_GRAY).pack(side='left')
        recebido_var = tk.StringVar()
        recebido_entry = tk.Entry(troco_frame, textvariable=recebido_var, 
                                 font=('MS Sans Serif', 14, 'bold'), width=12, fg=Win95Style.DANGER)
        recebido_entry.pack(side='left', padx=5)

        troco_label = tk.Label(troco_frame, text="Troco: R$ 0,00", 
                              font=('MS Sans Serif', 12, 'bold'), fg=Win95Style.SUCCESS, 
                              bg=Win95Style.BG_GRAY)
        troco_label.pack(side='left', padx=10)

        def calc_troco(*args):
            try:
                val = float(recebido_var.get().replace(',', '.'))
                try:
                    desc = float(desconto_var.get().replace(',', '.'))
                except:
                    desc = 0
                total_final = self.total - desc
                t = val - total_final
                if t >= 0:
                    troco_label.config(text=f"Troco: R$ {t:.2f}", fg=Win95Style.SUCCESS)
                else:
                    troco_label.config(text=f"Falta: R$ {abs(t):.2f}", fg=Win95Style.DANGER)
            except:
                troco_label.config(text="Troco: R$ 0,00")

        recebido_var.trace('w', calc_troco)

        Win95Style.create_button(btn_frame, "CONFIRMAR (ENTER)", confirmar_venda,
                                bg_color=Win95Style.SUCCESS, fg_color="white", 
                                font=('MS Sans Serif', 12, 'bold'), width=18, pady=10).pack(side='left')

        Win95Style.create_button(btn_frame, "CANCELAR", janela.destroy,
                                bg_color=Win95Style.DANGER, fg_color="white", 
                                font=('MS Sans Serif', 12, 'bold'), width=15, pady=10).pack(side='right')

        recebido_entry.bind('<Return>', lambda e: confirmar_venda())

    def mostrar_cupom(self, numero, forma, desconto=0):
        cupom = tk.Toplevel(self.root)
        cupom.title(f"Cupom {numero}")
        cupom.geometry("380x550")
        cupom.configure(bg="white")
        cupom.resizable(False, False)

        frame = tk.Frame(cupom, bg="white", bd=2, relief='solid')
        frame.pack(padx=10, pady=10, fill='both', expand=True)

        tk.Label(frame, text=self.config[1], font=('Courier', 12, 'bold'), 
                bg="white").pack(pady=(10, 0))
        tk.Label(frame, text=f"CNPJ: {self.config[2]}", font=('Courier', 8), 
                bg="white").pack()
        tk.Label(frame, text=self.config[3], font=('Courier', 8), 
                bg="white").pack()
        tk.Label(frame, text="="*35, font=('Courier', 8), bg="white").pack()

        tk.Label(frame, text="CUPOM FISCAL", font=('Courier', 10, 'bold'), 
                bg="white").pack()
        tk.Label(frame, text=f"N: {numero}", font=('Courier', 8), 
                bg="white").pack()
        tk.Label(frame, text=f"{get_brasil_now().strftime('%d/%m/%Y %H:%M:%S')}", 
                font=('Courier', 8), bg="white").pack()
        tk.Label(frame, text="="*35, font=('Courier', 8), bg="white").pack()

        for idx, item in enumerate(self.carrinho, 1):
            if item.get('tipo_peso') == 1:
                qtd_str = f"{item['qtd']:.3f}"
            else:
                qtd_str = f"{int(item['qtd'])}"
            txt = f"{idx} {item['nome'][:20]:<20} {qtd_str}x {item['preco']*item['qtd']:.2f}"
            tk.Label(frame, text=txt, font=('Courier', 8), bg="white").pack()

        tk.Label(frame, text="-"*35, font=('Courier', 8), bg="white").pack()

        if desconto > 0:
            tk.Label(frame, text=f"DESCONTO: R$ {desconto:.2f}", 
                    font=('Courier', 9), bg="white", fg="red").pack()

        tk.Label(frame, text=f"TOTAL: R$ {self.total - desconto:.2f}", 
                font=('Courier', 10, 'bold'), bg="white", fg="red").pack()
        tk.Label(frame, text=f"Pagamento: {forma.upper()}", 
                font=('Courier', 8), bg="white").pack()
        tk.Label(frame, text="="*35, font=('Courier', 8), bg="white").pack()
        tk.Label(frame, text=self.config[5], font=('Courier', 8, 'bold'), 
                bg="white").pack(pady=10)

        Win95Style.create_button(cupom, "Fechar", cupom.destroy, width=15).pack(pady=5)

    def imprimir_cupom(self, numero, forma, desconto=0):
        try:
            linhas = []
            linhas.append(self.config[1])
            linhas.append(f"CNPJ: {self.config[2]}")
            linhas.append(self.config[3])
            linhas.append("=" * 35)
            linhas.append("CUPOM FISCAL")
            linhas.append(f"N: {numero}")
            linhas.append(get_brasil_now().strftime('%d/%m/%Y %H:%M:%S'))
            linhas.append("=" * 35)

            for idx, item in enumerate(self.carrinho, 1):
                if item.get('tipo_peso') == 1:
                    qtd_str = f"{item['qtd']:.3f}"
                else:
                    qtd_str = f"{int(item['qtd'])}"
                linhas.append(f"{idx} {item['nome'][:20]:<20} {qtd_str}x {item['preco']*item['qtd']:.2f}")

            linhas.append("-" * 35)

            if desconto > 0:
                linhas.append(f"DESCONTO: R$ {desconto:.2f}")

            linhas.append(f"TOTAL: R$ {self.total - desconto:.2f}")
            linhas.append(f"Pagamento: {forma.upper()}")
            linhas.append("=" * 35)
            linhas.append(self.config[5])
            linhas.append("")

            texto_cupom = "\n".join(linhas)

            temp_path = os.path.join(get_app_path(), "cupom_temp.txt")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(texto_cupom)

            os.system(f'notepad /p "{temp_path}"')

        except Exception as e:
            messagebox.showerror("Erro de Impressao", f"Nao foi possivel imprimir:\n{str(e)}")

    def abrir_cadastro_produtos(self):
        CadastroProdutos(self.root, self.db)

    def abrir_cadastro_usuarios(self):
        if self.user[4] != 'Gerente':
            messagebox.showerror("Acesso Negado", "Apenas gerentes podem acessar!")
            return
        CadastroUsuarios(self.root, self.db)

    def abrir_relatorio_vendas(self):
        RelatorioVendas(self.root, self.db)

    def abrir_consulta_estoque(self):
        ConsultaEstoque(self.root, self.db)

    def abrir_configuracoes(self):
        if self.user[4] != 'Gerente':
            messagebox.showerror("Acesso Negado", "Apenas gerentes podem acessar!")
            return
        ConfiguracoesSistema(self.root, self.db, self.backup_manager)

    def abrir_backup(self):
        if self.user[4] != 'Gerente':
            messagebox.showerror("Acesso Negado", "Apenas gerentes podem acessar!")
            return
        TelaBackup(self.root, self.db, self.backup_manager)

    def abrir_consulta_cpf(self):
        """Abre tela de consulta geral por CPF"""
        # Janela de entrada do CPF
        janela_cpf = tk.Toplevel(self.root)
        janela_cpf.title("Consulta por CPF")
        janela_cpf.geometry("400x200")
        janela_cpf.configure(bg=Win95Style.BG_GRAY)
        janela_cpf.resizable(False, False)
        janela_cpf.transient(self.root)
        janela_cpf.grab_set()

        tk.Label(janela_cpf, text="CONSULTA GERAL POR CPF", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(fill='x', ipady=10)

        tk.Label(janela_cpf, text="Digite o CPF:", 
                font=('MS Sans Serif', 11), bg=Win95Style.BG_GRAY).pack(pady=10)

        cpf_var = tk.StringVar()
        cpf_entry = tk.Entry(janela_cpf, textvariable=cpf_var, font=('MS Sans Serif', 14), 
                            width=18, justify='center')
        cpf_entry.pack(pady=5)
        cpf_entry.focus_set()

        def realizar_consulta():
            cpf = cpf_var.get().strip()
            if not cpf:
                messagebox.showerror("Erro", "Digite um CPF válido!")
                return

            # Buscar dados
            resultado = self.db.consulta_geral_por_cpf(cpf)
            janela_cpf.destroy()
            self.mostrar_resultado_consulta_cpf(cpf, resultado)

        Win95Style.create_button(janela_cpf, "🔍 CONSULTAR", realizar_consulta,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 11, 'bold'), width=15).pack(pady=15)

        janela_cpf.bind('<Return>', lambda e: realizar_consulta())

    def mostrar_resultado_consulta_cpf(self, cpf, resultado):
        """Mostra resultado da consulta por CPF"""
        janela = tk.Toplevel(self.root)
        janela.title(f"Resultado Consulta - CPF: {cpf}")
        janela.geometry("900x600")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.resizable(False, False)

        header = tk.Frame(janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text=f"CONSULTA GERAL - CPF: {cpf}", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Frame de informações do cliente
        if resultado['cliente']:
            c = resultado['cliente']
            info_frame = tk.LabelFrame(janela, text=" DADOS DO CLIENTE ", 
                                      font=('MS Sans Serif', 10, 'bold'),
                                      bg=Win95Style.BG_GRAY)
            info_frame.pack(fill='x', padx=10, pady=10)

            tk.Label(info_frame, text=f"Nome: {c[0]}", 
                    font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=10)
            tk.Label(info_frame, text=f"Telefone: {c[1] or 'N/A'}", 
                    font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=10)
            tk.Label(info_frame, text=f"Email: {c[2] or 'N/A'}", 
                    font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=10)
            tk.Label(info_frame, text=f"Endereço: {c[3] or 'N/A'}", 
                    font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=10)
            tk.Label(info_frame, text=f"Data Cadastro: {c[4]}", 
                    font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY).pack(anchor='w', padx=10)
            tk.Label(info_frame, text=f"Total Gasto: R$ {c[5]:.2f}", 
                    font=('MS Sans Serif', 11, 'bold'), bg=Win95Style.BG_GRAY, fg=Win95Style.DANGER).pack(anchor='w', padx=10, pady=5)
        else:
            tk.Label(janela, text="Cliente não cadastrado no sistema.", 
                    font=('MS Sans Serif', 11), bg=Win95Style.BG_GRAY, fg=Win95Style.DANGER).pack(pady=10)

        # Lista de transações
        trans_frame = tk.LabelFrame(janela, text=" HISTÓRICO DE TRANSAÇÕES ", 
                                   font=('MS Sans Serif', 10, 'bold'),
                                   bg=Win95Style.BG_GRAY)
        trans_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('tipo', 'data', 'descricao', 'valor', 'status')
        tree = ttk.Treeview(trans_frame, columns=cols, show='headings', height=15)

        tree.heading('tipo', text='TIPO')
        tree.heading('data', text='DATA')
        tree.heading('descricao', text='DESCRIÇÃO')
        tree.heading('valor', text='VALOR')
        tree.heading('status', text='STATUS')

        tree.column('tipo', width=100, anchor='center')
        tree.column('data', width=120, anchor='center')
        tree.column('descricao', width=300)
        tree.column('valor', width=100, anchor='e')
        tree.column('status', width=100, anchor='center')

        scroll = ttk.Scrollbar(trans_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y', pady=5)

        # Preencher dados
        if resultado['transacoes']:
            for t in resultado['transacoes']:
                if t['tipo'] == 'VENDA':
                    desc = f"Cupom: {t['cupom']} - {t['forma']}"
                    data_str = datetime.datetime.strptime(t['data'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                    valor_str = f"R$ {t['valor']:.2f}"
                    status_str = "CONCLUÍDA"
                else:  # FIADO ou PARCELADO
                    desc = f"{t['cliente']} - {t['parcelas']}"
                    data_str = t.get('vencimento', 'N/A')
                    valor_str = f"R$ {t['valor_total']:.2f} (Pago: R$ {t.get('valor_pago', 0):.2f})"
                    status_str = t['status']

                tree.insert('', 'end', values=(
                    t['tipo'],
                    data_str,
                    desc,
                    valor_str,
                    status_str
                ))
        else:
            tk.Label(trans_frame, text="Nenhuma transação encontrada.", 
                    font=('MS Sans Serif', 11), bg=Win95Style.BG_GRAY, fg=Win95Style.DARK_GRAY).pack(pady=20)

        Win95Style.create_button(janela, "❌ Fechar", janela.destroy,
                                width=15).pack(pady=10)

    def abrir_etiquetas(self):
        TelaEtiquetas(self.root, self.db)

    def imprimir_resumo_diario(self):
        """Imprime resumo compacto do dia na impressora térmica"""
        try:
            hoje = get_brasil_today().strftime('%Y-%m-%d')
            vendas = self.db.get_vendas_periodo(hoje, hoje, None)

            # Calcula totais por forma de pagamento
            totais = {'dinheiro': 0, 'credito': 0, 'debito': 0, 'pix': 0, 'total': 0}
            qtd_total = 0

            for v in vendas:
                forma = v[3].lower()
                valor = v[2]
                if forma in totais:
                    totais[forma] += valor
                totais['total'] += valor
                qtd_total += 1

            # Monta o resumo no formato compacto para impressora térmica
            linhas = []
            linhas.append(self.config[1])  # Nome da empresa
            linhas.append("RESUMO DO DIA")
            linhas.append("=" * 35)
            linhas.append(f"Data: {get_brasil_today().strftime('%d/%m/%Y')}")
            linhas.append(f"Hora: {get_brasil_now().strftime('%H:%M:%S')}")
            linhas.append(f"Operador: {self.user[3]}")
            linhas.append("-" * 35)
            linhas.append("FORMA DE PAGAMENTO:")
            linhas.append(f"Dinheiro:     R$ {totais['dinheiro']:>10.2f}")
            linhas.append(f"Credito:      R$ {totais['credito']:>10.2f}")
            linhas.append(f"Debito:       R$ {totais['debito']:>10.2f}")
            linhas.append(f"PIX:          R$ {totais['pix']:>10.2f}")
            linhas.append("-" * 35)
            linhas.append(f"Qtd Vendas:   {qtd_total:>10}")
            linhas.append(f"TOTAL DO DIA: R$ {totais['total']:>10.2f}")
            linhas.append("=" * 35)
            linhas.append("")
            linhas.append("Sistema PDV - Resumo Diario")
            linhas.append("")

            texto = "\n".join(linhas)

            # Salva em arquivo temporário e imprime
            with open("resumo_diario_temp.txt", "w", encoding="utf-8") as f:
                f.write(texto)

            os.system(f'notepad /p "resumo_diario_temp.txt"')
            messagebox.showinfo("Sucesso", "Resumo diário enviado para impressão!")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao imprimir resumo: {str(e)}")

    def abrir_cadastro_fiados(self):
        """Abre tela de cadastro de fiados"""
        if self.user[4] != 'Gerente':
            messagebox.showerror("Acesso Negado", "Apenas gerentes podem acessar!")
            return
        CadastroFiados(self.root, self.db)

    def consultar_cupom_por_cpf(self, cpf):
        """Consulta cupons de um cliente pelo CPF"""
        if not cpf:
            messagebox.showwarning("Aviso", "Digite o CPF!")
            return

        cpf = re.sub(r'[^0-9]', '', cpf)
        historico = self.db.get_historico_cliente(cpf)

        if not historico:
            messagebox.showinfo("Histórico", "Nenhuma compra encontrada para este CPF.")
            return

        # Mostra janela com histórico
        janela = tk.Toplevel(self.root)
        janela.title(f"Histórico de Compras - CPF: {cpf}")
        janela.geometry("700x500")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.resizable(False, False)

        header = tk.Frame(janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="HISTÓRICO DE COMPRAS", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        # Lista
        cols = ('cupom', 'data', 'valor', 'pagamento', 'parcelas')
        tree = ttk.Treeview(janela, columns=cols, show='headings', height=15)

        tree.heading('cupom', text='CUPOM')
        tree.heading('data', text='DATA/HORA')
        tree.heading('valor', text='VALOR')
        tree.heading('pagamento', text='PAGAMENTO')
        tree.heading('parcelas', text='PARCELAS')

        tree.column('cupom', width=120, anchor='center')
        tree.column('data', width=150, anchor='center')
        tree.column('valor', width=100, anchor='e')
        tree.column('pagamento', width=100, anchor='center')
        tree.column('parcelas', width=80, anchor='center')

        scroll = ttk.Scrollbar(janela, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scroll.pack(side='right', fill='y', pady=10)

        for h in historico:
            data = datetime.datetime.strptime(h[1], '%Y-%m-%d %H:%M:%S')
            tree.insert('', 'end', values=(
                h[0],
                data.strftime('%d/%m/%Y %H:%M'),
                f"R$ {h[2]:.2f}",
                h[3].upper(),
                h[4]
            ))

        Win95Style.create_button(janela, "Fechar", janela.destroy,
                                width=15).pack(pady=10)

    def reimprimir_cupom(self):
        """Reimprime um cupom já emitido pelo número"""
        janela = tk.Toplevel(self.root)
        janela.title("Reimprimir Cupom")
        janela.geometry("400x250")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        header = tk.Frame(janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="REIMPRIMIR CUPOM", font=('MS Sans Serif', 14, 'bold'), 
                bg=Win95Style.NAVY, fg="white").pack(pady=10)

        tk.Label(janela, text="Número do Cupom:", font=('MS Sans Serif', 11), 
                bg=Win95Style.BG_GRAY).pack(pady=15)

        cupom_var = tk.StringVar()
        cupom_entry = tk.Entry(janela, textvariable=cupom_var, font=('MS Sans Serif', 14), 
                              width=20, justify='center')
        cupom_entry.pack(pady=5)
        cupom_entry.focus_set()

        def buscar_e_imprimir():
            numero = cupom_var.get().strip()
            if not numero:
                messagebox.showerror("Erro", "Digite o número do cupom!")
                return

            # Buscar no banco de dados
            self.db.cursor.execute("SELECT * FROM vendas WHERE numero_cupom = ?", (numero,))
            venda = self.db.cursor.fetchone()

            if not venda:
                # Tentar no histórico
                self.db.cursor.execute("SELECT * FROM vendas_historico WHERE numero_cupom = ?", (numero,))
                venda = self.db.cursor.fetchone()

            if not venda:
                messagebox.showerror("Erro", f"Cupom {numero} não encontrado!")
                return

            # Buscar itens da venda
            self.db.cursor.execute("SELECT iv.quantidade, iv.preco_unitario, p.nome, p.tipo_peso FROM itens_venda iv JOIN produtos p ON iv.produto_id = p.id WHERE iv.venda_id = ?", (venda[0],))
            itens = self.db.cursor.fetchall()

            if not itens:
                # Tentar reconstruir do log se não achar itens
                messagebox.showwarning("Aviso", "Itens não encontrados no banco. Imprimindo cabeçalho apenas.")

            # Montar cupom
            try:
                linhas = []
                linhas.append(self.config[1])
                linhas.append(f"CNPJ: {self.config[2]}")
                linhas.append(self.config[3])
                linhas.append("=" * 35)
                linhas.append("CUPOM FISCAL - REIMPRESSAO")
                linhas.append(f"N: {numero}")
                linhas.append(f"Data: {venda[2]}")
                linhas.append("=" * 35)

                for idx, item in enumerate(itens, 1):
                    qtd, preco, nome, tipo_peso = item
                    if tipo_peso == 1:
                        qtd_str = f"{qtd:.3f}"
                    else:
                        qtd_str = f"{int(qtd)}"
                    linhas.append(f"{idx} {nome[:20]:<20} {qtd_str}x {preco*qtd:.2f}")

                linhas.append("-" * 35)
                linhas.append(f"TOTAL: R$ {venda[4]:.2f}")
                linhas.append(f"Pagamento: {venda[5].upper()}")
                linhas.append("=" * 35)
                linhas.append("CUPOM REIMPRESSO")
                linhas.append(self.config[5])
                linhas.append("")

                texto = "\n".join(linhas)

                temp_path = os.path.join(get_app_path(), "cupom_reimpresso_temp.txt")
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(texto)

                os.system(f'notepad /p "{temp_path}"')
                messagebox.showinfo("Sucesso", f"Cupom {numero} enviado para impressão!")
                janela.destroy()
                self.codigo_entry.focus_set()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao reimprimir: {str(e)}")

        cupom_entry.bind('<Return>', lambda e: buscar_e_imprimir())

        Win95Style.create_button(janela, "📄 REIMPRIMIR", buscar_e_imprimir,
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 11, 'bold'), width=18).pack(pady=15)
        Win95Style.create_button(janela, "Fechar", janela.destroy, width=12).pack(pady=5)

    def abrir_ajuda(self):
        ajuda = tk.Toplevel(self.root)
        ajuda.title("Ajuda - Atalhos do Sistema")
        ajuda.geometry("500x600")
        ajuda.configure(bg=Win95Style.BG_GRAY)
        ajuda.resizable(False, False)

        tk.Label(ajuda, text="ATALHOS DO SISTEMA", 
                font=('MS Sans Serif', 16, 'bold'), bg=Win95Style.NAVY, 
                fg="white").pack(fill='x', ipady=15)

        texto = """
TELA DE VENDAS:
• F1 - Esta ajuda
• F2 - Finalizar venda
• F3 - Editar item (qtd/valor)\n• Del - Cancelar ultimo item
• F4 - Cancelar venda completa
• F5 - Pesquisar produtos
• F6 - Cadastro de produtos
• F7 - Consulta de estoque
• F8 - Relatorio de vendas
• F9 - Gerar codigo de barras avulso
• F10 - Backup e restauracao
• F11 - Etiquetas com codigo de barras
• F12 - QR Code PIX rapido
• Ctrl+F - Fechar caixa (gerente)
• ESC - Sair do sistema

DICAS:
• Digite o codigo e pressione ENTER
• Use QTD*CODIGO (ex: 2*7891000315507)
• Duplo clique no item para editar quantidade
• Produtos por peso usam decimais (ex: 0.500)

LOGIN PADRAO:
• Usuario: admin
• Senha: admin123

BACKUP:
• Use F10 para acessar backup
• Crie backups diarios
• Restaure quando necessario

CAIXA:
• O caixa deve ser aberto ao iniciar
• Apenas gerentes podem fechar o caixa
• Ao fechar, os valores zeram automaticamente

Sistema totalmente offline.
Dados salvos localmente.
        """

        tk.Label(ajuda, text=texto, font=('Courier', 10), 
                justify='left', anchor='w', bg=Win95Style.BG_GRAY).pack(padx=20, pady=20, fill='both', expand=True)

        Win95Style.create_button(ajuda, "Fechar", ajuda.destroy,
                                font=('MS Sans Serif', 11, 'bold'), width=15, pady=10).pack(pady=20)

    def abrir_cadastro_clientes(self):
        """Abre tela de cadastro de clientes"""
        CadastroClientes(self.root, self.db)

    def sair(self):
        if messagebox.askyesno("Sair", "Deseja sair?"):
            self.root.quit()

    def abrir_log_administrativo(self):
        """Abre tela para visualização do log administrativo (somente admin)"""
        if self.user[4] != 'Gerente':
            messagebox.showerror("Acesso Negado", "Apenas gerentes podem acessar o log administrativo!")
            return

        janela = tk.Toplevel(self.root)
        janela.title("LOG ADMINISTRATIVO - Acesso Restrito")
        janela.geometry("900x700")
        janela.configure(bg=Win95Style.BG_GRAY)
        janela.resizable(False, False)

        header = tk.Frame(janela, bg=Win95Style.NAVY, height=50)
        header.pack(fill='x')
        tk.Label(header, text="LOG ADMINISTRATIVO DO SISTEMA", 
                font=('MS Sans Serif', 14, 'bold'), bg=Win95Style.NAVY, fg="white").pack(pady=10)

        tk.Label(janela, text="Registro completo de vendas e movimentações de caixa", 
                font=('MS Sans Serif', 10), bg=Win95Style.BG_GRAY, fg=Win95Style.DARK_GRAY).pack(pady=5)

        # Área de texto com scroll
        frame_text = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        frame_text.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame_text)
        scrollbar.pack(side='right', fill='y')

        texto = tk.Text(frame_text, font=('Courier', 9), wrap=tk.NONE, 
                       yscrollcommand=scrollbar.set, bg='white', fg='black')
        texto.pack(fill='both', expand=True)
        scrollbar.config(command=texto.yview)

        # Carrega o log
        logger = LoggerAdministrativo()
        conteudo = logger.ler_log()
        texto.insert('1.0', conteudo)
        texto.config(state='disabled')  # Somente leitura

        # Botões
        btn_frame = tk.Frame(janela, bg=Win95Style.BG_GRAY)
        btn_frame.pack(fill='x', pady=10)

        def exportar_log():
            arquivo = f"log_administrativo_{get_brasil_now().strftime('%Y%m%d_%H%M%S')}.txt"
            if logger.exportar_para_txt(arquivo):
                messagebox.showinfo("Sucesso", f"Log exportado para:\n{os.path.abspath(arquivo)}")
            else:
                messagebox.showerror("Erro", "Não foi possível exportar o log!")

        Win95Style.create_button(btn_frame, "📤 Exportar para TXT", exportar_log,
                                bg_color=Win95Style.SUCCESS, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=20).pack(side='left', padx=10)

        Win95Style.create_button(btn_frame, "🔄 Atualizar", 
                                lambda: [texto.config(state='normal'), 
                                        texto.delete('1.0', tk.END),
                                        texto.insert('1.0', logger.ler_log()),
                                        texto.config(state='disabled')],
                                bg_color=Win95Style.INFO, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(side='left', padx=10)

        Win95Style.create_button(btn_frame, "❌ Fechar", janela.destroy,
                                bg_color=Win95Style.DANGER, fg_color="white",
                                font=('MS Sans Serif', 10, 'bold'), width=15).pack(side='right', padx=10)


# =============================================================================
# INICIALIZACAO DO SISTEMA
# =============================================================================

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.db = Database()
        self.show_login()
        self.root.mainloop()

    def show_login(self):
        LoginScreen(self.root, self.db, self.on_login)

    def on_login(self, user):
        self.root.deiconify()
        for w in self.root.winfo_children():
            w.destroy()
        PDVSystem(self.root, self.db, user)

if __name__ == "__main__":
    MainApp()
