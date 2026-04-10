import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import hashlib
import datetime
import random
import os
import sys
import gc
import shutil

gc.enable()

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    return os.path.join(get_app_path(), "dados_pdv.db")

# Configurações de cores Windows 95
WIN95_COLORS = {
    'bg': '#c0c0c0',
    'button_bg': '#c0c0c0',
    'button_active': '#e0e0e0',
    'button_pressed': '#a0a0a0',
    'highlight': '#ffffff',
    'shadow': '#808080',
    'dark_shadow': '#404040',
    'text': '#000000',
    'blue': '#000080',
    'red': '#800000',
    'green': '#008000',
    'white': '#ffffff',
    'black': '#000000'
}

# ============ BANCO DE DADOS ============
class Database:
    def __init__(self):
        db_path = get_db_path()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_default_data()

    def create_tables(self):
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
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                preco_venda REAL NOT NULL,
                estoque INTEGER DEFAULT 0,
                unidade TEXT DEFAULT 'UN',
                ativo INTEGER DEFAULT 1
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_cupom TEXT UNIQUE NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER,
                total REAL,
                forma_pagamento TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                produto_id INTEGER,
                quantidade REAL,
                preco_unitario REAL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY,
                nome_empresa TEXT DEFAULT 'SUPERMERCADO CENTRAL',
                cnpj TEXT DEFAULT '00.000.000/0001-00',
                endereco TEXT DEFAULT 'Rua Principal, 100',
                telefone TEXT DEFAULT '(00) 0000-0000',
                mensagem_cupom TEXT DEFAULT 'Obrigado pela preferencia! Volte sempre!'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS caixa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_hora_fechamento TIMESTAMP,
                usuario_id INTEGER,
                valor_abertura REAL DEFAULT 0,
                valor_fechamento REAL,
                total_vendas REAL DEFAULT 0,
                status TEXT DEFAULT 'ABERTO'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                cpf TEXT,
                endereco TEXT,
                limite_fiado REAL DEFAULT 0,
                total_fiado REAL DEFAULT 0,
                ativo INTEGER DEFAULT 1
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_receber (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                venda_id INTEGER,
                valor REAL,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_pagamento TIMESTAMP,
                status TEXT DEFAULT 'PENDENTE'
            )
        """)
        self.conn.commit()

    def insert_default_data(self):
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO usuarios (id, username, password, nome, cargo)
                VALUES (1, 'admin', ?, 'Administrador', 'Gerente')
            """, (hashlib.sha256('admin123'.encode()).hexdigest(),))
            self.cursor.execute("""
                INSERT OR IGNORE INTO usuarios (id, username, password, nome, cargo)
                VALUES (2, 'caixa', ?, 'Operador', 'Caixa')
            """, (hashlib.sha256('caixa123'.encode()).hexdigest(),))
            self.cursor.execute("INSERT OR IGNORE INTO configuracoes (id) VALUES (1)")
            produtos = [
                ('7891000315507', 'Leite Integral 1L', 5.99, 50, 'UN'),
                ('7891000100103', 'Arroz 5kg', 22.90, 30, 'UN'),
                ('7896002300103', 'Feijao 1kg', 8.99, 40, 'UN'),
                ('7891000053508', 'Cafe 500g', 14.99, 25, 'UN'),
                ('7891000123456', 'Pao de Forma', 6.49, 20, 'UN'),
            ]
            for p in produtos:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO produtos (codigo_barras, nome, preco_venda, estoque, unidade)
                    VALUES (?, ?, ?, ?, ?)
                """, p)
            self.conn.commit()
        except Exception as e:
            print(f"Erro: {e}")

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
            numero_cupom = f"CF{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
            self.cursor.execute("""
                INSERT INTO vendas (numero_cupom, usuario_id, total, forma_pagamento)
                VALUES (?, ?, ?, ?)
            """, (numero_cupom, venda_data['usuario_id'], 
                   venda_data['total'], venda_data['forma_pagamento']))
            venda_id = self.cursor.lastrowid
            for item in venda_data['itens']:
                self.cursor.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                    VALUES (?, ?, ?, ?)
                """, (venda_id, item['produto_id'], item['quantidade'], item['preco']))
                self.update_estoque(item['produto_id'], item['quantidade'])
            if venda_data['forma_pagamento'] == 'fiado' and 'cliente_id' in venda_data:
                self.cursor.execute("""
                    INSERT INTO contas_receber (cliente_id, venda_id, valor)
                    VALUES (?, ?, ?)
                """, (venda_data['cliente_id'], venda_id, venda_data['total']))
                self.cursor.execute("""
                    UPDATE clientes SET total_fiado = total_fiado + ? WHERE id = ?
                """, (venda_data['total'], venda_data['cliente_id']))
            self.conn.commit()
            return venda_id, numero_cupom
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_produto(self, codigo, nome, preco, estoque, unidade):
        try:
            self.cursor.execute("""
                INSERT INTO produtos (codigo_barras, nome, preco_venda, estoque, unidade)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nome, preco, estoque, unidade))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_produto(self, produto_id, nome, preco, estoque, unidade):
        try:
            self.cursor.execute("""
                UPDATE produtos SET nome=?, preco_venda=?, estoque=?, unidade=?
                WHERE id=?
            """, (nome, preco, estoque, unidade, produto_id))
            self.conn.commit()
            return True
        except:
            return False

    def delete_produto(self, produto_id):
        try:
            self.cursor.execute("UPDATE produtos SET ativo=0 WHERE id=?", (produto_id,))
            self.conn.commit()
            return True
        except:
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
        except:
            return False

    def desativar_usuario(self, user_id):
        try:
            self.cursor.execute("UPDATE usuarios SET ativo=0 WHERE id=?", (user_id,))
            self.conn.commit()
            return True
        except:
            return False

    def get_all_usuarios(self):
        self.cursor.execute("SELECT id, nome, username, cargo, CASE WHEN ativo=1 THEN 'Ativo' ELSE 'Inativo' END FROM usuarios")
        return self.cursor.fetchall()

    def update_config(self, nome, cnpj, endereco, telefone, mensagem):
        try:
            self.cursor.execute("""
                UPDATE configuracoes SET nome_empresa=?, cnpj=?, endereco=?, telefone=?, mensagem_cupom=?
                WHERE id=1
            """, (nome, cnpj, endereco, telefone, mensagem))
            self.conn.commit()
            return True
        except:
            return False

    def get_vendas_periodo(self, data_ini, data_fim):
        self.cursor.execute("""
            SELECT numero_cupom, data_hora, total, forma_pagamento 
            FROM vendas 
            WHERE date(data_hora) BETWEEN ? AND ?
            ORDER BY data_hora DESC
        """, (data_ini, data_fim))
        return self.cursor.fetchall()

    def get_vendas_por_forma_pagamento(self, data_ini, data_fim):
        self.cursor.execute("""
            SELECT forma_pagamento, COUNT(*) as qtd, SUM(total) as total
            FROM vendas 
            WHERE date(data_hora) BETWEEN ? AND ?
            GROUP BY forma_pagamento
        """, (data_ini, data_fim))
        return self.cursor.fetchall()

    def add_estoque(self, codigo, quantidade):
        self.cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE codigo_barras = ?", 
                          (quantidade, codigo))
        self.conn.commit()
        return self.cursor.rowcount

    def gerar_codigo_barras(self):
        prefixo = "789"
        numeros = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        codigo_sem_dv = prefixo + numeros
        soma = 0
        for i, digito in enumerate(codigo_sem_dv):
            if i % 2 == 0:
                soma += int(digito)
            else:
                soma += int(digito) * 3
        dv = (10 - (soma % 10)) % 10
        codigo_completo = codigo_sem_dv + str(dv)
        self.cursor.execute("SELECT id FROM produtos WHERE codigo_barras = ?", (codigo_completo,))
        if self.cursor.fetchone():
            return self.gerar_codigo_barras()
        return codigo_completo

    def abrir_caixa(self, usuario_id, valor_abertura):
        try:
            self.cursor.execute("SELECT id FROM caixa WHERE status = 'ABERTO'")
            if self.cursor.fetchone():
                return None, "Ja existe um caixa aberto!"
            self.cursor.execute("""
                INSERT INTO caixa (usuario_id, valor_abertura, status)
                VALUES (?, ?, 'ABERTO')
            """, (usuario_id, valor_abertura))
            self.conn.commit()
            return self.cursor.lastrowid, "Caixa aberto com sucesso!"
        except Exception as e:
            return None, str(e)

    def fechar_caixa(self, caixa_id, valor_fechamento, total_vendas):
        try:
            self.cursor.execute("""
                UPDATE caixa 
                SET data_hora_fechamento = CURRENT_TIMESTAMP,
                    valor_fechamento = ?,
                    total_vendas = ?,
                    status = 'FECHADO'
                WHERE id = ?
            """, (valor_fechamento, total_vendas, caixa_id))
            self.conn.commit()
            return True
        except:
            return False

    def get_caixa_aberto(self):
        self.cursor.execute("""
            SELECT c.*, u.nome as usuario_nome 
            FROM caixa c
            JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.status = 'ABERTO'
            ORDER BY c.id DESC LIMIT 1
        """)
        return self.cursor.fetchone()

    def get_resumo_caixa(self, caixa_id):
        self.cursor.execute("""
            SELECT forma_pagamento, COUNT(*) as qtd, SUM(total) as total
            FROM vendas 
            WHERE date(data_hora) = date('now') AND usuario_id IN (
                SELECT usuario_id FROM caixa WHERE id = ?
            )
            GROUP BY forma_pagamento
        """, (caixa_id,))
        return self.cursor.fetchall()

    def get_all_clientes(self):
        self.cursor.execute("""
            SELECT id, nome, telefone, limite_fiado, total_fiado, 
                   CASE WHEN ativo=1 THEN 'Ativo' ELSE 'Inativo' END 
            FROM clientes WHERE ativo = 1 ORDER BY nome
        """)
        return self.cursor.fetchall()

    def add_cliente(self, nome, telefone, cpf, endereco, limite):
        try:
            self.cursor.execute("""
                INSERT INTO clientes (nome, telefone, cpf, endereco, limite_fiado)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, telefone, cpf, endereco, limite))
            self.conn.commit()
            return True
        except:
            return False

    def get_contas_receber(self, cliente_id=None):
        if cliente_id:
            self.cursor.execute("""
                SELECT cr.*, c.nome as cliente_nome, v.numero_cupom
                FROM contas_receber cr
                JOIN clientes c ON cr.cliente_id = c.id
                JOIN vendas v ON cr.venda_id = v.id
                WHERE cr.cliente_id = ? AND cr.status = 'PENDENTE'
                ORDER BY cr.data_venda DESC
            """, (cliente_id,))
        else:
            self.cursor.execute("""
                SELECT cr.*, c.nome as cliente_nome, v.numero_cupom
                FROM contas_receber cr
                JOIN clientes c ON cr.cliente_id = c.id
                JOIN vendas v ON cr.venda_id = v.id
                WHERE cr.status = 'PENDENTE'
                ORDER BY cr.data_venda DESC
            """)
        return self.cursor.fetchall()

    def quitar_conta(self, conta_id, valor_pago):
        try:
            self.cursor.execute("""
                UPDATE contas_receber 
                SET status = 'QUITADO', data_pagamento = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (conta_id,))
            self.cursor.execute("""
                UPDATE clientes 
                SET total_fiado = total_fiado - ?
                WHERE id = (SELECT cliente_id FROM contas_receber WHERE id = ?)
            """, (valor_pago, conta_id))
            self.conn.commit()
            return True
        except:
            return False

    def backup_database(self, destino):
        try:
            self.conn.commit()
            shutil.copy2(get_db_path(), destino)
            return True
        except:
            return False

    def restore_database(self, origem):
        try:
            self.conn.close()
            shutil.copy2(origem, get_db_path())
            self.conn = sqlite3.connect(get_db_path(), check_same_thread=False)
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.cursor = self.conn.cursor()
            return True
        except:
            return False


# ============ CLASSES DE INTERFACE ============

class CadastroProdutos:
    def __init__(self, parent, db):
        self.db = db
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Produtos - Estoque")
        self.janela.geometry("900x650")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.create_interface()
        self.carregar_produtos()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x', side='top')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CADASTRO DE PRODUTOS / ESTOQUE", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'], 
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], fg=WIN95_COLORS['text'],
                 relief='raised', bd=2, font=('MS Sans Serif', 10, 'bold'),
                 width=2, cursor='hand2').pack(side='right', padx=2, pady=1)

        form_frame = tk.LabelFrame(main_container, text=" NOVO PRODUTO ", 
                                  font=('MS Sans Serif', 9, 'bold'), 
                                  bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                  relief='raised', bd=2)
        form_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(form_frame, text="Codigo de Barras:", bg=WIN95_COLORS['bg'],
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.codigo_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.codigo_var, 
                font=('MS Sans Serif', 9), width=20, relief='sunken', bd=2).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(form_frame, text="Gerar", command=self.gerar_codigo_automatico,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 8)).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(form_frame, text="Nome do Produto:", bg=WIN95_COLORS['bg'],
                font=('MS Sans Serif', 9)).grid(row=0, column=3, padx=5, pady=5, sticky='e')
        self.nome_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.nome_var, 
                font=('MS Sans Serif', 9), width=30, relief='sunken', bd=2).grid(row=0, column=4, padx=5, pady=5)

        tk.Label(form_frame, text="Preco (R$):", bg=WIN95_COLORS['bg'],
                font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.preco_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.preco_var, 
                font=('MS Sans Serif', 9), width=15, relief='sunken', bd=2).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Estoque:", bg=WIN95_COLORS['bg'],
                font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.estoque_var = tk.StringVar(value="0")
        tk.Entry(form_frame, textvariable=self.estoque_var, 
                font=('MS Sans Serif', 9), width=10, relief='sunken', bd=2).grid(row=1, column=3, padx=5, pady=5, sticky='w')

        tk.Label(form_frame, text="Unidade:", bg=WIN95_COLORS['bg'],
                font=('MS Sans Serif', 9)).grid(row=1, column=4, padx=5, pady=5, sticky='e')
        self.unidade_var = tk.StringVar(value="UN")
        ttk.Combobox(form_frame, textvariable=self.unidade_var, 
                     values=["UN", "CX", "KG", "LT", "PC"], width=8).grid(row=1, column=5, padx=5, pady=5)

        btn_frame = tk.Frame(form_frame, bg=WIN95_COLORS['bg'])
        btn_frame.grid(row=2, column=0, columnspan=6, pady=10)

        tk.Button(btn_frame, text="SALVAR", command=self.salvar_produto,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=15).pack(side='left', padx=5)

        tk.Button(btn_frame, text="LIMPAR", command=self.limpar_campos,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), padx=15).pack(side='left', padx=5)

        lista_frame = tk.LabelFrame(main_container, text=" PRODUTOS CADASTRADOS ", 
                                   font=('MS Sans Serif', 9, 'bold'),
                                   bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                   relief='raised', bd=2)
        lista_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'codigo', 'nome', 'preco', 'estoque', 'unidade')
        self.tree = ttk.Treeview(lista_frame, columns=cols, show='headings', height=12)

        self.tree.heading('id', text='ID')
        self.tree.heading('codigo', text='CODIGO')
        self.tree.heading('nome', text='NOME')
        self.tree.heading('preco', text='PRECO')
        self.tree.heading('estoque', text='ESTQ')
        self.tree.heading('unidade', text='UN')

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('codigo', width=120, anchor='center')
        self.tree.column('nome', width=300)
        self.tree.column('preco', width=80, anchor='e')
        self.tree.column('estoque', width=60, anchor='center')
        self.tree.column('unidade', width=50, anchor='center')

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        acao_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        acao_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(acao_frame, text="EDITAR", command=self.editar_produto,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Button(acao_frame, text="EXCLUIR", command=self.excluir_produto,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Button(acao_frame, text="ATUALIZAR", command=self.carregar_produtos,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='right', padx=5)

        separator = tk.Frame(main_container, bg=WIN95_COLORS['shadow'], height=2)
        separator.pack(fill='x', padx=10, pady=5)

        bottom_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        bottom_frame.pack(fill='x', padx=10, pady=5)

        self.status_label = tk.Label(bottom_frame, text="Pronto", 
                                    bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                    font=('MS Sans Serif', 9))
        self.status_label.pack(side='left')

        tk.Button(bottom_frame, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(side='right')

    def fechar(self):
        self.janela.destroy()

    def gerar_codigo_automatico(self):
        codigo = self.db.gerar_codigo_barras()
        self.codigo_var.set(codigo)
        messagebox.showinfo("Codigo Gerado", f"Codigo de barras gerado: {codigo}")

    def carregar_produtos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        produtos = self.db.get_all_produtos()
        for p in produtos:
            self.tree.insert('', 'end', values=(p[0], p[1], p[2], f"R$ {p[3]:.2f}", p[4], p[5]))
        self.status_label.config(text=f"Total de produtos: {len(produtos)}")

    def salvar_produto(self):
        codigo = self.codigo_var.get().strip()
        nome = self.nome_var.get().strip()
        preco_str = self.preco_var.get().strip().replace(',', '.')
        estoque_str = self.estoque_var.get().strip()
        unidade = self.unidade_var.get()

        if not codigo or not nome or not preco_str:
            messagebox.showerror("Erro", "Preencha codigo, nome e preco!")
            return

        try:
            preco = float(preco_str)
            estoque = int(estoque_str) if estoque_str else 0
        except ValueError:
            messagebox.showerror("Erro", "Preco e estoque devem ser numeros!")
            return

        if preco <= 0:
            messagebox.showerror("Erro", "Preco deve ser maior que zero!")
            return

        if self.db.add_produto(codigo, nome, preco, estoque, unidade):
            messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
            self.limpar_campos()
            self.carregar_produtos()
        else:
            messagebox.showerror("Erro", f"Codigo '{codigo}' ja existe!")

    def limpar_campos(self):
        self.codigo_var.set('')
        self.nome_var.set('')
        self.preco_var.set('')
        self.estoque_var.set('0')
        self.unidade_var.set('UN')

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
        edit_janela.configure(bg=WIN95_COLORS['bg'])
        edit_janela.resizable(False, False)
        edit_janela.transient(self.janela)
        edit_janela.grab_set()

        container = tk.Frame(edit_janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="EDITAR PRODUTO", bg=WIN95_COLORS['blue'],
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)
        tk.Button(title_bar, text='×', command=edit_janela.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        form = tk.Frame(container, bg=WIN95_COLORS['bg'])
        form.pack(padx=20, pady=20)

        tk.Label(form, text="Nome:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', pady=5)
        nome_edit = tk.StringVar(value=valores[2])
        tk.Entry(form, textvariable=nome_edit, font=('MS Sans Serif', 9), width=40, relief='sunken', bd=2).pack()

        tk.Label(form, text="Preco (R$):", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', pady=5)
        preco_edit = tk.StringVar(value=str(valores[3]).replace('R$ ', ''))
        tk.Entry(form, textvariable=preco_edit, font=('MS Sans Serif', 9), width=15, relief='sunken', bd=2).pack()

        tk.Label(form, text="Estoque:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', pady=5)
        estoque_edit = tk.StringVar(value=valores[4])
        tk.Entry(form, textvariable=estoque_edit, font=('MS Sans Serif', 9), width=10, relief='sunken', bd=2).pack()

        tk.Label(form, text="Unidade:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', pady=5)
        unidade_edit = tk.StringVar(value=valores[5])
        ttk.Combobox(form, textvariable=unidade_edit, values=["UN", "CX", "KG", "LT", "PC"], width=8).pack()

        def salvar_edicao():
            try:
                novo_preco = float(preco_edit.get().replace(',', '.'))
                novo_estoque = int(estoque_edit.get())
                if self.db.update_produto(produto_id, nome_edit.get(), novo_preco, novo_estoque, unidade_edit.get()):
                    messagebox.showinfo("Sucesso", "Produto atualizado!")
                    edit_janela.destroy()
                    self.carregar_produtos()
                else:
                    messagebox.showerror("Erro", "Nao foi possivel atualizar!")
            except ValueError:
                messagebox.showerror("Erro", "Preco e estoque devem ser numeros!")

        btn_frame = tk.Frame(container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(btn_frame, text="SALVAR", command=salvar_edicao,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=15).pack(side='left')

        tk.Button(btn_frame, text="CANCELAR", command=edit_janela.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), padx=15).pack(side='right')

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


class CadastroUsuarios:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Usuarios")
        self.janela.geometry("700x550")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()
        self.carregar_usuarios()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CADASTRO DE USUARIOS", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        form = tk.LabelFrame(main_container, text=" NOVO USUARIO ", 
                            font=('MS Sans Serif', 9, 'bold'),
                            bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                            relief='raised', bd=2)
        form.pack(fill='x', padx=10, pady=10)

        tk.Label(form, text="Nome:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.nome_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nome_var, width=30, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Usuario:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.user_var = tk.StringVar()
        tk.Entry(form, textvariable=self.user_var, width=20, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Senha:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.senha_var = tk.StringVar()
        tk.Entry(form, textvariable=self.senha_var, show="*", width=20, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=1, column=1, padx=5)

        tk.Label(form, text="Cargo:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.cargo_var = tk.StringVar(value="Caixa")
        ttk.Combobox(form, textvariable=self.cargo_var, values=["Gerente", "Caixa"], width=15).grid(row=1, column=3, padx=5)

        tk.Button(form, text="SALVAR USUARIO", command=self.salvar_usuario,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold')).grid(row=2, column=0, columnspan=4, pady=10)

        lista = tk.LabelFrame(main_container, text=" USUARIOS CADASTRADOS ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                             relief='raised', bd=2)
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

        btn_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(btn_frame, text="Resetar Senha", command=self.resetar_senha,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Desativar", command=self.desativar_usuario,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        separator = tk.Frame(main_container, bg=WIN95_COLORS['shadow'], height=2)
        separator.pack(fill='x', padx=10, pady=5)

        tk.Button(main_container, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=5)

    def fechar(self):
        self.janela.destroy()

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


class RelatorioVendas:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Relatorio de Vendas")
        self.janela.geometry("1000x750")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="RELATORIO DE VENDAS", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        filtros = tk.LabelFrame(main_container, text=" FILTROS ", 
                               font=('MS Sans Serif', 9, 'bold'),
                               bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                               relief='raised', bd=2)
        filtros.pack(fill='x', padx=10, pady=10)

        tk.Label(filtros, text="De:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.data_ini = tk.StringVar(value=datetime.date.today().strftime('%d/%m/%Y'))
        tk.Entry(filtros, textvariable=self.data_ini, width=12, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Label(filtros, text="Ate:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.data_fim = tk.StringVar(value=datetime.date.today().strftime('%d/%m/%Y'))
        tk.Entry(filtros, textvariable=self.data_fim, width=12, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Button(filtros, text="BUSCAR", command=self.buscar_vendas,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=20)

        tk.Button(filtros, text="HOJE", command=self.vendas_hoje,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        self.resumo_frame = tk.LabelFrame(main_container, text=" RESUMO POR FORMA DE PAGAMENTO ", 
                                         font=('MS Sans Serif', 9, 'bold'),
                                         bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                         relief='raised', bd=2)
        self.resumo_frame.pack(fill='x', padx=10, pady=5)

        self.resumo_labels = {}
        formas = ['dinheiro', 'credito', 'debito', 'pix', 'fiado']

        for i, forma in enumerate(formas):
            frame = tk.Frame(self.resumo_frame, bg=WIN95_COLORS['bg'])
            frame.grid(row=0, column=i, padx=15, pady=5)
            tk.Label(frame, text=forma.upper(), font=('MS Sans Serif', 9, 'bold'), 
                    fg=WIN95_COLORS['text'], bg=WIN95_COLORS['bg']).pack()
            self.resumo_labels[forma] = tk.Label(frame, text="R$ 0,00 (0 vendas)", 
                                               font=('MS Sans Serif', 9), bg=WIN95_COLORS['bg'])
            self.resumo_labels[forma].pack()

        self.lbl_total_geral = tk.Label(self.resumo_frame, text="TOTAL GERAL: R$ 0,00", 
                                       font=('MS Sans Serif', 11, 'bold'), 
                                       fg=WIN95_COLORS['blue'], bg=WIN95_COLORS['bg'])
        self.lbl_total_geral.grid(row=1, column=0, columnspan=5, pady=5)

        lista = tk.LabelFrame(main_container, text=" VENDAS DETALHADAS ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                             relief='raised', bd=2)
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

        btn_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(btn_frame, text="EXPORTAR PARA TXT", command=self.exportar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Button(btn_frame, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(side='right', padx=5)

        self.vendas_hoje()

    def fechar(self):
        self.janela.destroy()

    def vendas_hoje(self):
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        self.data_ini.set(datetime.date.today().strftime('%d/%m/%Y'))
        self.data_fim.set(datetime.date.today().strftime('%d/%m/%Y'))
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

        vendas = self.db.get_vendas_periodo(ini, fim)
        resumo = self.db.get_vendas_por_forma_pagamento(ini, fim)

        totais_por_forma = {forma: {'qtd': 0, 'total': 0.0} for forma in ['dinheiro', 'credito', 'debito', 'pix', 'fiado']}

        for forma, qtd, total in resumo:
            if forma in totais_por_forma:
                totais_por_forma[forma]['qtd'] = qtd
                totais_por_forma[forma]['total'] = total

        for forma, dados in totais_por_forma.items():
            self.resumo_labels[forma].config(
                text=f"R$ {dados['total']:.2f} ({dados['qtd']} vendas)"
            )

        total_geral = sum(d['total'] for d in totais_por_forma.values())
        self.lbl_total_geral.config(text=f"TOTAL GERAL: R$ {total_geral:.2f}")

        for v in vendas:
            data = datetime.datetime.strptime(v[1], '%Y-%m-%d %H:%M:%S')
            self.tree.insert('', 'end', values=(
                v[0],
                data.strftime('%d/%m/%Y'),
                data.strftime('%H:%M:%S'),
                f"R$ {v[2]:.2f}",
                v[3].upper()
            ))

    def exportar(self):
        arquivo = f"relatorio_vendas_{datetime.date.today().strftime('%Y%m%d')}.txt"
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write("RELATORIO DE VENDAS\n")
            f.write("="*50 + "\n\n")
            f.write("RESUMO POR FORMA DE PAGAMENTO:\n")
            for forma in ['dinheiro', 'credito', 'debito', 'pix', 'fiado']:
                texto = self.resumo_labels[forma].cget("text")
                f.write(f"{forma.upper()}: {texto}\n")
            f.write(f"\n{self.lbl_total_geral.cget('text')}\n\n")
            f.write("-"*50 + "\n\n")
            f.write("VENDAS DETALHADAS:\n")
            for item in self.tree.get_children():
                valores = self.tree.item(item)['values']
                f.write(f"Cupom: {valores[0]} | Data: {valores[1]} | Total: {valores[3]} | Pagamento: {valores[4]}\n")
        messagebox.showinfo("Sucesso", f"Relatorio salvo em:\n{os.path.abspath(arquivo)}")


class CadastroClientes:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Cadastro de Clientes - Fiado")
        self.janela.geometry("800x650")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()
        self.carregar_clientes()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CADASTRO DE CLIENTES (FIADO)", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        form = tk.LabelFrame(main_container, text=" NOVO CLIENTE ", 
                            font=('MS Sans Serif', 9, 'bold'),
                            bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                            relief='raised', bd=2)
        form.pack(fill='x', padx=10, pady=10)

        tk.Label(form, text="Nome:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.nome_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nome_var, width=40, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Telefone:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.tel_var = tk.StringVar()
        tk.Entry(form, textvariable=self.tel_var, width=15, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=0, column=3, padx=5)

        tk.Label(form, text="CPF:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.cpf_var = tk.StringVar()
        tk.Entry(form, textvariable=self.cpf_var, width=20, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=1, column=1, padx=5)

        tk.Label(form, text="Limite Fiado (R$):", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.limite_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=self.limite_var, width=15, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=1, column=3, padx=5)

        tk.Label(form, text="Endereco:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.end_var = tk.StringVar()
        tk.Entry(form, textvariable=self.end_var, width=60, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).grid(row=2, column=1, columnspan=3, padx=5)

        tk.Button(form, text="SALVAR CLIENTE", command=self.salvar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold')).grid(row=3, column=0, columnspan=4, pady=10)

        lista = tk.LabelFrame(main_container, text=" CLIENTES CADASTRADOS ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                             relief='raised', bd=2)
        lista.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'nome', 'telefone', 'limite', 'fiado_atual', 'status')
        self.tree = ttk.Treeview(lista, columns=cols, show='headings', height=12)

        for c in cols:
            self.tree.heading(c, text=c.upper().replace('_', ' '))

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('nome', width=200)
        self.tree.column('telefone', width=100, anchor='center')
        self.tree.column('limite', width=100, anchor='e')
        self.tree.column('fiado_atual', width=100, anchor='e')
        self.tree.column('status', width=80, anchor='center')

        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        btn_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(btn_frame, text="Contas a Receber", command=self.ver_contas,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Receber Pagamento", command=self.receber_pagamento,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        separator = tk.Frame(main_container, bg=WIN95_COLORS['shadow'], height=2)
        separator.pack(fill='x', padx=10, pady=5)

        tk.Button(main_container, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=5)

    def fechar(self):
        self.janela.destroy()

    def carregar_clientes(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for c in self.db.get_all_clientes():
            self.tree.insert('', 'end', values=c)

    def salvar(self):
        nome = self.nome_var.get().strip()
        if not nome:
            messagebox.showerror("Erro", "Nome e obrigatorio!")
            return
        try:
            limite = float(self.limite_var.get().replace(',', '.'))
        except:
            limite = 0
        if self.db.add_cliente(nome, self.tel_var.get(), self.cpf_var.get(), 
                              self.end_var.get(), limite):
            messagebox.showinfo("Sucesso", f"Cliente '{nome}' cadastrado!")
            self.limpar()
            self.carregar_clientes()
        else:
            messagebox.showerror("Erro", "Erro ao cadastrar cliente!")

    def limpar(self):
        self.nome_var.set('')
        self.tel_var.set('')
        self.cpf_var.set('')
        self.limite_var.set('0')
        self.end_var.set('')

    def ver_contas(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um cliente!")
            return
        cliente_id = self.tree.item(sel[0])['values'][0]
        cliente_nome = self.tree.item(sel[0])['values'][1]

        janela = tk.Toplevel(self.janela)
        janela.title(f"Contas a Receber - {cliente_nome}")
        janela.geometry("700x450")
        janela.configure(bg=WIN95_COLORS['bg'])
        janela.resizable(False, False)

        container = tk.Frame(janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=f"CONTAS A RECEBER - {cliente_nome.upper()}", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)
        tk.Button(title_bar, text='×', command=janela.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        cols = ('id', 'cupom', 'valor', 'data', 'status')
        tree = ttk.Treeview(container, columns=cols, show='headings', height=15)
        for c in cols:
            tree.heading(c, text=c.upper())
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        contas = self.db.get_contas_receber(cliente_id)
        for conta in contas:
            tree.insert('', 'end', values=(
                conta[0], conta[6], f"R$ {conta[3]:.2f}", 
                conta[4][:10], conta[5]
            ))

        tk.Button(container, text="FECHAR", command=janela.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=10)

    def receber_pagamento(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um cliente!")
            return
        cliente_id = self.tree.item(sel[0])['values'][0]
        cliente_nome = self.tree.item(sel[0])['values'][1]
        fiado_atual = float(self.tree.item(sel[0])['values'][4])
        if fiado_atual <= 0:
            messagebox.showinfo("Informacao", "Cliente nao possui debitos!")
            return
        valor = simpledialog.askfloat("Receber Pagamento", 
                                     f"Valor recebido de {cliente_nome}:",
                                     minvalue=0.01, maxvalue=fiado_atual)
        if valor:
            messagebox.showinfo("Sucesso", f"Pagamento de R$ {valor:.2f} registrado!")
            self.carregar_clientes()


class ContasReceber:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Contas a Receber")
        self.janela.geometry("900x650")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()
        self.carregar_contas()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CONTAS A RECEBER", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        lista = tk.LabelFrame(main_container, text=" TODAS AS CONTAS PENDENTES ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                             relief='raised', bd=2)
        lista.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('id', 'cliente', 'cupom', 'valor', 'data_venda', 'status')
        self.tree = ttk.Treeview(lista, columns=cols, show='headings', height=20)

        for c in cols:
            self.tree.heading(c, text=c.upper().replace('_', ' '))

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('cliente', width=200)
        self.tree.column('cupom', width=150, anchor='center')
        self.tree.column('valor', width=100, anchor='e')
        self.tree.column('data_venda', width=100, anchor='center')
        self.tree.column('status', width=100, anchor='center')

        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        btn_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(fill='x', padx=10, pady=5)

        self.lbl_total = tk.Label(btn_frame, text="TOTAL A RECEBER: R$ 0,00", 
                                 font=('MS Sans Serif', 11, 'bold'), 
                                 fg=WIN95_COLORS['red'], bg=WIN95_COLORS['bg'])
        self.lbl_total.pack(side='left')

        tk.Button(btn_frame, text="QUITAR SELECIONADA", command=self.quitar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=20)

        tk.Button(btn_frame, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(side='right')

    def fechar(self):
        self.janela.destroy()

    def carregar_contas(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        contas = self.db.get_contas_receber()
        total = 0
        for c in contas:
            self.tree.insert('', 'end', values=(
                c[0], c[6], c[7], f"R$ {c[3]:.2f}", c[4][:10], c[5]
            ))
            total += c[3]
        self.lbl_total.config(text=f"TOTAL A RECEBER: R$ {total:.2f}")

    def quitar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma conta!")
            return
        valores = self.tree.item(sel[0])['values']
        conta_id = valores[0]
        valor_str = valores[3].replace('R$ ', '').replace(',', '.')
        valor = float(valor_str)

        if messagebox.askyesno("Confirmar", f"Quitar conta no valor de {valores[3]}?"):
            if self.db.quitar_conta(conta_id, valor):
                messagebox.showinfo("Sucesso", "Conta quitada!")
                self.carregar_contas()
            else:
                messagebox.showerror("Erro", "Nao foi possivel quitar!")

class ConfiguracoesSistema:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Configuracoes do Sistema")
        self.janela.geometry("600x450")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()
        self.carregar_config()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CONFIGURACOES DO SISTEMA", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        form = tk.LabelFrame(main_container, text=" DADOS DA EMPRESA ", 
                            font=('MS Sans Serif', 9, 'bold'),
                            bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                            relief='raised', bd=2)
        form.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Label(form, text="Nome da Empresa:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', padx=10, pady=5)
        self.nome_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nome_var, width=50, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(anchor='w', padx=10)

        tk.Label(form, text="CNPJ:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', padx=10, pady=5)
        self.cnpj_var = tk.StringVar()
        tk.Entry(form, textvariable=self.cnpj_var, width=25, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(anchor='w', padx=10)

        tk.Label(form, text="Endereco:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', padx=10, pady=5)
        self.end_var = tk.StringVar()
        tk.Entry(form, textvariable=self.end_var, width=50, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(anchor='w', padx=10)

        tk.Label(form, text="Telefone:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', padx=10, pady=5)
        self.tel_var = tk.StringVar()
        tk.Entry(form, textvariable=self.tel_var, width=20, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(anchor='w', padx=10)

        tk.Label(form, text="Mensagem no Cupom:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(anchor='w', padx=10, pady=5)
        self.msg_var = tk.StringVar()
        tk.Entry(form, textvariable=self.msg_var, width=50, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(anchor='w', padx=10)

        btn_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(fill='x', padx=10, pady=10)

        tk.Button(btn_frame, text="SALVAR", command=self.salvar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=15).pack(side='left', padx=5)

        tk.Button(btn_frame, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(side='right')

    def fechar(self):
        self.janela.destroy()

    def carregar_config(self):
        config = self.db.get_config()
        if config:
            self.nome_var.set(config[1] or '')
            self.cnpj_var.set(config[2] or '')
            self.end_var.set(config[3] or '')
            self.tel_var.set(config[4] or '')
            self.msg_var.set(config[5] or '')

    def salvar(self):
        if self.db.update_config(
            self.nome_var.get(),
            self.cnpj_var.get(),
            self.end_var.get(),
            self.tel_var.get(),
            self.msg_var.get()
        ):
            messagebox.showinfo("Sucesso", "Configuracoes salvas!")
        else:
            messagebox.showerror("Erro", "Erro ao salvar!")


class ConsultaEstoque:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Consulta de Estoque")
        self.janela.geometry("800x600")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()
        self.carregar_produtos()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CONSULTA DE ESTOQUE", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        filtros = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        filtros.pack(fill='x', padx=10, pady=10)

        tk.Label(filtros, text="Buscar:", bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.busca_var = tk.StringVar()
        tk.Entry(filtros, textvariable=self.busca_var, width=40, relief='sunken', bd=2,
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Button(filtros, text="BUSCAR", command=self.buscar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        tk.Button(filtros, text="LIMPAR", command=self.carregar_produtos,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        lista = tk.LabelFrame(main_container, text=" PRODUTOS EM ESTOQUE ", 
                             font=('MS Sans Serif', 9, 'bold'),
                             bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                             relief='raised', bd=2)
        lista.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ('codigo', 'nome', 'preco', 'estoque', 'unidade')
        self.tree = ttk.Treeview(lista, columns=cols, show='headings', height=18)

        for c in cols:
            self.tree.heading(c, text=c.upper())

        self.tree.column('codigo', width=120, anchor='center')
        self.tree.column('nome', width=300)
        self.tree.column('preco', width=100, anchor='e')
        self.tree.column('estoque', width=80, anchor='center')
        self.tree.column('unidade', width=60, anchor='center')

        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scroll.pack(side='right', fill='y')

        tk.Button(main_container, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=10)

    def fechar(self):
        self.janela.destroy()

    def carregar_produtos(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.busca_var.set('')
        produtos = self.db.get_all_produtos()
        for p in produtos:
            self.tree.insert('', 'end', values=(p[1], p[2], f"R$ {p[3]:.2f}", p[4], p[5]))

    def buscar(self):
        termo = self.busca_var.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        produtos = self.db.get_all_produtos()
        for p in produtos:
            if termo in p[1].lower() or termo in p[2].lower():
                self.tree.insert('', 'end', values=(p[1], p[2], f"R$ {p[3]:.2f}", p[4], p[5]))

class ControleCaixa:
    def __init__(self, parent, db, usuario_id):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Controle de Caixa")
        self.janela.geometry("600x500")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.usuario_id = usuario_id
        self.caixa_aberto = None
        self.create_interface()
        self.verificar_caixa()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="CONTROLE DE CAIXA", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        self.status_frame = tk.LabelFrame(main_container, text=" STATUS DO CAIXA ", 
                                         font=('MS Sans Serif', 9, 'bold'),
                                         bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                         relief='raised', bd=2)
        self.status_frame.pack(fill='x', padx=10, pady=10)

        self.lbl_status = tk.Label(self.status_frame, text="Verificando...", 
                                  font=('MS Sans Serif', 14, 'bold'),
                                  bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'])
        self.lbl_status.pack(pady=10)

        self.info_frame = tk.Frame(self.status_frame, bg=WIN95_COLORS['bg'])
        self.info_frame.pack(fill='x', padx=10, pady=5)

        self.lbl_operador = tk.Label(self.info_frame, text="Operador: -", 
                                    font=('MS Sans Serif', 9), bg=WIN95_COLORS['bg'])
        self.lbl_operador.pack(anchor='w')

        self.lbl_abertura = tk.Label(self.info_frame, text="Abertura: -", 
                                    font=('MS Sans Serif', 9), bg=WIN95_COLORS['bg'])
        self.lbl_abertura.pack(anchor='w')

        self.acoes_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        self.acoes_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(self.acoes_frame, text="Valor:", bg=WIN95_COLORS['bg'], 
                font=('MS Sans Serif', 9)).pack(side='left', padx=5)
        self.valor_var = tk.StringVar(value="0.00")
        tk.Entry(self.acoes_frame, textvariable=self.valor_var, width=15, 
                relief='sunken', bd=2, font=('MS Sans Serif', 9)).pack(side='left', padx=5)

        self.btn_abrir = tk.Button(self.acoes_frame, text="ABRIR CAIXA", command=self.abrir_caixa,
                                  bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                                  font=('MS Sans Serif', 9, 'bold'))
        self.btn_abrir.pack(side='left', padx=10)

        self.btn_fechar = tk.Button(self.acoes_frame, text="FECHAR CAIXA", command=self.fechar_caixa,
                                   bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                                   font=('MS Sans Serif', 9, 'bold'))
        self.btn_fechar.pack(side='left', padx=10)

        self.resumo_frame = tk.LabelFrame(main_container, text=" RESUMO DO DIA ", 
                                         font=('MS Sans Serif', 9, 'bold'),
                                         bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                         relief='raised', bd=2)
        self.resumo_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.resumo_text = tk.Text(self.resumo_frame, height=10, width=50, 
                                  font=('Courier', 10), relief='sunken', bd=2)
        self.resumo_text.pack(fill='both', expand=True, padx=5, pady=5)

        tk.Button(main_container, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=10)

    def fechar(self):
        self.janela.destroy()

    def verificar_caixa(self):
        self.caixa_aberto = self.db.get_caixa_aberto()
        if self.caixa_aberto:
            self.lbl_status.config(text="CAIXA ABERTO", fg=WIN95_COLORS['green'])
            self.lbl_operador.config(text=f"Operador: {self.caixa_aberto[8]}")
            self.lbl_abertura.config(text=f"Abertura: {self.caixa_aberto[1]}")
            self.btn_abrir.config(state='disabled')
            self.btn_fechar.config(state='normal')
            self.atualizar_resumo()
        else:
            self.lbl_status.config(text="CAIXA FECHADO", fg=WIN95_COLORS['red'])
            self.lbl_operador.config(text="Operador: -")
            self.lbl_abertura.config(text="Abertura: -")
            self.btn_abrir.config(state='normal')
            self.btn_fechar.config(state='disabled')
            self.resumo_text.delete(1.0, tk.END)

    def abrir_caixa(self):
        try:
            valor = float(self.valor_var.get().replace(',', '.'))
        except:
            messagebox.showerror("Erro", "Valor invalido!")
            return

        caixa_id, msg = self.db.abrir_caixa(self.usuario_id, valor)
        if caixa_id:
            messagebox.showinfo("Sucesso", msg)
            self.verificar_caixa()
        else:
            messagebox.showerror("Erro", msg)

    def fechar_caixa(self):
        if not self.caixa_aberto:
            return

        try:
            valor = float(self.valor_var.get().replace(',', '.'))
        except:
            messagebox.showerror("Erro", "Valor invalido!")
            return

        resumo = self.db.get_resumo_caixa(self.caixa_aberto[0])
        total_vendas = sum(r[2] for r in resumo) if resumo else 0

        if messagebox.askyesno("Confirmar", f"Fechar caixa com R$ {valor:.2f}?"):
            if self.db.fechar_caixa(self.caixa_aberto[0], valor, total_vendas):
                messagebox.showinfo("Sucesso", "Caixa fechado!")
                self.verificar_caixa()
            else:
                messagebox.showerror("Erro", "Erro ao fechar caixa!")

    def atualizar_resumo(self):
        self.resumo_text.delete(1.0, tk.END)
        if not self.caixa_aberto:
            return

        resumo = self.db.get_resumo_caixa(self.caixa_aberto[0])
        self.resumo_text.insert(tk.END, "RESUMO DE VENDAS\n")
        self.resumo_text.insert(tk.END, "=" * 40 + "\n\n")

        total = 0
        for forma, qtd, valor in resumo:
            self.resumo_text.insert(tk.END, f"{forma.upper():12} {qtd:3} vendas  R$ {valor:>10.2f}\n")
            total += valor

        self.resumo_text.insert(tk.END, "\n" + "=" * 40 + "\n")
        self.resumo_text.insert(tk.END, f"{'TOTAL':12}          R$ {total:>10.2f}\n")


class BackupRestauracao:
    def __init__(self, parent, db):
        self.janela = tk.Toplevel(parent)
        self.janela.title("Backup e Restauracao")
        self.janela.geometry("500x350")
        self.janela.configure(bg=WIN95_COLORS['bg'])
        self.janela.resizable(False, False)
        self.db = db
        self.create_interface()

    def create_interface(self):
        main_container = tk.Frame(self.janela, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="BACKUP E RESTAURACAO", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(title_bar, text='×', command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 10, 'bold'), width=2).pack(side='right', padx=2)

        backup_frame = tk.LabelFrame(main_container, text=" BACKUP ", 
                                    font=('MS Sans Serif', 9, 'bold'),
                                    bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                    relief='raised', bd=2)
        backup_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(backup_frame, text="Criar backup do banco de dados", 
                bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(pady=10)

        tk.Button(backup_frame, text="FAZER BACKUP", command=self.fazer_backup,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=5)

        restore_frame = tk.LabelFrame(main_container, text=" RESTAURACAO ", 
                                     font=('MS Sans Serif', 9, 'bold'),
                                     bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                     relief='raised', bd=2)
        restore_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(restore_frame, text="Restaurar banco de dados a partir de backup", 
                bg=WIN95_COLORS['bg'], font=('MS Sans Serif', 9)).pack(pady=10)

        tk.Button(restore_frame, text="RESTAURAR", command=self.restaurar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=5)

        tk.Button(main_container, text="FECHAR", command=self.fechar,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(pady=10)

    def fechar(self):
        self.janela.destroy()

    def fazer_backup(self):
        data = datetime.date.today().strftime('%Y%m%d')
        arquivo = f"backup_pdv_{data}.db"
        if self.db.backup_database(arquivo):
            messagebox.showinfo("Sucesso", f"Backup criado:\n{os.path.abspath(arquivo)}")
        else:
            messagebox.showerror("Erro", "Erro ao criar backup!")

    def restaurar(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar arquivo de backup",
            filetypes=[("Database files", "*.db"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            if messagebox.askyesno("Confirmar", "Isso substituira o banco atual. Continuar?"):
                if self.db.restore_database(arquivo):
                    messagebox.showinfo("Sucesso", "Banco restaurado! Reinicie o sistema.")
                else:
                    messagebox.showerror("Erro", "Erro ao restaurar!")

class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.usuario_logado = None
        self.create_interface()

    def create_interface(self):
        self.root.title("PDV Windows 95 - Login")
        self.root.geometry("400x300")
        self.root.configure(bg=WIN95_COLORS['bg'])
        self.root.resizable(False, False)

        main_container = tk.Frame(self.root, bg=WIN95_COLORS['bg'], relief='raised', bd=2)
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=25)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 8)).pack(side='left', padx=2)
        tk.Label(title_bar, text="LOGIN DO SISTEMA", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        logo_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        logo_frame.pack(pady=20)

        tk.Label(logo_frame, text="╔═══════════════════════════╗", 
                bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['blue'], font=('Courier', 10)).pack()
        tk.Label(logo_frame, text="║      PDV WINDOWS 95       ║", 
                bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['blue'], font=('Courier', 10, 'bold')).pack()
        tk.Label(logo_frame, text="║   Sistema de Vendas v1.0  ║", 
                bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['blue'], font=('Courier', 10)).pack()
        tk.Label(logo_frame, text="╚═══════════════════════════╝", 
                bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['blue'], font=('Courier', 10)).pack()

        form_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Usuario:", bg=WIN95_COLORS['bg'], 
                font=('MS Sans Serif', 9)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.user_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.user_var, width=20, 
                relief='sunken', bd=2, font=('MS Sans Serif', 9)).grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="Senha:", bg=WIN95_COLORS['bg'], 
                font=('MS Sans Serif', 9)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.pass_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.pass_var, show="*", width=20, 
                relief='sunken', bd=2, font=('MS Sans Serif', 9)).grid(row=1, column=1, padx=5)

        btn_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="ENTRAR", command=self.login,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold'), padx=20).pack(side='left', padx=5)

        tk.Button(btn_frame, text="SAIR", command=self.root.quit,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), padx=20).pack(side='left', padx=5)

        tk.Label(main_container, text="Usuario padrao: admin / admin123", 
                bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['shadow'],
                font=('MS Sans Serif', 8)).pack(pady=5)

        self.root.bind('<Return>', lambda e: self.login())

    def login(self):
        user = self.user_var.get().strip()
        password = self.pass_var.get().strip()

        if not user or not password:
            messagebox.showerror("Erro", "Preencha usuario e senha!")
            return

        usuario = self.db.verify_login(user, password)
        if usuario:
            self.usuario_logado = usuario
            self.root.destroy()
        else:
            messagebox.showerror("Erro", "Usuario ou senha invalidos!")
            self.pass_var.set('')


class PDVSystem:
    def __init__(self, root, db, usuario):
        self.root = root
        self.db = db
        self.usuario = usuario
        self.itens_venda = []
        self.total_venda = 0.0
        self.cliente_selecionado = None
        self.caixa_aberto = None

        self.root.title("PDV Windows 95 - Sistema de Vendas")
        self.root.geometry("1024x768")
        self.root.configure(bg=WIN95_COLORS['bg'])
        self.root.state('zoomed')

        self.verificar_caixa()
        self.create_interface()
        self.root.bind('<Key>', self.on_key_press)

    def verificar_caixa(self):
        self.caixa_aberto = self.db.get_caixa_aberto()
        if not self.caixa_aberto:
            messagebox.showwarning("Aviso", "Caixa fechado! Abra o caixa antes de iniciar vendas.")

    def create_interface(self):
        # Container principal
        main_container = tk.Frame(self.root, bg=WIN95_COLORS['bg'])
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Barra de titulo estilo Windows 95
        title_bar = tk.Frame(main_container, bg=WIN95_COLORS['blue'], height=30)
        title_bar.pack(fill='x', side='top')
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text='■', bg=WIN95_COLORS['blue'], 
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 10)).pack(side='left', padx=3)
        tk.Label(title_bar, text=f"PDV WINDOWS 95 - Operador: {self.usuario[3]} ({self.usuario[4]})", 
                bg=WIN95_COLORS['blue'], fg=WIN95_COLORS['white'],
                font=('MS Sans Serif', 10, 'bold')).pack(side='left', padx=5)

        # Status do caixa
        status_text = "CAIXA ABERTO" if self.caixa_aberto else "CAIXA FECHADO"
        status_color = WIN95_COLORS['green'] if self.caixa_aberto else WIN95_COLORS['red']
        self.lbl_status_caixa = tk.Label(title_bar, text=status_text, 
                                        bg=WIN95_COLORS['blue'], fg=status_color,
                                        font=('MS Sans Serif', 9, 'bold'))
        self.lbl_status_caixa.pack(side='right', padx=10)

        # Menu principal
        menu_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        menu_frame.pack(fill='x', pady=5)

        menus = [
            ("Cadastros", self.menu_cadastros),
            ("Movimentos", self.menu_movimentos),
            ("Relatorios", self.menu_relatorios),
            ("Utilitarios", self.menu_utilitarios),
            ("Sair", self.sair)
        ]

        for texto, comando in menus:
            tk.Button(menu_frame, text=texto, command=comando,
                     bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                     font=('MS Sans Serif', 9), padx=15).pack(side='left', padx=2)

        # Area principal
        content_frame = tk.Frame(main_container, bg=WIN95_COLORS['bg'])
        content_frame.pack(fill='both', expand=True, pady=5)

        # Painel esquerdo - Entrada de produtos
        left_panel = tk.LabelFrame(content_frame, text=" VENDA ", 
                                  font=('MS Sans Serif', 10, 'bold'),
                                  bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                  relief='raised', bd=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=5)

        # Entrada de codigo
        input_frame = tk.Frame(left_panel, bg=WIN95_COLORS['bg'])
        input_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(input_frame, text="Codigo de Barras:", bg=WIN95_COLORS['bg'],
                font=('MS Sans Serif', 10)).pack(side='left')
        self.codigo_var = tk.StringVar()
        self.entry_codigo = tk.Entry(input_frame, textvariable=self.codigo_var, 
                                    font=('Courier', 14), width=25,
                                    relief='sunken', bd=2)
        self.entry_codigo.pack(side='left', padx=10)
        self.entry_codigo.focus()

        tk.Button(input_frame, text="Adicionar", command=self.adicionar_produto,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9, 'bold')).pack(side='left', padx=5)

        # Lista de itens
        cols = ('codigo', 'nome', 'qtd', 'preco', 'total')
        self.tree_itens = ttk.Treeview(left_panel, columns=cols, show='headings', height=15)

        self.tree_itens.heading('codigo', text='CODIGO')
        self.tree_itens.heading('nome', text='PRODUTO')
        self.tree_itens.heading('qtd', text='QTD')
        self.tree_itens.heading('preco', text='PRECO')
        self.tree_itens.heading('total', text='TOTAL')

        self.tree_itens.column('codigo', width=120, anchor='center')
        self.tree_itens.column('nome', width=250)
        self.tree_itens.column('qtd', width=60, anchor='center')
        self.tree_itens.column('preco', width=80, anchor='e')
        self.tree_itens.column('total', width=80, anchor='e')

        scroll = ttk.Scrollbar(left_panel, orient="vertical", command=self.tree_itens.yview)
        self.tree_itens.configure(yscrollcommand=scroll.set)

        self.tree_itens.pack(side='left', fill='both', expand=True, padx=10, pady=5)
        scroll.pack(side='right', fill='y', pady=5)

        # Painel direito - Total e pagamento
        right_panel = tk.Frame(content_frame, bg=WIN95_COLORS['bg'])
        right_panel.pack(side='right', fill='y', padx=5)

        # Display do total
        total_frame = tk.LabelFrame(right_panel, text=" TOTAL A PAGAR ", 
                                   font=('MS Sans Serif', 12, 'bold'),
                                   bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['red'],
                                   relief='raised', bd=2)
        total_frame.pack(fill='x', pady=10)

        self.lbl_total = tk.Label(total_frame, text="R$ 0,00", 
                                 font=('Courier', 24, 'bold'),
                                 bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['red'])
        self.lbl_total.pack(pady=20)

        # Botoes de acao
        acoes_frame = tk.LabelFrame(right_panel, text=" ACOES ", 
                                   font=('MS Sans Serif', 10, 'bold'),
                                   bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                   relief='raised', bd=2)
        acoes_frame.pack(fill='x', pady=10)

        botoes = [
            ("FINALIZAR (F2)", self.finalizar_venda, WIN95_COLORS['green']),
            ("CANCELAR (Del)", self.cancelar_venda, WIN95_COLORS['red']),
            ("REMOVER ITEM", self.remover_item, WIN95_COLORS['button_bg']),
            ("BUSCAR PRODUTO", self.buscar_produto, WIN95_COLORS['button_bg']),
        ]

        for texto, comando, cor in botoes:
            tk.Button(acoes_frame, text=texto, command=comando,
                     bg=cor, relief='raised', bd=2,
                     font=('MS Sans Serif', 9, 'bold'), 
                     width=18, height=2).pack(pady=3)

        # Formas de pagamento
        pag_frame = tk.LabelFrame(right_panel, text=" FORMA DE PAGAMENTO ", 
                                 font=('MS Sans Serif', 10, 'bold'),
                                 bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                 relief='raised', bd=2)
        pag_frame.pack(fill='x', pady=10)

        self.forma_pag = tk.StringVar(value="dinheiro")
        formas = [
            ("Dinheiro", "dinheiro"),
            ("Credito", "credito"),
            ("Debito", "debito"),
            ("PIX", "pix"),
            ("Fiado", "fiado")
        ]

        for texto, valor in formas:
            tk.Radiobutton(pag_frame, text=texto, variable=self.forma_pag, 
                          value=valor, bg=WIN95_COLORS['bg'],
                          font=('MS Sans Serif', 9)).pack(anchor='w', padx=10)

        # Barra de status
        status_bar = tk.Frame(main_container, bg=WIN95_COLORS['bg'], relief='sunken', bd=1)
        status_bar.pack(fill='x', side='bottom', pady=2)

        self.lbl_status = tk.Label(status_bar, text="Pronto", 
                                  bg=WIN95_COLORS['bg'], fg=WIN95_COLORS['text'],
                                  font=('MS Sans Serif', 9))
        self.lbl_status.pack(side='left', padx=5)

    def menu_cadastros(self):
        menu = tk.Toplevel(self.root)
        menu.title("Cadastros")
        menu.geometry("200x250")
        menu.configure(bg=WIN95_COLORS['bg'])
        menu.resizable(False, False)
        menu.transient(self.root)

        tk.Label(menu, text="CADASTROS", bg=WIN95_COLORS['blue'],
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 10, 'bold')).pack(fill='x')

        botoes = [
            ("Produtos", lambda: CadastroProdutos(self.root, self.db)),
            ("Clientes", lambda: CadastroClientes(self.root, self.db)),
            ("Usuarios", lambda: CadastroUsuarios(self.root, self.db)),
        ]

        for texto, comando in botoes:
            tk.Button(menu, text=texto, command=comando,
                     bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                     font=('MS Sans Serif', 9), width=15).pack(pady=5)

        tk.Button(menu, text="Fechar", command=menu.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(pady=10)

    def menu_movimentos(self):
        ControleCaixa(self.root, self.db, self.usuario[0])

    def menu_relatorios(self):
        menu = tk.Toplevel(self.root)
        menu.title("Relatorios")
        menu.geometry("200x200")
        menu.configure(bg=WIN95_COLORS['bg'])
        menu.resizable(False, False)
        menu.transient(self.root)

        tk.Label(menu, text="RELATORIOS", bg=WIN95_COLORS['blue'],
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 10, 'bold')).pack(fill='x')

        tk.Button(menu, text="Vendas", command=lambda: RelatorioVendas(self.root, self.db),
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), width=15).pack(pady=5)

        tk.Button(menu, text="Contas a Receber", command=lambda: ContasReceber(self.root, self.db),
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), width=15).pack(pady=5)

        tk.Button(menu, text="Estoque", command=lambda: ConsultaEstoque(self.root, self.db),
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), width=15).pack(pady=5)

        tk.Button(menu, text="Fechar", command=menu.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(pady=10)

    def menu_utilitarios(self):
        menu = tk.Toplevel(self.root)
        menu.title("Utilitarios")
        menu.geometry("200x200")
        menu.configure(bg=WIN95_COLORS['bg'])
        menu.resizable(False, False)
        menu.transient(self.root)

        tk.Label(menu, text="UTILITARIOS", bg=WIN95_COLORS['blue'],
                fg=WIN95_COLORS['white'], font=('MS Sans Serif', 10, 'bold')).pack(fill='x')

        tk.Button(menu, text="Configuracoes", command=lambda: ConfiguracoesSistema(self.root, self.db),
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), width=15).pack(pady=5)

        tk.Button(menu, text="Backup", command=lambda: BackupRestauracao(self.root, self.db),
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9), width=15).pack(pady=5)

        tk.Button(menu, text="Fechar", command=menu.destroy,
                 bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                 font=('MS Sans Serif', 9)).pack(pady=10)

    def sair(self):
        if messagebox.askyesno("Confirmar", "Deseja realmente sair?"):
            self.root.quit()

    def on_key_press(self, event):
        if event.keysym == 'F2':
            self.finalizar_venda()
        elif event.keysym == 'Delete':
            self.cancelar_venda()
        elif event.keysym == 'Return' and event.widget == self.entry_codigo:
            self.adicionar_produto()

    def adicionar_produto(self):
        codigo = self.codigo_var.get().strip()
        if not codigo:
            return

        produto = self.db.get_produto_by_codigo(codigo)
        if not produto:
            messagebox.showerror("Erro", "Produto nao encontrado!")
            self.codigo_var.set('')
            return

        if produto[4] <= 0:
            messagebox.showerror("Erro", "Produto sem estoque!")
            self.codigo_var.set('')
            return

        # Verificar se ja existe na lista
        for i, item in enumerate(self.itens_venda):
            if item['produto_id'] == produto[0]:
                self.itens_venda[i]['quantidade'] += 1
                self.itens_venda[i]['total'] = self.itens_venda[i]['quantidade'] * item['preco']
                self.atualizar_tabela()
                self.codigo_var.set('')
                self.entry_codigo.focus()
                return

        # Adicionar novo item
        self.itens_venda.append({
            'produto_id': produto[0],
            'codigo': produto[1],
            'nome': produto[2],
            'preco': produto[3],
            'quantidade': 1,
            'total': produto[3]
        })

        self.atualizar_tabela()
        self.codigo_var.set('')
        self.entry_codigo.focus()

    def atualizar_tabela(self):
        for item in self.tree_itens.get_children():
            self.tree_itens.delete(item)

        self.total_venda = 0
        for item in self.itens_venda:
            self.tree_itens.insert('', 'end', values=(
                item['codigo'],
                item['nome'],
                item['quantidade'],
                f"R$ {item['preco']:.2f}",
                f"R$ {item['total']:.2f}"
            ))
            self.total_venda += item['total']

        self.lbl_total.config(text=f"R$ {self.total_venda:.2f}")

    def remover_item(self):
        selecionado = self.tree_itens.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um item para remover!")
            return

        indice = self.tree_itens.index(selecionado[0])
        del self.itens_venda[indice]
        self.atualizar_tabela()

    def buscar_produto(self):
        ConsultaEstoque(self.root, self.db)

    def cancelar_venda(self):
        if messagebox.askyesno("Confirmar", "Cancelar venda atual?"):
            self.itens_venda = []
            self.atualizar_tabela()
            self.lbl_status.config(text="Venda cancelada")

    def finalizar_venda(self):
        if not self.itens_venda:
            messagebox.showwarning("Aviso", "Adicione produtos antes de finalizar!")
            return

        if not self.caixa_aberto:
            messagebox.showerror("Erro", "Caixa fechado! Abra o caixa primeiro.")
            return

        forma = self.forma_pag.get()
        cliente_id = None

        if forma == 'fiado':
            # Selecionar cliente
            clientes = self.db.get_all_clientes()
            if not clientes:
                messagebox.showerror("Erro", "Nenhum cliente cadastrado!")
                return

            janela = tk.Toplevel(self.root)
            janela.title("Selecionar Cliente")
            janela.geometry("400x300")
            janela.configure(bg=WIN95_COLORS['bg'])
            janela.resizable(False, False)
            janela.transient(self.root)
            janela.grab_set()

            tk.Label(janela, text="SELECIONE O CLIENTE", bg=WIN95_COLORS['blue'],
                    fg=WIN95_COLORS['white'], font=('MS Sans Serif', 10, 'bold')).pack(fill='x')

            cols = ('id', 'nome', 'fiado')
            tree = ttk.Treeview(janela, columns=cols, show='headings', height=10)
            tree.heading('id', text='ID')
            tree.heading('nome', text='NOME')
            tree.heading('fiado', text='FIADO ATUAL')
            tree.column('id', width=50, anchor='center')
            tree.column('nome', width=200)
            tree.column('fiado', width=100, anchor='e')
            tree.pack(padx=10, pady=10, fill='both', expand=True)

            for c in clientes:
                tree.insert('', 'end', values=(c[0], c[1], f"R$ {c[4]:.2f}"))

            def selecionar():
                sel = tree.selection()
                if sel:
                    nonlocal cliente_id
                    cliente_id = tree.item(sel[0])['values'][0]
                    janela.destroy()

            tk.Button(janela, text="SELECIONAR", command=selecionar,
                     bg=WIN95_COLORS['button_bg'], relief='raised', bd=2,
                     font=('MS Sans Serif', 9, 'bold')).pack(pady=10)

            self.root.wait_window(janela)

            if not cliente_id:
                return

        venda_data = {
            'usuario_id': self.usuario[0],
            'total': self.total_venda,
            'forma_pagamento': forma,
            'itens': self.itens_venda,
            'cliente_id': cliente_id
        }

        try:
            venda_id, numero_cupom = self.db.save_venda(venda_data)
            messagebox.showinfo("Sucesso", f"Venda finalizada!\nCupom: {numero_cupom}")
            self.itens_venda = []
            self.atualizar_tabela()
            self.lbl_status.config(text=f"Venda {numero_cupom} finalizada")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar venda: {str(e)}")

# ============ INICIALIZACAO ============
if __name__ == "__main__":
    root = tk.Tk()
    login = LoginScreen(root)
    root.mainloop()

    if login.usuario_logado:
        root = tk.Tk()
        app = PDVSystem(root, login.db, login.usuario_logado)
        root.mainloop()
