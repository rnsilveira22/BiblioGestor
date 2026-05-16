import sqlite3
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANILHA = os.path.join(BASE_DIR, "BIBLIOTECA_CATEGORIZADA_2026.xlsx")
DB_FILE = os.path.join(BASE_DIR, "biblioteca.db")


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def importar():
    print("Lendo planilha...")
    df = pd.read_excel(PLANILHA, sheet_name="Acervo Completo")
    df.columns = [str(c).strip() for c in df.columns]

    col_id = "ID"
    col_cat = "CATEGORIA"
    col_titulo = "TÍTULO DO LIVRO"
    col_autor = "AUTOR"
    col_esp = "PELO ESPÍRITO"
    col_exemplares = "TOTAL EXEMPLARES"

    df[col_esp] = df[col_esp].fillna("")

    # Extrair prefixo do ID (sem o número da cópia: CHX-0001-01 → CHX-0001)
    df["ID_PREFIX"] = df[col_id].str.rsplit("-", n=1).str[0]

    # Agrupar por livro único agregando os prefixos de ID
    grupos = df.groupby([col_cat, col_titulo, col_autor, col_esp],
                        as_index=False).agg(
        exemplares=(col_exemplares, "first"),
        id_prefixes=("ID_PREFIX", lambda xs: "/".join(sorted(set(xs))))
    )

    print(f"Total de livros a importar: {len(grupos)}")
    print(f"Total de exemplares: {grupos['exemplares'].sum()}")

    with get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")

        conn.execute("DELETE FROM emprestimos")
        conn.execute("DELETE FROM livros")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='livros'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='emprestimos'")

        conn.execute("PRAGMA foreign_keys = ON")

        inseridos = 0
        for _, row in grupos.iterrows():
            titulo = str(row[col_titulo]).strip()
            autor = str(row[col_autor]).strip()
            espirito = str(row.get(col_esp, "")).strip()
            if espirito == "nan":
                espirito = ""
            categoria = str(row[col_cat]).strip()
            numero = str(row["id_prefixes"]).strip()
            try:
                qtd = int(row["exemplares"])
            except (ValueError, TypeError):
                qtd = 1

            try:
                conn.execute(
                    """INSERT INTO livros(numero, titulo, autor, pelo_espirito, categoria, exemplares, disponivel)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (numero, titulo, autor, espirito, categoria, qtd, qtd)
                )
                inseridos += 1
            except sqlite3.Error as e:
                logger.error(f"Erro ao inserir '{titulo}': {e}")

    print(f"\n✅ Importação concluída!")
    print(f"   Livros inseridos : {inseridos}")
    print(f"   Total exemplares : {grupos['exemplares'].sum()}")


if __name__ == "__main__":
    importar()
