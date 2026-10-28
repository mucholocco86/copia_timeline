# 22 — Runtime de Choice, edição de store e rollback no SDK 7.4.11

**Data:** 2026-10-16  
**Escopo:** validar em runtime a propagação de ChoiceReturn para alternativa com condição falsa e testar restauração de uma variável alterada durante uma interação.  
**Estado:** os dois contratos reduzidos passaram em fixture sintética; a integração integral da screen original do URM ainda não foi executada.  
**Proteções:** testes em cópia temporária do jogo the_question. Nenhum arquivo de wells/, wells_beta/, SDK ou fonte original do URM foi alterado.

## Fontes examinadas

Repositório mucholocco86/laborat-rio_renpy, branch main.

| Fonte | Símbolo/linhas | Evidência |
|---|---|---|
| renpy-7.4.11-sdk/renpy/test/testexecution.py | execute(), test_command() | Quando a testcase termina, o runner retorna sem encerrar o engine. |
| renpy-7.4.11-sdk/renpy/test/testast.py | _test.timeout; Assert, Label, Python | Timeout de teste parado é 5 s; asserções e Python são executados pelo loop de interação. |
| renpy-7.4.11-sdk/renpy/ast.py | Menu.execute(), L1639–1697 | Resultado não-None é usado como índice estrutural e aponta para o bloco AST. |
| renpy-7.4.11-sdk/renpy/exports.py | display_menu(), L1127–1319 | Resultado da interação passa por checkpoint(rv) e retorna ao Menu. |
| renpy-7.4.11-sdk/renpy/ui.py | ChoiceReturn.__call__(), aprox. L749–755 | Registra opção escolhida quando aplicável e retorna self.value. |
| renpy-7.4.11-sdk/renpy/exports.py | checkpoint(), L267; rollback(), L1690; quit(), L1879 | Checkpoint é delegado ao log; rollback fecha as mudanças pendentes; quit termina o engine. |
| renpy-7.4.11-sdk/renpy/python.py | RollbackLog, L1550; complete(), L1707; rollback(), L1945 | O log coleta deltas/snapshots, reverte entradas e reinicia o Context. |
| renpy-7.4.11-sdk/renpy/game.py | call_in_new_context() | A documentação da função diz que o novo contexto desativa rollback. |
| URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy | três testcases | Fixture sintética para Choice visível, condição falsa e edição/rollback. |

## Diagnóstico do runner

O runner de teste do SDK deixa o processo aberto depois de a testcase terminar: testexecution.execute() apenas retorna quando node é None. A fixture passou a invocar renpy.quit() após suas asserções.

Os primeiros testes forçados não chegavam à ação porque seus botões não estavam focáveis no ponto em que o runner tentava clicar. A tela modal passou a ser mostrada pelo script antes do Menu. Essa configuração passou no run 38946951166.

## Choice com condição falsa

**OBSERVADO EM RUNTIME — run 38946951166, job 117128365515:** baseline nativo e seleção forçada terminaram com exit=0. A testcase forçada só chama renpy.quit() após assert urm_probe_result == "forced-hidden". Assim, na fixture, a ação que chama ChoiceReturn devolveu o índice estrutural 1, e Menu.execute executou o bloco da alternativa declarada com if False.

Isso confirma o circuito reduzido: screen modal durante o Menu → ChoiceReturn(index) → valor de retorno da interação → Menu.execute → bloco AST da alternativa.

**Limite:** a fixture não carrega as screens/classes convertidas do URM. Prova o contrato estreito de seleção no SDK 7.4.11; não demonstra todo o processo de abertura, sensibilidade e projeção de dados do URM.

## Edição de variável e rollback

**CONFIRMADO NO SDK 7.4.11:** exports.rollback() verifica _rollback, Context.rollback e config.rollback_enabled, exceto quando force=True. Antes de restaurar, chama RollbackLog.complete(). Esse método fecha as deltas dos stores e os snapshots de objetos mutados. RollbackLog.rollback() percorre registros até o checkpoint solicitado, restaura as mudanças e o Context e reinicia a execução.

A primeira fixture de rollback falhou com “Couldn't find a place to stop rolling back”. A inspeção do estado mostrou por que o harness era inadequado: testes são executados durante o menu principal, em contexto criado por call_in_new_context(), onde o rollback é desativado. Checkpoint() não havia estabelecido uma fronteira utilizável nesse contexto. O run 38947615122 passou da falha de checkpoint, mas a asserção recebeu valor diferente de 10; aquela versão atribuía 10 imediatamente antes do checkpoint, dentro do período que o teste pretendia restaurar.

A fixture foi ajustada para:
1. registrar que o Context inicial da testcase tinha rollback=False;
2. habilitar Context.rollback somente na cópia descartável para simular contexto de gameplay;
3. manter 10 como valor inicial do store antes do checkpoint;
4. alterar a variável para 99 pela ação da screen;
5. avançar pela interação de pausa;
6. chamar rollback(force=True, checkpoints=1, label="urm_edit_rollback_verify");
7. verificar o valor no label de retorno.

**OBSERVADO EM RUNTIME — run 38947765822, job 117131138428:** baseline e escolha falsa passaram; o teste de edição/rollback terminou com exit=0. O log imprime ROLLBACK_VALUE_AT_VERIFY 10, e a asserção confirma o valor 10. Portanto, no contexto configurado da fixture, a atribuição de store 10→99 foi desfeita ao restaurar o checkpoint anterior.

**Limites:** a ação altera diretamente renpy.store.urm_rollback_value; não executa Var.setValue nem SetVarValue do URM. O rollback é iniciado por chamada de script com force=True, não pelo gesto manual do usuário na interface nativa. A fixture habilita Context.rollback explicitamente porque o runner usa contexto de menu principal. O teste demonstra reversibilidade do store e do checkpoint nativo nesse arranjo; não demonstra ainda os detalhes do StoreMonitor, avanço por várias Choices, rollback interativo do jogador, nem save/load.

## Artefatos e execuções

- Fixture inicial: 2fc71d411ce2266132d342ef61c121216ca078b7.
- Runner encerrado após assertions: 379d150512d7832fd9c61b59d8231f67a1c38585.
- Fixture final da Choice falsa: e103cbc5669523609b65a036628e73f67647059a.
- Fixture com primeiro teste de rollback: d81556607c2f4780455f541f6ccdd9daebd1d7e9.
- Workflow com etapa de rollback: db7f36550a27253c8923a3dc74e954b2f80af117.
- Fixture que modela Context.rollback=True e checkpoint ajustado: f53f3fbc9b414f040a4a4f700b0fca8a0ffb6afa.
- Fixture final com estado inicial antes do checkpoint: 1cf7c039bd2540a114f047ebc4ebb3f4553faf65.
- Run 38947312511: rollback falhou porque não encontrou ponto de restauração.
- Run 38947615122: rollback alcançou o label, mas a asserção não encontrou valor 10.
- Run 38947765822: **SUCCESS**; baseline, escolha falsa e edição/rollback passaram.

## Classificação e próxima etapa

| Afirmação | Classificação |
|---|---|
| ChoiceReturn pode devolver índice estrutural usado pelo Menu | **CONFIRMADO NO SDK 7.4.11** |
| A fixture executou alternativa marcada if False | **OBSERVADO EM RUNTIME**, run 38946951166 |
| O runner começa essa testcase em contexto com rollback desativado | **OBSERVADO EM RUNTIME** pela asserção da fixture e compatível com call_in_new_context() |
| Store alterado de 10 para 99 foi restaurado a 10 no checkpoint anterior | **OBSERVADO EM RUNTIME**, run 38947765822 |
| Var.setValue/SetVarValue do URM apresenta o mesmo resultado | **PENDENTE** de teste que use o circuito da fonte URM |
| A screen original do URM seleciona condição falsa e abre no contexto correto | **PENDENTE** de teste integrado com fonte convertida |
| Edição seguida de várias interações e rollback manual do jogador | **PENDENTE** |
| Relação dessa edição com save/load nativo e arquivo .urm | **PENDENTE** de matriz específica |

Próxima prioridade: reproduzir em fixture a semântica exata de Var.setValue/SetVarValue e depois executar edição → avanço por menu/dialogue → rollback nativo, sem usar force=True quando o cenário permitir. Em seguida, testar salvar/carregar após a edição.

## Extensão — reprodução reduzida de Var.setValue e SetVarValue

**OBSERVADO EM RUNTIME — run 38950917699, job 117141762569, commit da fixture `2152010526df150214c230b41dc96e18cd81c981`:** as três etapas do workflow terminaram com sucesso: baseline nativo, seleção da alternativa com condição falsa e edição/rollback.

A fixture agora contém uma reprodução mínima do caminho escalar inteiro observado em `classes/vars.rpy`: a ação `SetVarValue.__call__` chama `Var.setValue`; para o caso inteiro raiz, o método valida o tipo e executa uma atribuição ao nome em `renpy.store`. Após o valor inicial 10, a ação gravou 99; depois de avançar pela interação e executar rollback forçado para o checkpoint, o log apresentou `ROLLBACK_VALUE_AT_VERIFY 10`, e a asserção terminou com exit=0.

Isso é evidência de que a semântica reproduzida de edição escalar do URM participa do estado reversível do Ren'Py no contexto de teste. Não é ainda um teste de integração do módulo URM: a fixture copia o trecho relevante do código convertido, usa stubs para dependências (incluindo VarsStore/Search) e simplifica a construção do objeto Var. O caso cobre somente uma variável inteira raiz, editável e não congelada. Não cobre tipos/containers, variável filha, CreateVar, StoreMonitor, save/load ou gesto manual de rollback.

O rollback ainda é iniciado pelo script com `force=True`, e o contexto descartável habilita `Context.rollback` devido à limitação do runner de testes. Portanto o resultado não estabelece quando o rollback manual do jogador cruza a edição em uma sequência normal de menus.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| O fluxo reproduzido `SetVarValue → Var.setValue` alterou 10 para 99 no store | **OBSERVADO EM RUNTIME**, run 38950917699 |
| O rollback do checkpoint restaurou esse inteiro para 10 | **OBSERVADO EM RUNTIME**, run 38950917699 |
| O módulo original convertido do URM, carregado integralmente, tem o mesmo resultado em jogo real | **PENDENTE** de integração |
| Edição seguida de várias interações e rollback manual do jogador | **PENDENTE** |
| Persistência após save/load e efeitos de StoreMonitor/frozen | **PENDENTE** |

Próximo passo: preparar uma sequência de gameplay na fixture com edição, avanço por mais de uma interação e rollback nativo não forçado, registrando em qual interação o valor reaparece. Em seguida testar save/load sem misturar o arquivo `.urm` com o save nativo.


## Extensão — rollback elegível após duas interações de Choice

**OBSERVADO EM RUNTIME — run 38973243038, job 117216599068, fixture commit `babf6425462521343f7e00504087e7a7a06f6ab5`:** o teste executou novamente a edição reduzida por `SetVarValue → Var.setValue`, avançou por duas interações nativas de menu, e chamou `renpy.rollback(force=False, checkpoints=3, label=...)`. Os registros do runner foram:

- imediatamente antes do rollback: `ORDINARY_ROLLBACK_PRE 99 2`;
- gates de rollback: `ORDINARY_ROLLBACK_GATES True True True` (`store._rollback`, `Context.rollback`, `config.rollback_enabled`);
- depois do retorno ao label: `ORDINARY_ROLLBACK_AT_VERIFY 10 0`;
- a etapa terminou com exit=0, incluindo asserções de que o valor editado voltou a 10 e o marcador alterado pelas duas Choices voltou a 0.

Logo, nesta fixture, rollback pela API com `force=False` foi elegível e cruzou os dois checkpoints de menu até o checkpoint anterior à edição. A reversão abrangeu tanto a escrita escalar que reproduz o caminho URM quanto os efeitos de estado colocados nos blocos das duas Choices.

**Limite de interpretação:** o teste chama a API `renpy.rollback` pelo script depois das duas escolhas; não simula o jogador acionando a tecla ou botão de rollback da interface. O contexto do test runner foi habilitado manualmente no ambiente descartável porque ele entra por um contexto de menu principal com rollback desativado. O número `checkpoints=3` foi escolhido para atravessar as duas interações e alcançar o checkpoint marcado antes da edição. Portanto, a prova não determina ainda a UX/contagem de passos de rollback manual, nem integra as classes e screens completas do URM.

### Execução intermediária do workflow

O run 38973224110, commit `2c9024f90f963d2091c8b9a6bb4d95bff8cb839b`, falhou apenas na nova etapa porque o commit adicionou a etapa ao workflow antes de a fixture conter o testcase; o log diz `Testcase urm_edit_ordinary_rollback was not found.` O run de validação 38973243038 usou o commit seguinte, com fixture e workflow juntos, e passou todas as etapas.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| A edição reproduzida ficou em 99 após duas escolhas e a variável de rota chegou a 2 | **OBSERVADO EM RUNTIME**, run 38973243038 |
| Com rollback elegível e `force=False`, o valor voltou a 10 e a rota voltou a 0 | **OBSERVADO EM RUNTIME**, run 38973243038 |
| A chamada cruzou duas interações de Choice até checkpoint anterior à edição | **OBSERVADO EM RUNTIME** na fixture; compatível com seleção de checkpoints do SDK |
| A tecla/botão nativo do jogador produz a mesma contagem/posição em qualquer jogo | **PENDENTE** de teste de interação manual |
| O URM completo integrado tem o mesmo resultado, incluindo StoreMonitor e variáveis complexas | **PENDENTE** |

Próxima etapa: testar a interface de rollback nativa do Ren'Py via harness de entrada, ou construir uma sequência de rollback interativo que registre cada passo e o valor após cada retorno. Depois disso, a próxima dimensão da matriz é save/load nativo após edição, separando raízes de StoreDict, snapshots de containers revertíveis e metadados do arquivo .urm.


## Inspeção do harness para rollback por tecla

Após o run de rollback pela API, foi verificado se o test runner do SDK permite injetar a entrada nativa usada pelo jogador.

**CONFIRMADO NO SDK 7.4.11:**

- `renpy/test/testparser.py`, blob `dcade9a19bbf1abaad136d30820f0b96ee3301b3`, `parse_clause`: o testcase aceita a instrução `type` seguida por um keysym.
- `renpy/test/testast.py`, blob `fe2a5e93d408e11ff70dea96858297ebaf412173`, `Type.perform`: a instrução chama `renpy.test.testkey.down/up` para sintetizar as teclas.
- `renpy/test/testkey.py`, blob `fd5fd33444bdf2839919dcb52ef35da8e9bc8343`, `get_keycode`, `down`, `up`: o keysym `K_PAGEUP` é convertido em eventos SDL keydown/keyup.
- `renpy/common/00keymap.rpy`, blob `7806011325fa1942e6bdd65e802c4a59e1ba0921`: o mapa padrão associa `rollback` a `K_PAGEUP` (além de outras entradas).

Isso torna possível construir um próximo teste de entrada real pelo harness, sem chamar `renpy.rollback()` no script. Ainda é necessário provar runtime que a tecla sintética é entregue na interação correta, que o rollback é aceito no estado de menu/dialogue escolhido e quantos eventos são necessários para cruzar a edição. Nenhum resultado foi inferido apenas desta disponibilidade do mecanismo de teste.


## Resultado — tecla nativa de rollback via evento do harness

**OBSERVADO EM RUNTIME — run 38978993727, job 117235153584; fixture commit `30de2fa3d3d09e4e0d96301b354f618c647775c7`:** o testcase usou `type PAGEUP` enquanto o jogo estava na interação de diálogo após duas Choices. O test runner emitiu os eventos SDL da tecla Page Up; a underlay padrão do SDK associa o evento `rollback` a `renpy.rollback`, cujo argumento `force` padrão é False. Não houve chamada de rollback no script nessa prova.

Sequência registrada:

| Momento | Variável editada | Rota das duas Choices |
|---|---:|---:|
| Antes da primeira tecla | 99 | 2 |
| Depois de 1 evento Page Up | 99 | 2 |
| Depois de 2 eventos Page Up | 99 | 1 |
| Depois de 3 eventos Page Up | 10 | 0 |

A asserção final verificou valor 10, rota 0 e contexto de teste originalmente com rollback desativado; o testcase habilitou rollback no contexto descartável antes de iniciar a sequência. A etapa terminou com exit=0.

**Interpretação limitada:** o evento de rollback real do SDK foi exercitado pela entrada de teclado sintética do runner, e o estado observado voltou progressivamente através da sequência. O primeiro evento deixou os valores medidos iguais; os seguintes reverteram a rota e então cruzaram a edição. A sequência é compatível com checkpoints/estado de interação distintos, mas não atribuímos um destino interno específico ao primeiro evento sem instrumentação do log. Isso ainda não é um teste com teclado físico nem uma integração com as screens completas do URM.

Na primeira tentativa, o testcase usou `type K_PAGEUP`; o parser acrescenta `K_` ao nome informado e procurou `K_K_PAGEUP`. A falha foi somente de sintaxe do keysym. A forma correta no DSL é `type PAGEUP`; a repetição corrigida passou.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| O SDK 7.4.11 associa a tecla Page Up ao evento rollback pela underlay padrão, que chama `renpy.rollback` sem forçar | **CONFIRMADO NO SDK 7.4.11** |
| Após edição e duas Choices, eventos Page Up resultaram na sequência observada 99/2 → 99/2 → 99/1 → 10/0 | **OBSERVADO EM RUNTIME**, run 38978993727 |
| A entrada nativa sintética cruzou o estado de uma Choice por evento após o primeiro retorno observado | **OBSERVADO EM RUNTIME** nesta fixture; não generalizar a contagem |
| O teclado físico e as preferências/configurações de qualquer jogo produzem a mesma sequência | **PENDENTE** |
| O URM integrado, incluindo StoreMonitor e suas screens, segue o mesmo circuito | **PENDENTE** |

Com isso, a hipótese de que uma edição do store pode permanecer ativa durante o avanço e ser desfeita pelo rollback do jogador recebeu uma reprodução próxima do gesto nativo no SDK 7.4.11, ainda em fixture reduzida. A próxima prova prioritária passa a ser save/load nativo após a edição, incluindo variável-raiz e container revertível, mantendo o arquivo `.urm` separado.


## Resultado — save/load nativo após edição manual reduzida

**OBSERVADO EM RUNTIME — run 38979502224, job 117236768906; fixture/workflow commit `f230c151d7efd8c27aa2853f813c844e66e4fb3e`:** a reprodução reduzida de `SetVarValue → Var.setValue` editou `urm_rollback_value` de 10 para 99. O save nativo foi gravado nesse estado; depois o teste alterou o valor em memória para 123 e chamou `renpy.load("urm-probe-edit-roundtrip")`. O log do runner registrou:

```text
SAVELOAD_BEFORE_SAVE 99
SAVELOAD_BEFORE_LOAD 123
SAVELOAD_AFTER_LOAD 99
```

A testcase terminou com exit=0 e verificou `urm_rollback_value == 99` depois do load. Portanto, nesse cenário controlado, o save nativo conservou a edição manual já presente no estado salvo; carregar o slot substituiu o valor posterior 123 pelo valor salvo 99. Isso complementa — sem contradizer — a prova de rollback: a edição 10→99 pôde ser desfeita ao voltar a um checkpoint anterior, mas ficou incluída no estado quando o save foi feito após a edição.

**CONFIRMADO NO SDK 7.4.11 por inspeção estática:** `renpy.save` congela/serializa raízes do store junto com o RollbackLog; `renpy.load` restaura esses dados e chama `RollbackLog.unfreeze`, que reinicia o contexto do jogo. O resultado de runtime acima é consistente com esse caminho. A fixture usa um marcador de reentrada no módulo do test runner, fora dos stores serializados, para detectar que a continuação veio do load; isso impede a repetição da mutação 123 e evita o falso loop da primeira tentativa.

### Limites

- O teste usa uma variável inteira raiz e uma reprodução reduzida do código convertido, com stubs para dependências do URM; não carrega o módulo URM integral.
- O save é feito pelo script de teste após a ação sintética da screen. Não valida todos os instantes possíveis em que o usuário pode salvar durante uma interação real.
- A prova não cobre variáveis criadas, atributos/itens aninhados, containers revertíveis, variáveis congeladas, StoreMonitor nem alterações nos metadados próprios do arquivo `.urm`.
- O resultado não significa persistência fora do slot nativo: prova somente que a edição faz parte do estado serializado por esse save/load.
- O run anterior 38979350434 falhou por um marcador guardado no store do jogo, que também era restaurado pelo load e causava reentrada repetida. Esse run é falha do harness e não evidência contra a semântica de save/load.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| O save nativo guardou o valor 99 já editado, e o load restaurou 99 após uma mutação posterior para 123 | **OBSERVADO EM RUNTIME**, run 38979502224 |
| No SDK 7.4.11, save/load envolve raízes do store e RollbackLog | **CONFIRMADO NO SDK 7.4.11** |
| A alteração escalar reduzida do URM pode ser desfeita por rollback anterior e também incluída em save posterior à alteração | **OBSERVADO EM RUNTIME** nas fixtures de rollback (runs 38973243038/38978993727) e save/load (run 38979502224) |
| `.urm` armazena o estado completo da partida ou substitui o save nativo | **NÃO DEMONSTRADO**; os mecanismos são separados e essa conclusão não pode ser inferida |
| Criação de variáveis, mutações aninhadas, containers, frozen/monitor e URM integral têm o mesmo resultado | **PENDENTE** |

### Próxima etapa

Manter separados os dois eixos que já têm prova escalar: rollback de gameplay restaura uma edição ao cruzar o checkpoint anterior; save/load nativo restaura o valor que estava presente no instante do save. A próxima extensão de runtime deve cobrir um objeto/container revertível e uma variável criada/editada pela ação correspondente do URM reduzido. Depois, investigar se o StoreMonitor solicita checkpoint antes/depois da escrita e testar as operações de variável congelada. Não generalizar a semântica para arquivos `.urm` ou para o URM integral sem testes específicos.


## Resultado — mutação de lista revertível pela ação reduzida de adicionar item

**OBSERVADO EM RUNTIME — run 38979672209, job 117237325776; fixture commit a50858a554c236a5f2c632f66d4e2614ba0cbcb8, workflow atualizado no commit 9a08953e91321f8fefc05116d35a4c58b9b7a313:** o novo testcase reproduziu o caminho da tela URM_add_item: SetVarValue → Var.setValue, com overruleVarType="int" e operator="append", sobre uma lista declarada por literal Ren'Py. O teste avançou por duas Choices e chamou rollback elegível (force=False). O log registrou:

    CONTAINER_ROLLBACK_PRE [10, 20] 2
    CONTAINER_ROLLBACK_AT_VERIFY [10] 0

As asserções verificaram a lista restaurada para [10], a rota de volta a zero e o contexto de teste inicialmente sem rollback. A etapa terminou com exit=0.

**CONFIRMADO NO SDK 7.4.11 por inspeção estática:** literais de lista compilados pelo Ren'Py são transformados pelos construtores especiais em RevertableList; os mutators guardam um estado limpo no log corrente e Rollback.rollback() chama _rollback dos objetos coletados. O resultado runtime é consistente com esse caminho e mostra que, no fixture, o append feito pela ação reduzida participou do histórico restaurável, apesar de a raiz urm_rollback_list não ter sido substituída.

### Limites

- O teste reproduz o circuito de URM_add_item e SetVarValue com classes reduzidas; não carrega screens/classes originais do URM integralmente.
- O container é um literal compilado pelo Ren'Py. Não cobre listas/dicionários de biblioteca externa, objetos desserializados ou outras origens.
- A chamada de rollback é programática pela API com force=False; não foi enviada tecla Page Up neste caso.
- A prova cobre somente append de inteiro em lista. Chave de dicionário, edição/exclusão de índice, nested containers, objetos/atributos e containers congelados seguem pendentes.
- Não prova que StoreMonitor notifique ou detecte a mutação interna; o mecanismo nativo de snapshot reversível pode atuar independentemente do monitor.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| A ação reduzida de adicionar item mudou a lista de [10] para [10, 20] | **OBSERVADO EM RUNTIME**, run 38979672209 |
| Rollback elegível restaurou a lista para [10] e a rota 2 para 0 | **OBSERVADO EM RUNTIME**, run 38979672209 |
| Literais de lista compilados pelo Ren'Py 7.4.11 usam o mecanismo RevertableList | **CONFIRMADO NO SDK 7.4.11** |
| A mutação interna da lista foi desfeita por snapshot de objeto, não por substituição da raiz | **INFERÊNCIA sustentada** pelo código de fixture e pelo mecanismo estático do SDK; o runtime comprova o resultado, mas não instrumentou o objeto/log diretamente |
| Toda coleção encontrada pelo URM é revertível ou observada pelo StoreMonitor | **PENDENTE / não demonstrado** |

O resultado fecha uma parte importante do circuito: tanto a atribuição de escalar raiz (10→99) quanto uma mutação interna de lista (append) puderam ser revertidas pela fixture, desde que a variável/objeto estivesse no estado Ren'Py revertível e o rollback atravessasse o checkpoint anterior. A evidência ainda é reduzida e não equivale a validar toda a implementação URM.

### Continuação da matriz

A próxima prioridade prática é testar a edição de chave/índice e exclusão de item, depois separar save/load de container do rollback. Em paralelo, investigar CreateVar para confirmar ou refutar em runtime a rejeição de valores falsy no código convertido. Em seguida, introduzir instrumentação isolada para medir quando o StoreMonitor observa uma edição de screen e se sua solicitação de checkpoint muda a contagem/destino do rollback.


## Resultado — edição de item de dicionário e rollback

**OBSERVADO EM RUNTIME — run 39013297447, job 117340165072; fixture final commit 6664efa6a611b7d38277ae54875f58de4222f9ce; workflow commit 8a3735791f08213957f5008072caa73a01f66cb0:** o fixture estendeu a reprodução reduzida de Var.getChild para resolver uma chave de dicionário e aplicou SetVarValue com overruleVarType="int" sobre o item "a". Depois de editar de 10 para 20 e avançar por duas Choices, o rollback elegível com force=False restaurou o item a 10 e a rota a 0. Os logs:

    DICT_ROLLBACK_PRE {u'a': 20} 2
    DICT_ROLLBACK_AT_VERIFY {u'a': 10} 0

A etapa terminou com exit=0 e asserções sobre o conteúdo do dicionário, a rota e o estado inicial do contexto passaram.

**CONFIRMADO NO SDK 7.4.11 por inspeção estática:** literais dict transformados pelo compilador usam RevertableDict. A atribuição a uma chave é mutação do objeto; o log de rollback registra e restaura os objetos mutáveis alcançáveis. O runtime observado é consistente com esse mecanismo.

### Limites e classificação

- **OBSERVADO EM RUNTIME:** no fixture, o item "a" mudou de 10 para 20 e voltou a 10 ao cruzar o checkpoint anterior; a rota 2 voltou a 0.
- **CONFIRMADO NO SDK 7.4.11:** o compilador transforma literais de dicionário para o mecanismo RevertableDict.
- **INFERÊNCIA sustentada:** a restauração ocorreu pelo snapshot do objeto revertível; o fixture não instrumentou Rollback.objects nem registrou type(obj) durante a mutação.
- O teste cobre apenas um dicionário de literal Ren'Py, chave string simples e valor inteiro. Chaves complexas, containers externos, objetos filhos, exclusão de chave e integração com StoreMonitor continuam pendentes.
- A ação e classes continuam sendo reprodução reduzida; não se carregaram as screens/classes originais completas do URM.

Com as provas dos runs 38979672209 e 39013297447, a matriz de runtime cobre agora três tipos de mutação editável pela via reduzida do URM: atribuição de escalar raiz, append em lista e substituição de valor em chave de dicionário. Nos três casos, rollback elegível depois de duas Choices restaurou o estado anterior e também desfez os marcadores de rota das Choices. Isso não prova uniformidade para todos os tipos ou para qualquer estado encontrado pelo pesquisador do URM.

### Próxima etapa

Testar remoção de item (del em lista e del de chave em dicionário) pela semântica de Var.delete, depois save/load de lista/dicionário. Em paralelo, avaliar CreateVar, incluindo a hipótese estática de rejeição de valores falsy, e planejar um teste isolado do instante em que StoreMonitor coleta deltas e solicita checkpoint.


## Resultado — exclusão de índice de lista e chave de dicionário

**OBSERVADO EM RUNTIME — run 39013412540, job 117340518148; fixture commit ee19f952238c3da6f60e0a60505c25028df0b4da, workflow commit 22025181fea6c2714133912ee41e8997e9ff4509:** a fixture adicionou uma reprodução limitada de Var.delete para caminhos filhos e executou a exclusão de um índice de lista e de uma chave de dicionário por ações de screen. Após duas Choices, antes do rollback o estado observado foi lista [20], dicionário com a chave b e rota 2. Depois de rollback force=False, o estado voltou à lista [10, 20], ao dicionário com as chaves a e b, e rota 0:

    DELETE_ROLLBACK_PRE [20] {u'b': 20} 2
    DELETE_ROLLBACK_AT_VERIFY [10, 20] {u'a': 10, u'b': 20} 0

As asserções passaram e a etapa terminou com exit=0.

**CONFIRMADO NA FONTE URM convertida:** Var.delete percorre o caminho da variável e, para itens de lista/dicionário, usa del sobre o container.  
**CONFIRMADO NO SDK 7.4.11:** os tipos revertíveis envolvem delitem com mutator e o rollback restaura snapshots dos objetos mutados.  
**OBSERVADO EM RUNTIME:** esta reprodução de exclusão de dois filhos foi desfeita quando o rollback cruzou o checkpoint anterior.

### Limites

- A classe Var.delete na fixture é uma reprodução simplificada para caminhos com uma raiz e um único índice/chave. Não cobre a lógica completa de parsing, objetos e stores múltiplos do URM.
- Os containers são literais compilados pelo Ren'Py; o resultado não se estende automaticamente a containers externos.
- A prova não instrumenta o RollbackLog nem o tipo concreto em execução; associa o resultado runtime ao mecanismo de objetos revertíveis por meio da fonte e da implementação SDK.
- O rollback foi chamado pela API com force=False depois de duas Choices. Este caso não usa tecla Page Up.
- Continua pendente validar a classe Var.delete original integrada, condições de frozen/monitor e save/load de containers após exclusão.

### Matriz runtime atualizada

| Mutação reduzida | Estado antes da mutação | Estado após rollback | Evidência |
|---|---|---|---|
| Atribuição escalar raiz | 10 → 99 | 10 | runs 38973243038 e 38978993727 |
| Append em lista | [10] → [10, 20] | [10] | run 38979672209 |
| Edição de chave dict | a: 10 → 20 | a: 10 | run 39013297447 |
| Exclusão de índice e chave | lista [10,20]/dict {a,b} → lista [20]/dict {b} | lista [10,20]/dict {a,b} | run 39013412540 |

Esses casos demonstram reversibilidade de quatro operações na fixture reduzida: atribuição de raiz, append, sobrescrita de chave e exclusão de itens. Não estabelecem a reversibilidade de qualquer objeto ou de todos os caminhos de dados do URM.

### Próxima etapa

A sequência agora deve avançar em duas dimensões separadas: (1) save/load nativo com lista e dicionário mutados, para verificar se os containers atuais entram nas raízes serializadas; (2) CreateVar para testar runtime da rejeição de valores falsy deduzida da fonte convertida. Depois, construir uma instrumentação que observe StoreMonitor sem confundir seus checkpoints solicitados com os snapshots nativos que já demonstraram reversão.


## Resultado — CreateVar rejeita valores convertidos falsy na reprodução runtime

**OBSERVADO EM RUNTIME — run 39064784962, job 117490042033; fixture final commit 5ebd99072cc7fd77c31444b3c4cdccc9f10d90bc; workflow commit 157d333b7cc035c6f00374b361dda54ee50f9158:** o testcase reproduziu a classe CreateVar convertida, manteve a screen ativa para receber as mensagens de erro e tentou criar três valores falsy, além de um controle positivo. A saída foi:

    0x52: No valid value for urm_created_zero (varType: int)
    0x52: No valid value for urm_created_false (varType: boolean)
    0x52: No valid value for urm_created_empty (varType: string)

As asserções verificaram que os nomes dos três valores não foram criados no store; o controle inteiro 7 foi criado com sucesso. A etapa terminou com exit=0. A execução completa do workflow também repetiu com sucesso as provas anteriores de Choice, rollback, container deletion e save/load.

**CONFIRMADO NA FONTE URM convertida:** CreateVar converte os tipos e depois condiciona a atribuição a if settableValue. Portanto int 0, boolean False, float 0.0 e string vazia não atravessam esse ramo; valores truthy válidos podem ser atribuídos.  
**OBSERVADO EM RUNTIME:** a reprodução reduzida recusou int 0, boolean False e string vazia e aceitou int 7.

### Limites

- Runtime usa uma reprodução da classe convertida com stubs para Search/VarsStore e uma screen de teste; não executa a classe original carregada do URM.
- Float 0.0 não foi incluído neste testcase, embora a mesma condição de truthiness e a conversão correspondente indiquem o mesmo resultado na fonte.
- Não foram testados overwrite=True, nome já existente, frozen/unfreeze, valores numéricos malformados, callbacks de falha da interface nem persistência/save/rollback após criar.
- A fonte convertida não é garantia de equivalência perfeita ao binário/original; conclusão sobre o URM completo ainda exige integração.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| CreateVar convertido usa truthiness depois da conversão | **CONFIRMADO NA FONTE URM CONVERTIDA** |
| A reprodução runtime rejeitou int 0, boolean False e string vazia | **OBSERVADO EM RUNTIME**, run 39064784962 |
| A reprodução runtime criou o inteiro truthy 7 | **OBSERVADO EM RUNTIME**, run 39064784962 |
| A classe original do URM, em um jogo-alvo, sempre rejeita esses valores | **PENDENTE** de integração/runtime original |
| Float 0.0 tem o mesmo resultado runtime | **HIPÓTESE forte pela fonte**, ainda sem caso de teste próprio |

Esse resultado esclarece um comportamento da interface de criação, mas não deve ser generalizado para edição com SetVarValue: os fluxos são distintos. A matriz de edição/rollback de variáveis e containers permanece independente da regra de criação.

### Próxima etapa

Seguir para persistência de containers em save/load nativo, separando lista e dicionário, depois testar criação de variável com rollback e save/load. Em seguida, investigar o instante do StoreMonitor: quando a screen altera o store, quando o callback Python executa e quando a solicitação de checkpoint chega a RollbackLog. Essa cronologia deve ser medida sem atribuir ao monitor as reversões que já são explicadas pelos deltas/snapshots nativos.


## Resultado — save/load nativo de lista e dicionário já editados

**OBSERVADO EM RUNTIME — run 39064935980, job 117490480797; fixture commit 9b578720e460134ccd927b77d5dfa8ff7b7a6398; workflow commit 57296517dbba58d180a33f5bb8b59841ddeacc0a:** a fixture alterou uma lista e um dicionário por ações reduzidas equivalentes a URM SetVarValue. O estado foi salvo quando a lista era [10, 20] e o dicionário {a: 20}. Depois o teste mutou os mesmos objetos em memória para [10, 20, 30] e {a: 30}, e carregou o save nativo. Logs:

    CONTAINER_SAVE_BEFORE_SAVE [10, 20] {u'a': 20}
    CONTAINER_SAVE_BEFORE_LOAD [10, 20, 30] {u'a': 30}
    CONTAINER_SAVE_AFTER_LOAD [10, 20] {u'a': 20}

As asserções confirmaram que o load devolveu a lista e o dicionário ao conteúdo presente no instante do save. A etapa terminou com exit=0.

**CONFIRMADO NO SDK 7.4.11 por inspeção estática:** save congela e serializa roots e RollbackLog; os valores raiz do store mantêm referências para os containers, e os objetos alcançáveis entram no grafo serializado.  
**OBSERVADO EM RUNTIME:** na fixture, o save/load nativo restaurou tanto uma lista revertível mutada quanto um dicionário revertível mutado para o estado gravado.

### Limites

- São containers literais compilados pelo Ren'Py e uma reprodução reduzida das ações URM; não se carregou a implementação original integral.
- O teste não instrumentou roots, pickle ou RollbackLog internamente. Confirma o resultado observável no runtime, não os detalhes byte-a-byte do save.
- Não cobre objetos externos, containers não revertíveis, estruturas aninhadas, aliases/referências compartilhadas, save durante uma tela real do URM, nem interação com arquivo .urm.
- Não se deve concluir que todo valor achado por Search seja serializável, alcançável ou restaurável do mesmo modo.

### Classificação atualizada

| Afirmação | Classificação |
|---|---|
| Save nativo após editar lista/dict manteve [10,20] e {a:20}; após alterações posteriores, load restaurou esses conteúdos | **OBSERVADO EM RUNTIME**, run 39064935980 |
| O SDK serializa roots junto com o RollbackLog e grafo alcançável | **CONFIRMADO NO SDK 7.4.11** |
| A edição de containers na reprodução reduzida pode ser revertida por rollback anterior e preservada no estado salvo por save posterior | **OBSERVADO EM RUNTIME** nos runs 38979672209, 39013297447 e 39064935980 |
| Isso prova persistência dos metadados .urm ou serialização de qualquer objeto pesquisável | **NÃO DEMONSTRADO** |

### Síntese da matriz de estado

No cenário reduzido, a mesma classe geral de estado editado pode ter dois destinos dependendo da operação nativa:

- **Rollback para checkpoint anterior à mutação:** restaura valores escalares e alterações de RevertableList/RevertableDict, como mostram as provas anteriores.
- **Save depois da mutação, seguido de load:** restaura os valores/containers que existiam no instante do save, em vez de apagar a edição.

Isso sustenta a distinção do usuário entre alteração ativa no estado do jogo, reversível por rollback, e inclusão dessa alteração no estado serializado quando se salva depois. A conclusão é limitada às reproduções e tipos testados; não demonstra equivalência da integração URM completa.

### Próxima etapa

A cronologia do StoreMonitor continua sem prova de runtime. O próximo experimento deve instrumentar a sequência exata: ação de screen altera store/container; interação seguinte executa nó Python; callback python_callbacks do URM é chamado; Context.force_checkpoint é transferido ao RollbackLog; rollback/save fecha o registro. Compare com a mesma sequência sem o monitor e não atribua ao monitor a reversão nativa já observada.

## Atualização de cobertura — 2026-10-28

O estado do cabeçalho corresponde à primeira fase do runner, em 2026-10-16. Os contratos reduzidos deste documento continuam úteis para isolar o SDK. As pendências de integração com URM original foram parcialmente cobertas depois: docs [36](36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md), [38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md), [41](41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md)–[47](47_SAVE_LOAD_CHOICE_PROCESSO_NOVO.md) exercitam telas/classes originais em jogo descartável, rollback e save/load. Docs [49](49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md)–[51](51_SNAPSHOTS_DIFF_RUNTIME_CONTAINERS.md) cobrem persistência de stores e snapshots.

Isso não fecha a integração visual de Gamesaves, o clique físico do hyperlink CodeView, o render final de substituições de texto, nem toda mutação de variável/container. Consulte cada documento posterior para a fronteira de evidência; o cabeçalho original é histórico, não o status geral atual.
