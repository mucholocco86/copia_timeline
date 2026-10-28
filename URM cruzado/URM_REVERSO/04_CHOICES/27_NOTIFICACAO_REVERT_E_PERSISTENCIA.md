# 27 — Notificação de variável, ação “Revert” e persistência

**Data:** 2026-10-20  
**Escopo:** separar notificações do StoreMonitor, a ação visual “Revert”, configurações de notificação, arquivo .urm e save nativo.  
**Evidência:** inspeção estática do código convertido do URM. Não foi executado o pacote completo do URM nesta etapa.  
**Proteções:** nenhum arquivo original do URM, SDK, wells/ ou wells_beta/ foi alterado.

## Conclusão principal

A notificação de variável alterada é um objeto transitório em uma lista de NotificationsClass. O botão chamado **Revert** na janela da notificação não aciona renpy.rollback(): ele usa SetVarValue para atribuir à variável o valor anterior recebido pela tela. É uma correção manual do valor corrente, não uma restauração do histórico de execução.

A configuração notificationTimeout é persistida pelos mecanismos de Settings. Isso não demonstra que os objetos das notificações sejam persistidos junto com ela.

## Circuito da notificação

1. StoreMonitor.handleVarChange detecta que a variável tem a flag monitor, compara valor antigo e atual, e chama Notifications.add(...) se a tela de edição do URM não estiver aberta.
2. NotificationsClass.add cria Notification, adiciona o objeto a self.notifications e reinicia a interação.
3. A screen URM_notifications percorre essa lista e exibe rótulo/texto. Ao clicar, a ação do objeto é executada e a notificação é removida.
4. Se Settings.notificationTimeout for diferente de zero, add agenda uma thread para remover a notificação após o intervalo.

A lista é criada como [] em NotificationsClass.__init__; os métodos examinados alteram essa lista em memória. A classe de notificações não escreve diretamente em persistent, em arquivo .urm ou em arquivo global.

## O que “Revert” realmente faz

A tela URM_var_changed(varName, prevVal) apresenta valor anterior e valor atual. O botão Revert invoca SetVarValue(var, newValue=prevVal). Isso leva a Var.setValue, que faz atribuição no store do jogo. A ação não chama renpy.rollback(), não restaura o Context e não desfaz outros efeitos que ocorreram depois da mudança.

Portanto, se a variável monitorada mudou de 10 para 20, o botão tenta escrever 10 novamente no estado atual. Esse ato pode ele próprio ser registrado no histórico nativo como uma nova mutação do store, mas o efeito temporal exato na sessão integral ainda não foi testado.

Se a variável estiver congelada, Var.setValue tenta removê-la temporariamente da lista congelada, realiza a escrita e a congela novamente no bloco finally. O botão Revert usa essa mesma rota.

## Quatro superfícies de dados separadas

| Superfície | Conteúdo confirmado | Relação com notificações |
|---|---|---|
| Lista Notifications.notifications | objetos com rótulo, texto e ação; remoção por fechar, limpar ou timeout | Dados transitórios em memória no circuito examinado |
| Configuração notificationTimeout | intervalo de duração das notificações | Settings.set persiste em persistent.URMSettings por padrão; opção global escreve JSON em arquivo compactado próprio |
| Arquivo .urm | stores de ferramentas como vars, watched, labels, replacements e propriedades | A classe Notifications não aparece como store consumidor/produtor no circuito consultado |
| Save nativo | Gamesaves.save/load delegam para renpy.save/load | É o mecanismo de save de gameplay; a interação de objetos de notificação com esse ciclo precisa de teste |

### Cuidado com save/load nativo

NotificationsClass herda de x52NonPicklable. No código convertido, essa base define __getstate__ como {} e __setstate__ como operação vazia. Isso demonstra que o estado Python serializado por esses hooks não inclui os atributos normais do objeto. **Não é suficiente, isoladamente, para afirmar o resultado visível de um save/load**: o ciclo de reconstrução do store do Ren’Py e a disponibilidade da lista após carregar ainda precisam ser observados em runtime.

A mesma distinção vale para StatesClass: o mapa _states mostrado na fonte pertence ao objeto URM e não é escrito explicitamente em persistent nem no arquivo .urm pelos métodos examinados. Não inferir sua vida útil após carregar uma partida sem teste.

## Classificação

- **CONFIRMADO NA FONTE URM CONVERTIDA:** NotificationsClass mantém e remove objetos de uma lista em memória; timeout também remove dessa lista.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** o botão “Revert” chama SetVarValue com prevVal; é uma atribuição, não uma chamada ao mecanismo de rollback.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** notificationTimeout é uma configuração acessada por Settings, cujos destinos de persistência são persistent.URMSettings e arquivo global próprio.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** os hooks de x52NonPicklable retornam estado vazio e não restauram estado próprio.
- **PENDENTE DE RUNTIME:** se notificações visíveis sobrevivem, desaparecem ou são reconstruídas após carregar save nativo; e se uma notificação pendente acompanha um rollback da sessão.
- **PENDENTE DE RUNTIME:** se a atribuição executada pelo botão Revert é imediatamente reversível e qual fronteira a desfaz, considerando a posição corrente no histórico.

## Fontes consultadas

| Arquivo convertido | Símbolos / intervalos | Blob SHA |
|---|---|---|
| classes/notifications.rpy | NotificationsClass, Notification (5–43) | 3283ec4b1615967a71ad21cc34670bf8158ab96d |
| classes/vars.rpy | StoreMonitor.handleVarChange, callback e Var.setValue | 57482937e14f215dac0ecb22a62da8ad160cba58 |
| screens/vars.rpy | URM_var_changed: botões Change/Revert/Close (453–487) | 7959b2c0e6249df0edbb9ebe683481d46e4537e1 |
| screens/watchpanel.rpy | renderiza e executa notificações; ação para limpar todas (330–351) | 8cc83f00838ed409183e85e4ebdb37ddf4433823 |
| classes/settings.rpy | leitura/escrita de Settings e destinos persistentes (151–218) | 13fd70596135c4389c9ab01cae982f80bfcad461 |
| classes/URMFiles.rpy | stores do arquivo, serialização ZIP/JSON e load/save (194–220, 308–372) | 888aba28d9d2e7870d8c4e6526417390179cd326 |
| classes/gamesaves.rpy | wrappers de save/load nativos | bbedbd08f9ce106c77a12bdb984e11008cf995bf |
| classes/states.rpy | mapa local de flags transitórias | b787b94fc40183b24165d2844a0f91bc12980626 |
| framework/modules/01utils.rpy | hooks de x52NonPicklable | e558a2d5a5137608e542238a1d81fd65e6db349d |

## Próximo teste reduzido recomendado

No SDK 7.4.11, gerar uma notificação sintética com valor anterior conhecido; comparar três ações isoladas: fechar a notificação, clicar Revert, e acionar rollback nativo. Registrar valor do store, fronteira/contexto e existência da notificação antes/depois. Em outro cenário, salvar e carregar com uma notificação pendente, observando a screen e o objeto. Esse teste separa a semântica da ação Revert da persistência visual da lista sem executar ou modificar o pacote integral do URM.

## Atualização de runtime — fixtures reduzidas (2026-10-20)

Esta seção atualiza as pendências de runtime acima com resultados posteriores. Ela **não** substitui os limites de escopo indicados no restante do documento.

### Ação “Revert”

A fixture reproduziu a chamada da tela: `SetVarValue(Var(...), newValue=prevVal)()`. No run [39379101294](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39379101294), o valor corrente começou em 20, com marcador independente de rota em 1 e valor anterior 10. Após a ação, o valor passou a 10 e o marcador permaneceu 1 (`20 / rota 1 / prev 10 → 10 / rota 1`). O teste passou no SDK 7.4.11.

**Classificação:** observado em runtime numa fixture reduzida; confirma que a reprodução da ação faz uma atribuição e não retrocede o fluxo ou desfaz o marcador de rota. Isso corrobora a leitura estática, mas não é um teste da tela nem do pacote integral do URM. A interação dessa atribuição com um rollback posterior e com os deltas internos do log continua pendente.

### Notificações: resultados de save/load e rollback já registrados

O documento [31 — Ciclo de vida das notificações do URM e rollback](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md) e os runs associados já fecharam parte da antiga pendência:

- **Mesma sessão:** nos runs [39214784786](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214784786) e [39215118198](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39215118198), após salvar e mutar a lista em seguida, o load reduziu a lista ao item pós-save observado pela fixture, em vez de restaurar o item que existia no instante do save. É um resultado específico da rota testada, não uma regra universal para qualquer objeto URM.
- **Processo novo:** nos runs [39215564208](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39215564208), [39229685100](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39229685100) e [39230107907](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39230107907), o singleton da fixture começou vazio após init e permaneceu vazio depois do load; a screen foi reconstruída sem o botão que representaria a notificação. O último teste reproduziu um callback pós-load, mas não carregou o pacote dinâmico original do URM nem seu arquivo `.urm`.
- **Rollback da lista:** o run [39205520906](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39205520906) comparou `clear()` e remoção in-place, além do timeout reduzido. Com a screen ativa, `clear()` deixou a lista vazia após rollback; `remove()` restaurou o item; a remoção temporizada também foi revertida na execução controlada. Esses resultados pertencem ao harness reduzido e não demonstram concorrência geral nem integração com a `NotificationsClass` real.

Assim, a antiga formulação “save/load pendente” precisa ser lida como **save/load reduzido parcialmente observado; integração do URM integral pendente**. O singleton, o callback e a screen da fixture reproduzem partes do circuito, não o loader real e os módulos `.x52` do URM.

### Fontes de evidência e limites

- Fixture e workflow do teste “Revert”: fixture commit [8d08fa82d3a7e3bdd2862c2dd8ddd2a60c538524](https://github.com/mucholocco86/laborat-rio_renpy/commit/8d08fa82d3a7e3bdd2862c2dd8ddd2a60c538524) e workflow commit [ee18b6cbb823cf7f91cdf6ac69173d43e58fae40](https://github.com/mucholocco86/laborat-rio_renpy/commit/ee18b6cbb823cf7f91cdf6ac69173d43e58fae40).
- A fixture é uma reprodução reduzida no SDK Ren’Py 7.4.11. Não editou o Wells estável, `wells_beta/`, o SDK ou fontes originais do URM.
- Continua pendente executar o pacote convertido completo: o loader exige módulos e telas dinâmicas `.rpy.x52` que não estão presentes no jogo reduzido. Também falta testar a atribuição Revert seguida por rollback em diferentes pontos do histórico, bem como a interação com freeze/monitor e save/load do jogo real.

### Classificação atualizada

- **CONFIRMADO NA FONTE URM CONVERTIDA:** Revert encaminha `prevVal` para `SetVarValue`; não chama `renpy.rollback()`.
- **OBSERVADO EM RUNTIME (fixture reduzida, SDK 7.4.11):** a ação reproduzida reatribui 10 ao valor corrente 20 e conserva o marcador de rota 1.
- **OBSERVADO EM RUNTIME (fixtures reduzidas):** há diferenças entre rollback de `clear()` e remoção in-place da lista, e entre load na mesma sessão e load em processo novo, conforme casos e runs acima.
- **PENDENTE:** comportamento da screen e dos objetos da `NotificationsClass` no pacote integral, além do rollback posterior à ação Revert e suas combinações com save/load e metadados de monitoramento.
## Atualização runtime — “Revert” atravessado por rollback (2026-10-21)

A primeira execução do novo teste falhou porque a fixture habilitava `context.rollback`, mas deixava `renpy.store._rollback=False`. O teste imprimiu valor 10/rota 0 ao chegar à verificação: a chamada de rollback recuou além do ponto que o cenário pretendia testar. A fonte de `renpy.checkpoint(data, keep_rollback, hard)` no SDK 7.4.11 confirma a causa: o argumento efetivo é `renpy.store._rollback and hard`; assim, com `_rollback=False`, o checkpoint solicitado com `hard=True` vira soft. O run [39560687256](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39560687256) é registrado como tentativa inválida para a pergunta sobre fronteira, não como evidência de que a atribuição não seja reversível.

Na repetição, a fixture ativou `renpy.store._rollback`, `context.rollback` e `config.rollback_enabled`, verificando esses três valores antes do checkpoint. No run [39560909296](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39560909296), a sequência foi:

```text
checkpoint: valor 20, rota 1
ação Revert reduzida: valor 10, rota 1
rollback nativo para o checkpoint: valor 20, rota 1
```

O teste passou. **OBSERVADO EM RUNTIME na fixture reduzida do SDK 7.4.11:** a atribuição correspondente ao Revert entrou no estado reversível e o rollback até o checkpoint imediatamente anterior restaurou o valor anterior à atribuição. O marcador de rota já presente naquele checkpoint permaneceu 1. Portanto, o botão não faz rollback por si; uma chamada posterior ao rollback nativo pode desfazer a atribuição do botão conforme a fronteira alcançada.

### Limites deste resultado

- O probe reproduz `SetVarValue(Var(...), newValue=prevVal)` com uma variável escalar raiz; não executa a screen `URM_var_changed` nem a `NotificationsClass` do pacote integral.
- O teste estabelece deliberadamente um checkpoint hard imediatamente antes da atribuição. Ele não determina quais fronteiras de rollback ficam disponíveis em todo jogo nem o número de interações que o jogador precisaria recuar.
- Não foram combinados neste caso save/load, freeze, monitoramento ou outras mutações posteriores.
- A primeira execução expôs uma condição do harness: para criar checkpoint hard na fixture, foi necessário habilitar também o store global `_rollback`, além do `Context.rollback`.

### Artefatos

- Fixture: commit [aff996dd95da4056c086b0ac76a0250b14499acd](https://github.com/mucholocco86/laborat-rio_renpy/commit/aff996dd95da4056c086b0ac76a0250b14499acd).
- Workflow com os dois probes: commit [c7cc72e3f4d07f3a568a986eaa61024b9cab1a78](https://github.com/mucholocco86/laborat-rio_renpy/commit/c7cc72e3f4d07f3a568a986eaa61024b9cab1a78).
- SDK 7.4.11, `renpy/exports.py`, `checkpoint()`, blob SHA `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`.

**Classificação atualizada:** Revert como reatribuição permanece confirmado na fonte convertida e observado em runtime reduzido; a reversibilidade da atribuição por rollback até um checkpoint hard imediatamente anterior também foi observada na fixture. A validação da screen/URM integral e os cruzamentos com monitor, freeze, save/load e fronteiras de gameplay permanecem pendentes.
## Atualização runtime — Revert em variável congelada e monitorada (2026-10-21)

A fixture reduziu `Var.setValue` com a mesma estrutura relevante da fonte URM: consulta se a variável está congelada, remove temporariamente essa flag, atribui o valor e reaplica a flag em `finally`. O caso também marcou a variável como monitorada, pois a implementação de `StoreMonitor.handleVarChange` testa primeiro `isFrozen` e só depois `isMonitored`.

No run [39561988378](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39561988378), a sequência observada foi:

```text
antes: valor 20, rota 1
após ação Revert reduzida: valor 10, frozen=True, notificações=0
após chamar StoreMonitor.handleVarChange(nome, 20, 10): valor 20, notificações=0, frozen=True
```

**OBSERVADO EM RUNTIME na fixture reduzida:** a atribuição de Revert pode alterar uma variável marcada como frozen pela rota própria de `Var.setValue`, e a flag é reaplicada. Quando o handler recebe explicitamente o delta `20→10`, a regra frozen restaura o valor antigo informado e retorna antes do ramo de notificação; logo, a configuração monitorada não produz aviso nesse caso.

### Limite sobre a callback

Este probe chamou diretamente `StoreMonitor.handleVarChange` com um delta conhecido. Ele **não** demonstrou que `renpy.config.python_callbacks` necessariamente entrega esse delta depois da ação Revert. A disponibilidade do delta depende do ciclo `StoreDict.get_changes`/checkpoint; testes anteriores mostraram que a callback pode não encontrá-lo com rollback habilitado. Portanto, a consequência comprovada é condicional: **se** o handler receber uma mudança enquanto a variável está frozen, ele prioriza freeze, restaura o valor antigo recebido e não notifica.

Também não se testou aqui o pacote integral, a screen real, nem o rollback após o handler. O caso de rollback de Revert sem freeze está no run [39560909296](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39560909296); integrar ambos os mecanismos em um percurso real continua pendente.

### Artefatos e classificação

- Fixture isolada: commit [235718c545673a83f79c8eb32a3645d621bddddf](https://github.com/mucholocco86/laborat-rio_renpy/commit/235718c545673a83f79c8eb32a3645d621bddddf).
- Workflow: commit [cc3ce013ba6fe869642fdb62c78d734bfed54520](https://github.com/mucholocco86/laborat-rio_renpy/commit/cc3ce013ba6fe869642fdb62c78d734bfed54520).
- Fonte convertida: `classes/vars.rpy`, `StoreMonitorClass.handleVarChange` e `Var.setValue`, blob SHA `57482937e14f215dac0ecb22a62da8ad160cba58`; tela real `screens/vars.rpy`, `URM_var_changed`, blob SHA `7959b2c0e6249df0edbb9ebe683481d46e4537e1`.

- **CONFIRMADO NA FONTE URM CONVERTIDA:** `handleVarChange` dá precedência a frozen sobre monitor; `Var.setValue` remove e reaplica temporariamente freeze.
- **OBSERVADO EM RUNTIME (fixture reduzida):** ação Revert reduziu valor frozen de 20 para 10 e preservou a flag; entrega explícita do delta ao handler o restaurou para 20 sem notificação.
- **PENDENTE:** se e quando a callback real encontra o delta gerado pela ação Revert, e o efeito combinado dessa callback com rollback/save-load na execução integral.
## Atualização runtime — callback natural após “Revert” (2026-10-21)

Foi acrescentado um probe que aciona a ação reduzida de Revert por botão de screen e deixa `renpy.config.python_callbacks` processar o fluxo normalmente. A callback da fixture lê `StoreDict.get_changes(False)` e chama `StoreMonitor.handleVarChange`, como no circuito convertido. Os casos distinguem rollback desabilitado no contexto de teste e rollback de gameplay habilitado.

| Modo | Delta visto pela callback | Resultado de `handleVarChange` | Valor final do probe |
|---|---|---|---|
| Sem rollback | sim: `20→10` | um registro de monitor/notificação, com `prevVal=20` e `newVal=10` | `10` |
| Com rollback | não | nenhum registro | `10` antes do rollback; `20` após voltar ao checkpoint |

Os dois casos passaram no workflow [39562762194](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39562762194). Nos logs do primeiro, a callback recebeu o delta 20→10 e produziu um registro; no segundo, os campos de delta ficaram vazios e a lista de registros permaneceu vazia, enquanto o rollback nativo restaurou o valor do checkpoint.

**OBSERVADO EM RUNTIME (fixture reduzida, SDK 7.4.11):** sem rollback habilitado, o Revert pela screen alterou o store; a callback posterior detectou essa atribuição e a rota monitorada registrou uma nova mudança. Com rollback habilitado, a callback não recebeu o delta neste percurso; o valor continuou reatribuído até o rollback, que restaurou 20. Isso reforça que notificação do StoreMonitor e reversibilidade do store são canais distintos.

### Interpretação limitada

Na fonte convertida, `handleVarChange` para variável monitorada cria uma notificação cuja ação abre `URM_var_changed` com o valor antigo. Portanto, o registro `20→10` reproduzido sem rollback é coerente com a possibilidade de o próprio Revert gerar uma notificação subsequente sobre a reversão do valor. O teste usou um coletor reduzido, não a tela nem a classe `NotificationsClass` real; não demonstra a aparência, recursão visual ou tempo de vida dessa notificação no URM integral.

A diferença entre callback com/sem rollback é compatível com os probes anteriores sobre `get_changes(False)` e checkpoints, mas não identifica por si só toda a causa interna do delta ausente. O SDK fecha mudanças no `RollbackLog` e pode ciclar o StoreDict em outros pontos; instrumentação direta desses registros durante este percurso ficou fora deste probe.

### Fontes, commits e pendências

- Fixture: commit [548cfecca85d01334ff9c7bdce8d3633cf122b84](https://github.com/mucholocco86/laborat-rio_renpy/commit/548cfecca85d01334ff9c7bdce8d3633cf122b84).
- Workflow: commit [58c79fc5b1e44e546e31c12d011d986512c96480](https://github.com/mucholocco86/laborat-rio_renpy/commit/58c79fc5b1e44e546e31c12d011d986512c96480).
- Fontes URM convertidas: `classes/vars.rpy` (`_m1_vars__pythonCallback`, `handleVarChange`, `Var.setValue`) e `screens/vars.rpy` (`URM_var_changed`), SHAs listados acima.
- **PENDENTE:** verificar a lista/tela real de notificações ao Revert ser monitorado; a ciclagem do delta em `get_changes(True)` foi localizada na fixture reduzida, conforme documento [32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md); testar variável simultaneamente frozen/monitored nesse percurso natural e reproduzir com o loader e pacote integral.
### Fechamento da pendência de ciclagem do delta

O trace do run [39663561168](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39663561168) localizou a captura do delta no caminho `RollbackLog.complete(True) → StoreDict.get_changes(True)`, chamado por `RollbackLog.begin()` antes do próximo nó. A callback posterior não vê a mudança porque `StoreDict.old` já avançou. Veja [32 — Ciclagem do StoreDict antes da callback após Revert](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md). Isso fecha a localização do mecanismo na fixture/SDK 7.4.11, mas a integração runtime do StoreMonitor e das notificações do URM integral continua pendente.

### Continuação de 2026-10-21 — freeze + monitor + callback natural após Revert

O run [39664217382](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39664217382) passou os dois novos casos da fixture reduzida. Sem rollback, callback recebeu `20→10`; o handler frozen escreveu `20` durante a callback e não notificou, mas a leitura após a interação foi novamente `10`. Com rollback, callback não recebeu o delta e o rollback restaurou `20`. A razão para a diferença temporal no caso sem rollback segue pendente. A fixture usa metadados de freeze/monitor simplificados, não os stores `.urm` integrais. Ver detalhes e limites no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Correção do teste freeze + monitor — snapshot anterior à callback

O run [39665745692](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39665745692) separou o snapshot `10` capturado pelo próprio nó Python da leitura feita no nó seguinte: como `Python.execute()` chama callbacks somente depois de executar o bytecode, o handler de freeze restaura `20` após a primeira leitura. Portanto, retiro a interpretação anterior de que `10` voltava depois da interação; ela confundia o snapshot pré-callback com o estado subsequente. Sem rollback, o handler mantém `20` e não notifica; com rollback, callback não recebe delta e o rollback retorna a `20`. Ver detalhes no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Atualização de 2026-10-21 — pedido de checkpoint da callback

A fonte convertida mostra que `_m1_vars__pythonCallback` define `context.force_checkpoint=True` antes de consultar o delta, inclusive em callback sem mudança utilizável. No SDK 7.4.11, o próximo nó transfere esse pedido para `RollbackLog.force_checkpoint` quando rollback está ativo; `RollbackLog.complete()` o consome como `checkpoint(hard=False)`. O trace reduzido observou a transferência, mas ainda não contou os checkpoints soft efetivamente materializados nem executou o URM pelo loader integral. Detalhes no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Trace de 2026-10-23 — checkpoints soft

O run [39893930678](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39893930678) confirmou no harness que chamadas `checkpoint(hard=False)` marcam o registro corrente quando ainda não era checkpoint e não elevam `hard_checkpoint`; chamadas repetidas em registro já marcado não criam outra marca. Foram observadas 9 e 10 transições efetivas ao longo dos dois testcases, incluindo setup e rollback. Isso não mede checkpoints por ação nem valida o URM carregado integralmente. Ver [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Fonte 7.4.11 — checkpoint soft e rollback

No rollback normal, `RollbackLog.rollback()` reduz a contagem solicitada somente ao atravessar `hard_checkpoint`; checkpoint soft não incrementa `rollback_limit`. O caminho greedy pode atravessar registros soft depois de encontrar o hard checkpoint alvo. O código trata `on_load=True` de modo diferente e também conta checkpoints soft. O probe runtime [39894546076](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39894546076) falhou por configuração do harness e não valida essa regra; seu testcase foi removido. Veja fonte e classificação no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).