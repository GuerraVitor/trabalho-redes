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
| 2. Bufferbloat | 2,5 | ✅ `run_p2.sh`, `analise/analise_p2.py` | ⏳ a rodar | ⏳ 2.1 rascunhada |
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
* só existe cgroups v2, por isso `Host` no lugar de `CPULimitedHost`;
* `mn --test iperf` trava porque o Mininet usa `telnet` (ausente) para esperar o servidor;
  nossos scripts não usam esse teste.

## Como reproduzir

| Parte | Rodar os experimentos | Regenerar gráficos e tabelas | Saídas |
|---|---|---|---|
| 2 | `sudo ./run_p2.sh` (~21 min) | `./plot_all.sh p2` | `graficos/p2-q100.png`, `graficos/p2-q20.png`, `resultados/p2.txt` |
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

## Notas para o relatório

Respostas e números organizados pela numeração do enunciado. O que ainda é previsão (antes
dos experimentos) está marcado como tal.

### Parte 2

**2.1 (rascunho, a partir do código).** No `dumbbell.py` com `--n 1`, o buffer de q pacotes
fica na saída `s1 → s2` (interface `s1-eth2`): um `htb rate C` com uma fila folha
`pfifo limit q` (drop-tail). O atraso de propagação inteiro (20 ms) é aplicado com
`netem delay` na saída do próprio emissor (`h1-eth0`). Motivo: emissor e "roteador" estão
no mesmo kernel; sem o netem, um pacote parado na fila do gargalo continua contado no
socket do emissor, e o *TCP Small Queues* limita cada fluxo a poucos pacotes nessa fila, que
então nunca enche. O netem "solta" o pacote do socket ao enfileirá-lo. Conferir os
comandos exatos no `metadata.json` (`comandos_tc`) quando a rodada existir.

**Previsões para 2.2–2.4** (C = 1,5 Mb/s, pacotes de 1500 B, RTT de propagação 20 ms):
* cada pacote na fila acrescenta 1500 × 8 / 1,5e6 = **8 ms** ao RTT; RTT entre 20 ms e
  20 + 8q ms: até ~180 ms (q = 20) e ~820 ms (q = 100);
* BDP = 1,5e6 × 0,02 / 12000 = **2,5 pacotes**; pico da cwnd ≈ BDP + q = 22,5 ou 102,5;
* vale/pico ≈ β = 0,5; com q = 100 cada dente dura ~30 s;
* regra B = RTT · C = 1 BDP = 2,5 pacotes para manter o gargalo ocupado com um fluxo.

## Licenças

Código: MIT ([`LICENSE`](LICENSE)). Dados (`dados/`, `resultados/`, `graficos/`): CC-BY 4.0
([`LICENSE-DADOS`](LICENSE-DADOS)). O código em `ig_starter/` é dos professores da
disciplina (repositório `danielsadoc/trabalho-redes-ig`).
