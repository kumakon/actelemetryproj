import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# использование:
#   python analyze_laps.py session_XXXX.csv          -> лучший круг против медианного
#   python analyze_laps.py session_XXXX.csv 5        -> лучший круг против круга №5 (по таблице)

GRID = np.linspace(0, 1, 1000)  # сетка позиций на круге

df = pd.read_csv(sys.argv[1])

# 1. Режем на круги по сбросу позиции (1.0 -> 0.0), а не по счётчику completedLaps
df["seg"] = (df.pos.diff() < -0.5).cumsum()
for seg_id, part in df.groupby("seg"):
    if part.pos.iloc[0] > 0.02 or part.pos.iloc[-1] < 0.98:
        continue
    mine = part.t.iloc[-1] - part.t.iloc[0]
    game = part.iCurrentTime.max() / 1000
    ratio = part.pos.nunique() / len(part)
    print(f"seg {seg_id}: моё {mine:.3f}  игра {game:.3f}  уникальных pos {ratio:.0%}")
laps = []
for seg_id, part in df.groupby("seg"):
    # полный круг: начался около старт/финиша и закончился около него
    if part.pos.iloc[0] > 0.02 or part.pos.iloc[-1] < 0.98:
        continue
    # позиция должна расти; отбрасываем кадры, где она откатывалась (вылет, телепорт)
    pos = np.maximum.accumulate(part.pos.values)
    keep = np.append(True, np.diff(pos) > 0)
    pos = pos[keep]
    t = part.t.values[keep] - part.t.values[0]
    speed = part.speed.values[keep]
    gas = part.gas.values[keep]
    brake = part.brake.values[keep]
    laps.append({
        "id": len(laps),
        "time": t[-1],
        "t_grid": np.interp(GRID, pos, t),
        "speed": np.interp(GRID, pos, speed),
        "gas": np.interp(GRID, pos, gas),
        "brake": np.interp(GRID, pos, brake),
    })

if len(laps) < 2:
    sys.exit("Нужно минимум 2 полных круга")

print("Полные круги:")
for lap in laps:
    m, s = divmod(lap["time"], 60)
    print(f"  #{lap['id']:2d}  {int(m)}:{s:06.3f}")

best = min(laps, key=lambda l: l["time"])
if len(sys.argv) > 2:
    other = laps[int(sys.argv[2])]
else:
    other = sorted(laps, key=lambda l: l["time"])[len(laps) // 2]  # медианный по времени

# 2. Дельта времени по дистанции: сколько секунд ты потерял к лучшему кругу в каждой точке
delta = other["t_grid"] - best["t_grid"]

print(f"\nЛучший: #{best['id']}, сравниваем с #{other['id']}, итоговая дельта {delta[-1]:+.3f} с")

fig, ax = plt.subplots(4, 1, sharex=True, figsize=(10, 9))
ax[0].plot(GRID, best["speed"], label=f"лучший #{best['id']}")
ax[0].plot(GRID, other["speed"], label=f"круг #{other['id']}")
ax[0].set_ylabel("км/ч"); ax[0].legend()
ax[1].plot(GRID, best["gas"]); ax[1].plot(GRID, other["gas"]); ax[1].set_ylabel("газ")
ax[2].plot(GRID, best["brake"]); ax[2].plot(GRID, other["brake"]); ax[2].set_ylabel("тормоз")
ax[3].plot(GRID, delta); ax[3].axhline(0, color="gray", lw=0.5)
ax[3].set_ylabel("дельта, с"); ax[3].set_xlabel("позиция на круге")
plt.tight_layout()
plt.figure(figsize=(10, 4))
for lap in laps:
    if lap is best:
        continue
    plt.plot(GRID, lap["t_grid"] - best["t_grid"], label=f"#{lap['id']}")
plt.axhline(0, color="gray", lw=0.5)
plt.xlabel("позиция на круге"); plt.ylabel("дельта к лучшему, с")
plt.legend(ncol=3)
plt.show()
