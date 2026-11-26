#!/usr/bin/env python3
"""Testes de ig_metrics.py (bônus B4 e a detect_backoffs da pergunta 4.3).

    python3 -m pytest tests/        ou        python3 tests/test_ig_metrics.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ig_starter"))
from ig_metrics import (detect_backoffs, inefficiency, itakura_saito, optimum,  # noqa: E402
                        unfairness)

RNG = np.random.default_rng(20261125)


# ------------------------------------------------------------------ B4: identidade (11)
def _identidade(mu, pontos=1000):
    mu = np.asarray(mu, float)
    pior = 0.0
    for _ in range(pontos):
        x = RNG.uniform(0.01, 100.0, mu.size)
        c = RNG.uniform(1.0, 200.0)
        D = itakura_saito(x, optimum(mu, c))
        U, I = unfairness(x, mu), inefficiency(x, mu, c)
        assert U >= -1e-12 and I >= -1e-12
        pior = max(pior, abs(D - (U + I)))
    return pior


def test_pitagoras_mu_uniforme():
    for n in (2, 3, 5, 10):
        assert _identidade(np.ones(n)) < 1e-10


def test_pitagoras_mu_heterogeneo():
    assert _identidade([1, 1 / 4, 1 / 9]) < 1e-10


def test_invariancia_por_escala():
    for mu in (np.ones(3), np.array([1, 1 / 4, 1 / 9])):
        for _ in range(1000):
            x = RNG.uniform(0.01, 100.0, 3)
            lam = 10 ** RNG.uniform(-3, 3)
            assert abs(unfairness(lam * x, mu) - unfairness(x, mu)) < 1e-10


def test_exemplo_da_secao_3():
    # x = (8, 2), c = 10: U = 2 log 1,25 ~ 0,446 e I = 0; x = (4, 1): U igual, I ~ 0,386
    mu = np.ones(2)
    assert abs(unfairness([8, 2], mu) - 2 * np.log(1.25)) < 1e-12
    assert abs(inefficiency([8, 2], mu, 10)) < 1e-12
    assert abs(unfairness([4, 1], mu) - unfairness([8, 2], mu)) < 1e-12
    assert abs(inefficiency([4, 1], mu, 10) - 2 * (0.5 - np.log(0.5) - 1)) < 1e-12


def test_minimo_so_no_otimo():
    mu = np.array([1.0, 2.0, 3.0])
    xs = optimum(mu, 12.0)
    assert abs(unfairness(xs, mu)) < 1e-12 and abs(inefficiency(xs, mu, 12.0)) < 1e-12


# ------------------------------------------------------------------ detect_backoffs
def _dente(picos, dt=0.01, rtt=0.05, beta=0.5, prr=0.05, ssthresh_primeiro=True):
    """cwnd sintética: sobe 1 pacote/RTT, cai para beta*pico ao longo de prr segundos."""
    t, w, ss = [], [], []
    cur, s, tt = picos[0] * beta, (np.nan if not ssthresh_primeiro else np.nan), 0.0
    eventos = []
    for p in picos:
        while cur < p:
            t.append(tt); w.append(cur); ss.append(s)
            cur += dt / rtt; tt += dt
        eventos.append(tt)
        s = max(2, int(beta * p))
        alvo, passos = beta * p, max(1, int(prr / dt))
        for j in range(passos):
            t.append(tt); w.append(p - (p - alvo) * (j + 1) / passos); ss.append(s)
            tt += dt
        cur = alvo
    return np.array(t), np.floor(np.array(w)), np.array(ss), np.array(eventos)


def test_backoffs_picos_iguais():
    # mesmo pico todo ciclo -> ssthresh nunca muda depois do primeiro corte
    t, w, ss, ev = _dente([40] * 6)
    red, to = detect_backoffs(t, w, ss)
    assert len(red) == len(ev) and len(to) == 0
    assert np.all(np.abs(red - ev) < 0.05)


def test_backoffs_picos_diferentes():
    t, w, ss, ev = _dente([30, 50, 35, 60, 45])
    red, _ = detect_backoffs(t, w, ss)
    assert len(red) == len(ev)


def test_backoffs_cubic_beta07():
    t, w, ss, ev = _dente([60, 60, 70, 60], beta=0.7)
    red, _ = detect_backoffs(t, w, ss)
    assert len(red) == len(ev)


def test_backoffs_sem_ssthresh():
    t, w, _, ev = _dente([40, 50, 40])
    red, _ = detect_backoffs(t, w, None)
    assert len(red) == len(ev)


def test_timeout():
    t = np.arange(0, 3, 0.01)
    w = np.where(t < 1.0, 40.0, 1.0)
    w[t >= 2.0] = 1 + (t[t >= 2.0] - 2.0) * 10
    ss = np.where(t < 1.0, np.nan, 20.0)
    red, to = detect_backoffs(t, w, ss)
    assert len(to) == 1 and len(red) == 0


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_") and callable(f):
            try:
                f()
                print(f"ok    {nome}")
            except AssertionError as e:
                falhas += 1
                print(f"FALHA {nome} {e}")
    sys.exit(1 if falhas else 0)
