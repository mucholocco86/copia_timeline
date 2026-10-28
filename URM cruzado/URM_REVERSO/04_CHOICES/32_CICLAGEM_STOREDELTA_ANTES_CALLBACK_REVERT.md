# 32 — Ciclagem do StoreDict antes da callback após Revert

**Data:** 2026-10-21  
**Escopo:** localizar em runtime reduzido quando o delta produzido pela ação Revert deixa de estar disponível a `StoreMonitor` com rollback habilitado.  
**SDK:** Ren’Py 7.4.11.  
**Evidência:** inspeção das fontes do SDK e do URM convertido, mais instrumentação runtime numa fixture isolada.  
**Proteções:** a instrumentação delega ao método original e só registra; não altera arquivos do SDK, fontes URM originais, `wells/` ou `wells_beta/`.

## Resultado

A diferença observada anteriormente entre callback com e sem rollback foi rastreada até a fronteira de execução do próximo nó Ren’Py:

```text
ação de screen altera StoreDict
        ↓
retorno da interação ao Context.run
        ↓
RollbackLog.begin() para o próximo nó
        ↓
RollbackLog.complete(begin=True)
        ↓
StoreDict.get_changes(True): captura delta e avança StoreDict.old
        ↓
execução do próximo nó Python
        ↓
callback URM chama get_changes(False): delta já não aparece
```

Sem rollback habilitado, não há esse `begin()` do log neste percurso. A callback no fim do nó Python seguinte ainda encontra o delta com `get_changes(False)`.

## Evidência runtime

O wrapper da fixture chamou o método original `StoreDict.get_changes` sem alterar seus argumentos ou retorno. Quando a chave alvo era retornada, registrou `cycle`, valor antigo, valor atual e a pilha de chamadas. O teste natural usou a ação de screen reduzida equivalente a `SetVarValue(var, newValue=prevVal)`, com `20→10`.

### Rollback desabilitado

Log relevante no run [39663561168](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39663561168):

```text
REVERT_GET_CHANGES_TARGET False 20 10 urm_revert_monitor_callback/execute/run/...
REVERT_MONITOR_CALLBACK_DELTA 20 10
REVERT_MONITOR_CALLBACK_HANDLED 10 1
```

A callback consumiu a visão do delta sem ciclar `old`; o handler monitorado registrou uma mudança.

### Rollback habilitado

Log relevante no mesmo run:

```text
REVERT_GET_CHANGES_TARGET True 20 10 complete/begin/run/run_context/call_in_new_context/...
REVERT_MONITOR_AFTER_ACTION 10 False None None [] ...
REVERT_MONITOR_AFTER_ROLLBACK 20 False []
```

O trace mostra que o delta 20→10 foi retornado numa chamada com `cycle=True` dentro de `complete/begin`, antes da consulta da callback. A callback não encontrou a chave, não criou registro e o valor ficou em 10 até o rollback restaurá-lo para 20.

### Ruído de inicialização separado

O log também contém linhas `REVERT_GET_CHANGES_TARGET True <StoreDeleted> 20 ...`. Elas correspondem à criação/marcação inicial da variável da fixture, não à atribuição Revert. Para a conclusão, a linha relevante é a que registra `True 20 10`.

## Confronto com o SDK 7.4.11

### StoreDict

`StoreDict.get_changes(cycle)` compara `self.old` com o store atual. Se `cycle=True`, troca `self.old` pela captura atual (`new`) e atualiza `ever_been_changed`; com `cycle=False`, retorna as diferenças sem avançar `old`. Após o ciclo verdadeiro, a próxima consulta pode retornar vazio para a mesma mutação, pois a base de comparação já inclui o valor novo.

### RollbackLog.begin e complete

`RollbackLog.begin()` roda antes de um nó. Quando o contexto permite rollback e o método decide criar um novo registro (por interação anterior, checkpoint ou `force=True`), chama `self.complete(True)` para fechar o registro anterior. `RollbackLog.complete(begin=True)` passa `begin` a `StoreDict.get_changes(begin)`, portanto pede `cycle=True`.

### Context.run e callback Python

`Context.run()` chama `renpy.game.log.begin(...)` no início do nó quando o rollback está ativo e a política determina atualizar o log. Depois o nó executa. `renpy.ast.Python.execute()` chama `renpy.config.python_callbacks` no `finally`, ao término do nó Python fora da fase de init. Assim, no caso observado, a ciclagem pelo log precede a callback que consulta o delta.

Esse encadeamento explica a ausência da mudança no callback sem implicar que ela saiu do histórico reversível: `complete(True)` arquiva a mudança no registro corrente, enquanto `get_changes(False)` é apenas uma consulta à diferença ainda aberta desde o último `begin` do StoreDict. O runtime confirma que rollback posterior restaurou o valor.

## Classificação

- **CONFIRMADO NO SDK 7.4.11 — fonte:** `get_changes(True)` avança `StoreDict.old`; `complete(begin=True)` pede esse ciclo; `RollbackLog.begin()` chama `complete(True)` quando inicia novo registro; `Context.run()` inicia o registro antes da execução do nó; `ast.Python.execute()` chama callbacks no fim do nó.
- **OBSERVADO EM RUNTIME — fixture reduzida:** delta 20→10 foi capturado em `get_changes(True)` na pilha `complete/begin/run...` com rollback habilitado; a callback subsequente não o encontrou; rollback restaurou 20.
- **OBSERVADO EM RUNTIME — fixture reduzida:** sem rollback, a callback viu 20→10 por `get_changes(False)` e o handler gerou um registro.
- **INTERPRETAÇÃO corroborada:** o log reversível capturou o delta antes da callback; a ausência do delta no callback não significa ausência da mutação no histórico.
- **PENDENTE:** confirmar a mesma sequência com o StoreMonitor e a `NotificationsClass` integrais do URM carregados pelo loader, e identificar diferenças para ações executadas em outras posições do fluxo.

## Fontes e reprodução

| Fonte | Símbolos / intervalos | Blob SHA |
|---|---|---|
| SDK `renpy/python.py` | `StoreDict.get_changes` (aprox. 128–183), `RollbackLog.begin` (aprox. 1620–1685), `RollbackLog.complete` (1707–1755) | `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| SDK `renpy/execution.py` | `Context.run` (aprox. 500–555 e finalização do loop) | `547f73b26dad0fe08fda6333e5f4b60c97cf8772` |
| SDK `renpy/ast.py` | `Python.execute` e chamada de `python_callbacks` (aprox. 925–945) | `d81ffc13f28f0b7442ba6905f1745ee838f7b185` |
| URM convertido `classes/vars.rpy` | `_m1_vars__pythonCallback`, `handleVarChange`, `Var.setValue` | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| URM convertido `screens/vars.rpy` | `URM_var_changed`, botão `Revert` | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |

- Fixture instrumentada: commit [87cafd440572151f1d30c58758818e8cdc7d69d8](https://github.com/mucholocco86/laborat-rio_renpy/commit/87cafd440572151f1d30c58758818e8cdc7d69d8).
- Workflow: commit [58c79fc5b1e44e546e31c12d011d986512c96480](https://github.com/mucholocco86/laborat-rio_renpy/commit/58c79fc5b1e44e546e31c12d011d986512c96480).
- Run: [39663561168](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39663561168), conclusão **SUCCESS**.
- Contexto anterior: [25 — Callback, edição por screen e restauração por rollback](25_CALLBACK_ROLLBACK_STOREDELTA_GAMEPLAY.md) e [27 — Notificação, Revert e persistência](27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md).
## Combinação de Revert, freeze, monitor e callback natural

**Run:** [39664217382](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39664217382), conclusão **SUCCESS**. A fixture ampliada exercitou a ação reduzida Revert com a variável congelada e monitorada, primeiro sem rollback e depois com rollback habilitado.

### Sem rollback

Log relevante:

```text
REVERT_GET_CHANGES_TARGET False 20 10 urm_revert_monitor_callback/execute/...
REVERT_MONITOR_CALLBACK_DELTA 20 10
REVERT_MONITOR_CALLBACK_HANDLED 20 0
REVERT_MONITOR_AFTER_ACTION 10 True 20 10 [] 2
```

A callback recebeu o delta `20→10`. O handler reduzido viu `frozen=True`, chamou a edição URM reduzida para restaurar o valor anterior e, dentro do handler, o valor voltou a `20`. Nenhuma notificação foi registrada, consistente com freeze ter precedência sobre monitor na classe reduzida. Porém, depois que a interação retornou ao label, a leitura foi `10`. Logo, o efeito de restauração do handler não persistiu até esse ponto do fluxo. A causa dessa diferença temporal ainda não foi localizada; ela não deve ser descrita como um freeze que efetivamente bloqueou a atribuição, pois a atribuição para `20` ocorreu durante a callback.

### Com rollback habilitado

Log relevante:

```text
REVERT_GET_CHANGES_TARGET True 20 10 complete/begin/run/...
REVERT_MONITOR_AFTER_ACTION 10 False None None [] 2
REVERT_MONITOR_AFTER_ROLLBACK 20 False []
```

O delta foi ciclado por `get_changes(True)` antes da callback, portanto o handler congelado não foi chamado. O valor permaneceu em `10` após a ação e o rollback explícito restaurou `20`. Não houve registro de notificação.

## Classificação e limites

- **OBSERVADO EM RUNTIME — fixture reduzida:** com freeze + monitor e sem rollback, callback recebe `20→10`; handler registra internamente que reatribuiu `20`, sem notificação; depois da interação o valor é `10`.
- **OBSERVADO EM RUNTIME — fixture reduzida:** com freeze + monitor e rollback, callback não recebe o delta; valor fica `10` após a ação e rollback retorna a `20`.
- **CONFIRMADO NA FONTE REDUZIDA:** o handler prioriza freeze sobre monitor; em freeze tenta restaurar `oldVal` por `Var.setValue`.
- **PENDENTE:** identificar por que o valor escrito como `20` dentro da callback aparece como `10` depois da interação; confirmar se a mesma sequência ocorre com `StoreMonitor`, `VarsStore` e NotificationClass integrais do URM.
- **Limitação:** `_frozen_names`/`_monitored_names` são sets Python simples no harness, não os stores `.urm` reais. A fixture reproduz o circuito relevante, mas não carrega o pacote URM via loader.

A fixture e o workflow foram atualizados nos commits [32842a1aeb254e2c22d410302129c6927b8a6058](https://github.com/mucholocco86/laborat-rio_renpy/commit/32842a1aeb254e2c22d410302129c6927b8a6058) e [3ba4c679033c8a4bc75eb4b30caa0a2e2beedeb6](https://github.com/mucholocco86/laborat-rio_renpy/commit/3ba4c679033c8a4bc75eb4b30caa0a2e2beedeb6). O primeiro run após incluir a asserção inicial falhou porque revelou a diferença temporal; a fixture foi então instrumentada para separar o valor escrito dentro do handler da leitura após a interação. O run final acima passou com essas duas observações registradas.
## Correção da leitura temporal — callback altera o valor depois do snapshot

O run adicional [39665745692](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39665745692) corrigiu a interpretação da seção anterior. No SDK 7.4.11, `renpy.ast.Python.execute()` executa o bytecode e chama `renpy.config.python_callbacks` dentro do bloco `finally`. Por isso, no label, a atribuição `urm_revert_monitor_value_after = urm_revert_monitor_value` captura `10` antes que a callback processe o delta. O valor dessa variável auxiliar não era uma leitura posterior ao handler.

A fixture agora atribui outra auxiliar no próximo nó Python, depois que a callback já terminou. O log passou a mostrar:

```text
REVERT_MONITOR_CALLBACK_DELTA 20 10
REVERT_MONITOR_CALLBACK_HANDLED 20 0
REVERT_MONITOR_AFTER_ACTION 10 20 True 20 10 [] 2
```

Assim, sem rollback, o handler de freeze reatribui `20`; a leitura no nó Python seguinte confirma que o valor permanece `20`. Nenhuma notificação é criada. Com rollback habilitado, o ciclo de `StoreDict` ainda impede o callback de receber o delta, e o rollback explícito restaura `20` a partir do checkpoint.

- **CONFIRMADO NO SDK 7.4.11:** callbacks Python são chamados no `finally` de `Python.execute()`, após o bytecode daquele nó.
- **OBSERVADO EM RUNTIME — fixture reduzida:** snapshot antes da callback é `10`; leitura no nó seguinte, depois do handler, é `20`.
- **Correção:** a hipótese anterior de que outro mecanismo recolocava `10` após a callback estava baseada numa auxiliar lida antes da execução da callback e fica retirada.
- **PENDENTE:** validar o mesmo circuito com os stores e classes integrais do URM carregados pelo loader.

Fixture atualizada no commit [f0d1cdd298dfd990e4281c9bb91b579a3e5b214e](https://github.com/mucholocco86/laborat-rio_renpy/commit/f0d1cdd298dfd990e4281c9bb91b579a3e5b214e); run [39665745692](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39665745692) concluiu **SUCCESS**.
## Transferência de `Context.force_checkpoint` para o log

O fixture recebeu observação adicional no run [39669205656](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39669205656) para acompanhar os dois flags nas fronteiras da callback e do próximo nó.

### O que o SDK faz

Em `Context.run()`, quando `context.force_checkpoint` está ativo, o próximo nó força `RollbackLog.begin(force=True)`. Se o rollback daquele contexto está habilitado, o fluxo então transfere o pedido para `renpy.game.log.force_checkpoint = True` e limpa `context.force_checkpoint`. Em `RollbackLog.complete()`, um `force_checkpoint` pendente é consumido por `checkpoint(hard=False)`: é um checkpoint soft, não a marcação de rollback fixo.

O callback real do URM convertido segue esta ordem: define `context.force_checkpoint = True` e depois consulta `StoreDict.get_changes(False)`. A atribuição fica antes da leitura e é executada em todas as chamadas do callback, inclusive quando o delta está vazio. Só depois disso percorre as mudanças, quando houver.

### O que o trace viu

Com rollback desabilitado no harness, o flag ficou no contexto (`context=True`, `log=False`), pois `Context.run()` não transfere o pedido quando `self.rollback` está falso. Esse modo serve apenas para contrastar o mecanismo e não modela gameplay.

Com rollback habilitado, a primeira callback começou com ambos os flags falsos e deixou `context=True`. No nó seguinte, o SDK consumiu esse pedido: antes da callback desse próximo nó, a fixture observou `context=False`, `log=True`. Isso confirma a transferência para `RollbackLog.force_checkpoint`. Como o callback reduzido continua definindo o flag mesmo sem delta, as callbacks Python subsequentes podem voltar a enfileirar pedidos; a fixture registrou essa repetição, mas não contou de modo independente quantos checkpoints soft foram materializados.

### Classificação

- **CONFIRMADO NO SDK 7.4.11 — fonte:** `Context.run()` converte o flag do contexto em `RollbackLog.force_checkpoint` quando rollback está ativo; `RollbackLog.complete()` converte esse flag em `checkpoint(hard=False)`.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** `_m1_vars__pythonCallback` define o flag antes de consultar `get_changes`, mesmo quando a consulta não retorna mudanças utilizáveis.
- **OBSERVADO EM RUNTIME — fixture reduzida:** com rollback ativo, a flag passa de contexto para log entre o callback de um nó e a execução/callback do nó seguinte.
- **PENDENTE:** instrumentar o número e os limites dos checkpoints soft efetivamente criados em gameplay real; validar o padrão com o callback e loader do URM integral.

Referências de fonte: SDK `renpy/execution.py` (`Context.run`, aprox. linhas 515–550; blob `547f73b26dad0fe08fda6333e5f4b60c97cf8772`); SDK `renpy/python.py` (`RollbackLog.begin/complete`, blob `c5eb2819a3e4ee096dbf01130d70a77f9b623484`); URM convertido `classes/vars.rpy` (`_m1_vars__pythonCallback`, blob `57482937e14f215dac0ecb22a62da8ad160cba58`). Fixture probe commit [13cd486d01150046ec9e15052a386e14cd8899bc](https://github.com/mucholocco86/laborat-rio_renpy/commit/13cd486d01150046ec9e15052a386e14cd8899bc).
## Materialização do checkpoint soft — trace runtime

O wrapper diagnóstico da fixture delega a `RollbackLog.checkpoint` para a implementação original e registra somente chamadas com `hard=False`, observando `current.checkpoint` antes e depois. O run [39893930678](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39893930678) passou.

No testcase reduzido de callback com rollback, a instrumentação registrou 10 chamadas: uma encontrou `current.checkpoint=True` e permaneceu `True`; nove mudaram `False→True`. No caso frozen+monitor, foram 11 chamadas: uma `True→True` e dez transições `False→True`. A transição `False→True` confirma que aquele registro corrente foi marcado como checkpoint. Quando o valor já era `True`, a chamada não criou outra marca nesse mesmo registro.

Esses números cobrem o trecho instrumentado do testcase, que inclui nós de preparação, callbacks Python subsequentes e a transição do rollback. Portanto, não significam 9 ou 10 checkpoints por clique nem quantificam o comportamento do URM integral. O wrapper observa o efeito sobre o registro corrente; a confirmação de que `checkpoint(hard=False)` não eleva `hard_checkpoint` vem da inspeção da implementação original do SDK.

- **OBSERVADO EM RUNTIME — fixture reduzida:** chamadas soft podem marcar registros ainda não marcados; chamadas em registros já marcados não criam outra marca.
- **CONFIRMADO NO SDK 7.4.11 — fonte:** o método retorna se `current.checkpoint` já for verdadeiro; quando marca um checkpoint com `hard=False`, não promove `current.hard_checkpoint`.
- **PENDENTE:** isolar a contagem por fronteira de callback sem incluir nós de setup/rollback e executar o circuito com o URM integral.

Fixture instrumentada no commit [d4a132ae51d53a583e1167a6d6a0f79c962f0eb5](https://github.com/mucholocco86/laborat-rio_renpy/commit/d4a132ae51d53a583e1167a6d6a0f79c962f0eb5); run [39893930678](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39893930678), **SUCCESS**.
## Contagem de checkpoints soft no rollback normal

A revisão de `RollbackLog.rollback()` mostra como o pedido `checkpoint(hard=False)` influencia o retrocesso:

- `RollbackLog.checkpoint()` marca `current.checkpoint=True`, mas, com `hard=False`, não incrementa `rollback_limit` nem define `current.hard_checkpoint`.
- `can_rollback()` depende de `rollback_limit > 0`; portanto, o checkpoint soft não cria por si só capacidade adicional de rollback interativo.
- No rollback normal (`on_load=False`), o laço decrementa `checkpoints` somente quando encontra `rb.hard_checkpoint`. Um registro com apenas `rb.checkpoint=True` não satisfaz a contagem solicitada.
- Depois de localizar o hard checkpoint solicitado, o caminho `greedy=True` pode remover registros posteriores não hard, incluindo os que só têm checkpoint soft, até o limite/condição seguinte.
- A exceção no mesmo método é `on_load=True`: nesse modo, `rb.checkpoint` soft também reduz a variável local `checkpoints`. O carregamento tem, portanto, regra própria.

Essa conclusão é **CONFIRMADA NO SDK 7.4.11 pela fonte** (`renpy/python.py`, `RollbackLog.checkpoint`, `can_rollback`, `rollback`; blob `c5eb2819a3e4ee096dbf01130d70a77f9b623484`). A API pública `renpy.checkpoint()` também transforma `hard` em `renpy.store._rollback and hard` (`renpy/exports.py`, blob `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`).

### Tentativa runtime não conclusiva

A tentativa [39894546076](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39894546076) falhou nas asserções e **não** é evidência de runtime para a regra. O harness adicionou interações/checkpoints próprios, e o rollback retornou a um estado anterior ao valor de setup. As saídas mostraram `rollback_limit` ficar em 1 após o pedido soft numa variante, mas a sequência final não isolou a fronteira de estado pretendida. O testcase foi removido da fixture e do workflow para não deixar uma etapa vermelha. O run anterior [39894376572](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39894376572) também falhou por loop de teste antes de uma validação útil.

- **CONFIRMADO NO SDK 7.4.11 — fonte:** soft não incrementa `rollback_limit` e não conta como checkpoint normal em `rollback(on_load=False)`.
- **PENDENTE:** desenhar um teste runtime com boundary/interaction e log de rollback controlados, sem usar os menus do harness como pontos hard implícitos.
- **Não concluído:** nenhum comportamento do URM integral foi validado por esses dois runs com falha.