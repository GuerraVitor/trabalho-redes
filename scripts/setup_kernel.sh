#!/bin/bash
# Prepara o kernel para os experimentos (rodar com sudo, antes de cada sessão).
# No WSL2 os módulos e sysctls se perdem quando o WSL reinicia.
set -e
if [ "$(id -u)" -ne 0 ]; then echo "rode com sudo" >&2; exit 1; fi
modprobe -a sch_netem sch_red sch_htb sch_codel sch_fq_codel tcp_scalable openvswitch
sysctl -qw net.ipv4.tcp_no_metrics_save=1
service openvswitch-switch start >/dev/null 2>&1 || true
mn -c >/dev/null 2>&1 || true
echo "kernel pronto: $(sysctl -n net.ipv4.tcp_available_congestion_control)"
