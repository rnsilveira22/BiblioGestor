import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date, timedelta
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── BANCO DE DADOS ────────────────────────────────────────────────────────────

DB_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biblioteca.db")
PRAZO_DIAS = 14
MULTA_DIA  = 0.50

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
        CREATE TABLE IF NOT EXISTS emprestimos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            livro_id        INTEGER NOT NULL,
            associado_id    INTEGER NOT NULL,
            data_emprestimo TEXT NOT NULL,
            data_prevista   TEXT NOT NULL,
            data_devolucao  TEXT,
            multa           REAL DEFAULT 0,
            multa_paga      INTEGER DEFAULT 0,
            FOREIGN KEY(livro_id)    REFERENCES livros(id),
            FOREIGN KEY(associado_id) REFERENCES associados(id)
        );
        CREATE INDEX IF NOT EXISTS idx_emprestimos_devolucao ON emprestimos(data_devolucao, data_prevista);
        CREATE INDEX IF NOT EXISTS idx_livros_titulo ON livros(titulo);
        CREATE INDEX IF NOT EXISTS idx_associados_nome ON associados(nome);
        """)
    migrate_db()

def migrate_db():
    with get_conn() as c:
        tabelas = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

        if "usuarios" in tabelas and "associados" in tabelas:
            count = c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
            if count > 0:
                c.execute("""INSERT OR IGNORE INTO associados(id,nome,tipo,matricula,telefone,email,ativo)
                             SELECT id,nome,tipo,matricula,telefone,email,ativo FROM usuarios""")

        cols_emp = [r[1] for r in c.execute("PRAGMA table_info(emprestimos)").fetchall()]
        if "usuario_id" in cols_emp and "associado_id" not in cols_emp:
            c.execute("ALTER TABLE emprestimos ADD COLUMN associado_id INTEGER")
            c.execute("UPDATE emprestimos SET associado_id = usuario_id WHERE associado_id IS NULL")

        cols_liv = [r[1] for r in c.execute("PRAGMA table_info(livros)").fetchall()]
        if "numero" not in cols_liv:
            c.execute("ALTER TABLE livros ADD COLUMN numero TEXT")
        if "pelo_espirito" not in cols_liv:
            c.execute("ALTER TABLE livros ADD COLUMN pelo_espirito TEXT")

        c.execute("CREATE INDEX IF NOT EXISTS idx_emprestimos_devolucao ON emprestimos(data_devolucao, data_prevista)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_livros_titulo ON livros(titulo)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_associados_nome ON associados(nome)")

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

def calcular_multa(data_prevista, data_devolucao=None):
    prev = datetime.strptime(data_prevista, "%Y-%m-%d").date()
    dev  = datetime.strptime(data_devolucao, "%Y-%m-%d").date() if data_devolucao else date.today()
    return round(max(0, (dev - prev).days) * MULTA_DIA, 2)

# ─── ESTILO GLOBAL ─────────────────────────────────────────────────────────────

COR_FUNDO    = "#1e2533"
COR_PAINEL   = "#252d3d"
COR_CARD     = "#2e3a50"
COR_AZUL     = "#4a90d9"
COR_VERDE    = "#3cb371"
COR_LARANJA  = "#e07b39"
COR_VERMELHO = "#d94a4a"
COR_TEXTO    = "#e8eaf0"
COR_SUBTEXTO = "#8899aa"
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

# ─── JANELA PRINCIPAL ──────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚 BiblioGestor")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(bg=COR_FUNDO)
        _style_tree()
        init_db()
        self._build_ui()

    def _build_ui(self):
        sidebar = tk.Frame(self, bg=COR_PAINEL, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="📚", font=("Segoe UI", 32), bg=COR_PAINEL,
                 fg=COR_AZUL).pack(pady=(28, 4))
        tk.Label(sidebar, text="BiblioGestor", font=("Segoe UI", 13, "bold"),
                 bg=COR_PAINEL, fg=COR_TEXTO).pack()
        tk.Label(sidebar, text="Gestão de Biblioteca", font=("Segoe UI", 8),
                 bg=COR_PAINEL, fg=COR_SUBTEXTO).pack(pady=(0, 24))
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=16, pady=4)

        self.frames = {}
        self.nav_buttons = {}

        menus = [
            ("🏠  Painel",        PainelFrame),
            ("📖  Livros",        LivrosFrame),
            ("👤  Associados",    AssociadosFrame),
            ("🔄  Empréstimos",   EmprestimosFrame),
            ("↩️  Devoluções",    DevolucoesFrame),
            ("📊  Relatórios",    RelatoriosFrame),
        ]

        self.content = tk.Frame(self, bg=COR_FUNDO)
        self.content.pack(side="left", fill="both", expand=True)

        for name, FrameClass in menus:
            f = FrameClass(self.content, self)
            f.place(relwidth=1, relheight=1)
            self.frames[name] = f

        def nav(name):
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
            multas_pend  = c.execute(
                "SELECT COALESCE(SUM(multa),0) FROM emprestimos WHERE multa>0 AND multa_paga=0"
            ).fetchone()[0]

        cards = [
            ("📚 Livros\nCadastrados",   tot_livros,  COR_AZUL),
            ("👤 Associados\nAtivos",    tot_assoc,   COR_VERDE),
            ("🔄 Empréstimos\nAbertos",  em_aberto,   COR_LARANJA),
            ("⚠️ Em Atraso",            atrasados,   COR_VERMELHO),
            ("💰 Multas\nPendentes",     f"R$ {multas_pend:.2f}", "#9b59b6"),
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

# ─── EMPRÉSTIMOS ───────────────────────────────────────────────────────────────

class EmprestimosFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COR_FUNDO)
        self.app = app
        self._livro_selecionado_id    = None
        self._usuario_selecionado_id  = None
        self._livros_resultados       = {}
        self._usuarios_resultados     = {}
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COR_FUNDO)
        top.pack(fill="x", padx=30, pady=(20, 10))
        label(top, "🔄  Registrar Empréstimo", bold=True, font=FONTE_TITULO).pack(side="left")

        form = tk.Frame(self, bg=COR_CARD, padx=24, pady=20)
        form.pack(fill="x", padx=30, pady=(0, 16))

        # ── Livro ──
        tk.Label(form, text="Livro*", bg=COR_CARD, fg=COR_TEXTO, font=FONTE).grid(
            row=0, column=0, sticky="w", pady=6, padx=(0, 12))
        self.livro_var = tk.StringVar()
        self.livro_var.trace_add("write", lambda *_: self._filtrar_livros())
        self.livro_entry = entry_widget(form, textvariable=self.livro_var, width=50)
        self.livro_entry.grid(row=0, column=1, pady=6, padx=(0, 20))

        self.livro_listbox = tk.Listbox(form, bg=COR_CARD, fg=COR_TEXTO, font=FONTE,
                                        height=5, relief="flat", selectbackground=COR_AZUL, width=50)
        self.livro_listbox.grid(row=1, column=1, pady=(0, 6), padx=(0, 20), sticky="w")
        self.livro_listbox.bind("<<ListboxSelect>>", self._selecionar_livro)
        self.livro_listbox.grid_remove()

        # ── Associado ──
        tk.Label(form, text="Associado*", bg=COR_CARD, fg=COR_TEXTO, font=FONTE).grid(
            row=0, column=2, sticky="w", pady=6, padx=(0, 12))
        self.usuario_var = tk.StringVar()
        self.usuario_var.trace_add("write", lambda *_: self._filtrar_usuarios())
        self.usuario_entry = entry_widget(form, textvariable=self.usuario_var, width=38)
        self.usuario_entry.grid(row=0, column=3, pady=6)

        self.usuario_listbox = tk.Listbox(form, bg=COR_CARD, fg=COR_TEXTO, font=FONTE,
                                          height=5, relief="flat", selectbackground=COR_AZUL, width=38)
        self.usuario_listbox.grid(row=1, column=3, pady=(0, 6), sticky="w")
        self.usuario_listbox.bind("<<ListboxSelect>>", self._selecionar_usuario)
        self.usuario_listbox.grid_remove()

        # ── Prazo ──
        tk.Label(form, text="Prazo (dias)", bg=COR_CARD, fg=COR_TEXTO, font=FONTE).grid(
            row=2, column=0, sticky="w", pady=6, padx=(0, 12))
        self.prazo_var = tk.StringVar(value=str(PRAZO_DIAS))
        entry_widget(form, textvariable=self.prazo_var, width=8).grid(row=2, column=1, sticky="w", pady=6)

        b = tk.Button(form, text="✅  Registrar Empréstimo", command=self._registrar)
        style_btn(b, COR_VERDE)
        b.grid(row=2, column=2, columnspan=2, pady=6)

        # ── Lista ──
        label(self, "Empréstimos em Aberto", bold=True,
              font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=30, pady=(4, 6))

        cols = ("ID", "Livro", "Associado", "Empréstimo", "Prevista", "Status")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=14)
        widths = [40, 260, 180, 110, 110, 100]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Livro", "Associado") else "center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=(0, 20))
        sb.pack(side="left", fill="y", pady=(0, 20), padx=(0, 10))

    def _filtrar_livros(self):
        q = self.livro_var.get().strip().lower()
        self._livro_selecionado_id = None
        self.livro_listbox.delete(0, "end")
        if len(q) < 2:
            self.livro_listbox.grid_remove()
            return
        with get_conn() as c:
            rows = c.execute(
                """SELECT id, titulo, autor FROM livros
                   WHERE disponivel > 0 AND (LOWER(titulo) LIKE ? OR LOWER(autor) LIKE ?)
                   LIMIT 10""",
                (f"%{q}%", f"%{q}%")
            ).fetchall()
        if not rows:
            self.livro_listbox.grid_remove()
            return
        self._livros_resultados = {f"{r[1]} — {r[2]}": r[0] for r in rows}
        for txt in self._livros_resultados:
            self.livro_listbox.insert("end", txt)
        self.livro_listbox.grid()

    def _selecionar_livro(self, event):
        sel = self.livro_listbox.curselection()
        if not sel: return
        texto = self.livro_listbox.get(sel[0])
        self._livro_selecionado_id = self._livros_resultados[texto]
        self.livro_var.set(texto)
        self.livro_listbox.grid_remove()

    def _filtrar_usuarios(self):
        q = self.usuario_var.get().strip().lower()
        self._usuario_selecionado_id = None
        self.usuario_listbox.delete(0, "end")
        if len(q) < 2:
            self.usuario_listbox.grid_remove()
            return
        with get_conn() as c:
            rows = c.execute(
                """SELECT id, nome, matricula FROM associados
                   WHERE ativo=1 AND (LOWER(nome) LIKE ? OR LOWER(matricula) LIKE ?)
                   LIMIT 10""",
                (f"%{q}%", f"%{q}%")
            ).fetchall()
        if not rows:
            self.usuario_listbox.grid_remove()
            return
        self._usuarios_resultados = {f"{r[1]} — {r[2] or 'sem matrícula'}": r[0] for r in rows}
        for txt in self._usuarios_resultados:
            self.usuario_listbox.insert("end", txt)
        self.usuario_listbox.grid()

    def _selecionar_usuario(self, event):
        sel = self.usuario_listbox.curselection()
        if not sel: return
        texto = self.usuario_listbox.get(sel[0])
        self._usuario_selecionado_id = self._usuarios_resultados[texto]
        self.usuario_var.set(texto)
        self.usuario_listbox.grid_remove()

    def refresh(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as c:
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, e.data_emprestimo, e.data_prevista
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.data_devolucao IS NULL
                ORDER BY e.data_prevista
            """).fetchall()
        for eid, titulo, nome, emp, prev in rows:
            status = "✅ OK" if prev >= hoje() else "⚠️ Atrasado"
            tag = "ok" if prev >= hoje() else "late"
            self.tv.insert("", "end", values=(eid, titulo, nome, fmt(emp), fmt(prev), status), tags=(tag,))
        self.tv.tag_configure("late", foreground=COR_VERMELHO)

    def _registrar(self):
        if not self._livro_selecionado_id or not self._usuario_selecionado_id:
            messagebox.showwarning("Aviso", "Selecione um livro e um associado da lista.")
            return
        try:
            prazo = int(self.prazo_var.get())
        except (ValueError, TypeError):
            prazo = PRAZO_DIAS
        prev = (date.today() + timedelta(days=prazo)).strftime("%Y-%m-%d")
        with get_conn() as c:
            cursor = c.execute("""INSERT INTO emprestimos(livro_id, associado_id, data_emprestimo, data_prevista)
                         VALUES(?,?,?,?)""",
                      (self._livro_selecionado_id, self._usuario_selecionado_id, hoje(), prev))
            c.execute("UPDATE livros SET disponivel = disponivel - 1 WHERE id=?",
                      (self._livro_selecionado_id,))
        logger.info("Empréstimo ID=%d: livro_id=%d, associado_id=%d, devolucao=%s",
                    cursor.lastrowid, self._livro_selecionado_id, self._usuario_selecionado_id, prev)
        messagebox.showinfo("Sucesso", f"Empréstimo registrado!\nDevolução prevista: {fmt(prev)}")
        self.livro_var.set("")
        self.usuario_var.set("")
        self._livro_selecionado_id   = None
        self._usuario_selecionado_id = None
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

        cols = ("ID", "Livro", "Associado", "Emprestado em", "Prevista", "Multa", "Status")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        widths = [40, 240, 160, 110, 110, 80, 100]
        for col, w in zip(cols, widths):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="w" if col in ("Livro", "Associado") else "center")

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
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, e.data_emprestimo, e.data_prevista, l.id
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.data_devolucao IS NULL
                ORDER BY e.data_prevista
            """).fetchall()
        for eid, titulo, nome, emp, prev, lid in rows:
            multa  = calcular_multa(prev)
            status = "✅ OK" if prev >= hoje() else f"⚠️ {(date.today()-datetime.strptime(prev,'%Y-%m-%d').date()).days}d atraso"
            tag    = "ok" if prev >= hoje() else "late"
            self.tv.insert("", "end",
                           values=(eid, titulo, nome, fmt(emp), fmt(prev),
                                   f"R$ {multa:.2f}" if multa else "-", status),
                           tags=(tag,))
        self.tv.tag_configure("late", foreground=COR_VERMELHO)

    def _devolver(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um empréstimo.")
            return
        eid = self.tv.item(sel[0])["values"][0]
        with get_conn() as c:
            emp = c.execute("SELECT livro_id, data_prevista FROM emprestimos WHERE id=?", (eid,)).fetchone()
        lid, data_prev = emp
        multa = calcular_multa(data_prev)
        msg = "Confirmar devolução?"
        if multa > 0:
            msg += f"\n\n⚠️ Multa por atraso: R$ {multa:.2f}"
        if not messagebox.askyesno("Confirmar Devolução", msg):
            return
        with get_conn() as c:
            c.execute("UPDATE emprestimos SET data_devolucao=?, multa=? WHERE id=?",
                      (hoje(), multa, eid))
            c.execute("UPDATE livros SET disponivel = disponivel + 1 WHERE id=?", (lid,))
        logger.info("Devolução ID=%d: livro_id=%d, multa=R$%.2f", eid, lid, multa)
        if multa > 0:
            pago = messagebox.askyesno("Multa", f"Multa de R$ {multa:.2f}. Já foi paga?")
            if pago:
                with get_conn() as c:
                    c.execute("UPDATE emprestimos SET multa_paga=1 WHERE id=?", (eid,))
                logger.info("Multa paga para empréstimo ID=%d", eid)
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
        self._tab_multas(tabs)
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

        cols = ("ID", "Livro", "Associado", "Emprestado", "Prevista", "Devolvido", "Multa", "Paga")
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
                       e.data_devolucao, e.multa, e.multa_paga
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE a.nome LIKE ? AND l.titulo LIKE ?
                ORDER BY e.id DESC
            """, (uq, lq)).fetchall()
        for r in rows:
            eid, titulo, nome, emp, prev, dev, multa, paga = r
            self.tv_hist.insert("", "end", values=(
                eid, titulo, nome, fmt(emp), fmt(prev),
                fmt(dev) if dev else "Em aberto",
                f"R$ {multa:.2f}" if multa else "-",
                "Sim" if paga else ("Não" if multa else "-")
            ))

    def _tab_atrasados(self, tabs):
        f = tk.Frame(tabs, bg=COR_FUNDO)
        tabs.add(f, text="  Em Atraso  ")
        cols = ("ID", "Livro", "Associado", "Prevista", "Dias Atraso", "Multa Atual")
        self.tv_atr = ttk.Treeview(f, columns=cols, show="headings", height=20)
        for col in cols:
            self.tv_atr.heading(col, text=col)
            self.tv_atr.column(col, width=150, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tv_atr.yview)
        self.tv_atr.configure(yscrollcommand=sb.set)
        self.tv_atr.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self._tv_atr = self.tv_atr

    def _tab_multas(self, tabs):
        f = tk.Frame(tabs, bg=COR_FUNDO)
        tabs.add(f, text="  Multas Pendentes  ")
        cols = ("ID", "Livro", "Associado", "Devolvido", "Multa", "Paga")
        self.tv_multas = ttk.Treeview(f, columns=cols, show="headings", height=18)
        for col in cols:
            self.tv_multas.heading(col, text=col)
            self.tv_multas.column(col, width=150, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tv_multas.yview)
        self.tv_multas.configure(yscrollcommand=sb.set)
        self.tv_multas.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        btn_frame = tk.Frame(f, bg=COR_FUNDO)
        btn_frame.pack(fill="x", pady=8, padx=8)
        b = tk.Button(btn_frame, text="✅  Marcar Multa Selecionada como Paga",
                      command=self._pagar_multa)
        style_btn(b, COR_VERDE); b.pack(side="left")

    def _pagar_multa(self):
        sel = self.tv_multas.selection()
        if not sel: return
        eid = self.tv_multas.item(sel[0])["values"][0]
        with get_conn() as c:
            c.execute("UPDATE emprestimos SET multa_paga=1 WHERE id=?", (eid,))
        messagebox.showinfo("Sucesso", "Multa registrada como paga.")
        self.refresh()

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
            dias  = (date.today() - datetime.strptime(prev, "%Y-%m-%d").date()).days
            multa = calcular_multa(prev)
            self._tv_atr.insert("", "end", values=(eid, titulo, nome, fmt(prev), dias, f"R$ {multa:.2f}"))

        self.tv_multas.delete(*self.tv_multas.get_children())
        with get_conn() as c:
            rows = c.execute("""
                SELECT e.id, l.titulo, a.nome, e.data_devolucao, e.multa, e.multa_paga
                FROM emprestimos e
                JOIN livros l ON l.id=e.livro_id
                JOIN associados a ON a.id=e.associado_id
                WHERE e.multa > 0
                ORDER BY e.multa_paga, e.multa DESC
            """).fetchall()
        for eid, titulo, nome, dev, multa, paga in rows:
            self.tv_multas.insert("", "end", values=(
                eid, titulo, nome, fmt(dev) if dev else "Em aberto",
                f"R$ {multa:.2f}", "✅ Sim" if paga else "❌ Não"
            ))

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
