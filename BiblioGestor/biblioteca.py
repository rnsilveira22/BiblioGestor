import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date, timedelta
import os
import logging
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── BANCO DE DADOS ────────────────────────────────────────────────────────────

DB_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biblioteca.db")
PRAZO_DIAS = 14

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS livros (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            numero        TEXT,
            titulo        TEXT NOT NULL,
            autor         TEXT NOT NULL,
            pelo_espirito TEXT,
            categoria     TEXT,
            exemplares    INTEGER DEFAULT 1,
            disponivel    INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS associados (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      TEXT NOT NULL,
            tipo      TEXT DEFAULT 'Associado',
            matricula TEXT,
            telefone  TEXT,
            email     TEXT,
            ativo     INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS dependentes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            associado_id  INTEGER NOT NULL,
            nome          TEXT NOT NULL,
            parentesco    TEXT,
            telefone      TEXT,
            email         TEXT,
            ativo         INTEGER DEFAULT 1,
            FOREIGN KEY(associado_id) REFERENCES associados(id)
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      TEXT NOT NULL,
            usuario   TEXT NOT NULL UNIQUE,
            senha     TEXT NOT NULL,
            tipo      TEXT DEFAULT 'Operador',
            ativo     INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS emprestimos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            livro_id        INTEGER NOT NULL,
            associado_id    INTEGER,
            dependente_id  INTEGER,
            data_emprestimo TEXT NOT NULL,
            data_prevista   TEXT NOT NULL,
            data_devolucao  TEXT,
            FOREIGN KEY(livro_id)    REFERENCES livros(id),
            FOREIGN KEY(associado_id) REFERENCES associados(id),
            FOREIGN KEY(dependente_id) REFERENCES dependentes(id)
        );
        CREATE INDEX IF NOT EXISTS idx_emprestimos_devolucao ON emprestimos(data_devolucao, data_prevista);
        CREATE INDEX IF NOT EXISTS idx_livros_titulo ON livros(titulo);
        CREATE INDEX IF NOT EXISTS idx_associados_nome ON associados(nome);
        CREATE INDEX IF NOT EXISTS idx_dependentes_nome ON dependentes(nome);
        CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(usuario);
        """)
    migrate_db()

def migrate_db():
    with get_conn() as c:
        tabelas = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

        # Migração antiga: usuarios -> associados
        if "usuarios" in tabelas and "associados" in tabelas:
            count = c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
            if count > 0:
                c.execute("""INSERT OR IGNORE INTO associados(id,nome,tipo,telefone,email,ativo)
                             SELECT id,nome,tipo,'','',ativo FROM usuarios""")

        # Adicionar coluna associado_id se não existir
        cols_emp = [r[1] for r in c.execute("PRAGMA table_info(emprestimos)").fetchall()]
        if "usuario_id" in cols_emp and "associado_id" not in cols_emp:
            c.execute("ALTER TABLE emprestimos ADD COLUMN associado_id INTEGER")
            c.execute("UPDATE emprestimos SET associado_id = usuario_id WHERE associado_id IS NULL")
        if "associado_id" not in cols_emp:
            c.execute("ALTER TABLE emprestimos ADD COLUMN associado_id INTEGER")
        if "dependente_id" not in cols_emp:
            c.execute("ALTER TABLE emprestimos ADD COLUMN dependente_id INTEGER")

        # Adicionar colunas em livros se não existirem
        cols_liv = [r[1] for r in c.execute("PRAGMA table_info(livros)").fetchall()]
        if "numero" not in cols_liv:
            c.execute("ALTER TABLE livros ADD COLUMN numero TEXT")
        if "pelo_espirito" not in cols_liv:
            c.execute("ALTER TABLE livros ADD COLUMN pelo_espirito TEXT")

        # Criar tabela dependentes se não existir
        c.execute("""
            CREATE TABLE IF NOT EXISTS dependentes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                associado_id  INTEGER NOT NULL,
                nome          TEXT NOT NULL,
                parentesco    TEXT,
                telefone      TEXT,
                email         TEXT,
                ativo         INTEGER DEFAULT 1,
                FOREIGN KEY(associado_id) REFERENCES associados(id)
            )
        """)

        # Criar tabela usuarios (acesso ao sistema) se não existir
        c.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT NOT NULL,
                usuario   TEXT NOT NULL UNIQUE,
                senha     TEXT NOT NULL,
                tipo      TEXT DEFAULT 'Operador',
                ativo     INTEGER DEFAULT 1
            )
        """)

        # Criar usuário admin padrão se não houver nenhum usuário
        count_usuarios = c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if count_usuarios == 0:
            c.execute("INSERT INTO usuarios(nome, usuario, senha, tipo) VALUES(?,?,?,?)",
                      ("Administrador", "admin", "admin123", "Administrador"))

        c.execute("CREATE INDEX IF NOT EXISTS idx_emprestimos_devolucao ON emprestimos(data_devolucao, data_prevista)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_livros_titulo ON livros(titulo)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_associados_nome ON associados(nome)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_dependentes_nome ON dependentes(nome)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(usuario)")

# ─── UTILITÁRIOS ───────────────────────────────────────────────────────────────

def hoje():
    return date.today().strftime("%Y-%m-%d")

def fmt(d):
    if not d:
        return ""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return d


# ─── ESTILO GLOBAL ─────────────────────────────────────────────────────────────

# Paleta Verde Oliva
COR_FUNDO    = "#2d3319"
COR_PAINEL   = "#3a4420"
COR_CARD     = "#4a5530"
COR_AZUL     = "#6b8e23"
COR_VERDE    = "#556b2f"
COR_LARANJA  = "#8b9a5b"
COR_VERMELHO = "#8b4513"
COR_TEXTO    = "#f5f5dc"
COR_SUBTEXTO = "#b8b884"
FONTE        = ("Segoe UI", 10)
FONTE_BOLD   = ("Segoe UI", 10, "bold")
FONTE_TITULO = ("Segoe UI", 14, "bold")

def style_btn(btn, cor=COR_AZUL):
    btn.config(bg=cor, fg="white", relief="flat", font=FONTE_BOLD,
               activebackground=cor, activeforeground="white",
               padx=14, pady=6, cursor="hand2", bd=0)

def entry_widget(parent, **kw):
    return tk.Entry(parent, bg=COR_CARD, fg=COR_TEXTO, insertbackground=COR_TEXTO,
                    relief="flat", font=FONTE, **kw)

def label(parent, text, cor=COR_TEXTO, bold=False, font=None, **kw):
    f = font if font else (FONTE_BOLD if bold else FONTE)
    return tk.Label(parent, text=text, bg=parent["bg"], fg=cor, font=f, **kw)

# ─── LOGIN ──────────────────────────────────────────────────────────────────

class LoginFrame(tk.Frame):
    def __init__(self, parent, on_success):
        super().__init__(parent, bg=COR_FUNDO)
        self.parent = parent
        self.on_success = on_success
        self._build()

    def _build(self):
        center = tk.Frame(self, bg=COR_PAINEL)
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="📚", font=("Segoe UI", 48), bg=COR_PAINEL,
                 fg=COR_AZUL).pack(pady=(40, 10))
        tk.Label(center, text="BiblioGestor", font=("Segoe UI", 16, "bold"),
                 bg=COR_PAINEL, fg=COR_TEXTO).pack()
        tk.Label(center, text="Gestão de Biblioteca - Casa Espírita Joana Lima",
                 font=("Segoe UI", 8), bg=COR_PAINEL, fg=COR_SUBTEXTO).pack(pady=(0, 30))

        f = tk.Frame(center, bg=COR_PAINEL)
        f.pack()

        tk.Label(f, text="Usuário:", bg=COR_PAINEL, fg=COR_TEXTO, font=FONTE).grid(row=0, column=0, sticky="e", padx=(0, 8), pady=6)
        self.usuario_var = tk.StringVar()
        e1 = entry_widget(f, textvariable=self.usuario_var, width=20)
        e1.grid(row=0, column=1, pady=6)
        e1.focus()

        tk.Label(f, text="Senha:", bg=COR_PAINEL, fg=COR_TEXTO, font=FONTE).grid(row=1, column=0, sticky="e", padx=(0, 8), pady=6)
        self.senha_var = tk.StringVar()
        e2 = tk.Entry(f, textvariable=self.senha_var, width=20, show="*",
                      bg=COR_CARD, fg=COR_TEXTO, insertbackground=COR_TEXTO,
                      relief="flat", font=FONTE)
        e2.grid(row=1, column=1, pady=6)

        e2.bind("<Return>", lambda e: self._login())

        b = tk.Button(f, text="Entrar", command=self._login, width=15)
        style_btn(b, COR_VERDE)
        b.grid(row=2, column=0, columnspan=2, pady=20)

    def _login(self):
        usuario = self.usuario_var.get().strip()
        senha = self.senha_var.get().strip()
        with get_conn() as c:
            row = c.execute("SELECT id, nome, tipo FROM usuarios WHERE usuario=? AND senha=? AND ativo=1",
                           (usuario, senha)).fetchone()
        if row:
            self.on_success({"id": row[0], "nome": row[1], "tipo": row[2]})
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.", parent=self)

# ─── JANELA PRINCIPAL ──────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚 BiblioGestor - Casa Espírita Joana Lima")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(bg=COR_FUNDO)
        _style_tree()
        init_db()
        self.usuario_logado = None
        self._build_login()

    def _build_login(self):
        self.login_frame = LoginFrame(self, self._on_login_success)
        self.login_frame.pack(fill="both", expand=True)

    def _on_login_success(self, user_data):
        self.usuario_logado = user_data
        self.login_frame.destroy()
        self._build_main_ui()

    def _build_main_ui(self):
        self.bg_label = None
        if PIL_AVAILABLE:
            img_path = os.path.join(os.path.dirname(__file__), "imagens", "fundo.jpg")
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img = img.resize((1100, 680), Image.LANCZOS)
                    self.bg_photo = ImageTk.PhotoImage(img)
                    self.bg_label = tk.Label(self, image=self.bg_photo)
                    self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                except Exception as e:
                    logger.warning("Erro ao carregar imagem de fundo: %s", e)

        sidebar = tk.Frame(self, bg=COR_PAINEL, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="📚", font=("Segoe UI", 32), bg=COR_PAINEL,
                 fg=COR_AZUL).pack(pady=(28, 4))
        tk.Label(sidebar, text="BiblioGestor", font=("Segoe UI", 13, "bold"),
                 bg=COR_PAINEL, fg=COR_TEXTO).pack()
        tk.Label(sidebar, text="Gestão de Biblioteca", font=("Segoe UI", 8),
                 bg=COR_PAINEL, fg=COR_SUBTEXTO).pack(pady=(0, 24))
        tk.Label(sidebar, text="Casa Espírita Joana Lima", font=("Segoe UI", 7),
                 bg=COR_PAINEL, fg=COR_SUBTEXTO).pack(pady=(0, 16))
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=16, pady=4)

        tk.Label(sidebar, text=f"👤 {self.usuario_logado['nome']}",
                 bg=COR_PAINEL, fg=COR_SUBTEXTO, font=("Segoe UI", 8)).pack(pady=(0, 8))
        tk.Label(sidebar, text=f"({self.usuario_logado['tipo']})",
                 bg=COR_PAINEL, fg=COR_SUBTEXTO, font=("Segoe UI", 8)).pack(pady=(0, 16))

        self.frames = {}
        self.nav_buttons = {}

        menus = [
            ("🏠  Painel",        PainelFrame),
            ("📖  Livros",        LivrosFrame),
            ("👤  Associados",    AssociadosFrame),
            ("👥  Dependentes",   DependentesFrame),
            ("🔄  Empréstimos",   EmprestimosFrame),
            ("↩️  Devoluções",    DevolucoesFrame),
            ("📊  Relatórios",    RelatoriosFrame),
        ]

        if self.usuario_logado['tipo'] == 'Administrador':
            menus.append(("🔑  Usuários", UsuariosFrame))

        menus.append(("🚪  Sair", "logout"))

        self.content = tk.Frame(self, bg=COR_FUNDO)
        self.content.pack(side="left", fill="both", expand=True)

        for name, FrameClass in menus:
            if isinstance(FrameClass, type):
                try:
                    f = FrameClass(self.content, self)
                    f.place(relwidth=1, relheight=1)
                    self.frames[name] = f
                    logger.info("Frame criado: %s", name)
                except Exception as e:
                    logger.error("Erro ao criar frame %s: %s", name, e)

        def nav(name):
            logger.info("Navegando para: %s", name)
            if name == "🚪  Sair":
                if messagebox.askyesno("Sair", "Deseja sair do BiblioGestor?"):
                    self.destroy()
                return
            if name in self.frames:
                self.frames[name].tkraise()
                if hasattr(self.frames[name], "refresh"):
                    self.frames[name].refresh()
            for menu_name, btn in self.nav_buttons.items():
                btn.config(bg=COR_AZUL if menu_name == name else COR_PAINEL)

        for name, _ in menus:
            b = tk.Button(sidebar, text=name, anchor="w",
                          command=lambda n=name: nav(n),
                          bg=COR_PAINEL, fg=COR_TEXTO, font=FONTE,
                          relief="flat", padx=20, pady=10,
                          activebackground=COR_AZUL, activeforeground="white",
                          cursor="hand2", bd=0)
            b.pack(fill="x")
            self.nav_buttons[name] = b

        nav("🏠  Painel")

# ─── PAINEL ────────────────────────────────────────────────────────────────────

class PainelFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._build()

    def _build(self):
        label(self, "Painel Geral", bold=True, font=FONTE_TITULO).pack(anchor="w", padx=30, pady=(24, 4))
        label(self, f"Bem-vindo! Hoje é {date.today().strftime('%d/%m/%Y')}",
              cor=COR_SUBTEXTO).pack(anchor="w", padx=30, pady=(0, 20))
        self.cards_frame = tk.Frame(self, bg=COR_FUNDO)
        self.cards_frame.pack(fill="x", padx=30)
        self.alertas = tk.Frame(self, bg=COR_FUNDO)
        self.alertas.pack(fill="both", expand=True, padx=30, pady=16)

    def refresh(self):
        for w in self.cards_frame.winfo_children(): w.destroy()
        for w in self.alertas.winfo_children():     w.destroy()

        with get_conn() as c:
            tot_livros   = c.execute("SELECT COUNT(*) FROM livros").fetchone()[0]
            tot_assoc    = c.execute("SELECT COUNT(*) FROM associados WHERE ativo=1").fetchone()[0]
            em_aberto    = c.execute("SELECT COUNT(*) FROM emprestimos WHERE data_devolucao IS NULL").fetchone()[0]
            atrasados    = c.execute(
                "SELECT COUNT(*) FROM emprestimos WHERE data_devolucao IS NULL AND data_prevista < ?",
                (hoje(),)).fetchone()[0]

        cards = [
            ("📚 Livros\nCadastrados",   tot_livros,  COR_AZUL),
            ("👤 Associados\nAtivos",    tot_assoc,   COR_VERDE),
            ("🔄 Empréstimos\nAbertos",  em_aberto,   COR_LARANJA),
            ("⚠️ Em Atraso",            atrasados,   COR_VERMELHO),
        ]

        for i, (titulo, valor, cor) in enumerate(cards):
            card = tk.Frame(self.cards_frame, bg=cor, padx=20, pady=16)
            card.grid(row=0, column=i, padx=8, pady=4, sticky="ew")
            self.cards_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=str(valor), font=("Segoe UI", 22, "bold"), bg=cor, fg="white").pack()
            tk.Label(card, text=titulo, font=("Segoe UI", 9), bg=cor, fg="white").pack()

        label(self.alertas, "⚠️  Empréstimos em Atraso", bold=True,
              font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8, 6))

        cols = ("Livro", "Associado", "Prevista", "Dias em Atraso")
        tv = ttk.Treeview(self.alertas, columns=cols, show="headings", height=8)
        for col in cols:
            tv.heading(col, text=col)
            tv.column(col, width=220 if col in ("Livro", "Associado") else 120, anchor="center")

        with get_conn() as c:
            rows = c.execute("""
                SELECT l.titulo, a.nome, e.data_prevista
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.data_devolucao IS NULL AND e.data_prevista < ?
                ORDER BY e.data_prevista
            """, (hoje(),)).fetchall()

        for titulo, nome, prev in rows:
            dias = (date.today() - datetime.strptime(prev, "%Y-%m-%d").date()).days
            tv.insert("", "end", values=(titulo, nome, fmt(prev), f"{dias} dias"))

        sb = ttk.Scrollbar(self.alertas, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

# ─── LIVROS ────────────────────────────────────────────────────────────────────

class LivrosFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._sort_col = None
        self._sort_rev = False
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "📖  Gerenciar Livros", bold=True, font=FONTE_TITULO).pack(side="left")

        btn_frame = tk.Frame(top, bg=COR_FUNDO)
        btn_frame.pack(side="right")
        for txt, cmd, cor in [("＋  Novo Livro", self._novo, COR_VERDE),
                               ("✏️  Editar",    self._editar, COR_AZUL),
                               ("🗑  Excluir",   self._excluir, COR_VERMELHO)]:
            b = tk.Button(btn_frame, text=txt, command=cmd)
            style_btn(b, cor)
            b.pack(side="left", padx=4)

        busca_frame = tk.Frame(self, bg=COR_FUNDO)
        busca_frame.pack(fill="x", padx=30, pady=(0, 8))
        label(busca_frame, "🔍 Buscar:").pack(side="left", padx=(0, 6))
        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self.refresh())
        entry_widget(busca_frame, textvariable=self.busca_var, width=40).pack(side="left")

        cols = ("ID", "Número", "Título", "Autor", "Pelo Espírito", "Categoria", "Exemplares", "Disponíveis")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=20)
        widths = [40, 80, 240, 180, 160, 120, 80, 80]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col, command=lambda c=col: self._sort(c))
            self.tv.column(col, width=w, anchor="w" if col in ("Título", "Autor", "Pelo Espírito") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 20))
        sb.pack(side="left", fill="y", pady=(0, 20), padx=(0, 10))

    def _sort(self, col):
        self._sort_rev = not self._sort_rev if self._sort_col == col else False
        self._sort_col = col
        self.refresh()

    def refresh(self):
        q = self.busca_var.get().strip().lower() if hasattr(self, "busca_var") else ""
        self.tv.delete(*self.tv.get_children())
        with get_conn() as c:
            if q:
                rows = c.execute(
                    "SELECT id, numero, titulo, autor, pelo_espirito, categoria, exemplares, disponivel FROM livros "
                    "WHERE LOWER(titulo) LIKE ? OR LOWER(autor) LIKE ? OR LOWER(categoria) LIKE ? OR LOWER(numero) LIKE ?",
                    (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT id, numero, titulo, autor, pelo_espirito, categoria, exemplares, disponivel FROM livros"
                ).fetchall()
        if self._sort_col:
            idx = ["ID","Número","Título","Autor","Pelo Espírito","Categoria","Exemplares","Disponíveis"].index(self._sort_col)
            rows.sort(key=lambda r: str(r[idx]).lower(), reverse=self._sort_rev)
        for r in rows:
            self.tv.insert("", "end", values=r)

    def _form(self, dados=None):
        win = _modal(self, "Livro")
        campos = [
            ("Número do Livro", "numero"),
            ("Título*",         "titulo"),
            ("Autor*",          "autor"),
            ("Pelo Espírito",   "pelo_espirito"),
            ("Categoria",       "categoria"),
            ("Nº de Exemplares","exemplares"),
        ]
        entries = {}
        for i, (lbl, key) in enumerate(campos):
            tk.Label(win, text=lbl, bg=COR_PAINEL, fg=COR_TEXTO,
                     font=FONTE).grid(row=i, column=0, sticky="w", padx=16, pady=6)
            e = entry_widget(win, width=36)
            e.grid(row=i, column=1, padx=(4, 16), pady=6)
            if dados:
                e.insert(0, dados.get(key, "") or "")
            entries[key] = e

        def salvar():
            t = entries["titulo"].get().strip()
            a = entries["autor"].get().strip()
            if not t or not a:
                messagebox.showwarning("Aviso", "Título e Autor são obrigatórios.", parent=win)
                return
            try:
                ex = int(entries["exemplares"].get() or 1)
            except (ValueError, TypeError):
                ex = 1
            with get_conn() as c:
                if dados:
                    c.execute("""UPDATE livros SET numero=?,titulo=?,autor=?,pelo_espirito=?,
                              categoria=?,exemplares=? WHERE id=?""",
                              (entries["numero"].get(), t, a,
                               entries["pelo_espirito"].get(),
                               entries["categoria"].get(), ex, dados["id"]))
                    logger.info("Livro ID=%d atualizado: '%s'", dados["id"], t)
                else:
                    cursor = c.execute("""INSERT INTO livros(numero,titulo,autor,pelo_espirito,
                              categoria,exemplares,disponivel) VALUES(?,?,?,?,?,?,?)""",
                              (entries["numero"].get(), t, a,
                               entries["pelo_espirito"].get(),
                               entries["categoria"].get(), ex, ex))
                    logger.info("Livro ID=%d criado: '%s'", cursor.lastrowid, t)
            win.destroy()
            self.refresh()

        b = tk.Button(win, text="💾  Salvar", command=salvar)
        style_btn(b, COR_VERDE)
        b.grid(row=len(campos), column=0, columnspan=2, pady=16)

    def _novo(self):    self._form()
    def _editar(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um livro.")
            return
        lid = self.tv.item(sel[0])["values"][0]
        with get_conn() as c:
            r = c.execute("SELECT * FROM livros WHERE id=?", (lid,)).fetchone()
        cols = ["id","numero","titulo","autor","pelo_espirito","categoria","exemplares","disponivel"]
        self._form(dict(zip(cols, r)))

    def _excluir(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um livro.")
            return
        lid = self.tv.item(sel[0])["values"][0]
        with get_conn() as c:
            emprestimos_ativos = c.execute(
                "SELECT COUNT(*) FROM emprestimos WHERE livro_id=? AND data_devolucao IS NULL", (lid,)
            ).fetchone()[0]
            if emprestimos_ativos > 0:
                messagebox.showwarning("Aviso", "Não é possível excluir um livro com empréstimos em aberto.")
                return
        if not messagebox.askyesno("Confirmar", "Excluir este livro?"):
            return
        with get_conn() as c:
            c.execute("DELETE FROM livros WHERE id=?", (lid,))
        logger.info("Livro ID=%d excluído", lid)
        self.refresh()

# ─── ASSOCIADOS ────────────────────────────────────────────────────────────────

class AssociadosFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "👤  Gerenciar Associados", bold=True, font=FONTE_TITULO).pack(side="left")

        btn_frame = tk.Frame(top, bg=COR_FUNDO)
        btn_frame.pack(side="right")
        for txt, cmd, cor in [("＋  Novo", self._novo, COR_VERDE),
                               ("✏️  Editar", self._editar, COR_AZUL),
                               ("🗑  Excluir", self._excluir, COR_VERMELHO)]:
            b = tk.Button(btn_frame, text=txt, command=cmd)
            style_btn(b, cor)
            b.pack(side="left", padx=4)

        busca_frame = tk.Frame(self, bg=COR_FUNDO)
        busca_frame.pack(fill="x", padx=30, pady=(0, 8))
        label(busca_frame, "🔍 Buscar:").pack(side="left", padx=(0, 6))
        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self.refresh())
        entry_widget(busca_frame, textvariable=self.busca_var, width=40).pack(side="left")

        cols = ("ID", "Nome", "Tipo", "Matrícula", "Telefone", "Email")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=20)
        widths = [40, 240, 120, 110, 130, 200]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Nome", "Email") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 20))
        sb.pack(side="left", fill="y", pady=(0, 20), padx=(0, 10))

    def refresh(self):
        q = self.busca_var.get().strip().lower() if hasattr(self, "busca_var") else ""
        self.tv.delete(*self.tv.get_children())
        if q:
            with get_conn() as c:
                rows = c.execute(
                    "SELECT id,nome,tipo,matricula,telefone,email FROM associados WHERE ativo=1 AND (LOWER(nome) LIKE ? OR LOWER(matricula) LIKE ?)",
                    (f"%{q}%", f"%{q}%")
                ).fetchall()
        else:
            with get_conn() as c:
                rows = c.execute(
                    "SELECT id,nome,tipo,matricula,telefone,email FROM associados WHERE ativo=1"
                ).fetchall()
        for r in rows:
            self.tv.insert("", "end", values=r)

    def _form(self, dados=None):
        win = _modal(self, "Associado")
        campos = [("Nome*", "nome"), ("Tipo", "tipo"), ("Matrícula", "matricula"),
                  ("Telefone", "telefone"), ("E-mail", "email")]
        entries = {}
        for i, (lbl, key) in enumerate(campos):
            tk.Label(win, text=lbl, bg=COR_PAINEL, fg=COR_TEXTO,
                     font=FONTE).grid(row=i, column=0, sticky="w", padx=16, pady=6)
            if key == "tipo":
                var = tk.StringVar(value=dados.get(key, "Associado") if dados else "Associado")
                cb = ttk.Combobox(win, textvariable=var,
                                  values=["Associado", "Professor", "Funcionário", "Visitante"],
                                  state="readonly", width=33, font=FONTE)
                cb.grid(row=i, column=1, padx=(4, 16), pady=6)
                entries[key] = var
            else:
                e = entry_widget(win, width=36)
                e.grid(row=i, column=1, padx=(4, 16), pady=6)
                if dados:
                    e.insert(0, dados.get(key, "") or "")
                entries[key] = e

        def salvar():
            nome = entries["nome"].get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Nome é obrigatório.", parent=win)
                return
            with get_conn() as c:
                if dados:
                    c.execute("UPDATE associados SET nome=?,tipo=?,matricula=?,telefone=?,email=? WHERE id=?",
                              (nome, entries["tipo"].get(), entries["matricula"].get(),
                               entries["telefone"].get(), entries["email"].get(), dados["id"]))
                    logger.info("Associado ID=%d atualizado: '%s'", dados["id"], nome)
                else:
                    cursor = c.execute("INSERT INTO associados(nome,tipo,matricula,telefone,email) VALUES(?,?,?,?,?)",
                              (nome, entries["tipo"].get(), entries["matricula"].get(),
                               entries["telefone"].get(), entries["email"].get()))
                    logger.info("Associado ID=%d criado: '%s'", cursor.lastrowid, nome)
            win.destroy()
            self.refresh()

        b = tk.Button(win, text="💾  Salvar", command=salvar)
        style_btn(b, COR_VERDE)
        b.grid(row=len(campos), column=0, columnspan=2, pady=16)

    def _novo(self):    self._form()
    def _editar(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um associado.")
            return
        uid = self.tv.item(sel[0])["values"][0]
        with get_conn() as c:
            r = c.execute("SELECT * FROM associados WHERE id=?", (uid,)).fetchone()
        cols = ["id","nome","tipo","matricula","telefone","email","ativo"]
        self._form(dict(zip(cols, r)))

    def _excluir(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um associado.")
            return
        uid = self.tv.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "Excluir este associado?"):
            return
        with get_conn() as c:
            c.execute("UPDATE associados SET ativo=0 WHERE id=?", (uid,))
        self.refresh()

# ─── DEPENDENTES ─────────────────────────────────────────────────────────────

class DependentesFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "👥  Gerenciar Dependentes", bold=True, font=FONTE_TITULO).pack(side="left")

        btn_frame = tk.Frame(top, bg=COR_FUNDO)
        btn_frame.pack(side="right")
        for txt, cmd, cor in [("＋  Novo", self._novo, COR_VERDE),
                               ("✏️  Editar", self._editar, COR_AZUL),
                               ("🗑  Excluir", self._excluir, COR_VERMELHO)]:
            b = tk.Button(btn_frame, text=txt, command=cmd)
            style_btn(b, cor)
            b.pack(side="left", padx=4)

        # Filtro por associado
        filtro_frame = tk.Frame(self, bg=COR_FUNDO)
        filtro_frame.pack(fill="x", padx=30, pady=(0, 8))
        label(filtro_frame, "Associado:").pack(side="left", padx=(0, 6))
        self.assoc_var = tk.StringVar()
        self.assoc_var.trace_add("write", lambda *_: self.refresh())
        entry_widget(filtro_frame, textvariable=self.assoc_var, width=30).pack(side="left", padx=(0, 12))
        label(filtro_frame, "🔍 Buscar:").pack(side="left", padx=(0, 6))
        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self.refresh())
        entry_widget(filtro_frame, textvariable=self.busca_var, width=30).pack(side="left")

        cols = ("ID", "Associado", "Nome", "Parentesco", "Telefone", "Email")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=20)
        widths = [40, 160, 200, 100, 130, 200]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Nome", "Email", "Associado") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 20))
        sb.pack(side="left", fill="y", pady=(0, 20), padx=(0, 10))

    def refresh(self):
        q = self.busca_var.get().strip().lower() if hasattr(self, "busca_var") else ""
        assoc_q = self.assoc_var.get().strip().lower() if hasattr(self, "assoc_var") else ""
        self.tv.delete(*self.tv.get_children())
        with get_conn() as c:
            rows = c.execute("""
                SELECT d.id, a.nome, d.nome, d.parentesco, d.telefone, d.email
                FROM dependentes d
                JOIN associados a ON a.id=d.associado_id
                WHERE d.ativo=1 AND a.ativo=1
                AND (LOWER(d.nome) LIKE ? OR LOWER(a.nome) LIKE ?)
                AND (LOWER(a.nome) LIKE ? OR ? = '')
                ORDER BY a.nome, d.nome
            """, (f"%{q}%", f"%{q}%", f"%{assoc_q}%", assoc_q)).fetchall()
        for r in rows:
            self.tv.insert("", "end", values=r)

    def _form(self, dados=None):
        win = _modal(self, "Dependente")
        # Buscar associados para o combobox
        with get_conn() as c:
            associados = c.execute("SELECT id, nome FROM associados WHERE ativo=1 ORDER BY nome").fetchall()
        campos = [
            ("Associado*", "associado_id", associados),
            ("Nome*",      "nome"),
            ("Parentesco", "parentesco"),
            ("Telefone",   "telefone"),
            ("E-mail",     "email"),
        ]
        entries = {}
        for i, (lbl, key, *extra) in enumerate(campos):
            tk.Label(win, text=lbl, bg=COR_PAINEL, fg=COR_TEXTO, font=FONTE).grid(
                row=i, column=0, sticky="w", padx=16, pady=6)
            if key == "associado_id":
                var = tk.StringVar()
                cb = ttk.Combobox(win, textvariable=var, state="readonly", width=33, font=FONTE)
                cb['values'] = [f"{a[0]} - {a[1]}" for a in extra[0]]
                if dados:
                    var.set(f"{dados['associado_id']} - {dados.get('associado_nome', '')}")
                cb.grid(row=i, column=1, padx=(4, 16), pady=6)
                entries[key] = cb
            else:
                e = entry_widget(win, width=36)
                e.grid(row=i, column=1, padx=(4, 16), pady=6)
                if dados and dados.get(key):
                    e.insert(0, dados.get(key, ""))
                entries[key] = e

        def salvar():
            if not entries["associado_id"].get():
                messagebox.showwarning("Aviso", "Selecione um associado.", parent=win)
                return
            nome = entries["nome"].get().strip() if isinstance(entries["nome"], tk.Entry) else entries["nome"].get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Nome é obrigatório.", parent=win)
                return
            assoc_id = int(entries["associado_id"].get().split(" - ")[0])
            parentesco = entries["parentesco"].get().strip() if isinstance(entries["parentesco"], tk.Entry) else ""
            telefone = entries["telefone"].get().strip() if isinstance(entries["telefone"], tk.Entry) else ""
            email = entries["email"].get().strip() if isinstance(entries["email"], tk.Entry) else ""
            with get_conn() as c:
                if dados:
                    c.execute("""UPDATE dependentes SET associado_id=?, nome=?, parentesco=?, telefone=?, email=?
                               WHERE id=?""",
                              (assoc_id, nome, parentesco, telefone, email, dados["id"]))
                else:
                    c.execute("""INSERT INTO dependentes(associado_id, nome, parentesco, telefone, email)
                               VALUES(?,?,?,?,?)""",
                              (assoc_id, nome, parentesco, telefone, email))
            win.destroy()
            self.refresh()

        b = tk.Button(win, text="💾  Salvar", command=salvar)
        style_btn(b, COR_VERDE)
        b.grid(row=len(campos), column=0, columnspan=2, pady=16)

    def _novo(self):    self._form()
    def _editar(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um dependente.")
            return
        did = self.tv.item(sel[0])["values"][0]
        with get_conn() as c:
            r = c.execute("SELECT * FROM dependentes WHERE id=?", (did,)).fetchone()
            assoc_nome = c.execute("SELECT nome FROM associados WHERE id=?", (r[1],)).fetchone()[0]
        cols = ["id","associado_id","nome","parentesco","telefone","email","ativo"]
        dados = dict(zip(cols, r))
        dados["associado_nome"] = assoc_nome
        self._form(dados)

    def _excluir(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um dependente.")
            return
        did = self.tv.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "Excluir este dependente?"):
            return
        with get_conn() as c:
            c.execute("UPDATE dependentes SET ativo=0 WHERE id=?", (did,))
        self.refresh()

# ─── USUÁRIOS (ACESSO AO SISTEMA) ─────────────────────────────────────

class UsuariosFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "🔑  Gerenciar Usuários do Sistema", bold=True, font=FONTE_TITULO).pack(side="left")

        btn_frame = tk.Frame(top, bg=COR_FUNDO)
        btn_frame.pack(side="right")
        for txt, cmd, cor in [("＋  Novo", self._novo, COR_VERDE),
                               ("✏️  Editar", self._editar, COR_AZUL),
                               ("🗑  Excluir", self._excluir, COR_VERMELHO)]:
            b = tk.Button(btn_frame, text=txt, command=cmd)
            style_btn(b, cor)
            b.pack(side="left", padx=4)

        busca_frame = tk.Frame(self, bg=COR_FUNDO)
        busca_frame.pack(fill="x", padx=30, pady=(0, 8))
        label(busca_frame, "🔍 Buscar:").pack(side="left", padx=(0, 6))
        self.busca_var = tk.StringVar()
        self.busca_var.trace_add("write", lambda *_: self.refresh())
        entry_widget(busca_frame, textvariable=self.busca_var, width=40).pack(side="left")

        cols = ("ID", "Nome", "Usuário", "Tipo", "Status")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=20)
        widths = [40, 200, 150, 120, 80]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Nome", "Usuário") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 20))
        sb.pack(side="left", fill="y", pady=(0, 20), padx=(0, 10))

    def refresh(self):
        q = self.busca_var.get().strip().lower() if hasattr(self, "busca_var") else ""
        self.tv.delete(*self.tv.get_children())
        with get_conn() as c:
            if q:
                rows = c.execute(
                    "SELECT id, nome, usuario, tipo, ativo FROM usuarios WHERE LOWER(nome) LIKE ? OR LOWER(usuario) LIKE ?",
                    (f"%{q}%", f"%{q}%")
                ).fetchall()
            else:
                rows = c.execute("SELECT id, nome, usuario, tipo, ativo FROM usuarios").fetchall()
        for r in rows:
            status = "✅ Ativo" if r[4] else "❌ Inativo"
            self.tv.insert("", "end", values=(r[0], r[1], r[2], r[3], status))

    def _form(self, dados=None):
        win = _modal(self, "Usuário")
        campos = [
            ("Nome*",      "nome"),
            ("Usuário*",   "usuario"),
            ("Senha" + ("*" if not dados else " (deixe em branco para manter)"), "senha"),
            ("Tipo",       "tipo"),
        ]
        entries = {}
        for i, (lbl, key) in enumerate(campos):
            tk.Label(win, text=lbl, bg=COR_PAINEL, fg=COR_TEXTO, font=FONTE).grid(
                row=i, column=0, sticky="w", padx=16, pady=6)
            if key == "tipo":
                var = tk.StringVar(value=dados.get(key, "Operador") if dados else "Operador")
                cb = ttk.Combobox(win, textvariable=var,
                                   values=["Administrador", "Operador"],
                                   state="readonly", width=33, font=FONTE)
                cb.grid(row=i, column=1, padx=(4, 16), pady=6)
                entries[key] = var
            elif key == "senha":
                e = tk.Entry(win, width=36, show="*",
                             bg=COR_CARD, fg=COR_TEXTO, insertbackground=COR_TEXTO,
                             relief="flat", font=FONTE)
                e.grid(row=i, column=1, padx=(4, 16), pady=6)
                entries[key] = e
            else:
                e = entry_widget(win, width=36)
                e.grid(row=i, column=1, padx=(4, 16), pady=6)
                if dados and dados.get(key):
                    e.insert(0, dados.get(key, ""))
                entries[key] = e

        def salvar():
            nome = entries["nome"].get().strip()
            usuario = entries["usuario"].get().strip()
            senha = entries["senha"].get()
            if not nome or not usuario:
                messagebox.showwarning("Aviso", "Nome e Usuário são obrigatórios.", parent=win)
                return
            tipo = entries["tipo"].get()
            with get_conn() as c:
                if dados:
                    if senha:
                        c.execute("UPDATE usuarios SET nome=?, usuario=?, senha=?, tipo=? WHERE id=?",
                                  (nome, usuario, senha, tipo, dados["id"]))
                    else:
                        c.execute("UPDATE usuarios SET nome=?, usuario=?, tipo=? WHERE id=?",
                                  (nome, usuario, tipo, dados["id"]))
                else:
                    if not senha:
                        messagebox.showwarning("Aviso", "Senha é obrigatória para novos usuários.", parent=win)
                        return
                    c.execute("INSERT INTO usuarios(nome, usuario, senha, tipo) VALUES(?,?,?,?)",
                              (nome, usuario, senha, tipo))
            win.destroy()
            self.refresh()

        b = tk.Button(win, text="💾  Salvar", command=salvar)
        style_btn(b, COR_VERDE)
        b.grid(row=len(campos), column=0, columnspan=2, pady=16)

    def _novo(self):    self._form()
    def _editar(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um usuário.")
            return
        uid = self.tv.item(sel[0])["values"][0]
        with get_conn() as c:
            r = c.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone()
        cols = ["id","nome","usuario","senha","tipo","ativo"]
        self._form(dict(zip(cols, r)))

    def _excluir(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um usuário.")
            return
        uid = self.tv.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "Desativar este usuário?"):
            return
        with get_conn() as c:
            c.execute("UPDATE usuarios SET ativo=0 WHERE id=?", (uid,))
        self.refresh()

# ─── EMPRÉSTIMOS ───────────────────────────────────────────────────────────────

class EmprestimosFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._livro_selecionado_id    = None
        self._pessoa_selecionada_id   = None
        self._pessoa_tipo             = None  # 'associado' ou 'dependente'
        self._livros_resultados       = {}
        self._pessoas_resultados      = {}
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "🔄  Registrar Empréstimo", bold=True, font=FONTE_TITULO).pack(side="left")

        form = tk.Frame(self, bg=COR_CARD, padx=24, pady=20)
        form.pack(fill="x", padx=30, pady=(0, 16))

        tk.Label(form, text="Livro*", bg=COR_CARD, fg=COR_TEXTO, font=FONTE).grid(
            row=0, column=0, sticky="w", pady=6, padx=(0, 12))
        self.livro_var = tk.StringVar()
        self.livro_entry = ttk.Combobox(form, textvariable=self.livro_var, width=46,
                                         postcommand=self._preparar_livros)
        self.livro_entry.state(['!readonly'])
        self.livro_entry.grid(row=0, column=1, pady=6, padx=(0, 20))
        self.livro_entry.bind('<<ComboboxSelected>>', self._on_livro_select)
        self.livro_entry.bind('<KeyRelease>', self._filtrar_livros)

        tk.Label(form, text="Pessoa*", bg=COR_CARD, fg=COR_TEXTO, font=FONTE).grid(
            row=0, column=2, sticky="w", pady=6, padx=(0, 12))
        self.pessoa_var = tk.StringVar()
        self.pessoa_entry = ttk.Combobox(form, textvariable=self.pessoa_var, width=34,
                                          postcommand=self._preparar_pessoas)
        self.pessoa_entry.state(['!readonly'])
        self.pessoa_entry.grid(row=0, column=3, pady=6)
        self.pessoa_entry.bind('<<ComboboxSelected>>', self._on_pessoa_select)
        self.pessoa_entry.bind('<KeyRelease>', self._filtrar_pessoas)

        tk.Label(form, text="Prazo (dias)", bg=COR_CARD, fg=COR_TEXTO, font=FONTE).grid(
            row=2, column=0, sticky="w", pady=6, padx=(0, 12))
        self.prazo_var = tk.StringVar(value=str(PRAZO_DIAS))
        entry_widget(form, textvariable=self.prazo_var, width=8).grid(row=2, column=1, sticky="w", pady=6)

        b = tk.Button(form, text="✅  Registrar Empréstimo", command=self._registrar)
        style_btn(b, COR_VERDE)
        b.grid(row=2, column=2, columnspan=2, pady=6)

        label(self, "Empréstimos em Aberto", bold=True,
              font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=30, pady=(4, 6))

        cols = ("ID", "Livro", "Pessoa", "Tipo", "Empréstimo", "Prevista", "Status")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=14)
        widths = [40, 240, 150, 80, 110, 110, 100]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Livro", "Pessoa") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 20))
        sb.pack(side="left", fill="y", pady=(0, 20), padx=(0, 10))

    def _preparar_livros(self):
        q = self.livro_var.get().strip().lower()
        self._livro_selecionado_id = None
        with get_conn() as c:
            if len(q) < 3:
                rows = c.execute(
                    "SELECT id, titulo, autor FROM livros WHERE disponivel > 0 ORDER BY titulo LIMIT 10"
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT id, titulo, autor FROM livros WHERE disponivel > 0 AND (LOWER(titulo) LIKE ? OR LOWER(autor) LIKE ?) LIMIT 15",
                    (f"%{q}%", f"%{q}%")
                ).fetchall()
        if rows:
            items = [f"{r[1]} — {r[2]}" for r in rows]
            self._livros_resultados = {items[i]: rows[i][0] for i in range(len(rows))}
            self.livro_entry['values'] = items
        else:
            self.livro_entry['values'] = []

    def _preparar_pessoas(self):
        q = self.pessoa_var.get().strip().lower()
        self._pessoa_selecionada_id = None
        self._pessoa_tipo = None
        resultados = {}
        with get_conn() as c:
            if len(q) < 3:
                rows = c.execute(
                    "SELECT id, nome FROM associados WHERE ativo=1 ORDER BY nome LIMIT 8"
                ).fetchall()
                rows2 = c.execute(
                    "SELECT d.id, d.nome, a.nome FROM dependentes d JOIN associados a ON a.id=d.associado_id WHERE d.ativo=1 ORDER BY d.nome LIMIT 6"
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT id, nome FROM associados WHERE ativo=1 AND (LOWER(nome) LIKE ? OR LOWER(matricula) LIKE ?) LIMIT 10",
                    (f"%{q}%", f"%{q}%")
                ).fetchall()
                rows2 = c.execute(
                    "SELECT d.id, d.nome, a.nome FROM dependentes d JOIN associados a ON a.id=d.associado_id WHERE d.ativo=1 AND (LOWER(d.nome) LIKE ? OR LOWER(a.nome) LIKE ?) LIMIT 10",
                    (f"%{q}%", f"%{q}%")
                ).fetchall()
            for r in rows:
                resultados[f"{r[1]} (Associado)"] = (r[0], 'associado')
            for r in rows2:
                resultados[f"{r[1]} (Dependente de {r[2]})"] = (r[0], 'dependente')
        self._pessoas_resultados = resultados
        self.pessoa_entry['values'] = list(resultados.keys())

    def _filtrar_livros(self, event=None):
        self._preparar_livros()

    def _on_livro_select(self, event=None):
        texto = self.livro_entry.get()
        if texto in self._livros_resultados:
            self._livro_selecionado_id = self._livros_resultados[texto]

    def _filtrar_pessoas(self, event=None):
        self._preparar_pessoas()

    def _on_pessoa_select(self, event=None):
        texto = self.pessoa_entry.get()
        if texto in self._pessoas_resultados:
            self._pessoa_selecionada_id, self._pessoa_tipo = self._pessoas_resultados[texto]

    def refresh(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as c:
            # Empréstimos de associados
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, 'Associado', e.data_emprestimo, e.data_prevista
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.data_devolucao IS NULL AND e.associado_id IS NOT NULL
                ORDER BY e.data_prevista
            """).fetchall()
            # Empréstimos de dependentes
            rows2 = c.execute("""
                SELECT e.id, l.titulo, d.nome, 'Dependente', e.data_emprestimo, e.data_prevista
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN dependentes d ON d.id=e.dependente_id
                WHERE e.data_devolucao IS NULL AND e.dependente_id IS NOT NULL
                ORDER BY e.data_prevista
            """).fetchall()
            rows.extend(rows2)
        for eid, titulo, nome, tipo, emp, prev in rows:
            status = "✅ OK" if prev >= hoje() else "⚠️ Atrasado"
            tag = "ok" if prev >= hoje() else "late"
            self.tv.insert("", "end", values=(eid, titulo, nome, tipo, fmt(emp), fmt(prev), status), tags=(tag,))
        self.tv.tag_configure("late", foreground=COR_VERMELHO)

    def _registrar(self):
        livro_texto = self.livro_var.get().strip()
        pessoa_texto = self.pessoa_var.get().strip()
        
        if not livro_texto or livro_texto not in self._livros_resultados:
            messagebox.showwarning("Aviso", "Selecione um livro válido da lista.")
            return
        if not pessoa_texto or pessoa_texto not in self._pessoas_resultados:
            messagebox.showwarning("Aviso", "Selecione uma pessoa válida da lista.")
            return
        
        self._livro_selecionado_id = self._livros_resultados[livro_texto]
        self._pessoa_selecionada_id, self._pessoa_tipo = self._pessoas_resultados[pessoa_texto]
        try:
            prazo = int(self.prazo_var.get())
        except (ValueError, TypeError):
            prazo = PRAZO_DIAS
        prev = (date.today() + timedelta(days=prazo)).strftime("%Y-%m-%d")
        with get_conn() as c:
            if self._pessoa_tipo == 'associado':
                cursor = c.execute("""INSERT INTO emprestimos(livro_id, associado_id, dependente_id, data_emprestimo, data_prevista)
                             VALUES(?,?,NULL,?,?)""",
                           (self._livro_selecionado_id, self._pessoa_selecionada_id, hoje(), prev))
            else:
                dep_assoc = c.execute(
                    "SELECT associado_id FROM dependentes WHERE id=?",
                    (self._pessoa_selecionada_id,)
                ).fetchone()
                if dep_assoc is None:
                    messagebox.showerror("Erro", "Dependente não encontrado.")
                    return
                cursor = c.execute("""INSERT INTO emprestimos(livro_id, associado_id, dependente_id, data_emprestimo, data_prevista)
                             VALUES(?,?,?,?,?)""",
                           (self._livro_selecionado_id, dep_assoc[0], self._pessoa_selecionada_id, hoje(), prev))
            c.execute("UPDATE livros SET disponivel = disponivel - 1 WHERE id=?",
                      (self._livro_selecionado_id,))
        logger.info("Empréstimo ID=%d: livro_id=%d, %s_id=%d, devolução=%s",
                    cursor.lastrowid, self._livro_selecionado_id, self._pessoa_tipo, self._pessoa_selecionada_id, prev)
        messagebox.showinfo("Sucesso", f"Empréstimo registrado!\nDevolução prevista: {fmt(prev)}")
        self.livro_var.set("")
        self.pessoa_var.set("")
        self._livro_selecionado_id   = None
        self._pessoa_selecionada_id = None
        self._pessoa_tipo            = None
        self.refresh()

# ─── DEVOLUÇÕES ────────────────────────────────────────────────────────────────

class DevolucoesFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "↩️  Registrar Devolução", bold=True, font=FONTE_TITULO).pack(side="left")

        cols = ("ID", "Livro", "Pessoa", "Tipo", "Emprestado em", "Prevista", "Status")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        widths = [40, 240, 150, 80, 110, 110, 100]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Livro", "Pessoa") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 8))
        sb.pack(side="left", fill="y", pady=(0, 8), padx=(0, 10))

        btn_frame = tk.Frame(self, bg=COR_FUNDO)
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))
        b = tk.Button(btn_frame, text="↩️  Confirmar Devolução Selecionada", command=self._devolver)
        style_btn(b, COR_LARANJA)
        b.pack(side="left")

    def refresh(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as c:
            # Empréstimos de associados
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, 'Associado', e.data_emprestimo, e.data_prevista, l.id
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.data_devolucao IS NULL AND e.associado_id IS NOT NULL
                ORDER BY e.data_prevista
            """).fetchall()
            # Empréstimos de dependentes
            rows2 = c.execute("""
                SELECT e.id, l.titulo, d.nome, 'Dependente', e.data_emprestimo, e.data_prevista, l.id
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN dependentes d ON d.id=e.dependente_id
                WHERE e.data_devolucao IS NULL AND e.dependente_id IS NOT NULL
                ORDER BY e.data_prevista
            """).fetchall()
            rows.extend(rows2)
        for eid, titulo, nome, tipo, emp, prev, lid in rows:
            status = "✅ OK" if prev >= hoje() else f"⚠️ {(date.today()-datetime.strptime(prev,'%Y-%m-%d').date()).days}d atraso"
            tag    = "ok" if prev >= hoje() else "late"
            self.tv.insert("", "end",
                           values=(eid, titulo, nome, tipo, fmt(emp), fmt(prev), status),
                           tags=(tag,))
        self.tv.tag_configure("late", foreground=COR_VERMELHO)

    def _devolver(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um empréstimo.")
            return
        eid = self.tv.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar Devolução", "Confirmar devolução?"):
            return
        with get_conn() as c:
            lid = c.execute("SELECT livro_id FROM emprestimos WHERE id=?", (eid,)).fetchone()[0]
            c.execute("UPDATE emprestimos SET data_devolucao=? WHERE id=?", (hoje(), eid))
            c.execute("UPDATE livros SET disponivel = disponivel + 1 WHERE id=?", (lid,))
        logger.info("Devolução ID=%d: livro_id=%d", eid, lid)
        messagebox.showinfo("Sucesso", "Devolução registrada com sucesso!")
        self.refresh()

# ─── RELATÓRIOS ────────────────────────────────────────────────────────────────

class RelatoriosFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._build()

    def _build(self):
        label(self, "📊  Relatórios e Histórico", bold=True,
              font=FONTE_TITULO).pack(anchor="w", padx=30, pady=(24, 12))
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self._tab_historico(tabs)
        self._tab_atrasados(tabs)
        self._tab_livros_pop(tabs)

    def _tab_historico(self, tabs):
        f = tk.Frame(tabs, bg=COR_FUNDO)
        tabs.add(f, text="  Histórico Geral  ")
        ff = tk.Frame(f, bg=COR_FUNDO)
        ff.pack(fill="x", pady=8)
        label(ff, "Associado:").pack(side="left", padx=(0, 4))
        self.hist_usuario = tk.StringVar()
        entry_widget(ff, textvariable=self.hist_usuario, width=24).pack(side="left", padx=(0, 12))
        label(ff, "Livro:").pack(side="left", padx=(0, 4))
        self.hist_livro = tk.StringVar()
        entry_widget(ff, textvariable=self.hist_livro, width=24).pack(side="left", padx=(0, 12))
        b = tk.Button(ff, text="🔍 Filtrar", command=self._load_historico)
        style_btn(b); b.pack(side="left")

        cols = ("ID", "Livro", "Pessoa", "Tipo", "Emprestado", "Prevista", "Devolvido")
        self.tv_hist = ttk.Treeview(f, columns=cols, show="headings", height=18)
        for col in cols:
            self.tv_hist.heading(col, text=col)
            self.tv_hist.column(col, width=180 if col in ("Livro","Associado") else 110, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tv_hist.yview)
        self.tv_hist.configure(yscrollcommand=sb.set)
        self.tv_hist.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

    def _load_historico(self):
        uq = f"%{self.hist_usuario.get().strip()}%"
        lq = f"%{self.hist_livro.get().strip()}%"
        self.tv_hist.delete(*self.tv_hist.get_children())
        with get_conn() as c:
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, e.data_emprestimo, e.data_prevista,
                       e.data_devolucao
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE a.nome LIKE ? AND l.titulo LIKE ?
                ORDER BY e.id DESC
            """, (uq, lq)).fetchall()
        for r in rows:
            eid, titulo, nome, emp, prev, dev = r
            self.tv_hist.insert("", "end", values=(
                eid, titulo, nome, fmt(emp), fmt(prev),
                fmt(dev) if dev else "Em aberto"
            ))

    def _tab_atrasados(self, tabs):
        f = tk.Frame(tabs, bg=COR_FUNDO)
        tabs.add(f, text="  Em Atraso  ")
        cols = ("ID", "Livro", "Pessoa", "Tipo", "Prevista", "Dias Atraso")
        self.tv_atr = ttk.Treeview(f, columns=cols, show="headings", height=20)
        for col in cols:
            self.tv_atr.heading(col, text=col)
            self.tv_atr.column(col, width=150, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tv_atr.yview)
        self.tv_atr.configure(yscrollcommand=sb.set)
        self.tv_atr.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self._tv_atr = self.tv_atr

    def _tab_livros_pop(self, tabs):
        f = tk.Frame(tabs, bg=COR_FUNDO)
        tabs.add(f, text="  Livros Mais Emprestados  ")
        cols = ("Livro", "Autor", "Total Empréstimos")
        self.tv_pop = ttk.Treeview(f, columns=cols, show="headings", height=20)
        for col in cols:
            self.tv_pop.heading(col, text=col)
            self.tv_pop.column(col, width=260 if col != "Total Empréstimos" else 160,
                               anchor="w" if col != "Total Empréstimos" else "center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tv_pop.yview)
        self.tv_pop.configure(yscrollcommand=sb.set)
        self.tv_pop.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

    def refresh(self):
        self._load_historico()

        self._tv_atr.delete(*self._tv_atr.get_children())
        with get_conn() as c:
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, e.data_prevista
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.data_devolucao IS NULL AND e.data_prevista < ?
                ORDER BY e.data_prevista
            """, (hoje(),)).fetchall()
        for eid, titulo, nome, prev in rows:
            dias = (date.today() - datetime.strptime(prev, "%Y-%m-%d").date()).days
            self._tv_atr.insert("", "end", values=(eid, titulo, nome, fmt(prev), dias))

        self.tv_pop.delete(*self.tv_pop.get_children())
        with get_conn() as c:
            rows = c.execute("""
                SELECT l.titulo, l.autor, COUNT(e.id) as total
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                GROUP BY l.id ORDER BY total DESC LIMIT 30
            """).fetchall()
        for r in rows:
            self.tv_pop.insert("", "end", values=r)

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _modal(parent, titulo):
    win = tk.Toplevel(parent)
    win.title(f"Cadastro — {titulo}")
    win.configure(bg=COR_PAINEL)
    win.grab_set()
    win.resizable(False, False)
    win.geometry("+%d+%d" % (parent.winfo_rootx()+120, parent.winfo_rooty()+80))
    return win

def _style_tree():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=COR_CARD, foreground=COR_TEXTO,
                    fieldbackground=COR_CARD, rowheight=26, font=FONTE)
    style.configure("Treeview.Heading", background=COR_PAINEL, foreground=COR_AZUL,
                    font=FONTE_BOLD, relief="flat")
    style.map("Treeview",
              background=[("selected", COR_AZUL)],
              foreground=[("selected", "white")])
    style.configure("TCombobox", fieldbackground=COR_CARD, background=COR_CARD,
                    foreground=COR_TEXTO)

# ─── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
