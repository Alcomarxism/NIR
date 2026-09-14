import csv
import matplotlib.pyplot as plt

class MetricsCollector:
    def __init__(self, squad_name):
        self.squad_name = squad_name
        self.history = [] 
        
    def collect_step(self, step_num, squad, sim, step_time):
        total_cells = len(squad.map) * len(squad.map[0])
        known_cells = sum(
            1 for r in range(len(squad.map)) 
            for c in range(len(squad.map[0])) 
            if squad.map[r][c] != '?'
        )
        coverage_pct = round((known_cells / total_cells) * 100, 2)
        
        step_data = {
            "step": step_num,
            "squad": self.squad_name,
            "coverage_pct": coverage_pct,
            "known_cells": known_cells,
            "active_agents": len(squad.agents),
            "step_latency_sec": round(step_time, 3)
        }
        self.history.append(step_data)

    def save_to_csv(self, filename):
        if not self.history:
            return
        keys = self.history[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.history)


def plot_squads_comparison(mestrics_dict, save_path="squads_comparison.png"):
    styles = {
        'RED': {'color': '#e74c3c', 'label': 'Красные (RED)', 'linestyle': '-'},
        'BLUE': {'color': '#3498db', 'label': 'Синие (BLUE)', 'linestyle': '--'}
    }
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle('Сравнительный анализ работы отрядов', fontsize=14, fontweight='bold')

    for name, metrics in mestrics_dict.items():
        history = metrics.history
        if not history:
            continue
            
        steps = [d["step"] for d in history]
        coverage = [d["coverage_pct"] for d in history]
        latency = [d["step_latency_sec"] for d in history]
        style = styles.get(name, {'color': 'black', 'label': f'Отряд {name}', 'linestyle': '-'})
        ax1.plot(
            steps, 
            coverage, 
            label=style['label'], 
            color=style['color'], 
            linestyle=style['linestyle'],
            linewidth=2
        )
        ax2.plot(
            steps, 
            latency, 
            label=style['label'], 
            color=style['color'], 
            linestyle=style['linestyle'],
            alpha=0.7,
            linewidth=1.5
        )
    ax1.set_ylabel('% открытой карты', fontsize=11)
    ax1.set_title('Скорость разведки (Coverage Rate)')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower right')
    ax1.set_ylim(0, 105) 
    ax2.set_xlabel('Шаг симуляции', fontsize=11)
    ax2.set_ylabel('Время шага (сек)', fontsize=11)
    ax2.set_title('Время генерации решений LLM (Latency)')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300) 
    print(f"[Метрики] Сводный график сохранен в файл: {save_path}")