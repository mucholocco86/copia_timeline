# Choices — sistema completo identificado até agora

> **Estado consolidado em 2026-10-28:** a investigação passou de leitura estática a runtime integrado com o URM original no Ren'Py 7.4.11. A tela do URM selecionou uma Choice de condição falsa e executou seu bloco (docs 41–42); edição de variável, rollback e save/load nativo foram observados em percursos específicos (docs 38–47). Stores `.urm` e Snapshots foram examinados em runtime nos docs 49–53. Pendências abaixo registram o estado da etapa original e devem ser lidas junto com os resultados posteriores e a [revisão documental](../00_README/REVISAO_DOCUMENTAL_URM_2026-10-28.md).


## Estado da investigação

A análise do sistema de Choices avançou de uma simples identificação de `ChoicesClass` para um modelo arquitetural mais completo: **AST/Choice estrutural**, **estado dinâmico**, **seleção real**, **checkpoint**, **rollback**, **Context** e **estrutura interna dos blocos AST** são canais relacionados, mas não são a mesma coisa.

Documentos detalhados desta etapa:

- `01_FLUXO_CHOICE_ROLLBACK.md` — fluxo da Choice desde a detecção no `renpy.ast.Menu`, passando pela seleção via `ChoiceReturn`, execução pelo Ren'Py, observação de alterações pelo `StoreMonitor` e retorno por rollback.
- `02_LIMITES_E_CASOS_ESPECIAIS.md` — limites, Choices ocultas, texto substituído versus valor real, `jumpTo`, CodeView, fixed rollback, Skip e regras de preservação para o Wells.
- `03_AST_MENU_BLOCOS_CALL_IF_JUMP.md` — estrutura real de `Menu.items`, blocos de Choice, `If.entries`, diferença entre `Call` e `Jump`, operações visuais separadas e limite estrutural de `URMChoice.jumpTo`.
- `06_CONTEXT_ROLLBACK_EXECUTION_7_4_11.md` — relação entre `Context`, `RollbackLog`, restauração do contexto, `current`, `Context.run()`, `RestartContext`, fixed rollback e retomada da execução do AST no Ren'Py 7.4.11.
- `07_URM_CHOICE_INFORMATION_PROJECTION.md` — `Menu.items` como fonte estrutural, `URMChoice` como camada de interpretação/projeção e distinção entre estrutura, estado, execução e apresentação.
- `08_FLUXO_EXECUCAO_BLOCO_CHOICE_IF_CALL_JUMP.md` — distinção entre próximo nó, destino direto, caminhos possíveis, caminho atualmente executável e consequências ao analisar `If`, `Call` e `Jump` dentro de uma Choice.
- `09_MENU_ROLLBACK_FORCE_E_CONTINUIDADE_BLOCO.md` — descoberta de que `Menu` possui `rollback = "force"` por padrão e análise da relação entre política de rollback, `Menu.execute()`, `Menu.next` e a continuidade dos blocos de Choice.
- `10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md` — fecha a ponte entre `Menu.items`, `URMChoice`, `MenuEntry`, `ChoiceReturn`, a Choice Screen e a interação nativa; incorpora o aprendizado do protótipo experimental e define a base mínima segura para um primeiro Walkthrough somente-leitura.

## Núcleo

`classes/choices.rpy` contém `ChoicesClass`.

`isDisplayingChoice` consulta o nó atual pelo contexto/script e verifica `renpy.ast.Menu`.

`currentChoices` percorre `script.items` e cria objetos `URMChoice` para os itens válidos.

`hiddenCount` conta escolhas não visíveis.

## URMChoice

O item é tratado como tupla com:

```text
item[0] → texto da Choice
item[1] → condição
item[2] → lista de nós AST da alternativa
```

Propriedades importantes:

- `isVisible` avalia a condição em `renpy.store.__dict__`;
- `text` usa `renpy.exports.substitute`;
- `condition` preserva a condição da alternativa;
- `code` usa `CodeView.nodesToCode`;
- `jumpTo` procura o primeiro `renpy.ast.Jump` direto no conteúdo da alternativa.

## Relação Context ↔ Rollback

A análise do SDK 7.4.11 confirmou que o rollback restaura não apenas valores do store, mas também estado de controle associado ao `Context`.

O fluxo consolidado é:

```text
RollbackLog
    ↓
seleciona entradas
    ↓
revlog
    ↓
rb.rollback()
    ↓
restauração do estado/contexto
    ↓
execute_default_statement(False)
    ↓
novo Rollback corrente
    ↓
Context.rollback_copy()
    ↓
RestartContext / RestartTopContext
    ↓
Context.run()
    ↓
AST continua do ponto restaurado
```

`Context` e `RollbackLog` têm responsabilidades diferentes:

```text
Context
  → estado de controle da execução atual

RollbackLog
  → histórico de estados restauráveis
```

O `Context` contém, entre outros dados, `current`, `return_stack`, `dynamic_stack`, `scene_lists`, `rollback`, `info` e `force_checkpoint`.

`RollbackLog.rollback()` usa os contextos associados aos registros restaurados e, ao final, cria um novo registro corrente baseado em `renpy.game.context().rollback_copy()`, seguido de uma reinicialização controlada da execução.

## Fixed rollback

No SDK 7.4.11, `fix_rollback()` estabelece uma `fixed_rollback_boundary`, mas não ativa diretamente `rollback_is_fixed`.

Durante a restauração dos registros em `rollback()`, quando o `Context.current` restaurado alcança essa fronteira, `rollback_is_fixed` passa a `True`.

Portanto:

```text
fix_rollback()
    ↓
define boundary
    ↓
rollback()
    ↓
restore entries
    ↓
reach boundary
    ↓
rollback_is_fixed = True
```

A semântica exata desse estado na seleção programática do URM continua sendo tratada junto com `ChoiceReturn` e o circuito de interação.

## StoreMonitor e checkpoint

O StoreMonitor permanece separado do dono do rollback.

O fluxo confirmado é:

```text
StoreMonitor
      ↓
Context.force_checkpoint
      ↓
Context.run()
      ↓
RollbackLog.force_checkpoint
      ↓
RollbackLog.complete()
      ↓
checkpoint(hard=False)
```

Isso não significa que toda alteração arbitrária de variável gere automaticamente um checkpoint. O caminho confirmado é o callback Python do StoreMonitor solicitando `force_checkpoint`, seguido do processamento nativo do Ren'Py.

## Choice e rollback

O circuito nativo continua sendo:

```text
Menu
 ↓
display_menu()
 ↓
ui.interact()
 ↓
ChoiceReturn
 ↓
checkpoint(rv)
 ↓
bloco escolhido
 ↓
execução AST
```

Se ocorrer rollback posteriormente, o Ren'Py restaura estado/contexto e reinicia a execução. O URM observa esse processo; ele não precisa manter um segundo mecanismo de rollback.

O próprio `Menu` possui `rollback = "force"` no AST 7.4.11. Essa propriedade participa da política de rollback consumida pelo executor e não deve ser confundida com a chamada posterior de `checkpoint(rv)` feita pelo circuito de interação.

## Execução do bloco de uma Choice

Uma alternativa de Menu possui um bloco AST próprio. Esse bloco pode conter Python, diálogo, `If`, `Call`, `Jump` e outras statements.

Portanto:

```text
Choice
 ↓
block AST
 ↓
execução dos nós
```

não equivale necessariamente a:

```text
Choice → Jump
```

Para análise completa, distinguimos:

```text
destino direto
próximo nó
caminhos possíveis
caminho atualmente executável
consequências efetivamente produzidas
```

`URMChoice.jumpTo` cobre somente uma pequena projeção dessa estrutura.

## Replay

`renpy.call_replay()` cria uma execução separada com novo `Context`, novo `RollbackLog` e stores preparados para replay. Ao terminar, o contexto de replay é removido e o log/store do jogo principal é restaurado.

Portanto:

```text
Jump
  → continua no contexto atual

Replay
  → cria uma bolha de execução separada
```

## Invariante arquitetural vs. detalhe de versão

Os mecanismos acima são **confirmados para Ren'Py 7.4.11**.

Não devemos assumir que nomes, campos, classes ou sequência interna sejam idênticos em SDKs posteriores. A futura comparação entre SDKs deverá separar:

```text
princípio arquitetural
        ×
implementação específica da versão
```

Essa separação será especialmente útil para investigar a fronteira de compatibilidade observada entre Ren'Py 8.5.2 e 8.5.3.

## Regra de preservação

Primeiro entender → depois inspecionar → depois planejar → só então modificar.

O objetivo continua sendo completar a árvore do URM antes de decidir o que será transplantado para o Wells Framework.

## Continuação de 2026-10-13 — identidade e índice da Choice

A nova análise [11 — Menu, Choice Screen e integridade da seleção](11_MENU_CHOICE_SCREEN_CORRELACAO_E_INTEGRIDADE_DA_SELECAO.md) aprofunda o documento 10: a posição original `i` de `Menu.items` é preservada em `URMChoice` e é o valor usado pela seleção nativa para resolver o bloco AST. A interface visual pode omitir/transformar entradas; não se deve tratar seu índice visual ou texto exibido como identificador estrutural universal.

**Questões pendentes:** menus com `condition=False`, legendas, alternativas com rótulos duplicados, `set`, tradução, argumentos por item e testes após rollback. Essas questões devem ser investigadas por leitura e experimentação controlada, preservando a separação entre observação, hipótese e prova.


## Continuação de 2026-10-16 — validação SDK e rollback

O documento [15 — Validação no SDK 7.4.11: ChoiceReturn, checkpoint, store e rollback](15_VALIDACAO_SDK_CHOICERETURN_CHECKPOINT_ROLLBACK.md) confirma por inspeção estática o caminho Menu → valor estrutural → ChoiceReturn → checkpoint → deltas de StoreDict → restauração de estado e Context. Também localiza RollbackLog em renpy/python.py.

A relação entre o relato de edição manual e o instante exato em que o rollback a desfaz continua pendente de runtime, assim como save/load e fixed rollback.

## Continuação de 2026-10-16 — CodeView e edição de variáveis

O documento [16 — CodeView, busca e edição de variáveis ligadas a Choices](16_CODEVIEW_BUSCA_EDICAO_VARIAVEIS.md) rastreia Choice.code → CodeView → hyperlink de variável → URM_modify_value → SetVarValue → store ativo. Registra os limites dos padrões regex e separa essa mutação dos metadados guardados em .urm.


## Continuação de 2026-10-16 — mutações de variáveis e objetos revertíveis

O documento [17 — Edição de itens, mutações de objetos e rollback](17_EDICAO_ITENS_MUTACOES_OBJETOS_ROLLBACK.md) cruza `Var.setValue`, `CreateVar`, exclusão de variáveis e edição de itens de listas/dicionários com `RevertableList`/`RevertableDict` e `RollbackLog.complete()/rollback()` do SDK 7.4.11. A evidência é estática. Permanecem pendentes testes de runtime do URM e o alcance do `StoreMonitor` em mutações aninhadas.


## Continuação de 2026-10-16 — callback Python e checkpoints

O documento [18 — Callback Python, construtores revertíveis e edição pela screen](18_CALLBACK_PYTHON_E_CHECKPOINTS_URM.md) localiza a chamada de python_callbacks em ast.Python.execute(), rastreia a transferência adiada de Context.force_checkpoint ao RollbackLog e confirma em minstore.py que os nomes especiais são ligados a RevertableList/RevertableDict. A mutação interna de container depende do log de objetos; o delta de StoreDict não é um snapshot do conteúdo.


## Continuação de 2026-10-16 — fechamento do estado antes do rollback

O documento [19 — Fechamento do estado corrente antes do rollback](19_FECHAMENTO_ESTADO_ANTES_ROLLBACK.md) confirma que exports.rollback() chama RollbackLog.complete() imediatamente antes da restauração. O log então coleta deltas do StoreDict e snapshots dos objetos mutados. Também esclarece que o checkpoint solicitado pelo StoreMonitor é soft (hard=False), não uma barreira rígida ao rollback. A aplicação exata a ações do URM segue pendente de runtime.


## Continuação de 2026-10-16 — edição manual e save nativo

O documento [20 — Edição manual e save nativo: raízes e ciclos do StoreDict](20_EDICAO_MANUAL_SAVE_NATIVO_E_ROOTS.md) detalha loadsave.save → RollbackLog.freeze → complete(False) → roots/log serializados. get_roots usa ever_been_changed, atualizado em ciclos cycle=True. Isso identifica casos que precisam ser testados ao salvar imediatamente após editar/criar variável pela screen; não conclui que haja perda de dados. O arquivo .urm permanece separado do save nativo.


## Continuação de 2026-10-16 — retorno da ação URM e condições do Menu

O documento [21 — Propagação da ação do URM e condições do Menu](21_PROPAGACAO_ACAO_URM_E_CONDICOES_MENU.md) acompanha o retorno não-None da ação Select pela interação Ren'Py até o índice estrutural consumido por `Menu.execute`. A análise estática indica uma possível seleção de alternativa cuja condição é falsa, pois não encontrou revalidação do índice após a interação; a integração de tela e o comportamento ponta a ponta continuam pendentes de teste runtime.


## Continuação de 2026-10-16 — runner e limites da validação runtime

O documento [22 — Runner de teste Ren'Py 7.4.11: encerramento e limite da evidência runtime](22_RUNNER_TESTE_RENPY_ENCERRAMENTO_E_EVIDENCIA_RUNTIME.md) registra que o runner deixa o processo ativo quando a testcase termina com node vazio. A fixture passou a encerrar explicitamente o engine depois das asserções, e o workflow agora limita ambos os comandos. O baseline nativo e a fixture de seleção forçada passaram em runtime no Ren'Py 7.4.11 (run 38946951166). A fixture adicional também alterou um valor de store de 10 para 99 e, após checkpoint e rollback, observou o valor restaurado em 10 (run 38947765822). Os dois resultados validam contratos sintéticos do SDK. A integração integral das telas e das ações originais convertidas do URM continua pendente. Uma reprodução reduzida do caminho escalar SetVarValue → Var.setValue passou em runtime no run 38950917699 e restaurou 10 após editar para 99 e executar rollback; limites e detalhes estão no documento 22. Uma prova seguinte passou no run 38973243038: após duas Choices, rollback pela API com force=False restaurou o valor editado (99→10) e os efeitos das duas alternativas (rota 2→0). Isso ainda não simula a tecla/botão de rollback do jogador; veja os limites no documento 22. A entrada `type PAGEUP` no harness passou em runtime no run 38978993727: após edição e duas Choices, as amostras foram 99/2 → 99/2 → 99/1 → 10/0; a contagem é específica da fixture. Veja documento 22.


A extensão mais recente de [22](22_RUNNER_TESTE_RENPY_ENCERRAMENTO_E_EVIDENCIA_RUNTIME.md) passou no run **38979502224**: depois de gravar save nativo com a variável editada em 99, o fixture mudou o valor para 123 e carregou o slot; o runtime observou 99 novamente. Isso comprova somente, para o caso escalar raiz reduzido, que a edição já existente no instante do save entrou no estado nativo serializado. O marcador do harness foi movido para o módulo do runner após a primeira tentativa ter sido reiniciada pelo próprio load. Containers, variáveis criadas, StoreMonitor, variáveis congeladas e URM integral seguem pendentes.


A validação de container também passou no run **38979672209**: a ação reduzida de URM_add_item acrescentou 20 a uma lista Ren'Py ([10] → [10, 20]); depois de duas Choices e rollback com force=False, a lista voltou a [10] e a rota a 0. A evidência cobre o caso de lista revertível compilada pelo Ren'Py e não demonstra reversibilidade de qualquer objeto/container nem notificação pelo StoreMonitor. Detalhes e limites no documento 22.


A edição de item em dicionário também passou no run **39013297447**: a ação reduzida baseada em Var.getChild/SetVarValue mudou a chave a de 10 para 20; após duas Choices e rollback com force=False, o runtime observou o valor 10 e a rota voltou a 0. O teste usa um dict literal Ren'Py e não instrumenta o objeto/log diretamente; veja os limites no documento 22. A matriz reduzida cobre agora escalar raiz, append em lista e edição de chave em dicionário.


O run **39013412540** validou também a exclusão de um índice de lista e uma chave de dicionário pela reprodução reduzida de Var.delete: antes do rollback, lista `[20]` e dicionário `{b: 20}`; depois, `[10, 20]` e `{a: 10, b: 20}`. As duas mutações e os efeitos das Choices foram restaurados. A matriz runtime e seus limites estão no documento 22.


O run **39064784962** validou na reprodução reduzida a regra de truthiness de CreateVar: valores convertidos para inteiro 0, boolean False e string vazia não foram criados; o inteiro 7 foi aceito. A fonte convertida também prevê 0.0 como rejeitado, mas esse valor ainda não foi testado em runtime. Isso é separado da edição de valores existente. Ver limites e classificação no documento 22.


O run **39064935980** validou save/load nativo de containers editados: uma lista salva como `[10, 20]` e um dicionário como `{a: 20}` foram alterados depois para `[10, 20, 30]` e `{a: 30}`; o load restaurou os conteúdos do momento do save. O teste é reduzido e usa literais Ren'Py; não valida objetos externos nem metadados `.urm`. Detalhes no documento 22.


### StoreMonitor: hook e edição direta (2026-10-18)

A análise estática separou o callback `python_callbacks` do hook que o StoreMonitor instala no helper nativo `_m1_00action_data__set_field`/`_set_field`. `SetVariable` passa pelo helper; o `Var.setValue` convertido usa atribuição direta via `exec`, e `CreateVar` usa `setattr`. Logo, o hook não deve ser atribuído automaticamente às ações de edição próprias do URM. A fixture runtime contrapõe esses caminhos, mas o run estava pendente/em execução na revisão; veja [documento 23](23_STOREMONITOR_INTERCEPTACAO_E_EDICAO_URM.md) para fontes e status.


A execução **39098070978** concluiu **SUCCESS** para o contraste do helper de atribuição. Na fixture reduzida, a ação nativa `SetVariable` chamou o helper uma vez (contador 1, valor 20); a ação reduzida `SetVarValue` mudou para 30 sem incrementar o contador. Isso confirma a diferença de rota no ambiente do teste, sem equivaler a integração completa do URM. Detalhes e logs em [documento 23](23_STOREMONITOR_INTERCEPTACAO_E_EDICAO_URM.md).


### Callback após edição por screen — runtime (2026-10-18)

No run [39098269040](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098269040), a ação da screen mudou o valor 10→99 sem incrementar o contador do callback; ao fim do primeiro nó Python posterior, o callback observou o novo valor e o delta anterior 10. O testcase usou rollback desabilitado, portanto não confirma a transferência de `force_checkpoint` ao log em gameplay. A evidência e os limites estão no [documento 24](24_CALLBACK_SCREEN_EDIT_RUNTIME.md).


### Callback com rollback habilitado — restauração verificada (2026-10-18)

O run [39098551052](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098551052) repetiu a edição por screen com rollback habilitado. A fixture observou valor 99 após a edição; o callback Python posterior não encontrou o delta do alvo em **StoreDict.get_changes(False)**, enquanto **RollbackLog.force_checkpoint=True**. Depois, o rollback explícito restaurou o valor a 10. Isso demonstra, para o escalar raiz da fixture reduzida, que a ausência do delta naquele callback não significa que a alteração esteja fora do histórico reversível. A explicação provável é a ciclagem anterior do StoreDict pelo caminho de checkpoint/registro; a fixture não instrumenta todas as estruturas internas do RollbackLog e não é integração completa do URM. Fontes, log e limites no [documento 25](25_CALLBACK_ROLLBACK_STOREDELTA_GAMEPLAY.md).


### Freeze, monitor e watch — distinção estática (2026-10-18)

A leitura de **classes/vars.rpy** e **screens/vars.rpy** separou três mecanismos do URM: freeze e monitor são flags no store **vars** e aceitam apenas variáveis escalares raiz segundo os predicados convertidos; watch usa o store **watched** e alimenta o painel de observação. **Var.setValue** remove temporariamente freeze, realiza a edição direta e volta a aplicar freeze, o que permite a edição feita pelo próprio URM. O hook SetField e o callback Python são caminhos de detecção diferentes; quando uma edição direta vira notificação depende do delta disponível ao callback. Esta etapa é estática e deixa a validação runtime em aberto. Detalhes, símbolos e pendências no [documento 26](26_FREEZE_MONITOR_WATCH_EDICAO_URM.md).


### Freeze em runtime — edição nativa, URM e callback (2026-10-18)

O probe [39104245128](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39104245128) passou. Na fixture reduzida, a escrita nativa foi bloqueada com valor 10 frozen; a edição direta SetVarValue mudou para 30 e manteve freeze; no callback seguinte, que ainda tinha o delta 10→30, o handler restaurou 10 e conservou freeze. Essa restauração foi observada com rollback desabilitado. O caso de rollback habilitado permanece pendente porque o callback pode não receber o delta, como observado no documento 25. Ver [documento 27](27_FREEZE_RUNTIME_EDICAO_E_CALLBACK.md) e revisão do modelo estático no [documento 26](26_FREEZE_MONITOR_WATCH_EDICAO_URM.md).


### Freeze com rollback habilitado (2026-10-18)

O segundo probe de freeze também passou no run [39104385145](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39104385145). A escrita nativa continuou bloqueada em 10; a edição URM reduziu o valor para 30 e reaplicou freeze; desta vez o callback posterior não recebeu o delta, então o valor permaneceu em 30 até o rollback explícito, que restaurou 10. Isso reproduz, para uma variável escalar e uma fixture reduzida, a relação relatada entre edição durante a execução e rollback para um estado anterior. O metadado frozen do URM real não foi validado; ver [documento 28](28_FREEZE_ROLLBACK_RUNTIME.md).


### Monitor de variáveis e notificações — runtime (2026-10-18)

O run [39148026518](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148026518) comparou SetVariable nativo e SetVarValue direto. No teste reduzido, a escrita nativa gerou uma notificação síncrona pelo hook; a edição direta não notificou durante a ação, mas foi detectada pelo callback posterior quando o delta estava disponível. Sem rollback, o callback simplificado processou repetidamente o mesmo delta não ciclado, acrescentando registros duplicados no harness. Isso levanta uma hipótese de duplicação no StoreMonitor, ainda sem confirmação no URM integral ou em gameplay com rollback. Detalhes e classificação no [documento 29](29_NOTIFICACOES_VARIAVEIS_MONITORADAS_RUNTIME.md).


### Monitor URM com rollback habilitado (2026-10-18)

No run [39148219484](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148219484), a edição direta SetVarValue de variável monitorada foi para 30, não passou pelo hook nativo e não produziu aviso no contexto testado. O callback posterior não encontrou o delta; o rollback explícito restaurou o valor a 10. Isso mostra que a restauração do estado do jogo pode ocorrer sem notificação do StoreMonitor reduzido naquele instante. A integração completa e a escrita nativa sob rollback continuam pendentes. Ver [documento 30](30_MONITOR_ROLLBACK_NOTIFICACAO_URM.md).


O contraponto nativo com rollback habilitado também passou no run [39148594202](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148594202): SetVariable gerou aviso imediato 10→20 pelo hook e o rollback restaurou a variável a 10. O coletor de avisos da fixture foi limpo pelo rollback porque era uma lista reversível do store; isso não prova que a lista interna da NotificationClass do URM seja revertida. A comparação está consolidada no [documento 30](30_MONITOR_ROLLBACK_NOTIFICACAO_URM.md).


### Notificações do URM e rollback — ciclo de vida

O documento [31 — Ciclo de vida das notificações do URM e rollback](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md) identifica `x52NonPicklable` como classe baseada no objeto Python comum e localiza `URM_notifications` em `screens/watchpanel.rpy`. O SDK 7.4.11 filtra snapshots de objetos por alcance a partir das raízes alteradas e dos displayables ativos. Nos runs [39156621298](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156621298) e [39156808878](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39156808878), as fixtures reduzidas observaram: singleton init-only sem raiz alterada manteve a lista com 1; referência raiz alterada ou screen visível com `action notif` levou a lista de volta a 0 após rollback. A screen real e o pacote URM completo ainda não foram executados. A hipótese de que a overlay real alcance a lista está fortemente apoiada pela correspondência estrutural, mas permanece inferência. Pendências: rollback antes do novo render, timeout/thread, save/load e integração ponta a ponta. Os probes `urm_x52_notification_clear_rollback` e `urm_x52_notification_remove_rollback` agora comparam a substituição de atributo feita por `clear()` com a mutação in-place de `RevertableList.remove()`, sob screen visível e checkpoint equivalente. Fixture commit [37deb35335fec1fb140ab6b26e565ac7bdd6ab3e](https://github.com/mucholocco86/laborat-rio_renpy/commit/37deb35335fec1fb140ab6b26e565ac7bdd6ab3e); workflow commit [537a46dcbc98ae76af80464efc7ae8582aa62eaa](https://github.com/mucholocco86/laborat-rio_renpy/commit/537a46dcbc98ae76af80464efc7ae8582aa62eaa). O run runtime [39205520906](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39205520906) concluiu os dois probes: `clear()` deixou a lista vazia após rollback (screen ativa), enquanto `remove()` restaurou o item (screen ativa). Isso foi observado na fixture reduzida, não no URM integral. A causa das falhas anteriores foi rollback não habilitado nos dois labels; detalhes, logs e limites estão no documento 31.


A análise estática do timeout, também registrada no [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md), confirmou que a remoção automática ocorre dentro da thread de `renpy.invoke_in_thread`. O SDK limita as operações esperadas nessa thread; `RevertableList.remove()` também grava no mapa de mutações do rollback. `RollbackLog.complete` tenta novamente se esse mapa muda durante a iteração, mas isso não comprova suporte semântico ou segurança para o padrão do URM. O run [39205520906](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39205520906) passou no probe de timeout: a lista voltou a 1 após rollback, e a flag do worker retornou a `False`. É um resultado do harness reduzido num agendamento controlado, não validação integral do URM nem garantia geral de concorrência.


Foi incluído também o testcase `urm_x52_notification_timeout_rollback` para medir uma remoção de `RevertableList` dentro de `renpy.invoke_in_thread`, seguida por rollback ao checkpoint anterior. Fixture commit [b4de1e4c476668f27da51775c48536f82fe16f91](https://github.com/mucholocco86/laborat-rio_renpy/commit/b4de1e4c476668f27da51775c48536f82fe16f91); workflow commit [4ffdae65e48c42dad9c314c62fd1c68b78e78c63](https://github.com/mucholocco86/laborat-rio_renpy/commit/4ffdae65e48c42dad9c314c62fd1c68b78e78c63). O run [39205520906](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39205520906) concluiu com sucesso: o item removido pela thread retornou após rollback. O probe é reduzido e não demonstra determinismo em outros agendamentos.

A revisão estática do save/load no documento 31 localizou outra pendência: o SDK salva roots do store e RollbackLog, enquanto o singleton de notificações é criado em init e sua classe customiza o estado de serialização para não restaurar atributos. O SDK cria o backup limpo depois do init, quando o singleton URM já foi criado; cópias rasas do StoreBackup mantêm sua referência sem copiar a lista interna. Snapshots do RollbackLog ainda podem restaurá-la quando alcançável, por exemplo via screen. A reconstrução de ScreenDisplayable deixa aberta a forma como a screen relê o estado. O primeiro roundtrip reduzido [39214784786](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39214784786) carregou na mesma sessão e manteve `Post-save notification` após o teste substituir a lista depois do save; isso sugere que o atributo do owner Python comum não foi restaurado nessa rota. O resultado não valida o URM integral e ainda requer comparação com mutação in-place e processo novo; ver limitações no documento 31.


**Save/load de notificações em processo novo — run 39215564208:** o processo que criou o save registrou a lista com `Saved notification`; ao carregar o mesmo slot em outro processo, o singleton iniciado por `init` tinha lista vazia antes e depois do load, embora a screen de probe aparecesse ativa. Isso é evidência runtime da fixture reduzida; não esclarece se os displayables/action guardados pela screen apontam para objetos salvos nem comprova o comportamento do pacote URM integral. A interpretação de que o singleton init-only ficou fora das roots serializadas permanece hipótese. Ver [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md).


**Reconstrução da screen após load — run 39229685100:** o fixture consultou o widget identificado após load em processo novo. A screen existia, mas o botão de notificação não; a asserção passou. O SDK 7.4.11 exclui os widgets filhos do estado serializado e os reconstrói executando novamente a função da screen. Na fixture, essa reconstrução leu o singleton recém-iniciado com lista vazia. Isso fecha a lacuna do probe anterior, mas ainda não valida a screen do pacote URM integral. Fontes, linhas e limites no [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md).


**Callback pós-load do URM — run 39230107907:** `main.rpy` registra `afterLoad` em `config.after_load_callbacks`; o Ren'Py 7.4.11 executa esses callbacks em `_after_load`. `afterLoad` mostra `URM_overlay`, que inclui `URM_notifications`. O fixture reproduziu esse callback em processo novo: callback executado, lista vazia, screen presente e botão da notificação ausente. Esse resultado é runtime da fixture reduzida, não prova do pacote URM integral. Fontes e limites no [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md).


**Estado `.urm` versus notificações temporárias:** a revisão de `afterLoad()` confirmou que `URMFiles.autoLoad()` carrega stores JSON do arquivo próprio do URM; a lista `NotificationsClass.notifications` permanece em outro singleton e não é serializada pelos métodos de `URMFile` examinados. O teste de callback do run 39230107907 não carregou `.urm` nem executou integralmente `afterLoad()`. Ver [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md#callback-de-load-e-arquivo-urm-são-canais-de-estado-distintos).

**Limite para integração runtime completa:** o `main.rpy` convertido espera módulos dinâmicos e 18 fontes `.rpy.x52` em `0x52-URM/` (17 telas e 1 arquivo de estilos); o workflow atual roda somente a fixture no jogo de teste do SDK. Nenhum `.rpy` convertido foi renomeado para forjar os assets originais. Consulte o limite e os SHAs no [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md#limite-atual-para-integração-runtime-do-urm-integral--inspeção-do-loader).


**Possível lacuna na marcação de `.urm` como alterado:** `freeze/unfreeze/monitor/unmonitor` editam metadados aninhados quando a variável já está lembrada, sem passar pelos mutadores externos que ativam `URMFileStore.unsaved`; `watch` e `ignore/unignore` seguem rotas que marcam a flag. Confirmado na fonte convertida; o efeito de UI está pendente. A gravação manual percorre todos os stores não vazios mesmo quando `unsaved` é falso; a hipótese é que o indicador/aviso de descarte pode não refletir a edição. Fixture isolada e workflow criados para comparar as rotas. Detalhes em [06 — stores de variáveis e monitoramento](../06_VARIABLES/01_URM_STORES_MONITORAMENTO_E_SUBSTITUICAO_DE_TEXTO.md#6-alterações-aninhadas-e-flag-unsaved-do-arquivo-urm).


### Continuação de 2026-10-19 — consumidores de metadados `vars`/ `watched`

A leitura de `afterLoad`, `StoreMonitor`, `PathDetection`, `CodeView` e das telas confirmou onde os metadados de acompanhamento são consumidos. `frozen` e `monitor` são consultados sob demanda pelo monitor; `ignored` filtra condições/código apresentados pelo URM; `watched` guarda rótulos e o painel resolve valores atuais do store. Isso separa preferências persistidas no `.urm` de estado do jogo sujeito a rollback. Veja a seção 7 do documento [Stores, monitoramento e substituição de texto](../06_VARIABLES/01_URM_STORES_MONITORAMENTO_E_SUBSTITUICAO_DE_TEXTO.md).

**Pendente:** runtime integral do URM confirmando leitura dos metadados depois de `autoLoad`; cobertura do StoreMonitor por rota de escrita; e efeitos ponta a ponta no rollback. Os testes reduzidos do SDK mencionados nos documentos 22–24 não equivalem a uma execução do pacote original convertido.


### Continuação de 2026-10-19 — interface de Choices para edição de variáveis

O documento [26 — Choices, CodeView e ações de variáveis](26_CHOICES_CODEVIEW_ACOES_DE_VARIAVEIS_E_LIMITES.md) delimita quais controles são alcançados a partir da Choice. O CodeView pode abrir a edição do valor e Remember/Watch; Freeze/Monitor/Ignore ficam na tabela geral. A edição altera o store ativo e é diferente dos metadados `.urm`. Uma fixture reduzida já observou rollback de escalar editado por screen; a integração com o URM completo permanece pendente.


### Continuação de 2026-10-20 — notificação e ação “Revert”

O documento [27 — Notificação de variável, ação Revert e persistência](27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md) confirma na fonte convertida que o botão Revert reatribui prevVal via SetVarValue; ele não executa renpy.rollback(). A lista de notificações é mantida em memória no circuito examinado, enquanto notificationTimeout é uma configuração persistida por Settings. A sobrevivência da notificação em save/load nativo ainda depende de validação runtime.

### Continuação de 2026-10-20 — ação Revert e ciclo de vida de notificações

O run [39379101294](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39379101294) passou na fixture reduzida para a ação Revert: valor 20 → 10, com marcador independente de rota preservado em 1. Isso confirma no harness 7.4.11 que a ação reproduzida é uma atribuição sem retroceder o fluxo. A atualização também consolida os probes anteriores de rollback e save/load de notificações, distinguindo mesma sessão de processo novo. **O rollback reduzido posterior ao Revert passou no teste seguinte; a integração do pacote URM completo e os efeitos combinados permanecem pendentes.** Detalhes, SHAs e limites no [documento 27](27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md) e no [documento 31](31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md).
### Continuação de 2026-10-21 — Revert e fronteira de rollback

No run [39560909296](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39560909296), a fixture do SDK 7.4.11 passou pela sequência: checkpoint hard em valor 20/rota 1 → Revert reduzido para 10/rota 1 → rollback para 20/rota 1. Isso observa que rollback nativo pode desfazer a reatribuição, preservando a rota já incluída no checkpoint. A tentativa inicial [39560687256](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39560687256) falhou por configuração do harness (`store._rollback=False` tornou o checkpoint soft) e não é evidência sobre o comportamento-alvo. A integração da screen/URM completa e combinações com save/load, freeze e monitor ainda estão pendentes; ver adendo no [documento 27](27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md).
### Continuação de 2026-10-21 — Revert, freeze e monitor

O run [39561988378](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39561988378) passou na fixture reduzida: Revert mudou 20→10 mantendo `frozen=True`; ao entregar ao handler o delta 20→10, `StoreMonitor` restaurou 20 e não gerou notificação, pois freeze tem precedência sobre monitor. O teste chamou o handler diretamente com delta conhecido; **não** prova que a callback real sempre receba o delta após Revert. A disponibilidade do delta, o rollback combinado e a execução do URM integral seguem pendentes. Detalhes e artefatos no adendo do [documento 27](27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md).
### Continuação de 2026-10-21 — callback natural após Revert

No run [39562762194](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39562762194), o probe da ação por screen observou dois comportamentos no SDK 7.4.11 reduzido: sem rollback, a callback leu `20→10` e o monitor registrou a mudança; com rollback habilitado, ela não recebeu o delta, não criou registro e o valor 10 persistiu até rollback restaurar 20. A notificação visual do URM integral continua pendente; o ponto em que o delta é ciclado na fixture foi identificado no trace do run seguinte. Detalhes e limites no adendo do [documento 27](27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md).
### Continuação de 2026-10-21 — localização da ciclagem do delta

O trace instrumentado no run [39663561168](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39663561168) observou `get_changes(True)` retornando o delta `20→10` na pilha `RollbackLog.complete → begin → Context.run`, antes do callback Python. Com rollback desabilitado, `get_changes(False)` da callback recebeu o mesmo delta. Isso localiza por que o callback perde a mudança sem que ela saia do histórico reversível. A fixture envolve wrapper delegante do método original; SDK e URM integral não foram modificados. Detalhes, fontes e limitações no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).

### Continuação de 2026-10-21 — freeze + monitor + callback natural após Revert

O run [39664217382](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39664217382) passou os dois novos casos da fixture reduzida. Sem rollback, callback recebeu `20→10`; o handler frozen escreveu `20` durante a callback e não notificou, mas a leitura após a interação foi novamente `10`. Com rollback, callback não recebeu o delta e o rollback restaurou `20`. A razão para a diferença temporal no caso sem rollback segue pendente. A fixture usa metadados de freeze/monitor simplificados, não os stores `.urm` integrais. Ver detalhes e limites no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Correção de 2026-10-21 — valor após callback de freeze

O run [39665745692](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39665745692) confirmou que a leitura `10` da primeira auxiliar era anterior à callback Python. `Python.execute()` chama callbacks em `finally`, depois do bytecode; no nó Python seguinte a variável já está em `20`, restaurada pelo handler frozen, sem notificação. Com rollback, callback não recebe o delta e rollback restaura `20`. Esta evidência substitui a interpretação provisória registrada logo acima. Detalhes no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Continuação de 2026-10-21 — `force_checkpoint` da callback

O run [39669205656](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39669205656) observou a transferência do flag: com rollback ativo, `context.force_checkpoint=True` ao final da callback foi consumido no próximo início de nó e apareceu como `game.log.force_checkpoint=True`, com o flag do contexto limpo. O SDK converte esse flag pendente em `checkpoint(hard=False)` durante `RollbackLog.complete()`. O callback convertido do URM define `context.force_checkpoint` antes de consultar mudanças, mesmo sem delta. O fixture não quantificou checkpoints soft realmente criados; integração real pendente. Ver [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Continuação de 2026-10-23 — materialização de checkpoints soft

O run [39893930678](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39893930678) instrumentou `RollbackLog.checkpoint(hard=False)` com delegação ao método original. Durante os testcases reduzidos, houve transições `current.checkpoint=False→True` em 9 chamadas no caso monitorado e 10 no frozen+monitor; uma chamada adicional em cada percurso encontrou o registro já marcado. Os totais incluem setup e rollback, não são contagem por clique. O SDK não promove `hard_checkpoint` nessa chamada soft. Detalhes e limites no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).
### Continuação de 2026-10-23 — significado do checkpoint soft no rollback

A fonte `RollbackLog.rollback()` confirma que a contagem de checkpoints num rollback normal considera `hard_checkpoint`; os registros soft não aumentam `rollback_limit` nem decrementam a contagem pedida. O algoritmo greedy pode atravessar registros soft posteriores ao hard checkpoint alcançado. Em `on_load=True`, o SDK também conta `rb.checkpoint` soft, portanto load segue regra distinta. A tentativa runtime [39894546076](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39894546076) falhou e foi descartada como prova; a fixture e o step foram removidos. Detalhes e fonte no [documento 32](32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md).

### Continuação de 2026-10-23 — fixed rollback e ação de Choice do URM

O [documento 33 — Fixed rollback e escolha acionada pelo URM](33_ROLLBACK_FIXO_E_ESCOLHA_URM.md) cruza `rollback_is_fixed` da ação URM com a sensibilidade de `ChoiceReturn`, a fronteira de `RollbackLog` e o retorno estrutural consumido por `Menu.execute()` no SDK 7.4.11. A fonte sustenta a intenção de liberar seleção via URM durante fixed rollback, mas a integração da tela modal e a seleção alternativa em runtime continuam pendentes. Não há evidência de que a ação apague `fixed_rollback_boundary` ou altere diretamente registros do histórico.


A validação reduzida do run [39895890714](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39895890714) mostrou que, com `rollback_is_fixed=True` definido diretamente no fixture, a tela modal análoga ao URM ainda devolve o índice e `Menu.execute()` executa a rota A sob `fix_rollback_without_choice=False` e `True`. Isso é runtime da ponte screen→menu→AST; o ciclo real que atravessa uma fronteira `renpy.fix_rollback()` permanece pendente. Fixture e limites no [documento 33](33_ROLLBACK_FIXO_E_ESCOLHA_URM.md).


### Continuação de 2026-10-23 — fixed rollback real e reescolha via URM

O run [39897163458](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39897163458) percorreu uma fronteira criada por `renpy.fix_rollback()` após uma escolha nativa B. No segundo `PAGEUP`, o trace confirmou `rollback_is_fixed=True` e `roll_forward_info()==1`; B nativa ficou sensível e A bloqueada. A ação URM reduzida limpou a flag, retornou índice 0 e o motor executou A. Isto valida um ciclo real da fronteira no fixture Ren'Py 7.4.11; URM integral, segundo rollback após a troca, configuração `fix_rollback_without_choice=True` com fronteira real e save/load seguem pendentes. Veja [documento 33](33_ROLLBACK_FIXO_E_ESCOLHA_URM.md) e [fixture](../tools/fixtures/urm_fixed_rollback_boundary_probe.rpy).


### Continuação de 2026-10-23 — segundo rollback após reescolha

O [documento 34](34_SEGUNDO_ROLLBACK_APOS_REESCOLHA_URM.md) corrige a leitura da tentativa inconclusiva anterior: a fixture retornava ao menu principal antes dos PAGEUP adicionais. A fixture diagnóstica corrigida confirma que A executa, que o script cria outra fronteira por `renpy.fix_rollback()` e que novos rollbacks são aceitos; os primeiros PAGEUP ainda param em checkpoints internos e a fronteira recriada segue sob investigação. O run [39902170129](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902170129) fornece os traces. A fixture está em [`urm_fixed_rollback_second_cycle_diagnostic.rpy`](../tools/fixtures/urm_fixed_rollback_second_cycle_diagnostic.rpy), com workflow isolado [`urm-fixed-rollback-second-cycle-diagnostic.yml`](../../.github/workflows/urm-fixed-rollback-second-cycle-diagnostic.yml). O run [39902267110](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902267110) confirmou que o quarto PAGEUP atravessa a segunda fronteira, deixa `rollback_is_fixed=True` e recupera `roll_forward_info()==0` (A). O limite chega a zero nesse ponto. O run [39902388045](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902388045) registrou `rollback_is_fixed=True`, `forward=0`, escolha nativa A sensível/B bloqueada e, mesmo com `can_rollback=False`, a ação equivalente a `ChoiceReturn` retornou índice 1 e o menu seguiu pela rota B. Ele falhou apenas numa asserção auxiliar da lista de `renpy.session`; o run corrigido [39902500519](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39902500519) concluiu SUCCESS e confirmou a rota B e os campos da ação. A lista append-only em `renpy.session` registrou `[B, B, A, A, B]` durante reexecuções de rollback/replay, mostrando que ela não serve como histórico de escolhas únicas.


### Continuação de 2026-10-23 — entrada real da tela Choices

O [documento 35](35_ENTRADA_DA_TELA_CHOICES_E_FIXED_ROLLBACK.md) localiza os pontos reais de entrada de `URM_choices`: notificação flutuante com tecla `Alt+C` e botão do watchpanel. O atalho `Alt+M` abre a interface principal, que não lista Choices como aba. A fonte convertida não bloqueia explicitamente a entrada por `rollback_is_fixed`, mas a disponibilidade sob fixed rollback real permanece **pendente de teste integrado** com loader, overlay e telas originais.


### Validação integrada em 2026-10-23 — screen original durante fixed rollback

O run [39903530535](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39903530535) passou com o pacote original copiado intacto para um jogo descartável Ren'Py 7.4.11. A notificação usou Alt+C, chamou a tela original `URM_choices` enquanto `rollback_is_fixed=True`, e a ação `ChoiceReturn` levou à rota A. O harness habilitou rollback no contexto de teste; os limites e próximos casos estão em [36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md](36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md). Isso confirma a rota de Choices nessa fixture, mas não encerra a investigação de edição de variáveis, save/load ou configurações alternativas.


### Circuito de edição de variável a partir de uma Choice

O [documento 37](37_CODEVIEW_EDICAO_VARIAVEL.md) segue a rota estática `Choice → CodeView → hyperlink URMVarDialog → URM_modify_value → SetVarValue → Var.setValue → renpy.store`. Ele separa o que a fonte confirma do que ainda depende de runtime, principalmente o checkpoint e a participação de uma escrita feita por ação de screen no monitor/rollback.


### Validação integrada em 2026-10-23 — edição de variável e rollback

O [documento 38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md) registra a edição 1→7 pelo editor original em fixed rollback e a leitura 7 pela rota. O trace por tecla [39907164916](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39907164916) localizou o retorno a 1/`None` no PAGEUP 3. Correção validada no run [39910519723](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39910519723): `get_changes(True)` retornou o valor antigo 1 e `complete()` o gravou no registro aplicado no PAGEUP 3. A conclusão anterior de delta ausente foi falso negativo causado por `dict` sombreado como `RevertableDict` no contexto do fixture. Clique visual do hyperlink e save/load seguem pendentes. A repetição com `VarsStore.monitor=True` [39910824879](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39910824879) passou sem chamada a `handleVarChange` ou criação de notificação para a variável; o delta continuou reversível e PAGEUP 3 restaurou 1/None. O monitor foi ativado diretamente por API, sem validar load do `.urm`. O run [39912065172](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912065172) rastreou a pilha: `ast.Python.execute` chamou `_m1_vars__pythonCallback`; a consulta `get_changes(False)` viu somente a rota, com a tela de edição fechada e após `complete(True)` consumir o delta da variável.


### Continuação de 2026-10-23 — PAGEUP exato da restauração

O trace corrigido do [run 39907164916](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39907164916) localizou a restauração no **terceiro PAGEUP**: os dois primeiros mantiveram valor/rota em 7; o terceiro restaurou 1/None; o quarto não mudou o estado. A fixture agora instala de fato o wrapper na classe `RollbackLog`. O [documento 38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md) foi refinado com esse resultado.

### Continuação de 2026-10-23 — edição por screen e StoreMonitor

O [documento 39](39_STOREMONITOR_DELTA_E_EDICAO_POR_SCREEN.md) cruza a tela original `URM_modify_value`, `python_callbacks`, `Context.run`, `RollbackLog` e `StoreDict`. A validação corrigida [39910519723](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39910519723) demonstrou que `get_changes(True)` capturou o valor antigo 1 após a edição 1→7; `complete()` o colocou no registro corrente; PAGEUP 3 reaplicou o valor. A interpretação anterior de delta ausente foi causada pelo teste de tipo do probe, não pelo comportamento do SDK. O probe reduzido do documento 32 permanece um percurso separado. A origem de `force_checkpoint=True` em cada fase, clique visual do hyperlink, save/load e notificações em outros caminhos/contextos do StoreMonitor permanecem pendentes.


### Continuação de 2026-10-23 — condições nativas e force_checkpoint

O [documento 40](40_MENU_CONDICOES_FORCE_CHECKPOINT_RUNTIME.md) confirma no SDK 7.4.11 que Menu.execute conserva o índice original e usa-o para entrar no bloco AST; renpy.exports.menu avalia as condições antes da seleção nativa; ChoiceReturn devolve seu value sem executar AST. A escolha invisível pela tela do URM ainda exige teste de runtime isolado. O mesmo documento detalha a trilha de Context.force_checkpoint → Context.run() → RollbackLog.begin/complete() → checkpoint soft e delta de StoreDict, separando-a de checkpoint(rv), que pede hard=True por padrão, com efetividade condicionada a renpy.store._rollback. A repetição integrada [39912696436](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912696436) terminou SUCCESS e reproduziu a edição 1→7, reversível no terceiro PAGEUP. A interceptação de Context.__setattr__ no run [39912551615](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912551615) causou recursão e foi removida; esse run é inválido para conclusões de runtime. Origem exata de cada escrita da flag, Choice com condição falsa e save/load seguem pendentes.


### Continuação de 2026-10-23 — Choice com condição falsa executada

O [documento 41](41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md) registra o teste integrado [39913014343](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39913014343): a tela original do URM listou Hidden route C com isVisible=False e índice AST 2; Alt+3/Enter chamou ChoiceReturn com value 2 e o bloco C executou. Neste percurso de Ren'Py 7.4.11, a seleção programática pela UI do URM conseguiu executar a alternativa cuja condição era literalmente False. Isso comprova o caso do fixture, não todas as expressões/configurações de menu. O documento 40 contém o cruzamento nativo de condições, retorno de Choice e checkpoints. Rollback depois da rota forçada, condição dinâmica e save/load continuam pendentes.


### Continuação de 2026-10-23 — rollback após Choice forçada

O [documento 42](42_ROLLBACK_APOS_CHOICE_CONDICAO_FALSA.md) registra o runtime integrado [39924626643](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39924626643). Depois de C, cuja condição era False, o terceiro PAGEUP restaurou a rota para None e retornou ao Menu; o quarto manteve o Menu em fixed rollback, com rollback_limit zero e roll-forward no índice 2 (C). A tela original do URM reabriu nesse estado e selecionou B, cuja rota executou. As contagens são próprias da fixture 7.4.11; não generalizar para qualquer jogo ou sequência. Save/load e condição variável seguem pendentes.


### Continuação de 2026-10-23 — condição dinâmica alterada durante a screen

O [documento 43](43_CONDICAO_DINAMICA_CHOICE_EDITADA_PELO_URM.md) registra o runtime integrado [39992488601](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39992488601). Com URM_choices aberta, C começou com condição variável False; Var.setValue(True) original do URM fez a mesma Choice reportar isVisible=True; após renpy.restart_interaction(), Alt+3/Enter executou o bloco C. O teste chamou diretamente o setter e não percorreu os controles gráficos de edição; rollback do booleano nesse mesmo circuito e atualização sem reiniciar interação seguem pendentes.

### Continuação de 2026-10-25 — rollback da variável-condição

O [documento 44](44_ROLLBACK_VARIAVEL_CONDICAO_CHOICE.md) registra o runtime final [40198340290](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40198340290). A variável booleana editada pelo setter original do URM tornou C visível e permitiu executar a rota; no terceiro PAGEUP desta fixture, rollback restaurou `False`, rota `None` e o contexto no Menu. A consulta seguinte confirmou `isVisible=False` para C. O primeiro run [40198189336](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40198189336) teve uma asserção inválida sobre marcadores da fixture, também revertidos pelo rollback; a correção e a execução final bem-sucedida estão descritas no documento. Contagem de PAGEUP é específica do roteiro. A edição pelos campos gráficos e save/load continuam pendentes.

### Continuação de 2026-10-25 — editor gráfico, Choice dinâmica e rollback

O [documento 45](45_EDITOR_GRAFICO_CHOICE_DINAMICA_ROLLBACK.md) registra o runtime integrado [40200078200](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40200078200). A tela URM_modify_value original recebeu o valor 1, submeteu-o por SetVarValue e fechou; a rota C executou. No terceiro PAGEUP deste roteiro, rollback restaurou variável 0, rota None e condição falsa para C. O harness chamou diretamente CodeView.handleVarClicked para abrir a edição, então o clique físico no hyperlink permanece fora desta prova; as telas originais, entrada, submit, seleção e rollback foram testados.

### Continuação de 2026-10-25 — save/load nativo da Choice editada

O [documento 46](46_SAVE_LOAD_NATIVO_APOS_EDICAO_CHOICE.md) registra o run integrado final [40212821209](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40212821209). Depois da edição pelo editor original do URM e da execução de C, o save nativo registrou variável 1 e rota C; a fixture mudou os valores para 0 e `mutated-after-save`; `renpy.load` restaurou 1/C e passou. Isso valida a serialização nativa na mesma sessão, não o conteúdo de `.urm` nem um processo novo. Os runs anteriores com erro de roteiro/guarda são documentados e não são evidência negativa.

### Continuação de 2026-10-25 — load em processo Ren'Py novo

O [documento 47](47_SAVE_LOAD_CHOICE_PROCESSO_NOVO.md) registra o run em dois processos [40213634448](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213634448). O primeiro processo editou a condição pelo URM, executou C, salvou 1/C, alterou os valores e encerrou; o segundo iniciou com 0/None e carregou o slot, restaurando 1/C. O teste chama `renpy.load` diretamente. A fonte `GameSavesClass.load` encaminha o slot a `renpy.load` por meio de `Confirm`, mas a interação visual de Gamesaves/Confirm ainda não foi testada. O resultado não demonstra persistência no `.urm`.

### Continuação — tentativa de Gamesaves modal após teste em processo novo

O load em processo novo continuou passando após restauração da fixture para `renpy.load` direto: [40214014928](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40214014928). A inspeção da fonte confirmou que Gamesaves.load chama Confirm com `Function(renpy.load, slot)` e o template do modal liga K_RETURN ao callback. As tentativas de acionar o modal no runner [40213802714](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213802714) e [40213906303](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213906303) falharam por `Could not locate the displayable`; nenhuma delas mede o resultado do load pelo modal. A seleção visual do slot e confirmação em runtime permanecem pendentes; detalhes no documento 47.

### Continuação de 2026-10-27 — fronteira .urm e save nativo

O [documento 48](48_FRONTEIRA_PERSISTENCIA_SAVE_NATIVO_E_URM.md) registra inspeção estática de URMFiles.rpy: URMFile.save serializa stores URM como JSON em ZIP; a fonte não percorre o store Ren'Py para criar snapshot global, e Var.setValue não chama o salvamento .urm. Os documentos 46–47 comprovam separadamente que o save nativo preservou a variável e a rota nas fixtures. Gravação/carregamento .urm com o URM original e comparação de seu conteúdo seguem pendentes de runtime.


### Validação runtime — stores próprios do .urm

O [documento 49](49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md) registra o run [40657558715](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40657558715), SUCCESS, em dois processos Ren'Py 7.4.11 com o URM original. `URMFiles.save()` gerou ZIP com `properties`, `vars` e `watched`; o JSON guardou nome/freeze/monitor/watch, não o valor de gameplay 7. Em outro processo, `URMFiles.load()` restaurou esses metadados e a variável permaneceu no default 0. O teste usa os métodos originais diretamente, sem automação da interface gráfica. Fixture e workflow: `tools/fixtures/urm_file_persistence_probe.rpy` e `.github/workflows/urm-file-persistence-probe.yml`.


### Continuação — labels, substituições de texto e snapshots

O [documento 50](50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md) distingue os stores `.urm` `labels` (nomes lembrados), `replacements` (regras de filtro de apresentação) e o recurso `Snapshots` (tabela de variáveis guardada em memória, fora dos stores `.urm`). A leitura do SDK `pydict.pyx` mostra que `DictItems.as_dict()` preserva referências a valores, sem cópia profunda; efeitos para listas/dicionários mutados in-place são uma inferência estática e seguem pendentes de runtime.


### Validação runtime dos snapshots (2026-10-28)

O [documento 51](51_SNAPSHOTS_DIFF_RUNTIME_CONTAINERS.md) registra os runs [40658456177](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40658456177) e [40676323550](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40676323550): o diff detectou escalar alterado e containers substituídos por conteúdo diferente; não detectou mutações in-place nem novas listas/dicionários com conteúdo igual. A fixture ampliada usa checagens explícitas. O mesmo doc valida que o objeto `Var` antigo é somente leitura e o atual pode editar o store; valores ausentes retornam `None`, e uma variável removida não é recriada por `setValue`. Em comparação entre dois snapshots, ambos os lados são somente leitura e chaves ausentes são representadas por `None`; um `None` real e uma chave ausente têm a mesma projeção `None/unknown`, embora a presença diferente gere entrada no diff. A ligação à screen foi confirmada estaticamente, sem clique automatizado. O documento 53 trata separadamente da persistência no save nativo.

## Consolidação de persistência — atualização 2026-10-28

- [48 — fronteira entre save nativo e `.urm`](48_FRONTEIRA_PERSISTENCIA_SAVE_NATIVO_E_URM.md), atualizado com provas runtime posteriores.
- [49 — stores `.urm` e estado de gameplay](49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md): metadados URM restaurados em processo novo; o valor de gameplay ficou no default.
- [50 — labels, replacements e snapshots](50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md): labels/replacements persistiram; regra carregada foi aplicada ao chamar diretamente o filtro; status atualizado com runtime.
- [51 — diff de snapshots](51_SNAPSHOTS_DIFF_RUNTIME_CONTAINERS.md): escalar substituído detectado; mutações in-place simples não listadas no diff.
- O [mapa 06_VARIABLES/03](../06_VARIABLES/03_MAPA_CANAIS_PERSISTENCIA_URM.md) separa save nativo, arquivo `.urm`, persistent, settings global e snapshots.

**Ainda não comprovado:** renderização end-to-end de Choice com substituição de texto; interação visual completa dos modais de save/load. A persistência do singleton Snapshots em save nativo foi testada em dois processos no doc 53: no caso coberto, o objeto não foi restaurado.

### Continuação — TextRepl e identidade estrutural da Choice (2026-10-28)

O [documento 52](52_TEXTREPL_MENU_AST_FILTER_PATH.md) rastreia no SDK 7.4.11 `Menu.execute()` → `say_menu_text_filter` → tupla com índice AST original → processamento de menu → continuação do bloco. Isso confirma que o texto transformado não substitui o índice usado pela seleção. O teste runtime do doc 50 validou o callback chamado diretamente; renderização final na screen segue pendente.


### Continuação — persistência de Snapshots em save nativo (2026-10-28)

O [documento 53](53_PERSISTENCIA_SNAPSHOTS_SAVE_NATIVO.md) registra um teste do URM original em dois processos Ren'Py 7.4.11. O processo novo carregou o slot nativo e restaurou um valor de gameplay controle, mas o singleton `x52URM.Snapshots` permaneceu vazio. As tentativas anteriores com harness inválido foram excluídas. A explicação estática cruza o marcador `_constant` do store `x52URM` com o `ConstantStoreHandler` do URM e o processo de roots/log do SDK. A conclusão fica delimitada a este caminho e versão; exportação ou persistência por outra ação da interface não foi testada.
