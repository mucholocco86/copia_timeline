# 31 — Ciclo de vida das notificações do URM e rollback

**Data:** 2026-10-18  
**Escopo:** revisão estática da lista interna de notificações e confronto com o rollback de objetos do Ren'Py 7.4.11.  
**Runtime:** nenhuma execução da NotificationClass/tela real nesta etapa. Os probes dos documentos 29–30 usam coletores reduzidos.

## Achado principal

O coletor de avisos usado nos probes anteriores não reproduz a estrutura de armazenamento do URM. O harness guardava notificações numa lista de store criada por `default`; essa lista é uma raiz direta do rollback. No URM convertido, os avisos ficam em `NotificationsClass.notifications`, atributo de uma instância criada em init.

A diferença impede concluir, a partir do coletor que foi limpo no rollback, que a lista real do URM também é revertida.

## Fluxo identificado na fonte URM convertida

1. `classes/notifications.rpy`, `NotificationsClass.__init__` inicializa `self.notifications = []`.
2. `classes/main.rpy`, no bloco `init 52 python in x52URM`, instancia `Notifications = NotificationsClass()`.
3. `NotificationsClass.add` cria um `Notification`, acrescenta-o à lista e chama `renpy.restart_interaction()`. Se `Settings.notificationTimeout` estiver ativo, uma thread aguarda e tenta remover o aviso.
4. `remove` remove o aviso e reinicia a interação; `clear` substitui a lista por uma lista vazia.
5. `screens/main.rpy` inclui `use URM_notifications` dentro de `URM_overlay`. A definição dessa screen não foi localizada ainda; não se conclui aqui sua política de renderização, descarte ou reconstrução.

**CONFIRMADO NA FONTE URM CONVERTIDA:** os pontos 1–5 correspondem ao código convertido. A conversão não é, por si só, prova de identidade perfeita com o pacote original.

## Confronto com o SDK 7.4.11

### Literais de lista

Em `renpy/python.py`, `py_compile` aplica `wrap_node.visit(tree)`. O transformador `WrapNode.visit_List` substitui literais de lista em contexto de leitura por chamadas a `__renpy__list__`; `minstore.py` liga esse nome a `RevertableList`.

Assim, o literal `[]` da classe compilada como código Ren'Py é convertido para a estrutura revertível do SDK. `RevertableList.append` usa o wrapper de mutação, que registra o estado limpo no log quando a lista é alterada. A compilação no escopo `init python in x52URM` e o tipo efetivo em runtime devem ser confirmados na fixture antes de afirmar o resultado para o pacote carregado integralmente.

### Alcance do rollback por grafo de objetos

`renpy.python.reached` interrompe a travessia quando encontra uma instância de `NoRollback`: marca o objeto como não participante e não percorre seus atributos nesse caminho. O código do SDK ressalva que objetos alcançáveis por outra raiz independente ainda podem participar.

Esse mecanismo torna a classe-base de `NotificationsClass` decisiva. A fonte convertida declara `NotificationsClass(x52NonPicklable)` e `Notification(x52NonPicklable)`, mas a definição de `x52NonPicklable` não foi localizada nas fontes atualmente examinadas. O nome não basta para equipará-la a `renpy.python.NoRollback`.

### Implicação condicional

- **CONFIRMADO NO SDK 7.4.11:** quando um objeto alcançado é `NoRollback`, a travessia não visita seus atributos por esse caminho.
- **PENDENTE:** se `x52NonPicklable` herda de `NoRollback`, a lista interna e seus avisos podem ficar fora do rollback por intermédio de `Notifications`, salvo se houver outra raiz que os alcance.
- **PENDENTE:** se a classe-base não é `NoRollback`, a lista revertível pode ser capturada e restaurada segundo o alcance e as mutações registradas no ciclo correspondente.
- Não há evidência nesta etapa para afirmar se avisos persistem ou desaparecem após rollback, nem se o timeout em thread afeta esse resultado.

## Por que o coletor de teste não responde sobre o URM

No run [39148594202](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148594202), o harness registrou o aviso imediato de `SetVariable` e o rollback restaurou a variável. O próprio coletor, por ser uma lista reversível na store da fixture, foi restaurado ao estado anterior. Isso valida o coletor do teste, mas não o atributo aninhado da NotificationClass do URM.

Essa limitação se aplica também ao teste reduzido do documento [29](29_NOTIFICACOES_VARIAVEIS_MONITORADAS_RUNTIME.md) e ao documento [30](30_MONITOR_ROLLBACK_NOTIFICACAO_URM.md).

## Classificação

- **CONFIRMADO NA FONTE URM CONVERTIDA:** Notifications é instanciada durante init; avisos são adicionados/removidos em um atributo de lista; o overlay inclui a screen de notificações.
- **CONFIRMADO NO SDK 7.4.11:** literais de lista compilados pelo pipeline Ren'Py são transformados em `RevertableList`; mutações de lista podem entrar no log de objetos; a travessia para em `NoRollback`.
- **OBSERVADO EM RUNTIME (fixture reduzida):** o coletor de avisos raiz do probe foi revertido junto com a variável no rollback.
- **HIPÓTESE:** o armazenamento real de avisos pode ter ciclo de vida diferente por estar aninhado em `Notifications` e depender da base `x52NonPicklable`.
- **PENDENTE:** definição de `x52NonPicklable`, implementação da screen `URM_notifications`, tipo real da lista e execução add → rollback → screen/timeout.

## Fontes consultadas

| Fonte | Símbolos / intervalo | Identificação |
|---|---|---|
| URM convertido `classes/notifications.rpy` | linhas 1–39; `NotificationsClass`, `Notification` | blob SHA `3283ec4b1615967a71ad21cc34670bf8158ab96d` |
| URM convertido `classes/main.rpy` | linhas 10–42; instanciação `Notifications` em init 52 | blob SHA `14f93406d2946eaed664ed72c1d47063984ce24f` |
| URM convertido `screens/main.rpy` | linhas 20–53; `URM_overlay` usa `URM_notifications` | blob SHA `ceb5dc63b3691a4b6244345e1c5a3e3b9d149291` |
| Ren'Py 7.4.11 `renpy/python.py` | linhas 354–405 (`NoRollback/reached`), 453–506 (`WrapNode`), 723–835 (`py_compile`), 953–1048 (`RevertableList`) | blob SHA `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| Ren'Py 7.4.11 `renpy/minstore.py` | `__renpy__list__ = RevertableList` | blob SHA `5dd44affc52aeb10a9c28433baee0b9948d3f759` |

## Próximos passos

1. Localizar a definição de `x52NonPicklable` no loader/dependências do URM e verificar sua relação efetiva com `NoRollback`.
2. Localizar a declaração de `URM_notifications` e suas ações de remoção/fechamento.
3. Fazer fixture isolada que use a mesma classe-base confirmada e o pipeline Ren'Py; observar type/list identity e add → checkpoint → rollback → renderização.
4. Separar os resultados de rollback do estado de jogo dos efeitos visuais/temporais da notificação e de seu comportamento em save/load.
5. Só então revisar se o resultado dos probes 29–30 pode ser refinado para o StoreMonitor integral.


## Continuação — definição da base e screen localizadas (2026-10-18)

A revisão da árvore completa localizou os dois itens que faltavam:

- `framework/modules/01utils.rpy`, linhas 10–21, define `x52NonPicklable(python_object)`. Em `renpy/minstore.py`, `python_object = _object = object` é guardado antes de substituir `object` por `RevertableObject`. Portanto, a base do URM é o objeto Python comum; ela **não** é `renpy.python.NoRollback`.
- A classe customiza `__getstate__`, `__setstate__`, `__getnewargs__` e iteração para o protocolo de serialização. Isso não impede a inspeção de atributos pelo algoritmo de alcance: em `renpy/python.py`, `reached` examina `vars(obj).values()` antes de tentar iterar, e captura exceções da tentativa de iteração.
- `screens/watchpanel.rpy`, linhas 260–353, contém `URM_notifications`. A screen percorre `x52URM.Notifications.notifications`, cria um botão para cada aviso (ação `notif`) e oferece `Dismiss all` por `Notifications.clear`. `screens/main.rpy` inclui essa screen no overlay.

**CONFIRMADO NA FONTE URM CONVERTIDA + SDK 7.4.11:** a lista de notificações é alcançável a partir do objeto `Notifications` e a classe-base não interrompe essa travessia como `NoRollback`. O SDK transforma o literal de lista da classe Ren'Py em `RevertableList`; `append` registra mutação. A previsão estática é, portanto, que uma adição rastreável possa ser desfeita pelo rollback.

**Ainda não confirmado em runtime:** a fixture abaixo testa o mesmo formato de grafo e a base equivalente no pipeline do SDK. Ela não importa o pacote URM inteiro nem a própria screen. Até o resultado do workflow, a previsão não deve ser descrita como comportamento observado do URM.

### Nova fixture isolada

Foi acrescentado o testcase `urm_x52_nonpicklable_notification_list_rollback` à fixture e um passo correspondente ao workflow. Ele usa uma classe-base com os mesmos métodos de `x52NonPicklable`, cria a lista por literal em bloco `init python`, acrescenta um objeto de notificação depois de checkpoint e solicita rollback. As asserções verificam o tipo `RevertableList`, a relação negativa com `NoRollback` e a lista vazia após retornar ao checkpoint.

A execução foi disparada pelo push do commit `021a78ffaea993c4f647daf5941e4fc44a5592d8`; **o resultado deve ser registrado após a conclusão do run**. Esta fixture mede semântica do SDK com classe reduzida, não integração integral do URM.

### Referências adicionadas

| Fonte | Símbolos / intervalo | Blob SHA |
|---|---|---|
| URM convertido `framework/modules/01utils.rpy` | linhas 10–21; `x52NonPicklable` | `e558a2d5a5137608e542238a1d81fd65e6db349d` |
| URM convertido `screens/watchpanel.rpy` | linhas 260–353; screen `URM_notifications` e lista de avisos | `8cc83f00838ed409183e85e4ebdb37ddf4433823` |
| URM convertido `framework/bootstrap.rpy` | mapa de módulos; `main` depende de `modules/01utils.x52rpy` | `9d72267c2d86c68aa9dac1fee94652c891a611fe` |
| Fixture runtime | testcase `urm_x52_nonpicklable_notification_list_rollback` | commit `196e17e0cd474620eb21a75aa1237a45a68c9c13` |
| Workflow | passo “Run x52 notification object rollback probe” | commit `021a78ffaea993c4f647daf5941e4fc44a5592d8` |


### Revisão após o primeiro runtime probe — raízes do log

O primeiro probe [39156073470](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156073470) terminou **FAILURE** porque a asserção esperava lista vazia e a fixture ficou presa procurando a interação textual errada. Antes da falha, o runtime imprimiu:

```text
X52_NOTIFICATION_PRE ProbeNotificationsClass RevertableList 0 False
X52_NOTIFICATION_AFTER_ADD 1 Variable changed
X52_NOTIFICATION_AFTER_ROLLBACK RevertableList 1
```

O marcador após a chamada de rollback indica que a execução chegou à etapa de verificação, mas o testcase não concluiu corretamente. O valor 1 é evidência intermediária; não é, isoladamente, uma prova integral do URM.

A revisão do SDK revelou uma condição que faltava ao raciocínio anterior:

- `RollbackLog.get_roots()` cria raízes a partir de `StoreDict.ever_been_changed`, ou seja, variáveis marcadas como alteradas desde o fim da fase init.
- `RollbackLog.complete()` registra objetos mutados, mas `purge_unreachable()` remove registros de objetos não alcançáveis a partir das raízes e do contexto.
- A instância `Notifications` do URM é atribuída durante `init 52`. A lista pode ser `RevertableList` e registrar o append, mas isso **não basta**: se o objeto dono não for alcançado por uma raiz elegível, o snapshot da lista pode ser descartado.
- Uma referência adicional a `Notifications` guardada numa variável de store alterada em runtime pode tornar o grafo alcançável e mudar o resultado do mesmo append.

Isso concilia a implementação de `x52NonPicklable` com o probe: a classe não interrompe a travessia como `NoRollback`, mas a raiz inicial ainda pode estar ausente de `get_roots()`. A screen em execução pode adicionar caminhos de alcance por displayables/actions; esse caminho ainda precisa de teste e não é inferido só por sua declaração estática.

**Classificação atual:** confirmado no SDK que mutações de objetos são filtradas por alcance; observado em runtime reduzido que o probe sem uma raiz de store alterada manteve a lista em 1 após a tentativa de rollback; hipótese forte que o singleton de init isolado seja descartado do log quando não houver outro caminho alcançável; pendente comparar a raiz init-only com uma raiz adicionada/alterada em runtime e com a screen ativa.

A fixture e o workflow foram ampliados para duas comparações controladas: (a) singleton init-only; (b) a mesma instância também referenciada por variável raiz alterada em runtime antes do checkpoint. O segundo run deve ser consultado antes de concluir a previsão.


### Comparação runtime com checagens explícitas — run 39156621298

O run [39156621298](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156621298) terminou **SUCCESS**. As duas comparações usaram exceções explícitas em vez de depender de `assert` no código Python da fixture.

**Singleton criado durante init, sem variável raiz alterada:**

```text
X52_NOTIFICATION_PRE ProbeNotificationsClass RevertableList 0 False
X52_NOTIFICATION_AFTER_ADD 1 Variable changed
X52_NOTIFICATION_AFTER_ROLLBACK RevertableList 1
```

O probe terminou com código 0 exigindo que a lista continuasse com uma entrada. Isso confirma no cenário reduzido que a mutação da lista interna do objeto init-only não foi restaurada quando não havia outra raiz considerada.

**A mesma instância referenciada por variável raiz alterada antes do checkpoint:**

```text
X52_NOTIFICATION_ROOTED_AFTER_ADD 1
X52_NOTIFICATION_ROOTED_AFTER_ROLLBACK RevertableList 0 False
```

O probe terminou com código 0 exigindo lista vazia e variável raiz de volta a `None`. A lista foi revertida; a referência temporária também voltou ao valor anterior.

**CONFIRMADO EM RUNTIME (fixture SDK reduzida):** o destino da mutação de uma lista revertível depende de o grafo do objeto ser alcançável pelas raízes do rollback no cenário testado. Isso corresponde ao código do SDK em `RollbackLog.get_roots()` (linhas 1757–1777) e `purge_unreachable()` (1779–1797). O run não carregou URM e não tinha screen ativa; logo, ainda não responde se os displayables/actions da `URM_notifications` real mantêm o singleton alcançável.

O probe final, [39156073470](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156073470), falhou por expectativa incorreta e interação do teste. O run [39156311306](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156311306) também falhou porque o diálogo de verificação repetiu o fluxo antes da asserção. Ambos foram substituídos pela fixture com saída direta no label de verificação e checagens explícitas. O run [39156468364](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156468364) passou, mas usava asserts Python que não eram uma garantia suficiente; seus valores de log coincidiram, e a conclusão é apoiada pelo run 39156621298.

### Screen ativa: comparação concluída

A fixture inclui `urm_x52_notification_overlay_probe`, com um `textbutton` cuja action é o objeto Notification. O run [39156808878](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156808878) concluiu **SUCCESS**. Os marcadores e a interpretação estão registrados na seção final deste documento.


### Screen ativa como raiz de alcance — run 39156808878

O run [39156808878](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156808878) terminou **SUCCESS**, incluindo o testcase `urm_x52_displayed_notification_list_rollback`. A fixture exibiu um screen com o mesmo padrão estrutural importante da screen URM: iteração pela lista e botão com `action notif`.

```text
X52_NOTIFICATION_SCREEN_BEFORE_ROLLBACK 1 True
X52_NOTIFICATION_SCREEN_AFTER_ROLLBACK 0 False
```

As verificações explícitas exigiram a lista vazia após rollback. Portanto, o displayable visível que contém a action alcançou o objeto de notificação e sua lista no cenário reduzido; ao voltar ao checkpoint, a lista foi revertida e a screen posterior foi retirada/restaurada conforme o estado do contexto.

### Síntese para o URM

- **CONFIRMADO NA FONTE URM CONVERTIDA:** `Notifications.add` acrescenta Notification à lista; `Notification` guarda referência ao dono `NotificationsClass`; `URM_notifications` percorre essa lista e usa cada objeto como action; `URM_overlay` inclui a screen; `afterLoad` mostra `URM_overlay`.
- **CONFIRMADO NO SDK 7.4.11:** `show_screen` insere `ScreenDisplayable` em `Context.scene_lists`; a purga de objetos do rollback percorre os displayables da scene list. A action do botão é, portanto, um possível caminho de alcance para Notification → NotificationsClass → lista.
- **OBSERVADO EM RUNTIME (fixture reduzida):** sem screen/action ou raiz de store alterada, a lista do singleton init-only permaneceu com um item; com raiz de store alterada ou com screen visível que carrega `action notif`, a lista retornou ao estado vazio no rollback.
- **INFERÊNCIA FORTE, ainda não integração runtime URM:** quando a overlay real já está visível e a notificação foi renderizada como botão, o caminho de alcance da action deve permitir que o rollback desfaça a inclusão. A estrutura fonte da screen real coincide no aspecto relevante, mas ainda falta executar o pacote URM completo.
- **PENDENTE:** testar notificação adicionada e rollback antes da screen concluir um novo render; testar timeout/thread e `clear()`; testar save/load da lista; carregar URM real para validar a hipótese ponta a ponta.

O erro anterior de esperar rollback da lista init-only sem uma raiz ativa estava no modelo inicial, não no SDK. Os runs [39156073470](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156073470) e [39156311306](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156311306) foram tentativas de fixture com expectativa/fluxo de interação incorretos; as conclusões agora apoiam-se nas comparações controladas dos runs [39156621298](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156621298) e [39156808878](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156808878).

### Novo alvo: `clear()` substitui o atributo (2026-10-18)

A fonte de `classes/notifications.rpy` distingue três operações:

- `add()` chama `self.notifications.append(notif)`;
- `remove()` chama `self.notifications.remove(notif)`;
- `clear()` faz `self.notifications = []`.

A diferença interessa porque o dono `NotificationsClass` herda de `x52NonPicklable`, que por sua vez herda de `python_object` (o `object` nativo preservado por `renpy/minstore.py)), e não de `RevertableObject`. Já os conteúdos são listas revertíveis: mutações como append/remove passam pelo wrapper `mutator`, que guarda um estado limpo no rollback log. Uma substituição de atributo em objeto Python comum não é automaticamente a mesma operação que uma mutação da `RevertableList`.

- **CONFIRMADO NA FONTE URM CONVERTIDA:** `clear()` substitui a referência da lista; `remove()` altera a lista atual.
- **CONFIRMADO NO SDK 7.4.11:** mutadores de `RevertableList` registram snapshot do próprio objeto. O SDK salva a classe nativa `object` como `python_object` antes de mapear `object` para `RevertableObject` no ambiente Ren'Py.
- **HIPÓTESE:** `clear()` pode não ser revertido como `remove()` quando o dono é a instância URM baseada no objeto Python comum. A screen pode restaurar um displayable antigo no contexto, mas isso não restaura necessariamente o atributo `notifications` do dono.
- **PENDENTE DE RUNTIME:** confirmar essa diferença com fixture reduzida e depois com o URM completo.

Foi acrescentado o testcase `urm_x52_notification_clear_rollback` à fixture e o passo “Run x52 notification clear rollback probe” ao workflow. O probe mantém uma screen com action de notificação visível, cria checkpoint, substitui a lista como o método `clear()` faz e retorna ao checkpoint. Commit do passo do workflow: [7cb6f6c5b0e20a9cb0198b3acbfd7dfb3b19a103](https://github.com/mucholocco86/laborat-rio_renpy/commit/7cb6f6c5b0e20a9cb0198b3acbfd7dfb3b19a103). **Resultado runtime ainda pendente; não tratar a previsão acima como observação.**

Para separar os dois mecanismos com condições equivalentes, foi adicionado também `urm_x52_notification_remove_rollback`: começa com uma notificação já alcançável pela screen, cria checkpoint, chama `RevertableList.remove()` no objeto atual e volta ao checkpoint. A expectativa testável é a lista retornar a um item, em contraste com a previsão de `clear()` permanecer vazia. Ambos os probes estão no workflow atualizado; o run de push não está exposto pelo conector disponível, então **os dois resultados seguem pendentes até que os logs do Actions sejam consultados**. A última alteração do workflow é o commit [537a46dcbc98ae76af80464efc7ae8582aa62eaa](https://github.com/mucholocco86/laborat-rio_renpy/commit/537a46dcbc98ae76af80464efc7ae8582aa62eaa), e a fixture foi atualizada no commit [37deb35335fec1fb140ab6b26e565ac7bdd6ab3e](https://github.com/mucholocco86/laborat-rio_renpy/commit/37deb35335fec1fb140ab6b26e565ac7bdd6ab3e).

Fontes adicionais consultadas:

| Fonte | Símbolos | Identificação |
|---|---|---|
| URM convertido `classes/notifications.rpy` | `NotificationsClass.add/remove/clear`, linhas 1–39 | blob SHA `3283ec4b1615967a71ad21cc34670bf8158ab96d5` |
| Ren'Py 7.4.11 `renpy/minstore.py` | aliases `python_object = _object = object`; substituição `object = RevertableObject` | blob SHA `5dd44affc52aeb10a9c28433baee0b9948d3f759` |
| Ren'Py 7.4.11 `renpy/python.py` | `mutator`, `RevertableList` | blob SHA `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| Fixture | testcase `urm_x52_notification_clear_rollback` | commit `1f3e253e01c2d713cf3ed72999c0dcfce347c6a1` |
| Workflow | passo de clear rollback | commit `7cb6f6c5b0e20a9cb0198b3acbfd7dfb3b19a103` |


### Timeout em thread e mutação da lista (2026-10-18)

A fonte convertida mostra que, quando `Settings.notificationTimeout` está ativo, `NotificationsClass.add` cria uma função que espera com `time.sleep` e então executa `self.notifications.remove(notif)`; essa função é enviada a `renpy.invoke_in_thread`.

No SDK 7.4.11, `invoke_in_thread` inicia uma thread daemon e reinicia a interação quando ela termina. A documentação da função delimita o que pode ser feito nessa thread: escrita de variáveis do store e `renpy.queue_event` são permitidas; a maior parte das outras APIs deve ficar na thread principal. A remoção não é uma simples atribuição a variável do store: `RevertableList.remove` passa por `mutator`, que acessa `renpy.game.log.mutated`, guarda o estado limpo e altera a lista.

Há um detalhe no rollback log: `RollbackLog.complete` percorre `self.mutated` para comprimir snapshots e tenta novamente até quatro vezes se ocorrer `RuntimeError` por mudança concorrente desse dicionário. Isso demonstra que o SDK reconhece concorrência nessa estrutura; **não prova** que toda mutação revertível em thread seja suportada, segura ou determinística. Também não prova que a remoção por timeout terá o mesmo ponto de rollback que uma remoção executada pela interação principal.

- **CONFIRMADO NA FONTE URM CONVERTIDA:** timeout chama `self.notifications.remove(notif)` dentro da função passada a `renpy.invoke_in_thread`.
- **CONFIRMADO NO SDK 7.4.11:** `invoke_in_thread` usa thread daemon e documenta limites de uso da API; `RevertableList` usa mutator ligado ao log; `RollbackLog.complete` repete a coleta se o mapa de mutações mudar durante a iteração.
- **HIPÓTESE / RISCO A VALIDAR:** timeout e rollback podem disputar o registro de mutação ou mudar o instante em que a lista é capturada. O retry nativo reduz um caso específico de erro de iteração, sem garantir o resultado semântico.
- **PENDENTE:** runtime com timeout real, rollback imediatamente antes/depois da remoção, encerramento do jogo durante a espera, e comparação entre timeout e remoção por botão.

Nenhum teste de thread foi adicionado nesta etapa; a conclusão acima é somente estática. Os probes pareados de `clear()` e `remove()` continuam sem logs runtime verificados, pois o conector não expõe runs de push.

| Fonte | Símbolos / intervalo | Blob SHA |
|---|---|---|
| URM convertido `classes/notifications.rpy` | `NotificationsClass.add`, linhas 9–17 | `3283ec4b1615967a71ad21cc34670bf8158ab96d5` |
| SDK 7.4.11 `renpy/exports.py` | `invoke_in_thread`, linhas 3698–3728 | `781b35b31522dafc6a24e7c3212d206c7bd6dfa5` |
| SDK 7.4.11 `renpy/python.py` | `mutator`, linhas 862–877; `RollbackLog.complete`, linhas 1707–1743 | `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |


### Probe de timeout em thread preparado (2026-10-18)

Foi adicionada a testcase `urm_x52_notification_timeout_rollback`. Ela exibe a notificação numa screen, registra checkpoint, inicia `renpy.invoke_in_thread`; a função worker espera brevemente, executa `ProbeNotifications.notifications.remove(notification)` e marca uma variável de conclusão. A execução principal aguarda o sinal e solicita rollback ao checkpoint anterior. A expectativa é que a mutação da lista seja desfeita e que o item retorne.

Esse teste mede se o SDK reduzido registra e restaura uma mutação `RevertableList` feita nessa thread. Não mede segurança geral de chamadas Ren'Py em thread, timeout longo, corrida na borda do checkpoint, encerramento durante a espera nem o pacote URM integral.

- **PENDENTE:** nenhum log runtime verificado até o momento.
- **Evidência estática preservada:** `invoke_in_thread` permite poucas operações na thread; `mutator` escreve em `renpy.game.log.mutated`; `RollbackLog.complete` repete a iteração do mapa em certos `RuntimeError`.
- **Fixture:** testcase `urm_x52_notification_timeout_rollback`, commit [b4de1e4c476668f27da51775c48536f82fe16f91](https://github.com/mucholocco86/laborat-rio_renpy/commit/b4de1e4c476668f27da51775c48536f82fe16f91).
- **Workflow:** passo “Run x52 notification timeout thread rollback probe”, commit [4ffdae65e48c42dad9c314c62fd1c68b78e78c63](https://github.com/mucholocco86/laborat-rio_renpy/commit/4ffdae65e48c42dad9c314c62fd1c68b78e78c63).

### Save/load nativo: interação com o singleton (revisão estática)

O fluxo do SDK adiciona uma hipótese importante para o ciclo de vida entre saves:

1. `renpy.loadsave.save` chama `RollbackLog.freeze`, depois serializa `(roots, log)`.
2. `freeze` chama `complete(False)`, obtém `get_roots()` e remove snapshots inalcançáveis.
3. `get_roots()` inclui variáveis de StoreDict que entraram em `ever_been_changed` desde init; alteração interna de uma lista aninhada não equivale, por si, a reatribuir a variável do store.
4. `renpy/main.py` chama `make_clean_stores()` depois de executar todo o init. Como o URM instancia `x52URM.Notifications` em init, esse backup limpo contém a referência ao singleton.
5. `clean_stores()`, chamado durante `RollbackLog.unfreeze` no load, restaura o backup dos stores. `StoreBackup` copia cada dicionário de store de forma rasa (`dict(d)`), mantendo a referência ao mesmo objeto; isso não copia nem restaura por si só a lista aninhada. O SDK também comenta que `store_dicts` e `store_modules` não são reinicializados durante reload. Essas evidências sustentam continuidade do objeto na mesma sessão, mas não resolvem quais snapshots do RollbackLog carregado restauram a lista. A classe-base define `__getstate__` como dicionário vazio e `__setstate__` sem restauração de atributos; se o objeto for efetivamente pickled, seus atributos não são reconstruídos por esses métodos.

Isso permite duas rotas possíveis, ainda não distinguidas em runtime: (a) a instância init-only permanece pela referência rasa do store durante o load na mesma sessão, mantendo seu estado de lista corrente; (b) referências alcançáveis pelo contexto/log entram no arquivo de save, onde a serialização customizada da classe pode omitir atributos. A screen também participa: `ScreenDisplayable` exclui `child`/widgets da serialização e reconstrói a screen após carregar, então a action pode ser refeita a partir do estado corrente do singleton em vez de preservar a action serializada.

- **CONFIRMADO NO SDK 7.4.11:** save serializa roots + RollbackLog; roots são limitadas a variáveis marcadas como alteradas; StoreBackup é cópia rasa; ScreenDisplayable não salva os widgets e reconstrói sua árvore.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** o singleton é criado em init; `x52NonPicklable` descarta atributos em seu protocolo de estado.
- **HIPÓTESE:** o comportamento de notificações após carregar um save depende de quais snapshots do log/contexto continuam alcançáveis e do ponto em que a screen é reconstruída. A simples presença de `__getstate__` não demonstra que `Notifications` é serializada.
- **PENDENTE:** runtime comparando (1) aviso ainda ativo no momento de salvar, (2) timeout remove depois do save, (3) load do slot, (4) processo novo versus load na mesma sessão, e (5) save/load sem overlay visível.

| Fonte | Símbolos / intervalo | Blob SHA |
|---|---|---|
| SDK 7.4.11 `renpy/loadsave.py` | `save`, linhas 373–410; `load`, linha 762 em diante | `c8b831ebfd5487f11a1d4dde8c87cde7f7ed93e3` |
| SDK 7.4.11 `renpy/main.py` | `make_clean_stores()` após o init, linha 621 | `e72bd59109ee72e36f124424fcbdd4761aab60ae` |
| SDK 7.4.11 `renpy/python.py` | `store_dicts/store_modules`, linhas 205–207; `StoreBackup`, linha 260 em diante; `clean_stores`, linha 323; `RollbackLog.get_roots`, linhas 1757–1777; `freeze/unfreeze` | `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| SDK 7.4.11 `renpy/display/screen.py` | `ScreenDisplayable`, linhas 290–315+; `nosave` exclui widgets/filhos; `after_setstate` reconstrói | `cf7997b04c3b17a337809f58aa6591ccd58a15a7` |
| URM convertido `classes/main.rpy` | instanciação de `Notifications`, linha 38 | `14f93406d2946eaed664ed72c1d47063984ce24f` |
| URM convertido `framework/modules/01utils.rpy` | `x52NonPicklable.__getstate__/__setstate__`, linhas 10–21 | `e558a2d5a5137608e542238a1d81fd65e6db349d` |



### Revisão dos probes clear/remove: falha de configuração do harness (2026-10-19)

Os runs [39161531256](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39161531256), [39170207046](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39170207046) e [39177581946](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39177581946) falharam no mesmo passo: o probe de `clear()`. Os logs mostram que os passos anteriores passaram, inclusive o probe com screen visível. O passo de `remove()` e o de timeout ficaram *skipped* por causa da falha anterior.

O erro foi lançado durante `renpy.rollback(...)`, antes do label de verificação:

```text
Exception: Couldn't find a place to stop rolling back. Perhaps the script changed in an incompatible way?
```

Inspeção comparativa do fixture encontrou uma diferença de setup: os labels de `clear()` e `remove()` não definiam `renpy.game.context().rollback = True`. O probe anterior de screen ativa, que passou, habilitava rollback no contexto inicial. Assim, a falha não mede se a substituição do atributo ou a mutação `remove()` foi revertida; a conclusão sobre esses dois mecanismos permanece pendente.

A fixture foi corrigida no commit [8ee3804dadb2320f574ef6550f71f38ba10e9bac](https://github.com/mucholocco86/laborat-rio_renpy/commit/8ee3804dadb2320f574ef6550f71f38ba10e9bac): ambos os labels agora habilitam rollback antes de preparar a lista e checkpoint. Essa alteração corrige apenas o harness experimental. **Aguardar e inspecionar o run acionado por esse commit antes de classificar os resultados de clear/remove;** o timeout também depende da conclusão do fluxo para deixar de ser skipped.

- **OBSERVADO EM RUNTIME:** nos três runs acima, os probes prévios ao clear concluíram; o rollback explícito do probe de clear não encontrou local de parada; remove/timeout foram skipped.
- **CONFIRMADO NA INSPEÇÃO DO FIXTURE:** rollback estava habilitado no probe de screen e no timeout, mas ausente nos labels de clear/remove.
- **HIPÓTESE DE CAUSA:** a ausência dessa configuração causou a falta de local de parada. A correção está no commit indicado, mas requer novo run para validar.
- **PENDENTE:** resultado runtime válido de clear, remove e timeout thread após a correção.



### Clear, remove e timeout: probes runtime válidos — run 39205520906

Depois de habilitar rollback nos dois labels que não tinham essa configuração, o run [39205520906](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39205520906) concluiu **SUCCESS**. Todos os passos do workflow passaram, inclusive clear, remove e timeout em thread. Os logs registram:

```text
X52_NOTIFICATION_CLEAR_BEFORE 1 True
X52_NOTIFICATION_CLEAR_AFTER_ROLLBACK 0 True
X52_NOTIFICATION_REMOVE_BEFORE 1 True
X52_NOTIFICATION_REMOVE_AFTER_ROLLBACK 1 True
X52_NOTIFICATION_TIMEOUT_AFTER_ROLLBACK 1 False
```

Interpretação restrita ao fixture reduzido:

- **clear() — OBSERVADO EM RUNTIME:** a lista ficou vazia depois do rollback; o screen permaneceu ativo. Neste harness, a substituição owner.notifications = [] não restaurou o atributo anterior do dono. Isso é consistente com o dono sendo um objeto Python comum não revertível.
- **remove() — OBSERVADO EM RUNTIME:** a lista voltou a conter um elemento, embora a remoção tenha alterado a RevertableList no lugar. É consistente com o snapshot do mutador da lista sendo reaplicado.
- **Timeout em thread — OBSERVADO EM RUNTIME:** após o worker remover o item, o rollback restaurou a lista a um item; timeout_done voltou a False, o valor do checkpoint. O probe demonstra resultado neste agendamento controlado, sem demonstrar segurança geral para mutações concorrentes ou determinismo em outras corridas.

Os três casos usam a classe reduzida ProbeNotifications, com formato equivalente ao ponto investigado, e uma screen de fixture. Eles **não carregam a classe, o loader, a thread de timeout nem a screen do URM integralmente**. Portanto, são evidência de runtime do SDK 7.4.11 sob o harness, e suporte para as previsões do código convertido, não prova ponta a ponta do pacote URM.

A comparação também revela uma diferença funcional de interesse: com screen ativa, rollback até o checkpoint preserva a própria screen nos probes clear/remove, enquanto o estado da lista depende da forma da operação. Em clear, a tela continua aberta, mas sem notificação; em remove, o item reaparece. Logo, screen ativa não implica que toda operação no objeto seja revertida uniformemente: mutação da lista e reatribuição de atributo seguem caminhos distintos.

| Caso | Resultado runtime | Classificação | Limite |
|---|---|---|---|
| Atribuir lista vazia (clear) | lista permanece vazia; screen ativa | Observado em runtime (fixture reduzida) | não executou método URM integral |
| RevertableList.remove | elemento reaparece; screen ativa | Observado em runtime (fixture reduzida) | mesma limitação |
| remove por invoke_in_thread | elemento reaparece; flag worker retorna ao checkpoint | Observado em runtime (fixture reduzida) | um agendamento controlado; sem garantia de corrida |

O run anterior [39177581946](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39177581946) falhou antes da verificação porque os probes clear/remove não habilitavam rollback. A correção de fixture está no commit [8ee3804dadb2320f574ef6550f71f38ba10e9bac](https://github.com/mucholocco86/laborat-rio_renpy/commit/8ee3804dadb2320f574ef6550f71f38ba10e9bac). O run 39205520906, com todos os três passos concluídos, substitui esses resultados inválidos.

- **PENDENTE:** validar a diferença no pacote URM carregado integralmente; repetir timeout em múltiplos atrasos relativos ao checkpoint/rollback; testar add → clear → rollback com a screen real; estudar save/load.


### Probe de save/load em preparação (2026-10-19)

A inspeção do SDK especifica o que será medido no novo roundtrip:

- `RollbackLog.freeze` chama `complete(False)`, obtém roots via `get_roots()` e executa `purge_unreachable(roots)`. O método `get_roots()` inclui variáveis do store alteradas depois de init e roots dinâmicas de contexto; mutação interna de um objeto, isoladamente, não torna o nome do singleton root de store.
- `reached()` percorre `vars(obj).values()`, então um objeto alcançado por uma screen pode levar a travessia até `Notification → NotificationsClass → notifications`; `NoRollback` interromperia esse caminho, mas a base convertida do URM não é `NoRollback`.
- `StoreBackup` copia os dicionários de store com `dict(d)`, portanto é cópia rasa: referências a objetos init-only permanecem apontando para as instâncias existentes durante o load na mesma sessão.
- `RollbackLog.unfreeze` restaura stores limpos e aplica roots e snapshots carregados. O screen/displayable também pode ser reconstruído; o save não equivale a serializar diretamente a árvore visual inteira.

O fixture agora acrescenta `ProbeNotifications.clear()` (mesma semântica de atribuição da fonte convertida) e um testcase de roundtrip: mantém um aviso visível no momento do save, substitui a lista e adiciona outro aviso, carrega o slot e imprime tipo/labels da lista e presença da screen. O teste não afirma antecipadamente se o estado esperado é o do save, o pós-save ou ausência de atributos serializados.

- Fixture: commit [6587ae8bbd3199d29d6e19ab7882dc8261511d81](https://github.com/mucholocco86/laborat-rio_renpy/commit/6587ae8bbd3199d29d6e19ab7882dc8261511d81).
- Workflow: commit [1f6585e91e163b9d97ed9927d0e76c62b9e8c3c6](https://github.com/mucholocco86/laborat-rio_renpy/commit/1f6585e91e163b9d97ed9927d0e76c62b9e8c3c6).
- Run inicial do workflow: [39214386042](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214386042); falhou por loop no controle de reentrada do fixture, sem chegar ao estado pós-load.
- **PENDENTE:** verificar se o load conclui e ler `X52_NOTIFICATION_SAVE_AFTER_LOAD`; este probe cobre load na mesma sessão e uma screen com action, não novo processo nem o pacote URM completo.



#### Correção do fluxo de reentrada

O primeiro run de save/load imprimiu o estado antes do save e depois da mutação pós-save, mas falhou com `Exception: Possible infinite loop.` A execução retomava no statement após `renpy.save`, porém o fixture não checava a flag de reentrada nesse ponto; assim, repetia a mutação e o load continuamente. O log não contém o marcador pós-load e não permite inferir o estado salvo.

A fixture agora segue o padrão já usado pelos roundtrips de containers do mesmo arquivo: logo após `renpy.save`, verifica se a execução está retornando do load e salta à verificação, sem repetir alterações nem chamar load de novo. Correção no commit [ce79b20e3775f2d8fd442a1a043c4f631637148a](https://github.com/mucholocco86/laborat-rio_renpy/commit/ce79b20e3775f2d8fd442a1a043c4f631637148a). O run acionado por essa correção deve substituir o primeiro; até sua conclusão, save/load permanece **PENDENTE**.


O segundo run [39214615646](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214615646) também falhou com loop: a flag guardada em `renpy.test.testexecution` não sobreviveu ao load do save com o objeto customizado em teste, e o marker pós-load não foi alcançado. Isso é uma descoberta sobre o mecanismo do harness neste cenário, não sobre a notificação salva. Para evitar repetir o slot, a nova tentativa armazena a guarda em `renpy.session`, estado consultado pelo SDK durante `RollbackLog.unfreeze`; a fixture limpa essa chave antes de iniciar e verifica após o save. Correção no commit [7558d97d6966fa3b1d43679b4eaaef6ba2979499](https://github.com/mucholocco86/laborat-rio_renpy/commit/7558d97d6966fa3b1d43679b4eaaef6ba2979499). Resultado do run acionado por essa mudança ainda pendente.


### Save/load com reatribuição após o save — run 39214784786

A terceira execução do testcase de roundtrip, [run 39214784786](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214784786), terminou **SUCCESS** após trocar o marker do harness para `renpy.session` (fixture commit [7558d97d6966fa3b1d43679b4eaaef6ba2979499](https://github.com/mucholocco86/laborat-rio_renpy/commit/7558d97d6966fa3b1d43679b4eaaef6ba2979499)). O log registrou:

```text
X52_NOTIFICATION_SAVE_BEFORE ProbeNotificationsClass RevertableList [u'Saved notification']
X52_NOTIFICATION_SAVE_MUTATED_AFTER [u'Post-save notification']
X52_NOTIFICATION_SAVE_AFTER_LOAD ProbeNotificationsClass RevertableList [u'Post-save notification'] True
```

**OBSERVADO EM RUNTIME (fixture reduzida, load na mesma sessão):** após salvar com a notificação `Saved notification`, o teste chamou `clear()` (substituição de atributo), acrescentou `Post-save notification` e carregou o slot. Depois do load, o dono ainda expunha uma `RevertableList` contendo `Post-save notification`, e a screen estava ativa. Portanto, nesse caminho do fixture, o load não restaurou o atributo do objeto dono ao valor que existia no save.

**INFERÊNCIA sustentada pelo SDK, ainda não prova do objeto URM integral:** `StoreBackup` usa cópia rasa para os stores, e `clean_stores()` reaplica referências aos mesmos objetos init-only. Como `clear()` substitui `owner.notifications` em um objeto Python comum, essa alteração ao atributo pode permanecer na instância viva durante load na mesma sessão. A lista nova e o append posterior são estados pós-save; este resultado não demonstra que o save preserva os valores originais de qualquer save URM. A screen permaneceu ativa e, após reconstrução, leu a lista atual do owner.

Os runs [39214386042](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214386042) e [39214615646](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214615646) falharam somente por controle de reentrada do fixture e não produziram evidência pós-load. O run 39214784786 é o primeiro resultado válido desse probe.

- **PENDENTE:** comparar com `remove()` in-place sobre a lista existente; executar em processo novo; carregar o URM integralmente e conferir se objetos `Notification` e owner têm a mesma semântica de serialização em runtime.


### Probe pareado de save/load para remove in-place

O teste anterior altera o atributo com `clear()` após o save e observa que o load na mesma sessão manteve a nova lista. Para separar esse resultado da semântica de `RevertableList`, foi acrescentado um roundtrip pareado: salva a lista existente com `Saved notification`; após o save, remove esse objeto da mesma lista in-place e acrescenta `Post-save notification`; carrega o slot e reporta os labels e o tipo da lista.

- Fixture commit [05f7603ca0e4b6243cbc04dbb5b62071e043081c](https://github.com/mucholocco86/laborat-rio_renpy/commit/05f7603ca0e4b6243cbc04dbb5b62071e043081c).
- Workflow commit [937afcdf65a3e7cd05892ab973a0975c13e69329](https://github.com/mucholocco86/laborat-rio_renpy/commit/937afcdf65a3e7cd05892ab973a0975c13e69329).
- **PENDENTE:** run acionado pelo workflow update, incluindo os marcadores `X52_NOTIFICATION_REMOVE_SAVE_AFTER_LOAD`.


### Roundtrip pareado com remove in-place — run 39215118198

O run [39215118198](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39215118198) concluiu **SUCCESS** nos dois testes de save/load. O segundo caso registrou:

```text
X52_NOTIFICATION_REMOVE_SAVE_BEFORE [u'Saved notification']
X52_NOTIFICATION_REMOVE_SAVE_MUTATED_AFTER [u'Post-save notification']
X52_NOTIFICATION_REMOVE_SAVE_AFTER_LOAD ProbeNotificationsClass RevertableList [u'Post-save notification'] True
```

**OBSERVADO EM RUNTIME (fixture reduzida, mesma sessão):** tanto a reatribuição via `clear()` quanto a mutação in-place (`remove` e `add`) mantiveram `Post-save notification` depois do load. A lista era `RevertableList` e a screen permaneceu ativa. Assim, neste desenho, o load não restaurou a lista ao conteúdo registrado no momento do save, nem quando o objeto da lista permaneceu o mesmo.

**INFERÊNCIA limitada:** isso é compatível com o comportamento do `StoreBackup` raso e com o singleton de init ainda vivo durante load na mesma sessão; contudo, o resultado não isola toda a identidade dos objetos internos nem prova que a lista/screen do URM integral age igual. O teste faz o load do save criado naquele mesmo processo e mostra o estado de owner/lista reapós o retorno.

A comparação não mostrou diferença entre atribuir lista nova e mutar a atual no caso de load na mesma sessão. A diferença anterior entre `clear()` (não revertido) e `remove()` (revertido) permanece válida para rollback de gameplay, mas não se transfere automaticamente para load de save. O experimento seguinte precisa começar um processo Ren'Py novo e carregar o slot criado pelo processo anterior.

- **PENDENTE:** fresh-process load do mesmo slot; teste do URM integral; separar como snapshots de lista alcançáveis são serializados e reconstituídos.


### Probe entre processos separados em preparação

Como os dois roundtrips na mesma sessão mantiveram o estado pós-save, a fixture foi estendida para um teste com dois processos Ren'Py separados e o mesmo diretório de jogo descartável: o primeiro cria o slot com `Saved notification`, remove o elemento in-place, acrescenta `Post-save notification` e encerra; o segundo inicia com o singleton recém-criado por init, carrega o mesmo slot e registra o conteúdo restaurado.

- Fixture commit [e2a8406a48a6635e2221bd3bf34043c87ebeeec5](https://github.com/mucholocco86/laborat-rio_renpy/commit/e2a8406a48a6635e2221bd3bf34043c87ebeeec5).
- Workflow commit [83f22cd90357dd5b64cd727415972bc39b6248c0](https://github.com/mucholocco86/laborat-rio_renpy/commit/83f22cd90357dd5b64cd727415972bc39b6248c0).
- **PENDENTE:** confirmar que o slot está visível ao segundo processo e ler os marcadores `X52_NOTIFICATION_FRESH_LOAD_BEFORE/AFTER`.


O run [39215399305](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39215399305) não executou os testes: o parser Ren'Py interrompeu a compilação na linha do `raise` Python solto dentro de um `if` de script. A fixture foi corrigida para usar `$ assert renpy.can_load(...)`, commit [403f67b801d5a44c81fa93b23e5007fb43dce6d4](https://github.com/mucholocco86/laborat-rio_renpy/commit/403f67b801d5a44c81fa93b23e5007fb43dce6d4). Esse run é falha de sintaxe do harness e não fornece evidência de runtime; aguardar o run seguinte.


### Save/load entre processos — run 39215564208

O run [39215564208](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39215564208) concluiu **SUCCESS** depois da correção de sintaxe no fixture. O workflow executou a criação do slot e o carregamento em dois processos Ren'Py separados, usando a mesma cópia descartável do jogo.

Marcadores relevantes:

```text
X52_NOTIFICATION_FRESH_SAVE_BEFORE [u'Saved notification']
X52_NOTIFICATION_FRESH_SAVE_MUTATED_AFTER [u'Post-save notification']
X52_NOTIFICATION_FRESH_LOAD_BEFORE ProbeNotificationsClass RevertableList []
X52_NOTIFICATION_FRESH_LOAD_AFTER ProbeNotificationsClass RevertableList [] True
```

No segundo processo, o singleton iniciado novamente pelo código `init` já apresentava lista vazia antes do load. Depois de carregar o slot, a lista continuou vazia; a screen `urm_x52_notification_overlay_probe` constava ativa.

**OBSERVADO EM RUNTIME (fixture reduzida, processo novo):** neste desenho, o load não repôs `Saved notification` na lista do owner. A conclusão limitada é que a lista/owner do modelo reduzido não teve seu conteúdo do momento do save restaurado no novo singleton.

**Não demonstrado:** o marcador `screen=True` só confirma que a screen existe após o load; o probe não inspecionou seus displayables nem validou se a ação do botão ainda aponta para o objeto de notificação salvo, se foi reconstruída, ou se a screen simplesmente renderizou a lista vazia. Portanto, não concluir que screen e objeto de ação tenham sido restaurados corretamente.

**Relação com o SDK:** o resultado é compatível com o fluxo nativo em que saves persistem roots do store e o RollbackLog, enquanto objetos iniciados em init e não incluídos como roots modificados podem continuar sendo criados no processo novo sem que o conteúdo do singleton seja substituído. A classe-base reduzida reproduz os métodos de serialização identificados em `x52NonPicklable`; o teste não isolou separadamente cada etapa de serialização nem carregou o pacote original do URM. Essa explicação permanece **INFERÊNCIA**, não causa confirmada pelo probe.

A tentativa anterior [39215399305](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39215399305) terminou na compilação do fixture e não executou probes; a correção sintática está no commit [403f67b801d5a44c81fa93b23e5007fb43dce6d4](https://github.com/mucholocco86/laborat-rio_renpy/commit/403f67b801d5a44c81fa93b23e5007fb43dce6d4). O run 39215564208 é o primeiro resultado válido do cenário entre processos.

- **CONFIRMADO NO SDK 7.4.11 (fonte):** o save/load opera sobre roots serializados e o log nativo; stores limpos têm backup raso no ciclo do rollback.
- **OBSERVADO EM RUNTIME:** no fixture com classes reduzidas, o segundo processo carregou o slot, mas o novo owner permaneceu com lista vazia; a screen aparecia ativa.
- **HIPÓTESE:** o singleton init-only não faz parte das roots restauradas e mantém o estado inicial do novo processo.
- **PENDENTE:** inspecionar o conteúdo/ações da screen carregada; repetir com o pacote URM integral; comparar um objeto modificado em store root e um singleton init-only; confirmar exatamente quais objetos/atributos entram no arquivo save e quais permanecem apenas em runtime.



### Reconstrução da screen após load — run 39229685100

A execução [39229685100](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39229685100) passou com uma checagem adicional da screen. O fixture deu um ID explícito ao botão de notificação e, após o load em processo novo, consultou esse widget via `renpy.display.screen.get_widget`.

Marcador:

```text
X52_NOTIFICATION_FRESH_LOAD_AFTER ProbeNotificationsClass RevertableList [] True False
```

Os últimos valores indicam: screen encontrada (`True`); widget de ação da notificação encontrado (`False`). A fixture exigiu que esse widget estivesse ausente e terminou com código 0.

#### O que o SDK explica

Na implementação 7.4.11:

- `renpy/display/screen.py`, `ScreenDisplayable.nosave`, exclui `child`, `children`, `widgets`, transforms e caches da serialização da screen.
- `ScreenDisplayable.after_setstate()` relocaliza a definição da screen por nome, limpa `child`, recria coleções de widgets e deixa a fase em `UPDATE`.
- `ScreenDisplayable.update()` executa novamente `self.screen.function(**self.scope)`, reconstruindo os widgets.
- `get_displayable()/get_widget()` chama `screen.update()` quando `screen.child is None`, depois procura o ID solicitado em `screen.widgets`.

**CONFIRMADO NO SDK 7.4.11 (fonte):** a presença de um `ScreenDisplayable` após load não implica que seu antigo widget/action tenha sido preservado. O displayable da screen pode ser restaurado e os filhos regenerados pela função da screen.

**OBSERVADO EM RUNTIME (fixture reduzida, fresh-process load):** a consulta de widget forçou a reconstrução e não encontrou o botão porque o novo singleton estava com a lista vazia. Isso demonstra o caminho de reconstrução no harness e responde à questão que o run 39215564208 deixava em aberto. Não valida o pacote URM integral.

**Interpretação delimitada:** a screen do fixture não recebe notificações em argumentos salvos; sua definição percorre a lista no singleton de módulo. Ao ser reconstruída no segundo processo, ela encontrou a lista atual vazia e, portanto, não criou o botão. Esse resultado é compatível com o comportamento que se espera do padrão `URM_notifications`, mas a equivalência permanece inferência até carregar a screen e classes originais do URM em runtime.

O commit da fixture é [e1102f73ae6ca75096026f6720eee8d41d6f8ec4](https://github.com/mucholocco86/laborat-rio_renpy/commit/e1102f73ae6ca75096026f6720eee8d41d6f8ec4).

| Fonte | Símbolos / linhas | Blob SHA |
|---|---|---|
| Ren'Py 7.4.11 `renpy/display/screen.py` | `ScreenDisplayable.nosave`, `after_setstate` (290–328); `update` (568–676); `get_displayable/get_widget` (1292–1332) | `cf7997b04c3b17a337809f58aa6591ccd58a15a7` |
| Ren'Py 7.4.11 `renpy/display/core.py` | `SceneLists.after_setstate` (799–820) | `14c920f9fe8c95627a698bd56a1e61c7f4b02074` |

- **PENDENTE:** repetir com o pacote URM real e inspecionar o resultado visual/interativo da screen após load; verificar separadamente telas com argumentos/scope contendo referências explícitas a objetos de notificação.


### Callback nativo de load do URM e probe correspondente — run 39230107907

A leitura cruzada revelou que a integração URM tem um caminho explícito de load:

1. Em `classes/main.rpy`, `afterLoad()` chama `renpy.show_screen('URM_overlay')`, configura o quickmenu e inicializa o StoreMonitor.
2. No fim do carregamento dos módulos, a fonte convertida registra `x52URM.afterLoad` em `renpy.config.after_load_callbacks`.
3. `screens/main.rpy` define `URM_overlay` e inclui `use URM_notifications`.
4. Em `screens/watchpanel.rpy`, `URM_notifications` percorre `x52URM.Notifications.notifications` e constrói um botão para cada objeto `Notification`.
5. No SDK 7.4.11, `loadsave.load()` chama `RollbackLog.unfreeze(roots, label="_after_load")`; o label comum `_after_load` executa cada função de `config.after_load_callbacks` antes de saltar para um eventual label do jogo chamado `after_load`.

Isso separa duas rotas que têm nomes parecidos: o callback de labels `LabelMon` também chama uma função URM quando o label é `start`, mas o caminho nativo de pós-load é `config.after_load_callbacks`, que executa `afterLoad` no label interno `_after_load`.

A fixture foi atualizada para registrar um callback antes de carregar o save em processo novo. Ele marca sua execução e chama `show_screen` para a screen reduzida que percorre a lista global do owner, reproduzindo o aspecto do URM relevante para esse teste. Fixture commit [7df9808eed40d0297c54fa3d0f1dfa22f23dc39c](https://github.com/mucholocco86/laborat-rio_renpy/commit/7df9808eed40d0297c54fa3d0f1dfa22f23dc39c).

O run [39230107907](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39230107907) concluiu **SUCCESS** e registrou:

```text
X52_NOTIFICATION_FRESH_LOAD_BEFORE ProbeNotificationsClass RevertableList []
X52_NOTIFICATION_FRESH_LOAD_AFTER ProbeNotificationsClass RevertableList [] True False True
```

A ordem dos campos pós-load é tipo do owner, tipo da lista, labels, screen existente, botão encontrado, callback executado. A fixture exigiu callback executado e widget ausente; ambas as condições passaram.

- **CONFIRMADO NA FONTE URM CONVERTIDA:** `afterLoad` reabre a overlay; a overlay usa `URM_notifications`; essa screen consulta o singleton e gera widgets a partir de sua lista.
- **CONFIRMADO NO SDK 7.4.11:** load transfere para `_after_load`; esse label executa `config.after_load_callbacks`; screen displayables reconstruídos atualizam seus widgets a partir da função da screen.
- **OBSERVADO EM RUNTIME (fixture reduzida):** no caminho de callback pós-load em processo novo, o callback executou, o singleton permaneceu vazio e a screen não produziu o widget identificado.
- **INFERÊNCIA forte, sem integração do pacote original:** para o mesmo grafo e padrão de tela, o URM tende a reabrir a overlay sem recuperar notificações temporárias cuja lista não veio do save. A conclusão sobre o pacote integral depende de validar loader, classes originais carregadas e screen compilada do URM em runtime.
- **PENDENTE:** executar esse mesmo fluxo com o URM real carregado; observar se o callback e a lista são afetados por algum outro módulo, autoLoad, estado persistent ou comportamento específico do loader X52MF2.

| Fonte | Símbolos / linhas | Blob SHA |
|---|---|---|
| URM convertido `classes/main.rpy` | `afterLoad` (54–69); registro de callback (217–218) | `14f93406d2946eaed664ed72c1d47063984ce24f` |
| URM convertido `classes/labels.rpy` | `LabelMonClass.init/labelCalled` (131–151) | `96713d0297cf1bedeb9232502aa0d631d2a0780e` |
| URM convertido `screens/main.rpy` | definição de `URM_overlay`, inclusão de `URM_notifications` | `ceb5dc63b3691a4b6244345e1c5a3e3b9d149291` |
| URM convertido `screens/watchpanel.rpy` | `URM_notifications`, iteração e botões de notificação (260–353) | `8cc83f00838ed409183e85e4ebdb37ddf4433823` |
| Ren'Py 7.4.11 `renpy/loadsave.py` | `load`, chamada a `unfreeze(..., label="_after_load")` (762–771) | `c8b831ebfd5487f11a1d4dde8c87cde7f7ed93e3` |
| Ren'Py 7.4.11 `renpy/common/00start.rpy` | label `_after_load`, loop de callbacks (84–120) | `96649d2d56b1262313375fef56646ec0db327ed2` |
| Ren'Py 7.4.11 `renpy/display/screen.py` | reconstrução de `ScreenDisplayable`, `get_widget` | `cf7997b04c3b17a337809f58aa6591ccd58a15a7` |


### Limite atual para integração runtime do URM integral — inspeção do loader

A conferência do caminho de carga confirma por que os probes de notificação permanecem fixtures reduzidas:

- **classes/main.rpy** chama `x52MF2.load(['dialogs','api','inputs','tooltips'], 'x52URM', '0x52-URM/framework')`. O catálogo em **framework/bootstrap.rpy** expande esses módulos e dependências para arquivos `.x52rpy`, `.x52` e recursos auxiliares.
- No bloco **init 999** de **classes/main.rpy**, há 18 chamadas explícitas a `loadFile` em `0x52-URM/` — 17 arquivos de tela em `screens/` e 1 arquivo de estilos (`URM_styles.rpy.x52`), incluindo `screens/watchpanel.rpy.x52` e `screens/choices.rpy.x52`. Depois, o código registra `afterLoad` em `config.after_load_callbacks`.
- A árvore convertida examinada contém `.rpy` organizados em `classes/` e `screens/`; o README da área diz que ela preserva a estrutura do pacote `MOD_ANALISE`. Essa árvore de inspeção não corresponde, por si só, aos caminhos `.x52` solicitados pelo loader.
- As tentativas de buscar no repositório os caminhos exatos `1_URM_ORIGINAL/0x52-URM/framework/modules/01utils.x52rpy`, `1_URM_ORIGINAL/0x52-URM/URM_styles.rpy.x52` e `1_URM_ORIGINAL/0x52-URM/screens/watchpanel.rpy.x52` retornaram 404. Isso confirma somente que esses caminhos presumidos não estão publicados ali; não prova que nenhum archive ou cópia equivalente exista em outro lugar do laboratório.
- O workflow de runtime `urm-choice-runtime-probe.yml` copia `renpy-7.4.11-sdk/the_question` para o runner temporário e acrescenta `urm_choice_runtime_probe.rpy`. Ele não copia nem carrega o pacote `.x52` do URM.

**CONFIRMADO NA FONTE URM CONVERTIDA:** `classes/main.rpy` depende em runtime de módulos dinâmicos, 17 fontes de tela e 1 arquivo de estilos. O callback real `afterLoad` também inicializa StoreMonitor, aplica ajustes visuais, chama `URMFiles.autoLoad()` e pode abrir telas de boas-vindas/atualização. A fixture anterior reproduziu apenas o aspecto relevante para a lista e screen de notificações, não essa rotina integral.

**CONFIRMADO NO LOADER URM:** `framework/bootstrap.rpy` seleciona `.x52t` quando disponível; caso contrário, lê `.x52`/`.x52rpy` e chama `renpy.load_string()`. Renomear ou copiar arbitrariamente `.rpy` convertidos para os nomes `.x52` não demonstraria o carregamento do pacote original e mudaria a fonte submetida ao parser.

**PENDENTE:** localizar no conteúdo versionado ou em outra fonte já disponível o archive/árvore que satisfaça os caminhos do loader; só então avaliar um teste integral em cópia descartável. Até lá, manter os resultados runtime como “fixture reduzida” e não inferir execução do URM completo.

| Fonte | Símbolos / evidência | Blob SHA |
|---|---|---|
| URM convertido `classes/main.rpy` | `x52MF2.load`, lista de 18 `loadFile` (17 telas + 1 estilo), registro do callback e corpo de `afterLoad` | `14f93406d2946eaed664ed72c1d47063984ce24f` |
| URM original/convertido `framework/bootstrap.rpy` | catálogo, expansão e `loadFile` | `9d72267c2d86c68aa9dac1fee94652c891a611fe` |
| README `2_URM_X52_CONVERTIDO` | localização/propósito da árvore convertida | `9b23130ab12cf47964b179ba1129528d8720bb47` |
| `.github/workflows/urm-choice-runtime-probe.yml` | cópia do jogo base e instalação exclusiva da fixture | `4fb78bb48cf695cde87ec0f9d7f84df0aa6bef64` |
| README `1_URM_ORIGINAL` | instrução para preservar material original | `362d0c0f675ffd6cdf06da804ea57fad0307ef7e` |


### Callback de load e arquivo .urm são canais de estado distintos

A inspeção do callback real revelou que `afterLoad()` também chama `URMFiles.autoLoad()`. Segui essa chamada para separar o estado persistido pelo URM da lista temporária de notificações:

- `URMFilesClass.autoLoad()` só tenta carregar `Settings.lastLoadedFile` quando o arquivo atual não tem alterações pendentes e o nome do arquivo salvo difere.
- `URMFilesClass.load()` lê o `.urm` mais recente da pasta `game/` ou do diretório de saves do URM; o formato é um ZIP com entradas JSON, carregadas como `URMFileStore`.
- `URMFile.save()` grava as entradas presentes em `URMFile._stores` como arquivos JSON dentro do ZIP. Os stores `vars`, `watched`, `labels` e `replacements` são estruturas de dados das ferramentas do URM.
- Separadamente, `main.rpy` cria `Notifications = NotificationsClass()`; `NotificationsClass.__init__()` cria `self.notifications = []`. `add`, `remove` e `clear` operam nessa lista. Nos caminhos examinados não há chamada que acrescente essa lista/objetos ao `URMFile` ou aos stores JSON.

**CONFIRMADO NA FONTE URM CONVERTIDA:** `afterLoad()` tem dois efeitos relevantes: reabrir a interface e chamar `autoLoad()` para o arquivo de configuração/estado das ferramentas. O conteúdo `.urm` percorre o grafo `URMFiles.file → stores → JSON`; a lista de avisos pertence ao objeto singleton `Notifications` e não aparece nesse caminho de serialização observado.

**INFERÊNCIA delimitada:** carregar o último `.urm` pode restaurar metadados das ferramentas (por exemplo, variáveis lembradas/monitoradas e outras configurações presentes nos stores), mas a fonte examinada não indica que isso repovoe notificações pendentes. A ausência de uma chamada nos caminhos examinados não exclui extensões externas ou código dinâmico ainda não analisado.

**Correção de escopo para o run 39230107907:** o probe reproduziu o callback e a reabertura de uma screen que consulta a lista; não reproduziu `StoreMonitor.init()`, ajustes de tema, `URMFiles.autoLoad()` nem telas de boas-vindas/atualização. Portanto, seu resultado continua sendo runtime da fixture reduzida; o exame estático do callback completo mostra que o autoLoad tem um canal separado da lista, mas não transforma o probe em integração URM.

- **CONFIRMADO NA FONTE URM CONVERTIDA:** `.urm` armazena stores serializados em JSON; `NotificationsClass.notifications` fica em outro objeto e não é serializada pelos métodos observados de `URMFile`.
- **CONFIRMADO NO SDK 7.4.11:** save nativo e restauração do rollback usam as estruturas do Ren'Py examinadas anteriormente; não se deve usar o arquivo `.urm` como sinônimo de save nativo.
- **PENDENTE:** validar em runtime a carga de um `.urm` real e uma edição de variável/condição associada; verificar se algum store dinâmico do URM acrescenta referência indireta à lista de notificações.

| Fonte | Símbolos / evidência | Blob SHA |
|---|---|---|
| URM convertido `classes/notifications.rpy` | `NotificationsClass`, `Notification`, lista e métodos add/remove/clear | `3283ec4b1615967a71ad21cc34670bf8158ab96d` |
| URM convertido `classes/URMFiles.rpy` | `autoLoad`, `load`, `URMFile.save/load`, `URMFileStore.toJSON` | `888aba28d9d2e7870d8c4e6526417390179cd326` |
| URM convertido `classes/vars.rpy` | `VarsStoreClass.store/watchedStore` vinculados aos stores do URMFile | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| URM convertido `classes/main.rpy` | instanciação de `Notifications`; chamada a `URMFiles.autoLoad()` em `afterLoad` | `14f93406d2946eaed664ed72c1d47063984ce24f` |


## Correção posterior — localização das fontes originais e teste integrado (2026-10-23)

As buscas históricas citadas acima usaram um nível de caminho presumido (`1_URM_ORIGINAL/0x52-URM/...`) que não existe no repositório. A inspeção posterior confirmou que o pacote original está preservado diretamente em `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/`, com `classes/`, `framework/`, `screens/`, `images/` e demais arquivos. Portanto, aqueles 404 demonstravam apenas o erro do caminho presumido, não a ausência de fontes originais.

O run integrado [39903530535](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39903530535) copiou o conteúdo original intacto para uma pasta temporária `game/0x52-URM/`, usou o loader real e abriu a tela original `URM_choices` durante fixed rollback. Essa execução atualiza a afirmação anterior de que ainda não havia teste com loader/pacote original para a entrada de Choices. Ela **não** testa o ciclo de vida da lista `NotificationsClass.notifications` em rollback/save/load; essa questão continua pendente e o restante deste documento mantém seu escopo.

Evidência detalhada: [documento 36 — Choices original do URM abertas durante fixed rollback real](36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md).
