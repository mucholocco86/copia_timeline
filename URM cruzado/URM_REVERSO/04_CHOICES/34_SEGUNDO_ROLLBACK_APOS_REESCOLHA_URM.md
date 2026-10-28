# 34 — Segundo rollback após reescolha via URM

**Data:** 2026-10-23  
**Escopo:** causa do testcase inconclusivo anterior e novo ciclo de rollback no Ren'Py 7.4.11.  
**Status:** código SDK confirmado; dois ciclos de fronteira atravessados em runtime reduzido; uma segunda ação de escolha após o segundo fixed rollback está em teste.

## Pergunta

Depois de voltar através de uma escolha fixada, usar uma ação equivalente a `URMChoice.Action` para trocar B por A e continuar o jogo, o Ren'Py estabelece uma nova fronteira? O usuário consegue voltar novamente até ela e trocar a escolha outra vez?

## Evidências de fonte do SDK

Snapshot do SDK no laboratório: `renpy-7.4.11-sdk`.

- `renpy/python.py`, blob `c5eb2819a3e4ee096dbf01130d70a77f9b623484`:
  - `StoreDict.get_changes(cycle)`, linha 160: compara o store atual com `old` e devolve, para cada chave alterada, o valor anterior (ou marcador de exclusão). Quando `cycle=True`, move a base de comparação para o estado atual.
  - `Rollback.rollback()`, linhas 1504–1528: restaura objetos e aplica ao store os deltas gravados no registro.
  - `RollbackLog.complete()`, linhas 1707–1726: coleta `sd.get_changes(begin)` e guarda as mudanças na entrada atual do histórico.
  - `RollbackLog.checkpoint()`, linhas 1822–1859: só cria checkpoint quando o contexto permite rollback; um checkpoint hard incrementa `rollback_limit` até `config.hard_rollback_limit`.
  - `RollbackLog.fix_rollback()`, linha 1911: se ainda não está em fixed rollback e há pelo menos duas entradas, define `fixed_rollback_boundary` como `self.log[-2].context.current`. Não altera `rollback_limit`.
  - `RollbackLog.can_rollback()`, linha 1915: retorna se `rollback_limit > 0`.
  - `RollbackLog.rollback()`, linha 1945 em diante: para rollback interativo (`checkpoints` truthy), retorna sem alterar estado se o limite for zero e a chamada não for forçada. Ao percorrer os registros removidos, decrementa o limite por checkpoint hard e ativa `rollback_is_fixed` quando um contexto restaurado coincide com a fronteira.
  - `RollbackLog.begin()`, aproximadamente linhas 1673–1704: controla a saída de fixed rollback ao continuar a execução e alcançar a fronteira.
- `renpy/exports.py`, blob `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`:
  - `can_rollback()`, linha 243: primeiro consulta `config.rollback_enabled`, depois delega ao log.
  - `checkpoint()`, linha 267: encaminha o pedido ao log e condiciona hard checkpoint ao estado `store._rollback`.
  - `fix_rollback()`, linha 324: delega ao método do log.
- `renpy/config.py`, blob `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`, linhas 75–82: `fix_rollback_without_choice` é falso por padrão e o limite interativo hard padrão é 100.
- `renpy/ast.py`, blob `d81ffc13f28f0b7442ba6905f1745ee838f7b185`, `Menu.execute()`, linhas 1639–1698: o valor da seleção continua sendo usado como índice em `Menu.items`.

## Diagnóstico da tentativa anterior

A tentativa de duas trocas ficou esperando a tela “URM route B” e não produziu um segundo trace de rollback (run [39897042594](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39897042594)).

A fixture histórica usada nessa tentativa terminava o fluxo da história com:

```renpy
label urm_fixed_rollback_boundary_done:
    return
```

Uma fixture diagnóstica isolada, mantendo essa estrutura e registrando o estado imediatamente após os PAGEUP adicionais, executou com sucesso no run [39901909826](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39901909826). No instante em que o testcase tentava os PAGEUP seguintes, o log mostrava:

```text
SECOND_CYCLE_STATE BEFORE_SECOND_PAGEUPS limit 0 can False
context_rollback False store_rollback True fixed False
forward None loglen 0
current (u'renpy/common/_layout/screen_main_menu.rpym', ..., 3762)
```

Isto confirma que a fixture já havia retornado ao menu principal: aqueles eventos não estavam sendo enviados dentro do contexto da história. A falha anterior era um defeito do percurso do testcase, não evidência de que o Ren'Py recusasse o segundo rollback.

Uma tentativa intermediária com `type K_RETURN` também falhou porque o runner não reconhece esse nome de keysym. A fixture diagnóstica foi corrigida para usar `type RETURN`; esse erro pertence ao harness de teste.

## Segundo ciclo corrigido — runtime observado

A fixture separada [`urm_fixed_rollback_second_cycle_diagnostic.rpy`](../tools/fixtures/urm_fixed_rollback_second_cycle_diagnostic.rpy) remove o retorno imediato ao menu principal, avança a fala após a reescolha e registra o estado antes/depois das entradas PAGEUP. O workflow isolado é [`urm-fixed-rollback-second-cycle-diagnostic.yml`](../../.github/workflows/urm-fixed-rollback-second-cycle-diagnostic.yml).

Run [39902170129](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902170129) concluiu **SUCCESS** no SDK 7.4.11. O log confirma:

1. Após rollback até a primeira fronteira e a ação equivalente ao URM que troca B por A, o bloco A executa.
2. O fluxo alcança novamente `renpy.fix_rollback()`. Como a ação da escolha limpou `rollback_is_fixed`, essa chamada define uma nova `fixed_rollback_boundary` no contexto do menu. A fronteira anterior não fica simplesmente “apagada para sempre”.
3. Antes dos PAGEUP seguintes, esta fixture tinha `rollback_limit=4`, `renpy.can_rollback()=True`, `context.rollback=True`, `store._rollback=True` e `rollback_is_fixed=False`.
4. Os dois PAGEUP seguintes fizeram duas novas chamadas reais a `RollbackLog.rollback()`. Ambas ficaram em registros internos da interação/tradução (`end_translate`), sem ainda alcançar a nova fronteira. O limite caiu de 4 para 2 e permaneceu positivo.
5. Um terceiro PAGEUP invocou rollback. O rollback terminou antes da fronteira, depois o fluxo restaurado executou novamente `fix_rollback()` e recalculou a fronteira no contexto seguinte. `can_rollback()` continuou verdadeiro.
6. Um quarto PAGEUP cruzou a fronteira recriada: o log terminou com `rollback_is_fixed=True`, `roll_forward_info()==0` (índice A) e `rollback_limit=0`, então `can_rollback()==False` nesse ponto.

Trechos representativos:

```text
SECOND_CYCLE_STATE BEFORE_SECOND_PAGEUPS limit 4 can True ... fixed False ... boundary (..., 40)
BOUNDARY_ROLLBACK_BEGIN 1 ... current (..., 52) ... forward None
BOUNDARY_ROLLBACK_END False ... current (..., 52, 'end_translate') ... forward None
BOUNDARY_ROLLBACK_BEGIN 1 ... forward True
BOUNDARY_ROLLBACK_END False ... current (..., 50, 'end_translate') ... forward None
SECOND_CYCLE_STATE AFTER_SECOND_PAGEUPS limit 2 can True ... fixed False
BOUNDARY_ROLLBACK_BEGIN 1 ... forward True
BOUNDARY_ROLLBACK_END False ... current (..., 41) ... boundary (..., 40)
SECOND_CYCLE_STATE AFTER_THIRD_PAGEUP limit 1 can True ... fixed False
BOUNDARY_ROLLBACK_BEGIN 1 ... forward True
BOUNDARY_ROLLBACK_END True ... boundary (..., 41) forward 0
SECOND_CYCLE_STATE AFTER_FOURTH_PAGEUP limit 0 can False ... fixed True forward 0
```

### Segunda seleção na segunda fronteira — runtime observado

O run [39902388045](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902388045) foi marcado como **FAILURE** por uma asserção auxiliar sobre a lista em `renpy.session`, não pela seleção. Antes dessa asserção, o log registrou:

```text
SECOND_CYCLE_STATE AFTER_FOURTH_PAGEUP limit 0 can False ... fixed True forward 0
BOUNDARY_URM_ACTION True 0 True False ... 1 False
BOUNDARY_AFTER_MENU B False None ...
```

Isso mostra, na fixture: fixed rollback ativo; forward index 0 (A); rollback interativo indisponível por `rollback_limit=0`; sensibilidade nativa A=True/B=False; a ação equivalente ao URM limpa o flag fixed e retorna índice 1; o menu executa a rota B. O testcase chegou à fala da rota B e falhou somente ao comparar uma lista de eventos armazenada em `renpy.session` com uma sequência cumulativa esperada. A lista não é usada como prova de seleção; a evidência direta é o trace da ação e `BOUNDARY_AFTER_MENU B`.

O run de acompanhamento [39902500519](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902500519) concluiu **SUCCESS**. Ele verificou a rota do store como B e os dados rollback-aware da segunda ação. O log também registrou a lista de execução da fixture como `[B, B, A, A, B]`, não como um histórico simples `[B, A, B]`; os blocos são reexecutados durante rollback/replay, então um array append-only dentro do jogo não é um contador confiável de escolhas únicas. A UI persistente da fixture é apenas um modo de reabrir o controle após rollback; não modela a política de esconder/abrir telas do URM real.

### Conclusões limitadas

- **CONFIRMADO NO SDK 7.4.11:** limite de rollback e fixed boundary são mecanismos separados. O estado `rollback_is_fixed` não determina `can_rollback()`; este último depende de rollback habilitado e de `rollback_limit > 0`.
- **CONFIRMADO NO SDK 7.4.11:** alterações do store são registradas como deltas de valores anteriores e restauradas pela entrada `Rollback`.
- **OBSERVADO EM RUNTIME — fixture reduzida:** após a reescolha A, o fluxo executa de novo `renpy.fix_rollback()` e cria uma nova fronteira.
- **OBSERVADO EM RUNTIME — fixture reduzida:** quatro PAGEUP depois da reescolha A chegaram à fronteira recriada. Os primeiros eventos atravessaram checkpoints internos; o quarto deixou `rollback_is_fixed=True` e forward index `0`, correspondente a A.
- **OBSERVADO EM RUNTIME — fixture reduzida:** ao atingir essa fronteira, o limite chegou a zero, de modo que `renpy.can_rollback()` passou a falso enquanto fixed rollback permanecia ativo.
- **OBSERVADO EM RUNTIME — fixture reduzida:** na segunda fronteira, mesmo com `renpy.can_rollback()==False`, a ação equivalente a `ChoiceReturn` selecionou B; o trace mostrou `rv=1` e o estado do menu registrou rota B. A escolha nativa A estava sensível e B insensível antes da ação.
- **NÃO É EVIDÊNCIA SOBRE O URM INTEGRAL:** o fixture reproduz a ação e a tela mínima; não carrega o URM pelo loader nem testa jogos de terceiros.

## Próximo passo

Continuar a sondagem já alcançada até verificar a segunda seleção. O run [39902388045](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902388045) já demonstra a segunda seleção, mas falhou na asserção da lista de `renpy.session`. Com a seleção B após o segundo fixed rollback confirmada no fixture, o próximo estudo é verificar quando a interface real do URM pode ser reaberta durante fixed rollback, carregar o URM pelo loader, e depois medir variáveis do store em ciclos de rollback e save/load.

Preservar a fixture verde de um único ciclo separada e não alterar `wells/`, `wells_beta/`, fontes originais do URM ou SDKs.
