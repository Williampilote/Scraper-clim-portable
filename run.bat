@echo off
REM ============================================================
REM  Scraper Clim Portable - lanceur Windows (double-clic)
REM  Installe tout la premiere fois, puis surveille en boucle.
REM ============================================================
setlocal
cd /d "%~dp0"
echo === Scraper Clim Portable ===
echo.

REM 1) Verifie que Python est installe
where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
  echo Installe-le depuis https://www.python.org/downloads/
  echo IMPORTANT : coche la case "Add Python to PATH" pendant l'installation.
  echo Puis relance ce fichier run.bat.
  pause
  exit /b 1
)

REM 2) Cree l'environnement Python isole la premiere fois
if not exist .venv (
  echo Creation de l'environnement Python...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

REM 3) Installe les dependances + le navigateur Chromium
echo Installation des dependances (peut prendre 1-2 min la 1ere fois)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
python -m playwright install chromium

REM 4) Verifie la configuration email
if not exist .env (
  copy .env.example .env >nul
  echo.
  echo [ACTION REQUISE] Un fichier .env vient d'etre cree.
  echo Ouvre-le avec le Bloc-notes, renseigne la ligne SMTP_PASSWORD=...
  echo puis relance run.bat.
  notepad .env
  pause
  exit /b 1
)

REM 5) Lance la surveillance en boucle (toutes les 15 min)
echo.
echo Surveillance demarree. Laisse cette fenetre OUVERTE.
echo (Ferme-la ou fais Ctrl+C pour arreter.)
echo.
python -m src.main --loop --interval 900
pause
