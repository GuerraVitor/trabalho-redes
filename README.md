# Trabalho de Redes 2026/2 — IC/UFRJ

**Bufferbloat, controle de congestionamento e a geometria da informação do AIMD**

Experimentos no Mininet que medem, no kernel Linux real, a janela de congestionamento de
fluxos TCP e testam as previsões da geometria da informação do AIMD (decomposição
pitagórica, contração por β², leis de escala janela × perda, sincronização de perdas).
O enunciado seguido é a versão de 25/11/2026 do repositório da disciplina
([`enunciado/enunciado_v2026-11-25.pdf`](enunciado/enunciado_v2026-11-25.pdf)).

## Ambiente

Ubuntu 24.04.5 no WSL2 (kernel `6.6.87.2-microsoft-standard-WSL2`), Mininet 2.3, Open
vSwitch, iperf 2 e iperf3. O kernel e as versões de cada rodada ficam no `metadata.json`
dela.

```bash
sudo apt install mininet openvswitch-switch openvswitch-testcontroller iperf iperf3 \
     ethtool git python3-numpy python3-pandas python3-matplotlib
sudo ./scripts/setup_kernel.sh   # módulos e sysctls; repetir a cada reinício do WSL
```

## Como reproduzir

| Parte | Rodar os experimentos | Regenerar gráficos e tabelas | Saídas |
|---|---|---|---|
| 2 | `sudo ./run_p2.sh` (~21 min) | `./plot_all.sh p2` | `graficos/p2-q100.png`, `graficos/p2-q20.png`, `resultados/p2.txt` |

`./plot_all.sh` sem argumentos regenera tudo a partir de `dados/`, sem rodar o Mininet.
Os scripts `run_*.sh` retomam de onde pararam (pulam rodadas que já têm `metadata.json`).
`REPS=5 sudo -E ./run_p2.sh` muda o número de repetições.

Testes das métricas: `python3 tests/test_ig_metrics.py`.

## Estrutura

```
ig_starter/     código fornecido pelos professores (dumbbell.py, ig_metrics.py, ...);
                detect_backoffs em ig_metrics.py foi implementada por nós
analise/        scripts de análise por parte
scripts/        utilitários (preparação do kernel)
tests/          testes das métricas
dados/pN/...    dados brutos: flow*.csv, queue.csv, ping.txt, metadata.json por rodada
graficos/       gráficos com os nomes pedidos no enunciado
resultados/     tabelas e resumos gerados pelas análises
relatorio/      relatório em LaTeX
enunciado/      enunciado (versão original e versão de 25/11/2026)
```

## Licenças

Código: MIT ([`LICENSE`](LICENSE)). Dados (`dados/`, `resultados/`, `graficos/`): CC-BY 4.0
([`LICENSE-DADOS`](LICENSE-DADOS)). O código em `ig_starter/` é dos professores da
disciplina (repositório `danielsadoc/trabalho-redes-ig`).
