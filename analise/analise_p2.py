#!/usr/bin/env python3
"""Análise da Parte 2 (perguntas 2.2–2.4): RTT, fila, vazão e dente de serra da cwnd.

    python3 analise/analise_p2.py dados/p2

Para cada q (subpastas qNN) e cada repetição, calcula:
  * RTT do ping: média e desvio (descartando os primeiros DESCARTE s, fase de slow start);
  * fila: média e máximo; RTT previsto = RTT_prop + fila_média * (1500*8 / C);
  * vazão do fluxo (bytes_acked) comparada com C;
  * pico e vale da cwnd em cada redução (pico = máx. da cwnd 1 s antes da mudança de
    ssthresh; vale = mín. da cwnd até a próxima redução), comparados com BDP + q e beta = 1/2;
  * loadavg no fim (sanidade da CPU).
Depois agrega as repetições (média ± IC 95%) e confere as faixas esperadas (caixa “Erros
comuns” do enunciado): 20 ms <= RTT <= 20 + 8q ms, máximo da fila ~ q, vazão <= C.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comum import fmt_ic, load_ping, media_ic, reps  # noqa: E402
from ig_metrics import detect_backoffs, load_run, throughput_mbps  # noqa: E402

DESCARTE = 20.0  # s iniciais descartados (slow start)
MTU = 1500


def analisa_rodada(run: str) -> dict:
    flows, meta = load_run(run)
    a = meta["args"]
    C = float(a["bw"]) * 1e6
    q = int(a["buffer"])
    rtt_prop = float(meta["rtt_prop_ms_por_fluxo"][0])
    ms_por_pacote = MTU * 8 / C * 1e3
    bdp = C * rtt_prop / 1e3 / (MTU * 8)
    df = next(iter(flows.values()))
    r = {"q": q, "C_mbps": C / 1e6, "rtt_prop_ms": rtt_prop, "ms_por_pacote": ms_por_pacote,
         "bdp_pkts": bdp, "loadavg_fim": meta.get("loadavg_fim", [np.nan])[0]}

    ping = load_ping(os.path.join(run, "ping.txt"), float(meta["inicio_epoch"]))
    p = ping[ping["t_s"] >= DESCARTE]["rtt_ms"]
    r.update(rtt_media=p.mean(), rtt_desvio=p.std(), rtt_min=p.min(), rtt_max=p.max())

    fila = np.loadtxt(os.path.join(run, "queue.csv"), delimiter=",", skiprows=1, ndmin=2)
    f = fila[fila[:, 0] >= DESCARTE]
    r.update(fila_media=f[:, 1].mean(), fila_max=fila[:, 1].max(),
             descartes=int(fila[-1, 3] - fila[0, 3]))
    # atraso de fila = ocupação / taxa de serviço. Em pacotes (8 ms cada) é uma
    # aproximação; em bytes é exato, porque a fila também guarda pings (98 B no fio).
    r["rtt_previsto"] = rtt_prop + r["fila_media"] * ms_por_pacote
    r["rtt_previsto_bytes"] = rtt_prop + f[:, 2].mean() * 8 / C * 1e3
    cheia = fila[fila[:, 1] >= q]
    r["bytes_por_pacote_fila_cheia"] = (cheia[:, 2] / cheia[:, 1]).mean() if len(cheia) else np.nan
    # pings dentro da fila cheia: 1514 (1 - f) + 98 f = bytes por pacote
    r["pings_na_fila_cheia"] = q * (1514 - r["bytes_por_pacote_fila_cheia"]) / (1514 - 98)

    # Saltos para trás do relógio de parede (no WSL2, a sincronização com o Windows pode
    # recuar o relógio). Pings enviados antes e recebidos depois do salto têm o RTT
    # subestimado pelo tamanho do salto.
    dt = np.diff(df["t_s"].to_numpy(float))
    r["saltos_relogio"] = int((dt < 0).sum())
    r["pior_salto_s"] = float(dt.min())

    r["vazao_mbps"] = throughput_mbps(df, t_from=DESCARTE)
    # vazão útil esperada: C menos os pings (98 B x 10/s), vezes a fração útil do pacote
    # (MSS 1448 B de 1514 B no fio: cabeçalhos Ethernet, IP e TCP com timestamps)
    r["vazao_util_esperada"] = (C - 98 * 8 * 10) / 1e6 * 1448 / 1514

    t = df["t_s"].to_numpy(float)
    w = df["cwnd_pkts"].to_numpy(float)
    red, to = detect_backoffs(t, w, df["ssthresh_pkts"].to_numpy())
    r["n_reducoes"], r["n_timeouts"] = len(red), len(to)
    picos, vales = [], []
    fronteiras = list(red) + [t[-1]]
    for k, tb in enumerate(red):
        if tb < DESCARTE:
            continue
        antes = (t >= tb - 1.0) & (t <= tb)
        depois = (t >= tb) & (t < fronteiras[k + 1])
        if antes.any() and depois.any():
            picos.append(w[antes].max())
            vales.append(w[depois].min())
    picos, vales = np.asarray(picos), np.asarray(vales)
    r["pico_medio"] = picos.mean() if picos.size else np.nan
    r["vale_medio"] = vales.mean() if vales.size else np.nan
    r["razao_vale_pico"] = (vales / picos).mean() if picos.size else np.nan
    r["periodo_dente_s"] = np.diff(red[red >= DESCARTE]).mean() if (red >= DESCARTE).sum() > 1 else np.nan
    return r


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "dados/p2"
    resumo = {}
    for qdir in sorted(os.listdir(base), key=lambda s: -int(s[1:]) if s[1:].isdigit() else 0):
        runs = reps(os.path.join(base, qdir))
        if not runs:
            continue
        linhas = [analisa_rodada(run) for run in runs]
        q = linhas[0]["q"]
        print(f"\n===== q = {q} pacotes ({len(runs)} repetições) =====")
        print(f"{'rep':>4} {'RTT méd':>8} {'desvio':>7} {'RTT prev':>8} {'fila méd':>8} {'fila máx':>8} "
              f"{'vazão':>6} {'pico':>6} {'vale':>6} {'v/p':>5} {'T dente':>7} {'red':>4} {'TO':>3} {'load':>5}")
        for run, r in zip(runs, linhas):
            print(f"{os.path.basename(run):>4} {r['rtt_media']:8.1f} {r['rtt_desvio']:7.1f} {r['rtt_previsto']:8.1f} "
                  f"{r['fila_media']:8.1f} {r['fila_max']:8.0f} {r['vazao_mbps']:6.3f} {r['pico_medio']:6.1f} "
                  f"{r['vale_medio']:6.1f} {r['razao_vale_pico']:5.2f} {r['periodo_dente_s']:7.1f} "
                  f"{r['n_reducoes']:4d} {r['n_timeouts']:3d} {r['loadavg_fim']:5.2f}")
        agg = {k: media_ic([r[k] for r in linhas]) for k in
               ("rtt_media", "rtt_desvio", "rtt_previsto", "rtt_previsto_bytes", "fila_media",
                "fila_max", "vazao_mbps", "pico_medio", "vale_medio", "razao_vale_pico",
                "periodo_dente_s", "bytes_por_pacote_fila_cheia", "pings_na_fila_cheia")}
        r0 = linhas[0]
        print("média ± IC95%:")
        print(f"  RTT do ping           {fmt_ic(*agg['rtt_media'][:2], 1)} ms "
              f"(desvio {fmt_ic(*agg['rtt_desvio'][:2], 1)} ms)")
        print(f"  RTT previsto pela fila {fmt_ic(*agg['rtt_previsto'][:2], 1)} ms "
              f"= {r0['rtt_prop_ms']:g} + fila (pacotes) × {r0['ms_por_pacote']:.1f} ms/pacote")
        print(f"  RTT previsto (bytes)  {fmt_ic(*agg['rtt_previsto_bytes'][:2], 1)} ms "
              f"= {r0['rtt_prop_ms']:g} + fila (bytes) × 8 / C")
        print(f"  vazão útil            {fmt_ic(*agg['vazao_mbps'][:2], 3)} Mb/s (C = {r0['C_mbps']:g}; "
              f"esperada {r0['vazao_util_esperada']:.3f} = (C − pings) × 1448/1514)")
        print(f"  fila cheia            {fmt_ic(*agg['bytes_por_pacote_fila_cheia'][:2], 0)} B/pacote "
              f"-> {fmt_ic(*agg['pings_na_fila_cheia'][:2], 1)} pings entre os {q} pacotes")
        print(f"  pico da cwnd          {fmt_ic(*agg['pico_medio'][:2], 1)} pacotes "
              f"(BDP + q = {r0['bdp_pkts']:.1f} + {q} = {r0['bdp_pkts'] + q:.1f}; "
              f"descontando os pings: {r0['bdp_pkts'] + q - agg['pings_na_fila_cheia'][0]:.1f})")
        print(f"  vale/pico             {fmt_ic(*agg['razao_vale_pico'][:2], 3)} (beta = 0,5)")
        print(f"  período do dente      {fmt_ic(*agg['periodo_dente_s'][:2], 1)} s")
        # conferências da caixa "Erros comuns"
        rtt_max_teorico = r0["rtt_prop_ms"] + q * r0["ms_por_pacote"]
        avisos = []
        for run, r in zip(runs, linhas):
            nome = os.path.basename(run)
            if r["rtt_min"] < 0.9 * r0["rtt_prop_ms"] or r["rtt_max"] > 1.15 * rtt_max_teorico + 10:
                avisos.append(f"{nome}: RTT fora de [{r0['rtt_prop_ms']:g}, {rtt_max_teorico:.0f}] ms "
                              f"(min {r['rtt_min']:.1f}, max {r['rtt_max']:.1f})")
            if not (0.8 * q <= r["fila_max"] <= q):
                avisos.append(f"{nome}: fila máxima {r['fila_max']:.0f} não bate com q = {q}")
            if r["vazao_mbps"] > 1.02 * r0["C_mbps"] or r["vazao_mbps"] < 0.85 * r0["C_mbps"]:
                avisos.append(f"{nome}: vazão {r['vazao_mbps']:.3f} Mb/s longe de C")
            if r["n_timeouts"]:
                avisos.append(f"{nome}: {r['n_timeouts']} timeout(s)")
            if r["saltos_relogio"]:
                avisos.append(f"{nome}: relógio recuou {r['saltos_relogio']}x (pior {r['pior_salto_s']:+.3f} s); "
                              "alguns RTTs do ping ficam subestimados perto do salto")
        print("  conferências: " + ("OK" if not avisos else ""))
        for av in avisos:
            print("   ! " + av)
        resumo[f"q{q}"] = {"rodadas": linhas, "agregado": agg, "avisos": avisos}
    os.makedirs("resultados", exist_ok=True)
    with open("resultados/p2.json", "w") as fh:
        json.dump(resumo, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
