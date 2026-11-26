from mininet.topo import Topo
from mininet.node import Host  # CPULimitedHost precisa de cgroups v1 (falha no Ubuntu 24.04)
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen

import sys
import os
import math

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default that doesn't have the usual sawtooth
# behaviour.  For those who are curious, invoke this script with
# --cong cubic and see what happens...
# sysctl -a | grep cong should list some interesting parameters.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

# Expt parameters
args = parser.parse_args()

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        # O atraso do TCLink vale em cada sentido de cada enlace: o caminho h1-s0-h2 tem
        # dois enlaces, entao RTT = 4 * delay (delay = 5 ms -> RTT de 20 ms).
        # O netem do enlace h1-s0 fica na saida de h1 e solta o pacote do socket, o que
        # evita que o TCP Small Queues limite a fila do gargalo (Apendice C do enunciado).
        self.addLink(h1, switch, bw=args.bw_host, delay='%gms' % args.delay)
        # gargalo: saida s0-eth2 (s0 -> h2), com buffer de maxq pacotes
        self.addLink(switch, h2, bw=args.bw_net, delay='%gms' % args.delay,
                     max_queue_size=args.maxq)

# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!

def start_iperf(net):
    h1 = net.get('h1')
    h2 = net.get('h2')
    print("Starting iperf server...")
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    server = h2.popen("iperf -s -w 16m")

    # fluxo longo: dura o experimento inteiro (+5 s de folga); -Z escolhe o algoritmo
    client = h1.popen("iperf -c %s -t %d -Z %s -w 16m > %s/iperf.txt 2>&1"
                      % (h2.IP(), args.time + 5, args.cong, args.dir), shell=True)
    return [server, client]

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_ping(net):
    # 10 pings por segundo de h1 para h2. O sentido importa pouco para o RTT (o ping vai
    # e volta), mas de h1 o pedido entra na mesma fila do gargalo que o fluxo TCP.
    h1, h2 = net.get('h1'), net.get('h2')
    return h1.popen("ping -i 0.1 -D %s > %s/ping.txt" % (h2.IP(), args.dir), shell=True)

def start_cwnd(net):
    # janela de congestionamento do fluxo, amostrada com ss dentro de h1
    h1, h2 = net.get('h1'), net.get('h2')
    mon = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ig_starter',
                       'cwnd_monitor.py')
    return h1.popen([sys.executable, mon, '--dst', h2.IP(), '--out',
                     '%s/cwnd.csv' % args.dir, '--duration', str(args.time + 10)])

def start_webserver(net):
    h1 = net.get('h1')
    proc = h1.popen("python webserver.py", shell=True)
    sleep(1)
    return [proc]

def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = BBTopo()
    net = Mininet(topo=topo, host=Host, link=TCLink)
    net.start()
    # offloads (TSO/GSO/GRO) distorcem cwnd e fila; nao reaproveitar metricas antigas
    for node in net.hosts + net.switches:
        for intf in node.intfList():
            if intf.name != 'lo':
                node.cmd('ethtool -K %s tso off gso off gro off 2>/dev/null' % intf.name)
    for h in net.hosts:
        h.cmd('sysctl -qw net.ipv4.tcp_no_metrics_save=1')
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()

    # Fila do gargalo: o enlace h1-s0 foi criado primeiro (s0-eth1) e o s0-h2 depois
    # (s0-eth2), entao o buffer de maxq pacotes na direcao h1 -> h2 esta em s0-eth2.
    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/q.txt' % (args.dir))

    procs = start_iperf(net)
    procs.append(start_ping(net))
    procs.append(start_cwnd(net))

    # A medicao do tempo de download da pagina (webserver.py + curl) do roteiro original
    # nao faz parte desta versao do trabalho (o enunciado diz "nao usado"); a cwnd
    # (cwnd.csv) entra no lugar dela.
    start_time = time()
    while True:
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print("%.1fs left..." % (args.time - delta))

    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    # CLI(net)

    for p in procs:
        p.terminate()
    qmon.terminate()
    os.system('pkill -f "iperf -s" 2>/dev/null')
    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()
