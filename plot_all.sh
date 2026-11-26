#!/bin/bash
# Regenera todos os gráficos e tabelas a partir de dados/ (sem rodar o Mininet).
# Uso: ./plot_all.sh          (todas as partes)
#      ./plot_all.sh p2       (só uma parte)
set -e
cd "$(dirname "$0")"
mkdir -p graficos resultados
partes=${1:-"p2"}

for p in $partes; do
  case $p in
    p2)
      for q in 100 20; do
        [ -d dados/p2/q$q/rep1 ] || { echo "sem dados para p2 q=$q"; continue; }
        python3 ig_starter/plot_cwnd.py dados/p2/q$q/rep1 -o graficos/p2-q$q.png
      done
      python3 analise/analise_p2.py dados/p2 | tee resultados/p2.txt
      ;;
    *) echo "parte desconhecida: $p" >&2; exit 1 ;;
  esac
done
