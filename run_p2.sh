#!/bin/bash
# Parte 2: bufferbloat e o dente de serra do Reno.
# Um fluxo Reno, RTT 20 ms, gargalo 1,5 Mb/s, buffer q in {100, 20}, 200 s por rodada.
# Uso: sudo ./run_p2.sh        (REPS=3 por padrão; retoma de onde parou)
# Tempo: ~3,5 min por rodada -> ~21 min com REPS=3.
set -e
cd "$(dirname "$0")"
REPS=${REPS:-3}
./scripts/setup_kernel.sh

for q in 100 20; do
  for rep in $(seq 1 "$REPS"); do
    out="dados/p2/q${q}/rep${rep}"
    [ -f "$out/metadata.json" ] && { echo "pulando $out (já existe)"; continue; }
    echo "=== q=$q rep=$rep"
    python3 ig_starter/dumbbell.py --n 1 --cc reno --rtt-ms 20 --bw 1.5 --buffer "$q" \
        --duration 200 --qmon --ping --out "$out"
    mn -c >/dev/null 2>&1 || true
  done
done

# gráficos e análise como o usuário (não root)
sudo -u "${SUDO_USER:-$USER}" ./plot_all.sh p2
