# Trabalho de Redes 2026/2 — IC/UFRJ

**Bufferbloat, controle de congestionamento e a geometria da informação do AIMD**

Experimentos no Mininet que medem, no kernel Linux real, a janela de congestionamento de
fluxos TCP e testam as previsões da geometria da informação do AIMD (decomposição
pitagórica, contração por β², leis de escala janela × perda, sincronização de perdas).

Este README também é o **diário do trabalho**: cada passo, decisão e resultado fica
registrado aqui, para servir de base ao relatório final (ver
[Diário](#diário-do-trabalho) e [Notas para o relatório](#notas-para-o-relatório)).

## Situação

| Parte | Pontos | Código | Experimentos | Análise / respostas |
|---|---|---|---|---|
| 1. Configuração | pré-requisito | ✅ | ✅ ambiente validado | ✅ |
| 2. Bufferbloat | 2,5 | ✅ `run_p2.sh`, `analise/analise_p2.py` | ✅ 3 rep. × q ∈ {20, 100} | ✅ 2.1–2.4 rascunhadas |
| 3. Aquecimento | 1,0 | ✅ métricas testadas | — | ⏳ |
| 4. Decomposição pitagórica | 4,0 | 🟡 `detect_backoffs` pronta | ⏳ | ⏳ |
| 5. Leis de escala | 2,5 | ⏳ | ⏳ | ⏳ |
| 6. Bônus e extras | bônus | 🟡 B1 e B4 prontos | ⏳ | ⏳ |
| 7. Trilha de pesquisa | bônus | ⏳ | ⏳ | ⏳ |
| Relatório (LaTeX) e slides | — | ⏳ | — | ⏳ |

Prazos: apresentação preliminar em 16 ou 18/12/2026; relatório final até 23/12/2026.

## Enunciado

Seguimos a **versão de 25/11/2026** do repositório da disciplina
([`enunciado/enunciado_v2026-11-25.pdf`](enunciado/enunciado_v2026-11-25.pdf)). A versão
distribuída antes ([`enunciado/enunciado_original.pdf`](enunciado/enunciado_original.pdf))
foi alterada no mesmo dia. Diferenças principais:

| | Versão original | Versão de 25/11 (seguida) |
|---|---|---|
| Partes que valem os 10 pontos | 2 a 7 | 2 a 5 (2,5 / 1,0 / 4,0 / 2,5) |
| Parte 2 | completar o `bufferbloat.py` | rodar o `dumbbell.py` (o `bufferbloat.py` virou o bônus B1) |
| Sincronização, dois gargalos | Partes 6 e 7, obrigatórias | bônus da Parte 6 |
| Repetições por configuração | ≥ 5 | ≥ 3 (5 se der tempo) |
| Entrega final | 21/12 | 23/12 |

## Ambiente

Ubuntu 24.04.5 LTS no **WSL2** (kernel `6.6.87.2-microsoft-standard-WSL2`), Mininet 2.3,
Open vSwitch, iperf 2 e iperf3. O kernel e as versões de cada rodada ficam no
`metadata.json` dela.

```bash
sudo apt install mininet openvswitch-switch openvswitch-testcontroller iperf iperf3 \
     ethtool git python3-numpy python3-pandas python3-matplotlib
sudo ./scripts/setup_kernel.sh   # módulos e sysctls; repetir a cada reinício do WSL
```

Validação do ambiente (25/11/2026), com h1 –s1– h2, gargalo de 10 Mb/s e 10 ms por sentido:

| Teste | Resultado | Esperado |
|---|---|---|
| módulos `sch_netem`, `sch_red`, `sch_htb`, `sch_codel`, `tcp_scalable`, `openvswitch` | carregam com `modprobe` | — |
| algoritmos disponíveis | `reno cubic scalable` | — |
| pingall | 0% de perda | 0% |
| RTT médio (netem) | 20,6 ms | ~20 ms |
| iperf2 Reno | 9,54 Mb/s | ~9,5 |
| iperf3 `-C cubic` / `-C scalable` | 9,36 / 8,88 Mb/s | ~9,5 |
| `simula_aimd.py` | identidade pitagórica com erro 3,6e-15; razão por ciclo 0,329 → 0,250 | β² = 0,25 |
| `simula_cubic.py` | α = 1,333326 | 4/3 |

Cuidados específicos do WSL2:
* módulos e sysctls não persistem após `wsl --shutdown`: todo `run_*.sh` chama
  `scripts/setup_kernel.sh` antes de começar;
* **o relógio de parede pode recuar** (sincronização do WSL2 com o Windows). Aconteceu
  uma vez nas 6 rodadas da Parte 2 (q100/rep1, −0,47 s em t ≈ 15,6 s): os timestamps
  do `cwnd_monitor.py`, da fila e do ping regridem juntos, e 5 pings enviados antes do
  salto e recebidos depois aparecem com RTT de ~85 ms em vez de ~565 ms. As análises
  detectam e avisam esses saltos;
* só existe cgroups v2, por isso `Host` no lugar de `CPULimitedHost`;
* `mn --test iperf` trava porque o Mininet usa `telnet` (ausente) para esperar o servidor;
  nossos scripts não usam esse teste.

## Como reproduzir

| Parte | Rodar os experimentos | Regenerar gráficos e tabelas | Saídas |
|---|---|---|---|
| 2 | `sudo ./run_p2.sh` (~21 min) | `./plot_all.sh p2` | `graficos/p2-q100.png`, `graficos/p2-q20.png`, `resultados/p2.txt` |
| 4 | `sudo ./run_p4.sh` (~13 min, Reno n=2 B=100, 5 rep.) | `./plot_all.sh p4` (em construção) | `graficos/p4-cwnd-reno-n2-B100.png`, `graficos/p4-decomp-reno-n2-B100.png` |
| B7/B8 | `sudo ETAPA=bonus ./run_p4.sh` (~3 h) | `./plot_all.sh p4` | tabela de razões por (algoritmo, n, B) |
| B1 | `sudo ./bufferbloat/run.sh` (~7 min) | (o próprio `run.sh`) | `graficos/b1-reno-{buffer,rtt,cwnd}-q{20,100}.png` |

`./plot_all.sh` sem argumentos regenera tudo a partir de `dados/`, sem rodar o Mininet.
Os scripts `run_*.sh` retomam de onde pararam (pulam rodadas que já têm `metadata.json`).
`sudo REPS=5 ./run_p2.sh` muda o número de repetições.

Testes das métricas: `python3 tests/test_ig_metrics.py`.

## Estrutura

```
ig_starter/     código fornecido pelos professores (dumbbell.py, ig_metrics.py, ...);
                detect_backoffs em ig_metrics.py foi implementada por nós
bufferbloat/    código do projeto original de bufferbloat (bônus B1), com os TODOs completados
analise/        scripts de análise por parte
scripts/        utilitários (preparação do kernel)
tests/          testes das métricas
dados/pN/...    dados brutos: flow*.csv, queue.csv, ping.txt, metadata.json por rodada
graficos/       gráficos com os nomes pedidos no enunciado
resultados/     tabelas e resumos gerados pelas análises
relatorio/      relatório em LaTeX
enunciado/      enunciado (versão original e versão de 25/11/2026)
```

## Decisões técnicas

**`detect_backoffs` (pergunta 4.3), em `ig_starter/ig_metrics.py`.** Une dois sinais:
1. *mudança de `ssthresh`*: no Linux ele só é recalculado numa redução de janela, e a
   primeira vez que aparece também é uma redução (antes disso o `ss` não o imprime). Um
   `ssthresh` maior que o anterior também conta, porque a perda pode vir com janela maior
   que a do corte anterior;
2. *queda acumulada da cwnd* de mais de 20% em relação ao último pico. Foi necessária
   porque, com um fluxo só, toda perda acontece com a mesma janela (BDP + B), então o
   `ssthresh` recalculado sai **igual** ao anterior e o sinal 1 não acusa nada. Os testes
   com dente de serra sintético encontraram esse problema. A queda é medida contra o pico,
   e não entre amostras vizinhas, porque com PRR a cwnd desce aos poucos ao longo de ~1 RTT.
   Se houve mudança de `ssthresh` na mesma subida, é o mesmo evento e não conta duas vezes.

Timeout: a cwnd vai a ≤ 2 pacotes até 1 s depois do evento; esses eventos são contados à parte.

**Análise da Parte 2 (`analise/analise_p2.py`).** Descarta os primeiros 20 s (slow start).
Pico = máximo da cwnd 1 s antes de cada redução; vale = mínimo até a redução seguinte. IC 95%
pela t de Student entre repetições. Confere automaticamente as faixas da caixa "Erros
comuns" do enunciado: 20 ≤ RTT ≤ 20 + 8q ms, fila máxima ≈ q, vazão ≤ C.

**Atraso de fila em bytes, não em pacotes.** O `pfifo` limita a fila em *pacotes*, mas a
fila também guarda os pings (98 B no fio), então o atraso de fila correto é
ocupação em bytes × 8 / C. Com isso o RTT previsto cai de 630,7 para 593,6 ms (q = 100) e
fica a ~4 ms do medido (ver 2.2).

**Bônus B1 (`bufferbloat/`).** `delay=5ms` em cada enlace: o caminho h1–s0–h2 tem dois
enlaces e o atraso do TCLink vale em cada sentido, então RTT = 4 × 5 = 20 ms. O buffer de
q pacotes fica em `s0-eth2` (s0 → h2). A medição do tempo de download da página do roteiro
original ficou de fora, porque esta versão do trabalho não a pede.

**`bufferbloat/index.html` fora do repositório.** É uma cópia da página do New York Times
de 2012 (conteúdo de terceiros), usada só pelo `webserver.py`, que esta versão não usa.

## Diário do trabalho

**25/11/2026**
* Leitura do enunciado e planejamento das fases.
* Validação do ambiente no WSL2 (tabela em [Ambiente](#ambiente)). Primeiro teste de iperf
  travou no `mn --test iperf` (falta de `telnet`); refeito com um script próprio.
* Descoberta de que o enunciado do repositório tinha sido atualizado (seção
  [Enunciado](#enunciado)); passamos a seguir a versão nova.
* Repositório criado com o `ig_starter`, e as verificações numéricas
  (`simula_aimd.py`, `simula_cubic.py`) rodadas com sucesso.
* `detect_backoffs` implementada; os testes sintéticos revelaram o caso de picos iguais e
  levaram ao segundo sinal (queda acumulada da cwnd).
* `tests/test_ig_metrics.py`: identidade pitagórica em 1000 pontos aleatórios (µ = 1 e
  µ = (1, 1/4, 1/9)), invariância por escala, exemplo da Seção 3 e detecção de reduções
  (picos iguais, picos diferentes, β = 0,7, sem ssthresh, timeout). 10 testes passando.
* Infraestrutura da Parte 2 (`run_p2.sh`, `plot_all.sh`, `analise/analise_p2.py`), testada
  com dados sintéticos: pico 102 (BDP + q = 102,5), vale/pico 0,50, período 31,6 s.
* Pacote original do bufferbloat incluído (checksums conferidos contra o zip) e TODOs do
  `bufferbloat.py` completados (bônus B1).
* **Parte 2 rodada**: 3 repetições × q ∈ {20, 100}, 200 s cada. Todas passaram nas
  conferências; repetições muito consistentes (IC do RTT médio de ±1,3 ms em ~598 ms).
  Três desvios da previsão simples investigados e explicados (ver
  [Notas da Parte 2](#parte-2)): pico da cwnd abaixo de BDP + q (pings ocupando a
  fila), vazão de 1,427 e não 1,5 Mb/s (cabeçalhos e pings), e RTT previsto em pacotes
  acima do medido (fila tem pacotes pequenos). Encontrado também um salto para trás do
  relógio do WSL2 em uma rodada; análise passou a detectá-lo.

## Notas para o relatório

Respostas e números organizados pela numeração do enunciado. O que ainda é previsão (antes
dos experimentos) está marcado como tal.

### Parte 2

Dados: `dados/p2/q{20,100}/rep{1,2,3}`. Gráficos: `graficos/p2-q100.png`, `graficos/p2-q20.png`
(rep1). Tabela completa: `resultados/p2.txt`. Valores abaixo: média ± IC 95% das 3
repetições, descartando os primeiros 20 s. Parâmetros: C = 1,5 Mb/s, RTT de propagação
20 ms (ping antes dos fluxos: 20,2 ms), MSS 1448 B (1514 B no fio).

| | q = 20 | q = 100 |
|---|---|---|
| RTT médio do ping | 131,1 ± 0,4 ms | 597,8 ± 1,3 ms |
| desvio padrão do RTT | 27,3 ± 0,5 ms | 120,4 ± 0,6 ms |
| RTT previsto = 20 ms + fila (bytes) × 8 / C | 127,6 ms | 593,6 ms |
| ocupação média da fila | 14,3 pacotes | 76,3 pacotes |
| fila mínima (20–195 s) | 6 pacotes | 46 pacotes |
| vazão útil (bytes confirmados) | 1,427 Mb/s | 1,427 Mb/s |
| pico da cwnd | 22,3 ± 0,2 | 96,4 ± 0,5 |
| BDP + q (BDP = 2,5 pacotes) | 22,5 | 102,5 |
| vale da cwnd | 11,0 | 48,0 |
| vale / pico | 0,494 ± 0,005 | 0,498 ± 0,002 |
| período do dente de serra | 1,7 s | 29,4 ± 0,3 s |
| pico do slow start | 42–45 | 197–199 |
| timeouts | 0 | 0 |

**2.1** No `dumbbell.py` com `--n 1`, o buffer de q pacotes fica na saída `s1 → s2`
(interface `s1-eth2`). Os comandos gravados no `metadata.json` são
`tc qdisc add dev s1-eth2 root handle 1: htb default 10`,
`tc class add dev s1-eth2 parent 1: classid 1:10 htb rate 1.5mbit` e
`tc qdisc add dev s1-eth2 parent 1:10 handle 20: pfifo limit q`: o HTB impõe a taxa C e a
fila folha `pfifo` (drop-tail) guarda até q pacotes. O atraso de propagação inteiro
(20 ms) é aplicado com `tc qdisc add dev h1-eth0 root netem delay 20.0ms limit 100000`,
na saída do próprio emissor. Motivo: emissor e "roteador" estão no mesmo kernel. Sem o
netem, um pacote parado na fila do gargalo continua contado no socket do emissor, e o
*TCP Small Queues* limita cada fluxo a poucos pacotes nessa fila, que então nunca enche
(num roteador de verdade isso não acontece). O netem "solta" o pacote do socket
(`skb_orphan_partial`) ao enfileirá-lo.

**2.2** RTT médio de 131,1 ms (desvio 27,3 ms) com q = 20 e de 597,8 ms (desvio 120,4 ms)
com q = 100, dentro das faixas esperadas (20 ≤ RTT ≤ 20 + 8q: até 180 e 820 ms; máximos
medidos ~175 e ~775 ms). Relação: RTT = RTT_prop + atraso de fila, com atraso de fila =
ocupação / taxa de serviço. Um pacote de dados (1514 B) leva 1514 × 8 / 1,5 Mb/s ≈ 8 ms.
Usando a ocupação média em pacotes × 8 ms, a previsão (134,7 e 630,7 ms) superestima o
medido, porque a fila também contém pings (98 B). Usando a ocupação em **bytes**, a
previsão é 127,6 e 593,6 ms, a 3,5 e 4,2 ms do medido. Essa diferença residual é
compatível com o tempo que o ping espera, em média, pelo pacote que já está sendo
transmitido quando ele chega (metade de um pacote, ~4 ms). O gráfico mostra o RTT
acompanhando a fila amostra a amostra.

**2.3** Vale/pico = 0,498 (q = 100) e 0,494 (q = 20), praticamente β = 1/2. O pico com
q = 20 (22,3) bate com BDP + q = 22,5. Com q = 100, o pico (96,4) fica ~6 pacotes abaixo
de 102,5. Explicação, conferida nos dados: com a fila cheia, o tamanho médio por pacote é
1420 B e não 1514 B, o que corresponde a ~6,7 pings (98 B) entre os 100 pacotes. Como o
`pfifo` conta pacotes, os pings tomam vagas dos dados: 102,5 − 6,7 ≈ 95,8, perto do pico
medido. Com q = 20 há só ~1,7 pings na fila cheia (RTT menor, menos pings em trânsito), e
o pico fica 1,5 pacote acima de 20,8; uma parte disso vem do crescimento da cwnd
durante o RTT entre a perda e sua detecção. O dente com q = 100 é côncavo: a cwnd cresce 1
pacote por RTT, e o RTT aumenta à medida que a fila enche, então o crescimento desacelera.
Cada dente dura 29,4 s (o enunciado fala em ~30 s).

**2.4** A vazão útil é **a mesma** com os dois buffers (1,427 Mb/s, que é exatamente
(C − tráfego dos pings) × 1448/1514, a fração útil de cada pacote no fio). O buffer
maior só aumenta o atraso: +467 ms no RTT médio. Isso acontece porque, quando o enlace
já está sempre ocupado, o que fica na fila além disso não acrescenta vazão: os pacotes só
esperam mais. A regra B = RTT · C dá 1 BDP = 2,5 pacotes para manter o gargalo sempre
ocupado com um fluxo Reno: logo após o corte, a janela é (BDP + B)/2, e isso precisa ser
≥ BDP. Nos dados, a fila nunca esvaziou (mínimo de 6 pacotes com q = 20 e 46 com q = 100,
entre 20 s e 195 s), então os dois buffers estão acima do necessário; q = 20 já é 8 BDPs.
O mínimo de 46 com q = 100 bate com (BDP + q)/2 − BDP ≈ 48 menos os pings.

Observações para o relatório:
* slow start: a cwnd chega a ~198 (q = 100) e ~43 (q = 20), o dobro de BDP + q, antes da
  primeira perda; os dados descartam os primeiros 20 s;
* uma rodada (q100/rep1) teve um salto para trás do relógio (ver [Ambiente](#ambiente));
  efeito de ~1 ms no RTT médio dessa rodada; mantida.

## Licenças

Código: MIT ([`LICENSE`](LICENSE)). Dados (`dados/`, `resultados/`, `graficos/`): CC-BY 4.0
([`LICENSE-DADOS`](LICENSE-DADOS)). O código em `ig_starter/` é dos professores da
disciplina (repositório `danielsadoc/trabalho-redes-ig`).
