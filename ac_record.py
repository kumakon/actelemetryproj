import ctypes, mmap, time, csv, datetime


class Physics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
    ]


class Graphics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("iCurrentTime", ctypes.c_int),
        ("iLastTime", ctypes.c_int),
        ("iBestTime", ctypes.c_int),
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int),
        ("currentSectorIndex", ctypes.c_int),
        ("lastSectorTime", ctypes.c_int),
        ("numberOfLaps", ctypes.c_int),
        ("tyreCompound", ctypes.c_wchar * 33),
        ("replayTimeMultiplier", ctypes.c_float),
        ("normalizedCarPosition", ctypes.c_float),
    ]


phys_map = mmap.mmap(-1, ctypes.sizeof(Physics), tagname="acpmf_physics")
gfx_map = mmap.mmap(-1, ctypes.sizeof(Graphics), tagname="acpmf_graphics")

fname = datetime.datetime.now().strftime("session_%Y%m%d_%H%M%S.csv")
cols = ["t", "lap", "pos", "speed", "gas", "brake", "steer", "gear", "rpm", "iCurrentTime"]

last_id = -1
t0 = time.perf_counter()
with open(fname, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(cols)
    print("Запись в", fname, "(Ctrl+C для остановки)")
    try:
        while True:
            p = Physics.from_buffer_copy(phys_map[:ctypes.sizeof(Physics)])
            g = Graphics.from_buffer_copy(gfx_map[:ctypes.sizeof(Graphics)])
            if p.packetId != last_id and g.status == 2:  # 2 = live, едем на трассе
                last_id = p.packetId
                w.writerow([
                    round(time.perf_counter() - t0, 4), g.completedLaps,
                    round(g.normalizedCarPosition, 5), round(p.speedKmh, 2),
                    round(p.gas, 3), round(p.brake, 3), round(p.steerAngle, 2),
                    p.gear, p.rpms, g.iCurrentTime,
                ])
            time.sleep(0.002)
    except KeyboardInterrupt:
        print("Готово")
