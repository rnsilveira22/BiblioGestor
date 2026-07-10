#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo ""
echo " ============================================"
echo "    Build do BiblioGestor - App macOS"
echo " ============================================"
echo ""

# ── Verifica Python ──
if ! command -v python3 &>/dev/null; then
    echo " [ERRO] Python3 nao encontrado."
    echo "        Instale Python 3.7 (ultima versao compativel com macOS 10.10)"
    exit 1
fi
echo " [OK] Python3 encontrado: $(python3 --version)"

# ── Cria virtualenv (evita PEP 668 em Debian/Ubuntu) ──
VENV="$DIR/.venv_build"
if [ ! -d "$VENV" ]; then
    echo " [*] Criando virtual environment..."
    python3 -m venv "$VENV"
fi
echo " [OK] Virtual env pronto"
source "$VENV/bin/activate"

# ── Instala/verifica PyInstaller ──
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo " [*] Instalando PyInstaller..."
    pip install pyinstaller
fi
echo " [OK] PyInstaller pronto"

# ── Instala dependencias do projeto ──
echo " [*] Verificando dependencias..."
pip install pandas openpyxl Pillow bcrypt --quiet
echo " [OK] Dependencias prontas"

# ── Remove build anterior ──
rm -rf dist build *.spec

# ── Executa o PyInstaller ──
echo ""
echo " [*] Compilando .app (pode levar alguns minutos)..."
echo ""

pyinstaller --noconfirm --onefile --windowed \
    --name "BiblioGestor" \
    --add-data "biblioteca.db:." \
    --hidden-import "pandas" \
    --hidden-import "openpyxl" \
    --hidden-import "PIL" \
    --hidden-import "PIL._tkinter_finder" \
    --hidden-import "bcrypt" \
    --collect-submodules "PIL" \
    --osx-bundle-identifier "org.bibliogestor.app" \
    "biblioteca.py"

# ── Limpa venv (opcional: comente se quiser manter) ──
echo " [*] Limpando virtual environment..."
rm -rf "$VENV"

echo ""
echo " ============================================"
echo "    Build concluido com sucesso!"
echo " ============================================"
echo ""
echo "  Executavel gerado em:"
echo "    $DIR/dist/BiblioGestor"
echo ""
echo "  Para distribuir em outro Mac:"
echo "    1. Copie o arquivo 'dist/BiblioGestor' para o Mac destino"
echo "    2. Execute (pode ser necessario dar permissao: xattr -rd com.apple.quarantine)"
echo ""
echo "  OBS: macOS 10.10 requer Python 3.7 e PyInstaller <= 3.6"
echo "       Para macOS mais recente use Python 3.12+ e PyInstaller mais novo."
echo ""
