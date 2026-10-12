"""GPU power/VRAM sampling with nvidia-smi (Windows and Linux).

Energy (J) = trapezoidal integral of board power over wall time. Some GPUs (often
laptop GPUs on Windows) report power.draw as [N/A]; the meter then tries
power.draw.instant and power.draw.average. VRAM is recorded even when no power
field is available. If nvidia-smi is missing, every field is None and the run continues.
"""
import shutil
import subprocess
import threading
import time

POWER_FIELDS = ("power.draw", "power.draw.instant", "power.draw.average")


def _num(x):
    try:
        return float(x.strip())
    except (ValueError, AttributeError):
        return None


def probe_power_field(gpu_index: int = 0):
    """Return the first power field that yields a number on this GPU, or None."""
    if not shutil.which("nvidia-smi"):
        return None
    for f in POWER_FIELDS:
        try:
            out = subprocess.run(["nvidia-smi", f"--id={gpu_index}", f"--query-gpu={f}", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=15).stdout
            if _num(out.splitlines()[0] if out else "") is not None:
                return f
        except Exception:
            pass
    return None


class GpuMeter:
    _power_field = "unprobed"

    def __init__(self, interval_ms: int = 200, gpu_index: int = 0):
        self.interval_ms, self.gpu_index = interval_ms, gpu_index
        self.available = shutil.which("nvidia-smi") is not None
        self.samples = []   # (t, watts or None, mem_mib or None)
        self._proc = self._thread = None

    def __enter__(self):
        if self.available:
            if GpuMeter._power_field == "unprobed":
                GpuMeter._power_field = probe_power_field(self.gpu_index)
            fields = ",".join(x for x in (GpuMeter._power_field, "memory.used") if x)
            cmd = ["nvidia-smi", f"--id={self.gpu_index}", f"--query-gpu={fields}",
                   "--format=csv,noheader,nounits", f"--loop-ms={self.interval_ms}"]
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self._thread = threading.Thread(target=self._read, daemon=True)
            self._thread.start()
        self.t0 = time.perf_counter()
        return self

    def _read(self):
        has_power = GpuMeter._power_field is not None
        for line in self._proc.stdout:
            parts = line.strip().split(",")
            w = _num(parts[0]) if has_power and parts else None
            mem = _num(parts[-1]) if parts else None
            if w is not None or mem is not None:
                self.samples.append((time.perf_counter(), w, mem))

    def __exit__(self, *exc):
        self.t1 = time.perf_counter()
        if self._proc:
            self._proc.terminate()
            self._thread.join(timeout=2)
        return False

    def summary(self) -> dict:
        wall = self.t1 - self.t0
        pw = [(t, w) for t, w, _ in self.samples if w is not None]
        mem = [m for _, _, m in self.samples if m is not None]
        energy = (sum((pw[i + 1][0] - pw[i][0]) * (pw[i][1] + pw[i + 1][1]) / 2 for i in range(len(pw) - 1))
                  if len(pw) >= 2 else None)
        return {"wall_s": wall, "energy_j": energy, "mean_power_w": (sum(w for _, w in pw) / len(pw)) if pw else None,
                "peak_vram_mib": max(mem) if mem else None, "power_field": GpuMeter._power_field}


def idle_power(seconds: float = 10.0) -> float:
    """Mean idle board power, to report net energy (measured minus idle x time)."""
    with GpuMeter() as m:
        time.sleep(seconds)
    return m.summary()["mean_power_w"]
