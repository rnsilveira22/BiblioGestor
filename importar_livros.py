import sqlite3
import pandas as pd
import os

PLANILHA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BIBLIOTECA_-_LIVROS_2026__2_.xlsx")
DB_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biblioteca.db")

ABAS = {
    "Obras Chico Xavier": "Espiritismo - Chico Xavier",
    "Obras de Divaldo":   "Espiritismo - Divaldo Franco",
    "Obras Diversas":     "Obras Diversas",
}

def get_conn():
    return sqlite3.connect(DB_FILE)

def importar():
    inseridos = 0
    ignorados = 0

    with get_conn() as conn:
        for aba, categoria in ABAS.items():
            df = pd.read_excel(PLANILHA, sheet_name=aba)
            df.columns = [str(c).strip() for c in df.columns]

            col_num    = next((c for c in df.columns if "NÚMERO" in c.upper() or "NUMERO" in c.upper()), None)
            col_titulo = next((c for c in df.columns if "TÍTULO" in c.upper() or "TITULO" in c.upper()), None)
            col_autor  = next((c for c in df.columns if "AUTOR" in c.upper()), None)
            col_esp    = next((c for c in df.columns if "ESPÍRITO" in c.upper() or "ESPIRITO" in c.upper()), None)
            col_qtd    = next((c for c in df.columns if "QTID" in c.upper() or "QUANT" in c.upper()), None)

            for _, row in df.iterrows():
                titulo = str(row.get(col_titulo, "")).strip()
                autor  = str(row.get(col_autor,  "")).strip()

                if not titulo or titulo.lower() == "nan":
                    ignorados += 1
                    continue
                if autor.lower() == "nan":
                    autor = "Desconhecido"

                numero   = str(row.get(col_num, "") or "").strip()
                espirito = str(row.get(col_esp, "") or "").strip()
                if numero   == "nan": numero   = ""
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

                conn.execute(
                    """INSERT INTO livros(numero, titulo, autor, pelo_espirito, categoria, exemplares, disponivel)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (numero, titulo, autor, espirito, categoria, qtd, qtd)
                )
                inseridos += 1

    print(f"\n✅ Importação concluída!")
    print(f"   Livros inseridos : {inseridos}")
    print(f"   Ignorados/duplos : {ignorados}")

if __name__ == "__main__":
    importar()
