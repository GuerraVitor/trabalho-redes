#!/bin/bash
# Parte 4: decomposição pitagórica. C = 10 Mb/s, RTT 40 ms igual para todos, fluxos
# escalonados a cada 15 s, 120 s depois do início do último.
#
# Uso:
#   sudo ./run_p4.sh                 # obrigatório: Reno, n=2, B=100, REPS repetições
#   sudo ETAPA=bonus ./run_p4.sh     # bônus B7/B8: CUBIC, n in {2,3,4}, B in {20,100}
#   sudo REPS=3 ./run_p4.sh          # menos repetições (padrão 5)
#
# Tempo por rodada: ~2,5 min (n=2) a ~3,5 min (n=4). Obrigatório com REPS=5: ~13 min.
# Bônus completo: 11 configurações x REPS -> ~3 h com REPS=5. Retoma de onde parou.
set -e
cd "$(dirname "$0")"
REPS=${REPS:-5}
ETAPA=${ETAPA:-obrigatoria}
RTT=40; BW=10; STAGGER=15; DUR=120
./scripts/setup_kernel.sh

roda() {  # roda <cc> <n> <B>
  local cc=$1 n=$2 B=$3
  for rep in $(seq 1 "$REPS"); do
    out="dados/p4/${cc}-n${n}-B${B}/rep${rep}"
    [ -f "$out/metadata.json" ] && { echo "pulando $out (já existe)"; continue; }
    echo "=== $(date +%H:%M:%S) $cc n=$n B=$B rep=$rep"
    python3 ig_starter/dumbbell.py --n "$n" --cc "$cc" --rtt-ms "$RTT" --bw "$BW" \
        --buffer "$B" --stagger "$STAGGER" --duration "$DUR" --qmon --out "$out"
    mn -c >/dev/null 2>&1 || true
  done
}

case $ETAPA in
  obrigatoria)
    roda reno 2 100 ;;
  bonus)
    for cc in reno cubic; do
      for n in 2 3 4; do
        for B in 100 20; do
          [ "$cc-$n-$B" = "reno-2-100" ] && continue   # já é a obrigatória
          roda "$cc" "$n" "$B"
        done
      done
    done
    roda reno 2 100 ;;   # garante a obrigatória também
  *) echo "ETAPA desconhecida: $ETAPA" >&2; exit 1 ;;
esac

sudo -u "${SUDO_USER:-$USER}" ./plot_all.sh p4 || echo "(análise da Parte 4 ainda não disponível)"
