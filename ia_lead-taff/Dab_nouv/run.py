#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
DABA · REVENUE-AT-RISK DECISION ENGINE — LAUNCHER UNIFIÉ
================================================================================
Lance le backend FastAPI (port 8000) et le frontend Streamlit (port 8501)
en parallèle dans un seul terminal.
================================================================================
"""

import os
import sys
import subprocess
import threading
import time
import signal
import webbrowser
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

BACKEND_PORT = 8000
FRONTEND_PORT = 8501
BACKEND_HOST = "0.0.0.0"
FRONTEND_HOST = "0.0.0.0"

# Couleurs pour le terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text, color=Colors.OKBLUE):
    print(f"{color}{text}{Colors.ENDC}")

# ============================================================================
# FONCTIONS
# ============================================================================

def check_dependencies():
    """Vérifie que les dépendances Python sont installées"""
    try:
        import fastapi
        import streamlit
        import uvicorn
        return True
    except ImportError as e:
        print_colored(f"❌ Dépendance manquante: {e}", Colors.FAIL)
        print_colored("\n📦 Installez les dépendances avec:", Colors.WARNING)
        print_colored("pip install -r requirements.txt", Colors.OKCYAN)
        return False

def get_project_root():
    """Retourne le chemin du projet"""
    return Path(__file__).parent

def launch_backend():
    """Lance le serveur FastAPI"""
    print_colored("\n" + "="*60, Colors.OKGREEN)
    print_colored("🚀 LANCEMENT DU BACKEND FASTAPI", Colors.OKGREEN)
    print_colored("="*60 + "\n", Colors.OKGREEN)
    
    # Le script main.py doit être dans le même dossier que run.py
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "main:app",
        "--host", BACKEND_HOST,
        "--port", str(BACKEND_PORT),
        "--reload",
        "--log-level", "info"
    ]
    
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

def launch_frontend():
    """Lance l'application Streamlit"""
    print_colored("\n" + "="*60, Colors.OKBLUE)
    print_colored("🖥️  LANCEMENT DU FRONTEND STREAMLIT", Colors.OKBLUE)
    print_colored("="*60 + "\n", Colors.OKBLUE)
    
    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run", "app.py",
        "--server.port", str(FRONTEND_PORT),
        "--server.address", FRONTEND_HOST,
        "--server.headless", "true",
        "--browser.serverAddress", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

def monitor_process(process, name):
    """Monitor un processus et affiche sa sortie"""
    for line in process.stdout:
        print(f"[{name}] {line.strip()}")

def open_browser():
    """Ouvre automatiquement le navigateur"""
    time.sleep(4)  # Attend que les serveurs démarrent
    frontend_url = f"http://localhost:{FRONTEND_PORT}"
    backend_url = f"http://localhost:{BACKEND_PORT}/docs"
    
    print_colored("\n" + "="*60, Colors.OKGREEN)
    print_colored("✅ TOUT EST LANCÉ !", Colors.OKGREEN)
    print_colored("="*60, Colors.OKGREEN)
    print_colored(f"📊 Frontend (Streamlit):   {frontend_url}", Colors.OKCYAN)
    print_colored(f"🔧 Backend (FastAPI):      {backend_url}", Colors.OKCYAN)
    print_colored("="*60 + "\n", Colors.OKGREEN)
    
    # Ouvre le frontend dans le navigateur
    try:
        webbrowser.open(frontend_url)
        print_colored("🌐 Navigateur ouvert automatiquement", Colors.OKGREEN)
    except:
        print_colored("⚠️  Ouvrez manuellement le navigateur", Colors.WARNING)

def signal_handler(sig, frame):
    """Gère l'arrêt propre du programme"""
    print_colored("\n\n🛑 Arrêt en cours...", Colors.WARNING)
    sys.exit(0)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print_colored("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🛰️  DABA · REVENUE-AT-RISK DECISION ENGINE                 ║
║                                                               ║
║   Lancement unifié du Backend + Frontend                     ║
║                                                               ║
║   Version: 1.0  |  Mission 2: Branding & Growth              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """, Colors.HEADER)

    # Vérification du répertoire
    project_root = get_project_root()
    os.chdir(project_root)
    print_colored(f"📁 Répertoire du projet: {project_root}", Colors.OKCYAN)

    # Vérification des fichiers nécessaires
    required_files = ["main.py", "app.py"]
    missing_files = [f for f in required_files if not (project_root / f).exists()]
    if missing_files:
        print_colored(f"❌ Fichiers manquants: {', '.join(missing_files)}", Colors.FAIL)
        print_colored("⚠️  Assurez-vous que main.py et app.py sont dans le même dossier.", Colors.WARNING)
        return

    # Vérification des dépendances
    if not check_dependencies():
        return

    # Création des variables d'environnement
    os.environ["API_URL"] = f"http://localhost:{BACKEND_PORT}"

    # Capturer SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Lancement des serveurs
    processes = []
    try:
        # Backend
        backend = launch_backend()
        processes.append(("Backend", backend))
        
        # Petit délai pour que le backend démarre
        time.sleep(2)
        
        # Frontend
        frontend = launch_frontend()
        processes.append(("Frontend", frontend))

        # Monitor les processus dans des threads séparés
        threads = []
        for name, proc in processes:
            thread = threading.Thread(target=monitor_process, args=(proc, name), daemon=True)
            thread.start()
            threads.append(thread)

        # Ouvrir le navigateur
        threading.Timer(3, open_browser).start()

        print_colored("\n⏳ Les serveurs sont en cours de démarrage...", Colors.WARNING)
        print_colored("Appuyez sur Ctrl+C pour arrêter tous les serveurs.\n", Colors.WARNING)

        # Garder le programme en vie
        while True:
            time.sleep(1)
            # Vérifier si un processus est mort
            for name, proc in processes:
                if proc.poll() is not None:
                    print_colored(f"⚠️  Le {name} s'est arrêté.", Colors.WARNING)
                    # Arrêter tout
                    for _, p in processes:
                        p.terminate()
                    return

    except KeyboardInterrupt:
        print_colored("\n\n🛑 Arrêt demandé par l'utilisateur...", Colors.WARNING)
    except Exception as e:
        print_colored(f"❌ Erreur inattendue: {e}", Colors.FAIL)
    finally:
        # Nettoyage
        for name, proc in processes:
            if proc.poll() is None:
                print_colored(f"🛑 Arrêt du {name}...", Colors.WARNING)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print_colored("\n👋 Tous les serveurs sont arrêtés.", Colors.OKGREEN)

if __name__ == "__main__":
    main()