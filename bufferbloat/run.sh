#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.
# Bônus B1: Parte 2 com o bufferbloat.py original (topologia montada do zero).
# Uso: sudo ./bufferbloat/run.sh    (~7 min: 2 buffers x 200 s)

cd "$(dirname "$0")"
time=200      # o enunciado pede >= 200 s (o original vinha com 90)
bwnet=1.5
# RTT de 20 ms: dois enlaces (h1-s0, s0-h2), e o atraso do TCLink vale em cada
# sentido, entao RTT = 4 * delay -> delay = 5 ms.
delay=5

iperf_port=5001
out=../dados/b1
mkdir -p "$out" ../graficos

for qsize in 20 100; do
    dir=$out/bb-q$qsize
    mn -c >/dev/null 2>&1
    python3 bufferbloat.py --bw-net $bwnet --delay $delay --dir $dir --time $time \
        --maxq $qsize --cong reno
    chown -R "${SUDO_UID:-$(id -u)}:${SUDO_GID:-$(id -g)}" "$out"

    python3 plot_queue.py -f $dir/q.txt -o ../graficos/b1-reno-buffer-q$qsize.png
    python3 plot_ping.py -f $dir/ping.txt -o ../graficos/b1-reno-rtt-q$qsize.png
    python3 plot_cwnd_simples.py $dir/cwnd.csv ../graficos/b1-reno-cwnd-q$qsize.png
done
