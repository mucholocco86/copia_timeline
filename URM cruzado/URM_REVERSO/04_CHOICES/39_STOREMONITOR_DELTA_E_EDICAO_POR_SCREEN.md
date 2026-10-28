# 39 — StoreMonitor, delta do StoreDict e edição iniciada por screen

**Data:** 2026-10-23  
**Escopo:** explicar a ausência de chamada a `StoreMonitor.handleVarChange` no teste integrado de edição e distinguir notificação do URM da captura reversível nativa do Ren'Py 7.4.11.  
**Evidência:** inspeção das fontes do URM original e do SDK; runtime integrado do URM original com variável marcada para monitoramento e rastreamento da pilha do callback; runtime reduzido anterior sobre ciclagem de delta.  
**Proteções:** não houve mudança em SDK, fontes originais URM, `wells/` ou `wells_beta/`.

## Resultado

A fonte do URM confirma que `URM_modify_value` escreve no store por `SetVarValue → Var.setValue`, sem chamar diretamente `StoreMonitor.handleVarChange`. O monitor consulta mudanças em callback de nó `ast.Python`.

O run integrado [39910519723](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39910519723) mostra que, após a edição 1→7, `RollbackLog.complete(begin=True)` chama `StoreDict.get_changes(True)`, recebe um delta contendo `urm_edit_probe_value: 1` e o grava no registro corrente. O PAGEUP 3 aplica esse registro e restaura 1/None. Portanto, neste cenário, a escrita 1→7 foi capturada como delta reversível nativo.

A leitura oposta dos runs 39909338891 e 39910066028 era um falso negativo no próprio probe. O gate `isinstance(changes, dict)` usava o nome global `dict`, que no contexto Ren’Py do fixture resolvia para `renpy.python.RevertableDict`; a coleção retornada era um `dict` nativo. A confirmação foi obtida em 39910519723 ao imprimir `type(changes)`, o binding de `dict` e testar diretamente `"urm_edit_probe_value" in changes`. A análise anterior foi corrigida, não se trata de mudança de comportamento entre execuções.

## Efeito sobre o StoreMonitor neste percurso

No run 39910519723, depois de `complete(begin=True)` ciclar a base do StoreDict com o valor atual 7, a consulta posterior `get_changes(False)` não continha `urm_edit_probe_value`; ela continha a alteração de `urm_edit_probe_route_value`. A fixture tampouco registrou chamada a `StoreMonitor.handleVarChange` para a variável editada. Como a fonte do callback do URM consulta `get_changes(False)` e só chama o handler para as chaves retornadas, a ordem observada explica por que a edição foi reversível sem gerar chamada do monitor nesse caso: o delta foi incorporado ao rollback antes de estar disponível ao callback. Isso é uma explicação sustentada pela combinação de fonte e trace, limitada ao caminho testado; não prova comportamento de toda edição ou configuração de monitoramento.

No run integrado [39910824879](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39910824879), `VarsStore.monitor("urm_edit_probe_value")` deixou `isMonitored=True`; a tela original editou 1→7, a rota leu 7 e o rollback retornou a 1/None. Não houve chamada a `StoreMonitor.handleVarChange` nem `Notifications.add` para essa variável. A flag foi ativada pela API, sem testar seu carregamento de `.urm`.

A pilha foi identificada no run [39912065172](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912065172): `ConstantStoreHandler.handler` → `StoreMonitor._m1_vars__pythonCallback` (vars.rpy, linha 547) → `renpy.ast.Python.execute` (linha 933). Nessa chamada real do callback, `get_changes(False)` continha `urm_edit_probe_route_value`, mas não `urm_edit_probe_value`; `URM_modify_value` já estava fechada. O trace imediatamente anterior mostrou `RollbackLog.complete(begin=True)` chamando `get_changes(True)`, capturando o valor antigo 1 e ciclando a base. Assim, a ausência de notificação fica explicada neste cenário: o delta da variável foi incorporado ao registro reversível antes da consulta do callback.

## Sequência que as fontes sustentam

O SDK permite o seguinte caminho genérico: interação anterior pode levar `Context.run()` a `RollbackLog.begin()`; quando começa novo período, `begin()` pode chamar `complete(True)`, que consulta `StoreDict.get_changes(True)`. Em outro momento, `ast.Python.execute()` chama os callbacks, e a callback do URM consulta `get_changes(False)`.

O fluxo foi observado diretamente no run 39910519723: `complete(begin=True)` chamou `get_changes(True)`; o delta continha o valor antigo 1 e foi atribuído ao campo de store do registro corrente. A callback do URM e `get_changes(False)` permanecem caminhos distintos de notificação/observação. O probe reduzido do documento 32 continua sendo um percurso separado, não a única evidência de ciclagem de delta.

## Evidência de fonte

### URM original

- A screen `URM_modify_value` vincula `valueInput.onEnter` a `SetVarValue(...)`; Change invoca a mesma ação.
- `Var.setValue` valida/converte o valor e executa a atribuição (ou mutação de item) sobre `renpy.store`. Não chama `handleVarChange`.
- `StoreMonitor.init()` registra `_m1_vars__pythonCallback` em `renpy.config.python_callbacks` e também injeta um setter para um caminho específico de atribuições.
- `_m1_vars__pythonCallback` primeiro define `renpy.game.context().force_checkpoint = True`; depois consulta `get_changes(False)` e chama `handleVarChange` para as chaves retornadas.
- `handleVarChange` só cria notificação quando a variável está monitorada, a tela de edição não está aberta e old/new diferem. Congelamento é tratado antes e retorna `False`.

### SDK Ren'Py 7.4.11

- `renpy.ast.Python.execute()` chama callbacks ao final do bytecode, fora da fase init.
- `Context.run()` decide se atualizará rollback antes da execução do nó e pode começar esse ciclo por interação anterior.
- `RollbackLog.begin()` não fecha um registro a cada nó incondicionalmente: a interação, checkpoint anterior ou force determina se começa. Quando começa com um registro atual, chama `complete(True)`.
- `RollbackLog.complete(begin=True)` passa o parâmetro a `StoreDict.get_changes(begin)`; com `True`, o StoreDict avança sua base de comparação enquanto fornece as alterações do intervalo.
- A flag de contexto `force_checkpoint` é transferida para `RollbackLog.force_checkpoint` em `Context.run()` depois de chamar `log.begin()`. O log consome essa flag em `complete()` com `checkpoint(hard=False)`; isso não equivale a um hard checkpoint criado no instante da edição.

A conclusão sobre ciclo de delta também está registrada em [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md); a semântica de checkpoint soft em [documentos 18 e 19](README.md).

## Evidência de runtime integrada

No run [39909338891](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39909338891) (**SUCCESS**), a fixture instrumentou `StoreDict.get_changes`, `StoreDict.begin`, `RollbackLog.complete` e `Rollback.rollback`, delegando aos métodos originais. O pacote URM original foi copiado sem alterações para o jogo descartável.

- `Var.setValue` alterou 1→7; o bloco da rota leu 7.
- No run [39910519723](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39910519723), imediatamente após `Var.setValue` mudar 1→7, `complete(begin=True)` foi chamado no nó 69. A repetição monitorada [39912065172](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912065172) rastreou a pilha do callback até `ast.Python.execute` e confirmou que `get_changes(False)` posterior não continha a variável editada, com a tela já fechada. Antes da chamada, o registro não tinha a chave-alvo e `StoreDict.old` continha 1.
- `get_changes(True)` retornou delta do tipo `dict` nativo com `urm_edit_probe_value: 1`; membership direto foi verdadeiro. `complete()` terminou com a mesma identidade de registro e o dicionário de store contendo o valor antigo 1. O próximo delta observado com `cycle=False` continha a rota, não repetiu a chave editada.
- PAGEUP 1 e 2 mantiveram valor/rota em 7; PAGEUP 3 aplicou o registro contendo 1 e restaurou valor 1/rota `None`; PAGEUP 4 não mudou o estado.

A restauração é, portanto, explicada pelo delta da escrita 1→7 presente no histórico. O run anterior [39907164916](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39907164916) localizou o evento de aplicação no terceiro PAGEUP.

## Correção de leitura de `force_checkpoint`

O run integrado registrou `context.force_checkpoint=True` durante a chamada de `Var.setValue`. Isso não prova que `Var.setValue` solicitou checkpoint: a fonte dessa função não escreve a flag. O callback do URM a define incondicionalmente ao final dos nós Python, e o SDK transfere a solicitação em outro ponto do ciclo do executor. Sem instrumentar cada escrita e transferência da flag nesse fixture, a origem daquele valor naquele instante permanece **PENDENTE**.

Do mesmo modo, o registro da flag não demonstra um hard checkpoint nem explica sozinho por que o valor foi revertido. A reversibilidade decorre da integração com o histórico nativo observada no teste, enquanto a flag de checkpoint tem semântica própria.

## Trace por evento de rollback

A fixture integrada foi corrigida para instalar o wrapper de `RollbackLog.rollback` na classe; antes, a função de trace estava definida, mas não substituía o método. No run [39907164916](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39907164916), o job terminou **SUCCESS** e imprimiu estado após cada PAGEUP:

| Evento | Valor da variável | Rota | Estado observado |
|---|---:|---|---|
| PAGEUP 1 | 7 | 7 | Ainda no fluxo posterior; limite de rollback 2 |
| PAGEUP 2 | 7 | 7 | Fixed rollback ativo no retorno; limite 1 |
| PAGEUP 3 | 1 | `None` | Aqui `RollbackLog.rollback()` restaurou o estado anterior ao menu; fixed rollback ativo, limite 0 |
| PAGEUP 4 | 1 | `None` | A chamada foi registrada, mas sem novo estado a restaurar; permaneceu na fronteira |

A execução anterior [39905267994](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39905267994) demonstrava apenas o estado final após quatro teclas. O run 39907164916 substitui essa incerteza sobre o evento: no cenário testado, a restauração ocorreu no **terceiro PAGEUP**.

O teste continua condicionado ao harness: `context.rollback=True`, `store._rollback=True`, `fix_rollback_without_choice=False`, uma Choice B, chamada direta ao handler do CodeView e quatro eventos de teclado do runner. Não generalizar a contagem de PAGEUP para outros scripts, políticas ou configurações.

## Classificação

- **CONFIRMADO NA FONTE URM ORIGINAL:** editor screen → `SetVarValue` → `Var.setValue`; callback do monitor é registrada em `python_callbacks`; callback define `force_checkpoint` e consulta mudanças; setter e callback são caminhos distintos.
- **CONFIRMADO NO SDK 7.4.11:** `ast.Python.execute()` chama callbacks depois do bytecode; `RollbackLog.begin/complete` pode ciclar StoreDict; `Rollback.rollback()` reaplica valores antigos armazenados em cada registro.
- **OBSERVADO EM RUNTIME INTEGRADO:** a edição 1→7 foi lida pela rota; no run 39910519723, `get_changes(True)` retornou o valor antigo 1, `complete()` o guardou no registro corrente e PAGEUP 3 o reaplicou. Nos runs 39910824879/39912065172, com `isMonitored=True`, a pilha confirmou a execução do callback: sua consulta `get_changes(False)` não tinha a variável; a tela já estava fechada e não houve chamada a `handleVarChange`/notificação.
- **CONFIRMADO NO SDK 7.4.11:** `StoreDict.get_changes(True)` retorna um mapeamento de valores anteriores ao ciclo e atualiza a base `old`; `RollbackLog.complete(begin=True)` grava o delta no registro corrente.
- **OBSERVADO EM RUNTIME REDUZIDO:** documento 32 mediu outro percurso de ciclo do delta (20→10) antes da callback.
- **CORRIGIDO:** o falso negativo dos runs 39909338891/39910066028 vinha do gate `isinstance(changes, dict)`, pois o nome `dict` do contexto Ren’Py resolvia para `RevertableDict`, mas o delta era `dict` nativo. O membership direto foi validado em 39910519723.
- **PENDENTE:** localizar a origem exata da solicitação/transferência de `force_checkpoint`; validar metadados carregados de arquivo `.urm`; testar variável congelada, save/load, clique visual no hyperlink e outros pontos de edição.

## Fontes

| Arquivo | Símbolos / intervalo aproximado | Blob SHA |
|---|---|---|
| SDK `renpy/ast.py` | `Python.execute`, ~910–940 | `d81ffc13f28f0b7442ba6905f1745ee838f7b185` |
| SDK `renpy/execution.py` | `Context.run`, início de nó e transferência de `force_checkpoint`, ~500–565 | `547f73b26dad0fe08fda6333e5f4b60c97cf8772` |
| SDK `renpy/python.py` | `StoreDict.get_changes` ~160–190; `RollbackLog.begin/complete/checkpoint`, ~1632–1860; `rollback`, ~1930–1995 | `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| SDK `renpy/pydict.pyx` | `DictItems` e `find_changes`, ~84–160; confirmação de que o delta é materializado como dicionário | `24fcb4d701afe6f3042aef6cd7e1f8f934ffc761` |
| URM original `classes/vars.rpy` | `Var.setValue`, `StoreMonitorClass`, ~232–269, 492–577 | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| URM original `screens/vars.rpy.x52` | `URM_modify_value` e ação Input/Change, ~181–254 | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |

- Fixture integrada e workflow: [run 39907164916](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39907164916).
- Fixture: [urm_real_loader_variable_edit_probe.rpy](../tools/fixtures/urm_real_loader_variable_edit_probe.rpy).
- Documento complementar de edição: [38 — Edição de variável pelo URM e retorno por rollback](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md).
