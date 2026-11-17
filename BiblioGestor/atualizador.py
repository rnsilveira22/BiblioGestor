#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiblioGestor - Atualizador Externo (com controle de versão)
==========================================================
Atualiza o sistema sem perder o banco de dados.

Modos de uso:
  1. ONLINE  → Baixa a versão mais recente do GitHub
  2. OFFLINE → Usa o pacote que está na mesma pasta do atualizador
               (pasta "pacote_atualizacao" ou um arquivo .zip)

Controle de versão:
  - Lê a versão instalada (versao.txt ou VERSAO dentro de biblioteca.py)
  - Lê a versão do pacote
  - Se o pacote for MAIS ANTIGO → avisa e pergunta se deseja fazer downgrade
  - Se for a MESMA versão → informa que já está atualizado
  - Se for MAIS NOVO → atualiza normalmente

Arquivos protegidos (NUNCA são sobrescritos):
  - biblioteca.db
  - database/  (backups)
  - .sessao_reinicio.json
"""

from __future__ import annotations

import os
import re
import sys
import shutil
import zipfile
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ─── Configuração ─────────────────────────────────────────────────────────────

REPO = "rnsilveira22/BiblioGestor"
BRANCH = "master"
ZIP_URL = f"https://github.com/{REPO}/archive/refs/heads/{BRANCH}.zip"

PROTEGER = {
    "biblioteca.db",
    "database",
    ".sessao_reinicio.json",
    ".git",
}

PASTA_INTERNA_ZIP = "BiblioGestor-master/BiblioGestor"

# ─── Interface ────────────────────────────────────────────────────────────────

def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def titulo():
    print("=" * 60)
    print("   BiblioGestor — Atualizador")
    print("   Casa Espírita Joana Lima")
    print("=" * 60)
    print()

def ok(msg):
    print(f"  [OK]  {msg}")

def info(msg):
    print(f"  [*]   {msg}")

def aviso(msg):
    print(f"  [!]   {msg}")

def erro(msg):
    print(f"  [ERRO] {msg}")

def pausar():
    print()
    input("  Pressione ENTER para fechar...")

def perguntar_sim_nao(pergunta: str) -> bool:
    while True:
        r = input(f"  {pergunta} [S/N]: ").strip().lower()
        if r in ("s", "sim", "y", "yes"):
            return True
        if r in ("n", "nao", "não", "no"):
            return False
        print("  Responda com S ou N.")

# ─── Controle de versão ───────────────────────────────────────────────────────

def parse_versao(texto: str):
    """Converte '1.2.3' ou 'v1.2.3-beta' em tupla comparável (1, 2, 3)."""
    if not texto:
        return (0,)
    m = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(texto).strip())
    if not m:
        return (0,)
    partes = [int(x) for x in m.groups() if x is not None]
    return tuple(partes) if partes else (0,)


def comparar_versoes(a: str, b: str) -> int:
    """-1 se a < b | 0 se iguais | 1 se a > b"""
    ta, tb = parse_versao(a), parse_versao(b)
    n = max(len(ta), len(tb))
    ta = ta + (0,) * (n - len(ta))
    tb = tb + (0,) * (n - len(tb))
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def ler_versao_pasta(pasta: Path) -> str:
    """
    Lê a versão de uma instalação ou pacote.
    Prioridade: versao.txt → VERSAO em biblioteca.py → 0.0.0
    """
    arq = pasta / "versao.txt"
    if arq.exists():
        try:
            txt = arq.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if txt:
                return txt.lstrip("vV")
        except Exception:
            pass

    py = pasta / "biblioteca.py"
    if py.exists():
        try:
            conteudo = py.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'VERSAO\s*=\s*["\']([^"\']+)["\']', conteudo)
            if m:
                return m.group(1).strip().lstrip("vV")
        except Exception:
            pass

    return "0.0.0"


def formatar_versao(v: str) -> str:
    return v if v != "0.0.0" else "desconhecida"

# ─── Detecção da instalação ───────────────────────────────────────────────────

def parece_instalacao(pasta: Path) -> bool:
    if not pasta.is_dir():
        return False
    return (pasta / "biblioteca.py").exists() or (pasta / "BiblioGestor.exe").exists()


def localizar_instalacao():
    candidatos = []
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    candidatos += [base, base / "BiblioGestor"]
    desktop = Path.home() / "Desktop"
    candidatos += [desktop / "BiblioGestor", desktop / "BiblioGestor" / "BiblioGestor"]
    docs = Path.home() / "Documents"
    candidatos.append(docs / "BiblioGestor")

    for c in candidatos:
        if parece_instalacao(c):
            return c
    return None


def pedir_pasta():
    print("  Não foi possível localizar a instalação automaticamente.")
    print("  Digite o caminho completo da pasta do BiblioGestor")
    print("  (exemplo: C:\\Users\\Usuario\\Desktop\\BiblioGestor)")
    print()
    while True:
        caminho = input("  Pasta: ").strip().strip('"').strip("'")
        if not caminho:
            return None
        p = Path(caminho)
        if parece_instalacao(p):
            return p
        if parece_instalacao(p / "BiblioGestor"):
            return p / "BiblioGestor"
        erro(f"Não encontrei 'biblioteca.py' ou 'BiblioGestor.exe' em:\n         {p}")
        print("  Tente novamente ou deixe em branco para cancelar.\n")

# ─── Backup ───────────────────────────────────────────────────────────────────

def fazer_backup(instalacao: Path):
    db = instalacao / "biblioteca.db"
    if not db.exists():
        aviso("biblioteca.db não encontrado (primeira instalação?). Continuando...")
        return None

    pasta_backup = instalacao / "database"
    pasta_backup.mkdir(exist_ok=True)
    nome = f"biblioteca_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    destino = pasta_backup / nome
    shutil.copy2(db, destino)
    ok(f"Backup criado: database/{nome}")
    return destino

# ─── Fonte da atualização ─────────────────────────────────────────────────────

def tem_pacote_local(base: Path):
    pasta = base / "pacote_atualizacao"
    if pasta.is_dir() and ((pasta / "biblioteca.py").exists() or (pasta / "versao.txt").exists()):
        return pasta

    for z in sorted(base.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
        return z

    for nome in ("atualizacao.zip", "BiblioGestor.zip", "pacote.zip"):
        if (base / nome).exists():
            return base / nome
    return None


def baixar_zip(url: str, destino: Path) -> None:
    info(f"Baixando de: {url}")
    req = Request(url, headers={"User-Agent": "BiblioGestor-Atualizador/2.0"})
    with urlopen(req, timeout=120) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        baixado = 0
        with open(destino, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                baixado += len(chunk)
                if total:
                    pct = baixado * 100 // total
                    print(f"\r  [*]   Progresso: {pct:3d}%  ({baixado // 1024} KB)", end="", flush=True)
                else:
                    print(f"\r  [*]   Baixado: {baixado // 1024} KB", end="", flush=True)
    print()
    ok(f"Download concluído ({baixado // 1024} KB)")


def extrair_fonte(fonte: Path, temp_dir: Path) -> Path:
    if fonte.is_dir():
        if (fonte / "biblioteca.py").exists() or (fonte / "versao.txt").exists():
            return fonte
        raise RuntimeError(f"Pasta de pacote inválida: {fonte}")

    info("Extraindo arquivos...")
    with zipfile.ZipFile(fonte, "r") as zf:
        zf.extractall(temp_dir)

    candidato = temp_dir / PASTA_INTERNA_ZIP
    if (candidato / "biblioteca.py").exists() or (candidato / "versao.txt").exists():
        return candidato

    for root, _, files in os.walk(temp_dir):
        if "biblioteca.py" in files or "versao.txt" in files:
            return Path(root)

    raise RuntimeError("Não foi possível localizar os arquivos do BiblioGestor dentro do pacote.")

# ─── Aplicação da atualização ─────────────────────────────────────────────────

def aplicar_atualizacao(origem: Path, destino: Path) -> int:
    contador = 0
    for item in origem.iterdir():
        nome = item.name
        if nome in PROTEGER:
            info(f"Protegido (não alterado): {nome}")
            continue

        dest_item = destino / nome
        if item.is_dir():
            if dest_item.exists():
                shutil.rmtree(dest_item)
            shutil.copytree(item, dest_item)
            contador += 1
            ok(f"Pasta atualizada: {nome}/")
        else:
            shutil.copy2(item, dest_item)
            contador += 1
            ok(f"Arquivo atualizado: {nome}")
    return contador

# ─── Fluxo principal ──────────────────────────────────────────────────────────

def main():
    limpar()
    titulo()

    if getattr(sys, "frozen", False):
        base_atualizador = Path(sys.executable).resolve().parent
    else:
        base_atualizador = Path(__file__).resolve().parent

    # 1. Localizar instalação
    info("Procurando instalação do BiblioGestor...")
    instalacao = localizar_instalacao()
    if instalacao is None:
        instalacao = pedir_pasta()
    if instalacao is None:
        erro("Atualização cancelada.")
        pausar()
        return

    ok(f"Instalação encontrada: {instalacao}")
    versao_instalada = ler_versao_pasta(instalacao)
    ok(f"Versão instalada: {formatar_versao(versao_instalada)}")
    print()

    # 2. Definir fonte (online ou offline)
    fonte_local = tem_pacote_local(base_atualizador)
    temp_dir = None

    try:
        if fonte_local is not None:
            info("Modo OFFLINE detectado.")
            ok(f"Usando pacote local: {fonte_local.name}")
            temp_dir = Path(tempfile.mkdtemp(prefix="bibliogestor_upd_"))
            pasta_origem = extrair_fonte(fonte_local, temp_dir)
        else:
            info("Modo ONLINE — baixando versão mais recente do GitHub...")
            print()
            temp_dir = Path(tempfile.mkdtemp(prefix="bibliogestor_upd_"))
            zip_path = temp_dir / "atualizacao.zip"
            try:
                baixar_zip(ZIP_URL, zip_path)
            except (URLError, HTTPError, TimeoutError, OSError) as e:
                erro(f"Falha ao baixar a atualização: {e}")
                print()
                aviso("Verifique a conexão com a internet.")
                aviso("Ou use o modo OFFLINE: coloque a pasta 'pacote_atualizacao'")
                aviso("ou um arquivo .zip ao lado deste atualizador.")
                pausar()
                return
            pasta_origem = extrair_fonte(zip_path, temp_dir)

        versao_pacote = ler_versao_pasta(pasta_origem)
        print()
        ok(f"Versão do pacote: {formatar_versao(versao_pacote)}")
        print()

        # 3. Comparar versões
        cmp = comparar_versoes(versao_pacote, versao_instalada)

        if cmp == 0:
            print("=" * 60)
            ok(f"O sistema já está na versão {formatar_versao(versao_instalada)}.")
            info("Nenhuma atualização é necessária.")
            print("=" * 60)
            pausar()
            return

        if cmp < 0:
            # Pacote é MAIS ANTIGO → aviso de downgrade
            print("=" * 60)
            aviso("ATENÇÃO: você está tentando instalar uma versão MAIS ANTIGA.")
            print()
            print(f"     Versão instalada : {formatar_versao(versao_instalada)}")
            print(f"     Versão do pacote : {formatar_versao(versao_pacote)}")
            print()
            aviso("Fazer isso é um DOWNGRADE.")
            aviso("O banco de dados será preservado, mas recursos novos")
            aviso("da versão atual podem deixar de funcionar.")
            print("=" * 60)
            print()
            if not perguntar_sim_nao("Deseja realmente fazer o DOWNGRADE?"):
                info("Operação cancelada pelo usuário.")
                pausar()
                return
            print()
            aviso("Downgrade confirmado. Continuando...")
            print()
        else:
            # Pacote é MAIS NOVO
            info(f"Nova versão disponível: {formatar_versao(versao_instalada)} → {formatar_versao(versao_pacote)}")
            print()
            if not perguntar_sim_nao("Deseja atualizar agora?"):
                info("Atualização cancelada pelo usuário.")
                pausar()
                return
            print()

        # 4. Backup
        info("Fazendo backup do banco de dados...")
        fazer_backup(instalacao)
        print()

        # 5. Aplicar
        info("Aplicando atualização (o banco de dados NÃO será alterado)...")
        print()
        qtd = aplicar_atualizacao(pasta_origem, instalacao)

        # Garante que versao.txt fique gravada na instalação
        try:
            (instalacao / "versao.txt").write_text(versao_pacote + "\n", encoding="utf-8")
        except Exception:
            pass

        print()
        print("=" * 60)
        if cmp < 0:
            ok(f"Downgrade concluído: {formatar_versao(versao_instalada)} → {formatar_versao(versao_pacote)}")
        else:
            ok(f"Atualização concluída: {formatar_versao(versao_instalada)} → {formatar_versao(versao_pacote)}")
        ok(f"{qtd} item(ns) atualizado(s).")
        ok("O banco de dados (biblioteca.db) foi preservado.")
        print()
        info("Agora você pode abrir o BiblioGestor normalmente.")
        print("=" * 60)

    except Exception as e:
        print()
        erro(f"Ocorreu um erro: {e}")
        print()
        traceback.print_exc()
        print()
        aviso("O banco de dados não foi alterado.")
        aviso("Se algo deu errado, restaure o backup da pasta 'database'.")
    finally:
        if temp_dir and Path(temp_dir).exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    pausar()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Operação cancelada pelo usuário.")
        sys.exit(0)
