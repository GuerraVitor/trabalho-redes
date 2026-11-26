"""Funções comuns às análises: caminhos, intervalo de confiança, leitura do ping."""
from __future__ import annotations

import os
import re
import sys

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "ig_starter"))

# quantis t de Student (bicaudal, 95%) por graus de liberdade
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 30: 2.042}


def t95(gl: int) -> float:
    if gl in _T95:
        return _T95[gl]
    menores = [k for k in _T95 if k <= gl]
    return _T95[max(menores)] if menores and gl < 30 else 1.96


def media_ic(valores) -> tuple[float, float, int]:
    """(média, meia-largura do IC 95% pela t de Student, n). IC = nan se n < 2."""
    v = np.asarray([x for x in valores if np.isfinite(x)], float)
    if v.size == 0:
        return np.nan, np.nan, 0
    if v.size == 1:
        return float(v[0]), np.nan, 1
    return float(v.mean()), float(t95(v.size - 1) * v.std(ddof=1) / np.sqrt(v.size)), int(v.size)


def fmt_ic(m: float, h: float, casas: int = 2) -> str:
    if not np.isfinite(h):
        return f"{m:.{casas}f}"
    return f"{m:.{casas}f} ± {h:.{casas}f}"


PING_RE = re.compile(r"^\[(\d+\.\d+)\].*time=([\d.]+) ms")


def load_ping(path: str, t0: float) -> pd.DataFrame:
    rows = []
    with open(path) as fh:
        for line in fh:
            m = PING_RE.match(line)
            if m:
                rows.append((float(m.group(1)) - t0, float(m.group(2))))
    return pd.DataFrame(rows, columns=["t_s", "rtt_ms"])


def reps(diretorio: str) -> list[str]:
    """Subdiretórios repN com metadata.json, em ordem numérica."""
    if not os.path.isdir(diretorio):
        return []
    out = [os.path.join(diretorio, d) for d in os.listdir(diretorio)
           if d.startswith("rep") and os.path.exists(os.path.join(diretorio, d, "metadata.json"))]
    return sorted(out, key=lambda p: int(os.path.basename(p)[3:]))
