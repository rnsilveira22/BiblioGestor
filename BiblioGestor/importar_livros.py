import sqlite3
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANILHA = os.path.join(BASE_DIR, "BIBLIOTECA_-_LIVROS_2026__2_.xlsx")
DB_FILE = os.path.join(BASE_DIR, "biblioteca.db")

ABAS = {
    "Obras Chico Xavier": "Espiritismo - Chico Xavier",
    "Obras de Divaldo": "Espiritismo - Divaldo Franco",
    "Obras Diversas": "Obras Diversas",
}

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def importar():
    inseridos = 0
    ignorados = 0

    with get_conn() as conn:
        for aba, categoria in ABAS.items():
            try:
                df = pd.read_excel(PLANILHA, sheet_name=aba)
            except Exception as e:
                logger.error(f"Erro ao ler aba {aba}: {e}")
                continue

            df.columns = [str(c).strip() for c in df.columns]

            col_num = next((c for c in df.columns if "NUMERO" in c.upper() or "NÚMERO" in c.upper()), None)
            col_titulo = next((c for c in df.columns if "TITULO" in c.upper() or "TÍTULO" in c.upper()), None)
            col_autor = next((c for c in df.columns if "AUTOR" in c.upper()), None)
            col_esp = next((c for c in df.columns if "ESPIRITO" in c.upper()), None)
            col_qtd = next((c for c in df.columns if "QT" in c.upper() or "QUANT" in c.upper()), None)

            for _, row in df.iterrows():
                titulo = str(row.get(col_titulo, "")).strip()
                autor = str(row.get(col_autor, "")).strip()

                if not titulo or titulo.lower() == "nan":
                    ignorados += 1
                    continue
                if autor.lower() == "nan":
                    autor = "Desconhecido"

                numero = str(row.get(col_num, "") or "").strip()
                espirito = str(row.get(col_esp, "") or "").strip()
                if numero == "nan": numero = ""
                if espirito == "nan": espirito = ""

                try:
                    qtd = int(float(row.get(col_qtd, 1) or 1))
                except (ValueError, TypeError):
                    qtd = 1

                existe = conn.execute(
                    "SELECT id FROM livros WHERE titulo=? AND autor=?", (titulo, autor)
                ).fetchone()
                if existe:
                    ignorados += 1
                    continue

                try:
                    conn.execute(
                        """INSERT INTO livros(numero, titulo, autor, pelo_espirito, categoria, exemplares, disponivel)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (numero, titulo, autor, espirito, categoria, qtd, qtd)
                    )
                    inseridos += 1
                except sqlite3.Error as e:
                    logger.error(f"Erro ao inserir livro '{titulo}': {e}")
                    ignorados += 1

    print(f"\n✅ Importação concluída!")
    print(f"   Livros inseridos : {inseridos}")
    print(f"   Ignorados/duplos : {ignorados}")

if __name__ == "__main__":
    importar()
