"""
LUIZxFFINFO - Entrypoint de Execução
Permite iniciar o servidor tanto via `python app.py` quanto via `python main.py`.
"""
import os
import sys
import threading
import time
from main import app, start_background_tasks

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 55)
    print("🚀 LUIZxFFINFO - Servidor Iniciado (app.py)")
    print("=" * 55)

    bg = threading.Thread(target=start_background_tasks, daemon=True)
    bg.start()

    time.sleep(3)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
