#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiblioGestor - Atualizador Externo
==================================
Atualiza o sistema sem perder o banco de dados.

Modos de uso:
  1. ONLINE  → Baixa a versão mais recente do GitHub
  2. OFFLINE → Usa o pacote que está na mesma pasta do atualizador
               (coloque a pasta "pacote_atualizacao" ou um arquivo .zip ao lado)

Como usar (cliente):
  - Feche o BiblioGestor
  - Execute este arquivo (ou o .exe)
  - Escolha a pasta onde o BiblioGestor está instalado (se não detectar)
  - Aguarde a mensagem de sucesso
  - Abra o BiblioGestor novamente

Arquivos protegidos (NUNCA são sobrescritos):
  - biblioteca.db
  - database/  (backups)
  - .sessao_reinicio.json
"""

import os
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
# URL do ZIP oficial do repositório (sempre a versão mais recente do branch)
ZIP_URL = f"https://github.com/{REPO}/archive/refs/heads/{BRANCH}.zip"

# Pastas/arquivos que NUNCA devem ser sobrescritos
PROTEGER = {
    "biblioteca.db",
    "database",
    ".sessao_reinicio.json",
    ".git",
}

# Nome da pasta interna dentro do ZIP do GitHub
# (GitHub gera: BiblioGestor-master/BiblioGestor/...)
PASTA_INTERNA_ZIP = "BiblioGestor-master/BiblioGestor"

# ─── Utilitários de interface ─────────────────────────────────────────────────

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

# ─── Detecção da instalação ───────────────────────────────────────────────────

def parece_instalacao(pasta: Path) -> bool:
    """Verifica se a pasta parece ser uma instalação válida do BiblioGestor."""
    if not pasta.is_dir():
        return False
    # Precisa ter o arquivo principal
    if (pasta / "biblioteca.py").exists():
        return True
    # Ou o executável gerado pelo PyInstaller
    if (pasta / "BiblioGestor.exe").exists():
        return True
    return False

def localizar_instalacao() -> Path | None:
    """Tenta achar a instalação automaticamente."""
    candidatos = []

    # 1. Pasta do próprio atualizador
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    candidatos.append(base)
    candidatos.append(base / "BiblioGestor")

    # 2. Área de Trabalho do usuário
    desktop = Path.home() / "Desktop"
    candidatos.append(desktop / "BiblioGestor")
    candidatos.append(desktop / "BiblioGestor" / "BiblioGestor")

    # 3. Documentos
    docs = Path.home() / "Documents"
    candidatos.append(docs / "BiblioGestor")

    for c in candidatos:
        if parece_instalacao(c):
            return c
    return None

def pedir_pasta() -> Path | None:
    """Pede ao usuário a pasta de instalação."""
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
        # Tenta uma subpasta comum
        if parece_instalacao(p / "BiblioGestor"):
            return p / "BiblioGestor"
        erro(f"Não encontrei 'biblioteca.py' ou 'BiblioGestor.exe' em:\n         {p}")
        print("  Tente novamente ou deixe em branco para cancelar.\n")

# ─── Backup ───────────────────────────────────────────────────────────────────

def fazer_backup(instalacao: Path) -> Path | None:
    """Cria backup do banco de dados."""
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

def tem_pacote_local(base: Path) -> Path | None:
    """Procura pacote offline na pasta do atualizador."""
    # Pasta "pacote_atualizacao"
    pasta = base / "pacote_atualizacao"
    if pasta.is_dir() and (pasta / "biblioteca.py").exists():
        return pasta

    # Qualquer ZIP na pasta
    for z in base.glob("*.zip"):
        return z

    # ZIP específico
    for nome in ("atualizacao.zip", "BiblioGestor.zip", "pacote.zip"):
        if (base / nome).exists():
            return base / nome

    return None

def baixar_zip(url: str, destino: Path) -> None:
    """Baixa o ZIP do GitHub com barra de progresso simples."""
    info(f"Baixando de: {url}")
    req = Request(url, headers={"User-Agent": "BiblioGestor-Atualizador/1.0"})
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
    """
    Extrai/prepara a pasta com os arquivos novos.
    Retorna o Path da pasta que contém biblioteca.py
    """
    if fonte.is_dir():
        # Já é pasta (modo offline com pacote_atualizacao)
        if (fonte / "biblioteca.py").exists():
            return fonte
        raise RuntimeError(f"Pasta de pacote inválida: {fonte}")

    # É um ZIP
    info("Extraindo arquivos...")
    with zipfile.ZipFile(fonte, "r") as zf:
        zf.extractall(temp_dir)

    # Tenta a estrutura padrão do GitHub
    candidato = temp_dir / PASTA_INTERNA_ZIP
    if (candidato / "biblioteca.py").exists():
        return candidato

    # Procura biblioteca.py em qualquer lugar extraído
    for root, _, files in os.walk(temp_dir):
        if "biblioteca.py" in files:
            return Path(root)

    raise RuntimeError("Não foi possível localizar 'biblioteca.py' dentro do pacote.")

# ─── Aplicação da atualização ─────────────────────────────────────────────────

def aplicar_atualizacao(origem: Path, destino: Path) -> int:
    """
    Copia arquivos da origem para o destino, respeitando a lista de proteção.
    Retorna a quantidade de arquivos atualizados.
    """
    contador = 0
    for item in origem.iterdir():
        nome = item.name

        # Proteção
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

    # Local do atualizador
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
    print()

    # 2. Backup
    info("Fazendo backup do banco de dados...")
    fazer_backup(instalacao)
    print()

    # 3. Definir fonte (online ou offline)
    fonte_local = tem_pacote_local(base_atualizador)
    temp_dir = None
    pasta_origem = None

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
            except (URLError, HTTPError, TimeoutError) as e:
                erro(f"Falha ao baixar a atualização: {e}")
                print()
                aviso("Verifique a conexão com a internet.")
                aviso("Ou use o modo OFFLINE: coloque a pasta 'pacote_atualizacao'")
                aviso("ou um arquivo .zip ao lado deste atualizador.")
                pausar()
                return
            pasta_origem = extrair_fonte(zip_path, temp_dir)

        print()
        info(f"Arquivos novos em: {pasta_origem}")
        print()

        # 4. Aplicar
        info("Aplicando atualização (o banco de dados NÃO será alterado)...")
        print()
        qtd = aplicar_atualizacao(pasta_origem, instalacao)

        print()
        print("=" * 60)
        ok(f"Atualização concluída! {qtd} item(ns) atualizado(s).")
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
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    pausar()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Atualização cancelada pelo usuário.")
        sys.exit(0)
