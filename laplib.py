import numpy as np
import pandas as pd

GRID = np.linspace(0, 1, 1000)  # общая сетка позиций на круге


def load_laps(path):
    """Читает CSV сессии, режет на полные круги и приводит их к общей сетке позиций."""
    df = pd.read_csv(path)

    # круги режем по сбросу позиции (1.0 -> 0.0), а не по счётчику completedLaps
    df["seg"] = (df.pos.diff() < -0.5).cumsum()

    laps = []
    for _, part in df.groupby("seg"):
        # полный круг: начался около старт/финиша и закончился около него
        if part.pos.iloc[0] > 0.02 or part.pos.iloc[-1] < 0.98:
            continue
        # позиция должна расти; кадры, где она откатывалась, отбрасываем
        pos = np.maximum.accumulate(part.pos.values)
        keep = np.append(True, np.diff(pos) > 0)
        pos = pos[keep]
        t = part.t.values[keep] - part.t.values[0]
        laps.append({
            "id": len(laps),
            "time": t[-1],
            "t_grid": np.interp(GRID, pos, t),
            "speed": np.interp(GRID, pos, part.speed.values[keep]),
            "gas": np.interp(GRID, pos, part.gas.values[keep]),
            "brake": np.interp(GRID, pos, part.brake.values[keep]),
        })
    return laps
