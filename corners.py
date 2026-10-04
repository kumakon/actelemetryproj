import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

from laplib import GRID, load_laps

# использование:
#   python corners.py session_XXXX.csv         -> эталон = лучший круг по времени
#   python corners.py session_XXXX.csv 8       -> эталон = круг №8 (по таблице)

PROMINENCE = 25   # км/ч: насколько провал скорости должен быть глубже окружения, чтобы считаться поворотом
MIN_DIST = 15     # минимум точек сетки между двумя поворотами (1000 точек = круг)
SMOOTH = 7        # окно сглаживания скорости, точек


def smooth(x, n=SMOOTH):
    return np.convolve(x, np.ones(n) / n, mode="same")


laps = load_laps(sys.argv[1])
if len(laps) < 2:
    sys.exit("Нужно минимум 2 полных круга")

if len(sys.argv) > 2:
    ref = laps[int(sys.argv[2])]
else:
    ref = min(laps, key=lambda l: l["time"])

# 1. Повороты = глубокие локальные минимумы скорости эталона
v = smooth(ref["speed"])
minima, _ = find_peaks(-v, prominence=PROMINENCE, distance=MIN_DIST)
if len(minima) == 0:
    sys.exit("Повороты не найдены, уменьши PROMINENCE")

# 2. Граница сегмента = точка максимальной скорости перед каждым минимумом
#    (то есть конец прямой / начало торможения)
bounds = []
prev = 0
for m in minima:
    bounds.append(prev + int(np.argmax(v[prev:m + 1])))
    prev = m
# сегменты: [0, b0), [b0, b1), ..., [b_last, конец]
edges = [0] + bounds + [len(GRID) - 1]
names = ["S/F->T1"] + [f"T{i + 1}" for i in range(len(minima))]
print(f"Эталон: круг #{ref['id']}, найдено поворотов: {len(minima)}")
print("Границы сегментов (позиция на круге):",
      ", ".join(f"{GRID[e]:.3f}" for e in edges))
print("Сегмент S/F->T1: от линии старта до начала торможения в первый поворот.")
print("Сегмент Tk: торможение, апекс и разгон до начала торможения в следующий поворот.\n")


def brake_onset(lap, start, apex):
    """Первая позиция торможения (brake > 0.5) между границей и апексом, в долях круга."""
    seg = lap["brake"][start:apex + 1]
    idx = np.where(seg > 0.5)[0]
    return GRID[start + idx[0]] if len(idx) else np.nan


# 3. Потери по сегментам для каждого круга относительно эталона
rows = []
seg_times = []
for lap in laps:
    delta = lap["t_grid"] - ref["t_grid"]
    losses = [delta[edges[k + 1]] - delta[edges[k]] for k in range(len(names))]
    seg_times.append([lap["t_grid"][edges[k + 1]] - lap["t_grid"][edges[k]]
                      for k in range(len(names))])
    rows.append([lap["id"], lap["time"]] + losses)

cols = ["круг", "время"] + names
table = pd.DataFrame(rows, columns=cols).sort_values("время")
pd.set_option("display.width", 200)
print("Потеря времени относительно эталона по сегментам, с (+ значит медленнее):")
print(table.round(3).to_string(index=False))

# контроль: сумма потерь по сегментам должна совпадать с итоговой дельтой
for lap, r in zip(laps, rows):
    total = lap["t_grid"][-1] - ref["t_grid"][-1]
    assert abs(sum(r[2:]) - total) < 1e-6, "сумма сегментов не сошлась"

# 4. Где ты стабильно теряешь: среднее и разброс потерь по кругам
others = table[table["круг"] != ref["id"]]
summary = pd.DataFrame({
    "сегмент": names,
    "в среднем, с": others[names].mean().values,
    "разброс (std), с": others[names].std().values,
})
print("\nСредняя потеря по сегментам (без эталона):")
print(summary.round(3).to_string(index=False))

# 5. Теоретический лучший круг: лучший результат в каждом сегменте из всех кругов
seg_times = np.array(seg_times)
best_per_seg = seg_times.min(axis=0)
theoretical = best_per_seg.sum()
print(f"\nЛучший круг: {ref['time']:.3f} с, теоретический (по лучшим сегментам): "
      f"{theoretical:.3f} с, потенциал {ref['time'] - theoretical:.3f} с")

# 6. Метрики поворотов для выбранного круга: вход, минимум, точка начала торможения
target = laps[int(sys.argv[3])] if len(sys.argv) > 3 else sorted(laps, key=lambda l: l["time"])[len(laps) // 2]
print(f"\nРазбор круга #{target['id']} против эталона #{ref['id']}:")
detail = []
for k, m in enumerate(minima):
    s, e = edges[k + 1], edges[k + 2]
    delta = target["t_grid"] - ref["t_grid"]
    b_t = brake_onset(target, s, m)
    b_r = brake_onset(ref, s, m)
    detail.append({
        "поворот": names[k + 1],
        "потеря, с": delta[e] - delta[s],
        "v входа": target["speed"][s],
        "v входа эт.": ref["speed"][s],
        "v мин": target["speed"][s:e].min(),
        "v мин эт.": ref["speed"][s:e].min(),
        "торможение, ‰ круга": (b_t - b_r) * 1000,
    })
print(pd.DataFrame(detail).round(2).to_string(index=False))
print("‰ круга: отрицательное значение значит, что торможение начато раньше эталона.")

# 7. Графики
fig, ax = plt.subplots(2, 1, figsize=(10, 7))
ax[0].plot(GRID, ref["speed"], label=f"эталон #{ref['id']}")
ax[0].plot(GRID, target["speed"], label=f"круг #{target['id']}")
for k, e in enumerate(edges):
    ax[0].axvline(GRID[e], color="gray", lw=0.6, ls="--")
for k, n in enumerate(names):
    ax[0].text(GRID[(edges[k] + edges[k + 1]) // 2], ax[0].get_ylim()[1] * 0.95, n,
               ha="center", va="top", fontsize=8)
ax[0].set_ylabel("км/ч"); ax[0].legend(loc="lower right")
ax[1].bar(range(len(names)), summary["в среднем, с"], yerr=summary["разброс (std), с"], capsize=3)
ax[1].set_xticks(range(len(names))); ax[1].set_xticklabels(names)
ax[1].axhline(0, color="gray", lw=0.5)
ax[1].set_ylabel("средняя потеря, с")
ax[1].set_xlabel("сегмент (график сверху идёт по позиции, этот нет)")
plt.tight_layout()
plt.show()
