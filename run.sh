#!/usr/bin/env bash
# ============================================================
#  Scraper Clim Portable - lanceur macOS / Linux
#  Installe tout la premiere fois, puis surveille en boucle.
# ============================================================
set -e
cd "$(dirname "$0")"
echo "=== Scraper Clim Portable ==="
echo

# 1) Verifie Python 3
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERREUR] Python 3 n'est pas installe."
  echo "macOS : installe-le via https://www.python.org/downloads/ ou 'brew install python'."
  exit 1
fi

# 2) Environnement Python isole
if [ ! -d .venv ]; then
  echo "Creation de l'environnement Python..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 3) Dependances + navigateur Chromium
echo "Installation des dependances (peut prendre 1-2 min la 1ere fois)..."
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt
python -m playwright install chromium

# 4) Configuration email
if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "[ACTION REQUISE] Un fichier .env vient d'etre cree."
  echo "Ouvre-le, renseigne la ligne SMTP_PASSWORD=... puis relance ./run.sh"
  exit 1
fi

# 5) Surveillance en boucle (toutes les 15 min)
echo
echo "Surveillance demarree. Laisse ce terminal OUVERT (Ctrl+C pour arreter)."
echo
python -m src.main --loop --interval 900
