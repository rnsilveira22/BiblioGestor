import sqlite3
import unittest
from datetime import date, timedelta

DB_SCHEMA = """
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
CREATE TABLE IF NOT EXISTS emprestimos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    livro_id        INTEGER NOT NULL,
    associado_id    INTEGER NOT NULL,
    dependente_id  INTEGER,
    data_emprestimo TEXT NOT NULL,
    data_prevista   TEXT NOT NULL,
    data_devolucao  TEXT,
    multa           REAL DEFAULT 0,
    multa_paga      INTEGER DEFAULT 0,
    FOREIGN KEY(livro_id)    REFERENCES livros(id),
    FOREIGN KEY(associado_id) REFERENCES associados(id),
    FOREIGN KEY(dependente_id) REFERENCES dependentes(id)
);
"""

class TestBibliotecaDB(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(DB_SCHEMA)
        self.conn.execute("PRAGMA foreign_keys = ON")

    def tearDown(self):
        self.conn.close()

    # ─── HELPERS ────────────────────────────────────────────────────────────────

    def _add_livro(self, titulo="Livro Teste", autor="Autor Teste", disp=3):
        cur = self.conn.execute(
            "INSERT INTO livros (titulo, autor, disponivel) VALUES (?,?,?)",
            (titulo, autor, disp)
        )
        return cur.lastrowid

    def _add_associado(self, nome="João"):
        cur = self.conn.execute(
            "INSERT INTO associados (nome) VALUES (?)", (nome,)
        )
        return cur.lastrowid

    def _add_dependente(self, associado_id, nome="Maria"):
        cur = self.conn.execute(
            "INSERT INTO dependentes (associado_id, nome) VALUES (?,?)",
            (associado_id, nome)
        )
        return cur.lastrowid

    # ─── SCHEMA TESTS ───────────────────────────────────────────────────────────

    def test_tabelas_criadas(self):
        tabelas = [r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in ("livros", "associados", "dependentes", "emprestimos"):
            self.assertIn(t, tabelas, f"Tabela '{t}' não foi criada")

    def test_emprestimos_associado_not_null(self):
        cols = {r[1]: r for r in self.conn.execute("PRAGMA table_info(emprestimos)")}
        self.assertEqual(cols["associado_id"][3], 1)  # notnull=1

    # ─── FILTER QUERIES ─────────────────────────────────────────────────────────

    def test_filtrar_livros_disponiveis(self):
        self._add_livro("ABC", "Autor1", disp=2)
        self._add_livro("XYZ", "Autor2", disp=0)
        rows = self.conn.execute(
            "SELECT id, titulo, autor FROM livros WHERE disponivel > 0 ORDER BY titulo"
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "ABC")

    def test_filtrar_livros_por_titulo(self):
        self._add_livro("Agenda Cristã", "Chico Xavier")
        self._add_livro("Abrigo", "Chico Xavier")
        self._add_livro("Astronautas", "Autor X")
        q = "age"
        rows = self.conn.execute(
            "SELECT id, titulo FROM livros WHERE disponivel>0 AND LOWER(titulo) LIKE ? LIMIT 15",
            (f"%{q}%",)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertIn("Agenda", rows[0][1])

    def test_filtrar_livros_por_autor(self):
        self._add_livro("Livro A", "Machado de Assis")
        self._add_livro("Livro B", "Chico Xavier")
        q = "chico"
        rows = self.conn.execute(
            "SELECT id, titulo, autor FROM livros WHERE disponivel>0 AND LOWER(autor) LIKE ? LIMIT 15",
            (f"%{q}%",)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertIn("Chico", rows[0][2])

    def test_filtrar_associados_por_nome(self):
        self._add_associado("José Maria")
        self._add_associado("Maria José")
        q = "josé"
        rows = self.conn.execute(
            "SELECT id, nome FROM associados WHERE ativo=1 AND LOWER(nome) LIKE ? LIMIT 10",
            (f"%{q}%",)
        ).fetchall()
        self.assertEqual(len(rows), 2)

    def test_filtrar_associados_por_matricula(self):
        a1 = self._add_associado("José")
        a2 = self._add_associado("Maria")
        self.conn.execute("UPDATE associados SET matricula=? WHERE id=?", ("MAT001", a1))
        q = "mat001"
        rows = self.conn.execute(
            "SELECT id, nome FROM associados WHERE ativo=1 AND LOWER(matricula) LIKE ? LIMIT 10",
            (f"%{q}%",)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "José")

    def test_filtrar_dependentes_por_nome(self):
        a1 = self._add_associado("João")
        a2 = self._add_associado("Pedro")
        self._add_dependente(a1, "Ana")
        self._add_dependente(a2, "Beatriz")
        q = "ana"
        rows = self.conn.execute(
            """SELECT d.id, d.nome, a.nome FROM dependentes d
               JOIN associados a ON a.id=d.associado_id
               WHERE d.ativo=1 AND LOWER(d.nome) LIKE ? LIMIT 10""",
            (f"%{q}%",)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Ana")

    def test_filtrar_dependentes_por_associado(self):
        a1 = self._add_associado("Carlos")
        a2 = self._add_associado("Pedro")
        self._add_dependente(a1, "Ana")
        self._add_dependente(a2, "Beatriz")
        q = "carlos"
        rows = self.conn.execute(
            """SELECT d.id, d.nome, a.nome FROM dependentes d
               JOIN associados a ON a.id=d.associado_id
               WHERE d.ativo=1 AND LOWER(a.nome) LIKE ? LIMIT 10""",
            (f"%{q}%",)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "Carlos")

    # ─── LOAN REGISTRATION ──────────────────────────────────────────────────────

    def test_registrar_emprestimo_associado(self):
        livro_id = self._add_livro("ABC", "Autor", disp=5)
        assoc_id = self._add_associado("João")

        hoje = date.today().strftime("%Y-%m-%d")
        prev = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

        cur = self.conn.execute(
            """INSERT INTO emprestimos(livro_id, associado_id, dependente_id, data_emprestimo, data_prevista)
               VALUES(?,?,NULL,?,?)""",
            (livro_id, assoc_id, hoje, prev)
        )
        self.conn.execute("UPDATE livros SET disponivel=disponivel-1 WHERE id=?", (livro_id,))

        emp = self.conn.execute("SELECT * FROM emprestimos WHERE id=?", (cur.lastrowid,)).fetchone()
        self.assertIsNotNone(emp)
        self.assertEqual(emp[1], livro_id)   # livro_id
        self.assertEqual(emp[2], assoc_id)    # associado_id
        self.assertIsNone(emp[3])              # dependente_id
        self.assertEqual(emp[4], hoje)

        disp = self.conn.execute("SELECT disponivel FROM livros WHERE id=?", (livro_id,)).fetchone()[0]
        self.assertEqual(disp, 4)

    def test_registrar_emprestimo_dependente(self):
        livro_id = self._add_livro("ABC", "Autor", disp=5)
        assoc_id = self._add_associado("João")
        dep_id = self._add_dependente(assoc_id, "Maria")

        hoje = date.today().strftime("%Y-%m-%d")
        prev = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

        dep_assoc = self.conn.execute(
            "SELECT associado_id FROM dependentes WHERE id=?", (dep_id,)
        ).fetchone()
        self.assertIsNotNone(dep_assoc)
        self.assertEqual(dep_assoc[0], assoc_id)

        cur = self.conn.execute(
            """INSERT INTO emprestimos(livro_id, associado_id, dependente_id, data_emprestimo, data_prevista)
               VALUES(?,?,?,?,?)""",
            (livro_id, dep_assoc[0], dep_id, hoje, prev)
        )
        self.conn.execute("UPDATE livros SET disponivel=disponivel-1 WHERE id=?", (livro_id,))

        emp = self.conn.execute("SELECT * FROM emprestimos WHERE id=?", (cur.lastrowid,)).fetchone()
        self.assertIsNotNone(emp)
        self.assertEqual(emp[1], livro_id)
        self.assertEqual(emp[2], assoc_id)    # associado_id preenchido
        self.assertEqual(emp[3], dep_id)      # dependente_id preenchido

    def test_emprestimo_sem_associado_deve_falhar(self):
        livro_id = self._add_livro("ABC", "Autor")
        dep_id = self._add_dependente(self._add_associado("João"), "Maria")

        hoje = date.today().strftime("%Y-%m-%d")
        prev = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """INSERT INTO emprestimos(livro_id, associado_id, dependente_id, data_emprestimo, data_prevista)
                   VALUES(?,NULL,?,?,?)""",
                (livro_id, dep_id, hoje, prev)
            )

    def test_dependente_busca_associado_id(self):
        assoc_id = self._add_associado("João")
        dep_id = self._add_dependente(assoc_id, "Maria")

        row = self.conn.execute(
            "SELECT associado_id FROM dependentes WHERE id=?", (dep_id,)
        ).fetchone()
        self.assertEqual(row[0], assoc_id)

    def test_livro_sem_estoque_nao_aparece(self):
        self._add_livro("Disponivel", "A", disp=2)
        self._add_livro("Indisponivel", "B", disp=0)
        rows = self.conn.execute(
            "SELECT titulo FROM livros WHERE disponivel > 0"
        ).fetchall()
        titulos = [r[0] for r in rows]
        self.assertIn("Disponivel", titulos)
        self.assertNotIn("Indisponivel", titulos)

    # ─── LISTAGEM EMPRESTIMOS ───────────────────────────────────────────────────

    def test_listar_emprestimos_abertos_associado(self):
        livro_id = self._add_livro("ABC")
        assoc_id = self._add_associado("João")
        hoje = date.today().strftime("%Y-%m-%d")
        prev = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")
        self.conn.execute(
            "INSERT INTO emprestimos(livro_id,associado_id,data_emprestimo,data_prevista) VALUES(?,?,?,?)",
            (livro_id, assoc_id, hoje, prev)
        )
        rows = self.conn.execute("""
            SELECT e.id, l.titulo, a.nome
            FROM emprestimos e
            JOIN livros l ON l.id=e.livro_id
            JOIN associados a ON a.id=e.associado_id
            WHERE e.data_devolucao IS NULL AND e.associado_id IS NOT NULL
        """).fetchall()
        self.assertEqual(len(rows), 1)

    def test_listar_emprestimos_abertos_dependente(self):
        livro_id = self._add_livro("ABC")
        assoc_id = self._add_associado("João")
        dep_id = self._add_dependente(assoc_id, "Maria")
        hoje = date.today().strftime("%Y-%m-%d")
        prev = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")
        self.conn.execute(
            "INSERT INTO emprestimos(livro_id,associado_id,dependente_id,data_emprestimo,data_prevista) VALUES(?,?,?,?,?)",
            (livro_id, assoc_id, dep_id, hoje, prev)
        )
        rows = self.conn.execute("""
            SELECT e.id, l.titulo, d.nome
            FROM emprestimos e
            JOIN livros l ON l.id=e.livro_id
            JOIN dependentes d ON d.id=e.dependente_id
            WHERE e.data_devolucao IS NULL AND e.dependente_id IS NOT NULL
        """).fetchall()
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
