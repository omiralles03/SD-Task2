import json
import matplotlib.pyplot as plt
import os

# Archivo generado por el controller
DATA_FILE = 'plot_data.json'

def plot_backlog():
    if not os.path.exists(DATA_FILE):
        print(f" [!] Error: No se encontró el archivo {DATA_FILE}")
        return

    # Cargar los datos
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    temps = data.get("times", [])
    backlog = data.get("backlogs", [])

    if not temps or not backlog:
        print(" [!] No hay suficientes datos para generar la gráfica.")
        return

    # Crear la gráfica
    plt.figure(figsize=(10, 6))
    plt.plot(temps, backlog, marker='o', linestyle='-', linewidth=2.5, color='#1f77b4', label='Mensajes en ticket_queue')
    plt.fill_between(temps, backlog, color='#1f77b4', alpha=0.1)

    # Personalización
    plt.title("Evolución de la cola (Backlog) vs Tiempo", fontsize=14, pad=15)
    plt.xlabel("Tiempo transcurrido (segundos)", fontsize=12)
    plt.ylabel("Mensajes pendientes (Backlog)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()

    # Guardar y mostrar
    plt.savefig('queue_backlog_vs_time.png', dpi=300)
    print(" [v] Gráfica guardada como 'queue_backlog_vs_time.png'.")
    plt.show()

if __name__ == "__main__":
    plot_backlog()