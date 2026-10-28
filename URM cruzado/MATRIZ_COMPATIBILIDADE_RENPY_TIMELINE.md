# Matriz de compatibilidade: Timeline × Ren’Py 6.99.4 / 7.4.11 / 8.5.3

**Data:** 2026-10-28  
**Referência de código do Timeline beta:** `mucholocco86/timeline`, commit `fd0259853f4351bf6528ccbe815b5da044219a86` (cópia beta atual no momento desta leitura).  
**SDKs:** fontes do laboratório no commit `05ceffdece80f9039328f8ccf5b921b0574bc982`.

Este relatório cruza o fluxo atual do Timeline com as três gerações. Ele separa leitura estática, cobertura já existente de CI e validação runtime. Não afirma que o Timeline passou em runtime nos três SDKs.

## Síntese

Há um contrato estrutural comum entre as três versões: o AST do Ren’Py preserva o índice original da alternativa e usa o valor que retorna da interação para selecionar o bloco AST. A interface pode filtrar ou ocultar opções, portanto a posição na tela e o texto não substituem a identidade estrutural da alternativa.

A implementação do Timeline tira proveito desse índice, mas também restaura um snapshot construindo um `RollbackLog` sintético e chamando `unfreeze()`. Essas classes e campos são internos, mudaram de módulo e de forma entre versões, e sua compatibilidade não fica provada apenas porque o arquivo compila.

## Contratos do SDK que afetam o Timeline

| Mecanismo | 6.99.4 | 7.4.11 | 8.5.3 | Implicação |
|---|---|---|---|---|
| AST `Menu` | `renpy/ast.py`; itens usam tuplas `(label, condition, block)`; Menu.execute passa índice original para alternativa com bloco e, ao receber o valor, chama o primeiro nó do bloco. | Mantém o índice original; acrescenta caption, argumentos de menu/itens e propriedade de rollback. Evidência URM estática e runtime documentada para fluxos específicos. | Mantém o índice AST e encaminhamento ao bloco; adiciona tipos/argumentos e múltiplos filtros de texto. | Índice estrutural, não índice visual nem texto, é a âncora portável para Choices. |
| Classe `Rollback` | Em `renpy/python.py`, versão 3; contém contexto, objetos reversíveis, checkpoint, stores, random/forward. | Em `renpy/python.py`, versão 5; estados adicionais para checkpoint/fixed rollback. | Em `renpy/rollback.py`, versão 5; campos adicionais, incluindo `not_greedy`, `fixed` e suspensão de checkpoint. | A construção manual de uma entrada pode depender de campos com diferenças de versão. |
| `RollbackLog` | Em `renpy/python.py`, versão 4; `begin()` sem argumento `force`; rollback e freeze/unfreeze ficam no mesmo módulo. | Em `renpy/python.py`, versão 5; ciclo de deltas/checkpoints evoluído, com `force_checkpoint` e mais estado. | Movido para `renpy/rollback.py`, versão 7; `begin(force=False)`, rollback_core/unfreeze_core e fluxo de exceção de unfreeze. | A seleção do módulo via fallback `renpy.rollback` → `renpy.python` é necessária, mas não garante compatibilidade semântica. |
| `Context.rollback_copy()` | Copia pilhas de chamada/retorno/dinâmica e nó atual; conjunto de campos mais antigo. | Acrescenta estado de execução anormal e pilha associada. | Preserva esses campos e acrescenta estado de interação. | Restaurar somente o rótulo atual não basta; pilhas e contexto devem continuar coerentes. |
| `RollbackLog.unfreeze()` | Descongela diretamente: instala o log, limpa/restaura stores e inicia o rollback de carga. | Também executa a rotina de descongelamento diretamente, com inicialização de tradução no percurso. | `unfreeze()` verifica se existe ponto válido e lança `UnfreezeException`; o trabalho real ocorre em `unfreeze_core()`. | Mesmo nome e parâmetros públicos, caminho de execução diferente. Testar exceções e retomada é essencial. |

### Evidência detalhada

- **6.99.4:** `renpy/ast.py` (`Menu.execute`); `renpy/execution.py` (`Context.rollback_copy`); `renpy/python.py` (`Rollback`, `RollbackLog`, checkpoints, freeze/unfreeze); `renpy/loadsave.py`.
- **7.4.11:** `renpy/ast.py`, `renpy/execution.py`, `renpy/python.py`; documentação URM, especialmente 34–42 e `06_RENPY_COMPATIBILITY/02_SDK_SAVELOAD_URM_PERSISTENCIA.md`.
- **8.5.3:** `renpy/ast.py`, `renpy/execution.py`, `renpy/rollback.py`.

Os números de versão serializados acima pertencem às classes do SDK e servem para identificar evolução interna. Não são garantia de que objetos sintéticos montados pelo Timeline sejam aceitos por todas as versões.

## Como o Timeline atual atravessa essa fronteira

No beta inspecionado:

1. Antes de um menu, `timeline_runtime.rpy` registra o nó e associa opções a índices AST estruturais.
2. O snapshot registra `get_roots()` e `context().rollback_copy()`; o contexto pode exigir cópia profunda de `info`, pois a cópia nativa do contexto é superficial.
3. Ao voltar a um menu, `backend/tl_state.rpy` constrói um `RollbackLog` novo e uma entrada `Rollback` sintética, define checkpoints/campos e chama `unfreeze(roots, label="_after_load")`.
4. Se não existe snapshot utilizável, o fluxo alternativo reproduz escolhas anteriores e deixa a seleção-alvo para o menu real do jogo.
5. O wrapper de menu decide quando retornar escolhas registradas durante a reprodução e quando deixar a tela nativa aparecer.

Isso sustenta uma separação útil: o card do Timeline escolhe **qual Menu revisitar**; a interação do jogo deve continuar a escolher e executar o bloco AST. O risco está em reconstruir a fronteira do menu ou o contexto incompletamente, especialmente quando o jogo tem menus aninhados, condicionais, chamadas, variáveis alteradas entre menus ou comportamento após rollback comum.

## URM como referência funcional do ciclo de Choice

O URM é a referência de comportamento para esta revisão. O ponto útil não é copiar sua tela: é preservar o contrato com o Ren’Py observado na documentação de análise.

1. **Descobre a Choice no estado real do motor.** O URM parte de `renpy.game.context().current`, resolve o nó pela AST e confirma que ele é um `renpy.ast.Menu`. Percorre `Menu.items` conservando o índice estrutural original; visibilidade da condição é informação separada.
2. **A interface projeta essa Choice.** Ao selecionar, o URM limpa `rollback_is_fixed` quando necessário e devolve `renpy.ui.ChoiceReturn(value, index)()`. O valor identifica a alternativa; o `Menu.execute()` do Ren’Py encaminha para o bloco AST correspondente.
3. **O motor executa o bloco e mantém o histórico.** O URM não chama manualmente os nós `Python`, `Call` ou `Jump` do bloco escolhido. Checkpoints, deltas, contexto e rollback continuam no `RollbackLog` nativo.
4. **A reescolha acontece dentro do circuito nativo.** Os testes integrados documentados mostram a tela do URM aberta durante fixed rollback; depois da seleção, o jogo executa o novo ramo e rollback posterior restaura rota e variáveis no roteiro testado.

Referências mais diretas na cópia documental: [fluxo geral](URM_REVERSO/04_CHOICES/01_FLUXO_CHOICE_ROLLBACK.md), [retorno por ChoiceReturn](URM_REVERSO/04_CHOICES/04_CHOICE_RETURN_ROLLBACK_7_4_11.md), [microciclo do menu](URM_REVERSO/04_CHOICES/05_MICROCICLO_INTERACAO_ROLLFORWARD.md), [teste integrado de reescolha](URM_REVERSO/04_CHOICES/36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md), [rollback após opção condicional falsa](URM_REVERSO/04_CHOICES/42_ROLLBACK_APOS_CHOICE_CONDICAO_FALSA.md) e [rollback da condição dinâmica](URM_REVERSO/04_CHOICES/44_ROLLBACK_VARIAVEL_CONDICAO_CHOICE.md).

### Diferença concreta no caminho atual do Timeline

| Etapa | URM de referência | Timeline beta atual |
|---|---|---|
| Identificar opção | Lê o `Menu` ativo da AST e mantém o índice original de `Menu.items`. | Também registra `option_ast_indices`; esta parte segue o contrato estrutural. |
| Voltar ao menu | O Ren’Py já está no contexto restaurado pelo rollback nativo; o URM chama a interação de Choice e devolve `ChoiceReturn`. | Tenta usar snapshot de `get_roots()` + `context().rollback_copy()`; depois constrói um `RollbackLog` novo, com uma única entrada sintética, e chama `unfreeze()`. Se não houver snapshot, carrega um save e seleciona automaticamente as escolhas anteriores durante o replay. |
| Executar a alternativa | `ChoiceReturn` devolve o índice; `Menu.execute()` executa o primeiro nó do bloco. | Na escolha-alvo, deixa a tela normal do jogo aparecer. No replay de menus anteriores, o wrapper chama o valor/ação guardado para atravessar o caminho. |
| Rollback após reescolha | Os documentos registram testes integrados de fixed rollback, reescolha e rollback de variáveis/rota no percurso testado. | Os testes atuais verificam a montagem do log sintético por monkeypatch; não executam o ciclo real de restaurar, escolher outro ramo e reverter esse ramo em cada SDK. |

A diferença de maior risco é **substituir o histórico nativo por um log sintético de uma entrada**. O snapshot tenta preservar roots e contexto, mas o log novo não preserva a sequência original de deltas e checkpoints. Além disso, a captura pode alterar `ctx.current` para o label envolvente quando ele está serializado como tupla. Esses fatos são observados no código e são candidatos a explicar a perda de continuidade do rollback; ainda precisam de um teste runtime que prove a relação causal.

O campo `_rollback_id` é registrado no nó de histórico, mas no código atual inspecionado não é usado para restaurar o ponto; `RollbackToIdentifier` aparece apenas no comentário junto à captura. Isso também precisa entrar na comparação, pois o Timeline já guarda um identificador que pode ser importante para voltar pelo log original sem reconstruí-lo.

### Próximo teste orientado pelo URM

Antes de trocar a implementação, reproduzir uma fixture mínima nos três SDKs, com o mesmo roteiro do modelo URM: escolha A/B nativa, alteração de variável no ramo, retorno ao Menu, escolha de outro ramo, avanço e rollback posterior. Comparar o Timeline atual com a sequência funcional documentada para o URM, registrando em cada marco o nó AST corrente, label/contexto, pilhas de chamada, rota/variáveis, entradas do log, `rollback_is_fixed`, `rollback_limit` e roll-forward.

Os critérios de sucesso são comportamentais: a escolha-alvo aparece no ponto certo; o bloco novo executa uma vez; nenhum diálogo anterior ao alvo é repetido; rollback posterior restaura a rota e variáveis esperadas; o fluxo continua válido após Shift+R. Lint sozinho não cobre esses critérios.

## Jogos do laboratório: padrões de escolha que pressionam o Timeline

A leitura estática dos quatro projetos fornecidos mostra que a palavra “choice” cobre estruturas diferentes. Estes casos ajudam a desenhar testes de replay sem presumir que todo jogo usa a mesma forma de menu.

| Projeto e arquivo examinado | Estrutura observada | Consequência para captura e retorno |
|---|---|---|
| [MyDorm 0.32.4 — `scripts/c32/c32.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/MyDorm-v0.32.4-Season4-Chapter5-pc/game/scripts/c32/c32.rpy) e [tela `choice`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/MyDorm-v0.32.4-Season4-Chapter5-pc/game/modules/screens/Dialogue/choice.rpy) | O capítulo contém menus aninhados e condicionais, flags de rota, chamadas e escolhas com metadados de walkthrough. A tela percorre `items`; títulos, manchetes e subtítulos são linhas auxiliares, e os botões reais executam `choice.action`. | A posição visual/atalho da opção não identifica seu índice no AST: itens auxiliares não são escolhas e podem alterar a numeração exibida. Associar o retorno à ação/nó AST original e restaurar o contexto de chamadas é essencial. O MyDorm já era fixture de lint; agora também entra no conjunto de casos da matriz ampliada. |
| [Intertwined 0.16 — `episode_3.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/Intertwined-0.16-pc/game/episode_3.rpy) e [`choice_tracker.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/Intertwined-0.16-pc/game/scripts/choice_tracker.rpy) | O episódio examinado contém 21 nós `menu`, incluindo menus aninhados, ramos condicionais, mudanças de flags/pontos e saltos para labels. O rastreador do próprio jogo localiza o nó de menu pelo arquivo/linha e cria uma impressão digital a partir do label e das legendas. | A reescolha precisa restaurar o estado antes do menu, depois executar o ramo escolhido uma única vez. Um nome de label ou texto de opção isolado não representa necessariamente uma instância única do menu. O rastreador do jogo é uma referência de identificação, não substitui a identidade AST nem prova que replay está correto. |
| [Godson — `5 events/release 1/intro.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/Godson-pc/game/5%20events/release%201/intro.rpy) | O arquivo examinado contém 67 nós `menu`, vários níveis de aninhamento (até sete níveis no trecho medido), chamadas e saltos, além de mudanças de variáveis de rota. | É um caso forte para verificar se o replay preserva a pilha dinâmica e distingue menus de mesmo texto em pontos diferentes; testes só com menus planos não cobrem isso. |
| [Him 0.5.0 — `is_scenes.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/Him-0.5.0-pc/game/is_scenes.rpy) e [`custom_screens.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/JOGOS%20PARA%20TESTES/Him-0.5.0-pc/game/custom_screens.rpy) | Nos arquivos de cenas interativas examinados, não há nós `menu:`; há chamadas a telas próprias e botões com ações `Jump(label)`. O arquivo de cenas contém 163 `call screen`; o arquivo de telas contém 27 chamadas a telas e muitas ações de salto. | Esses pontos não passam pelo wrapper de `renpy.exports.menu`. O Timeline baseado apenas no AST `Menu` não os verá como escolhas. Eles exigiriam uma integração específica com as telas/labels do jogo; não devem ser tratados como falha do replay de menus AST. |

### Casos que a próxima verificação deve distinguir

1. **Escolha Ren’Py comum:** voltar ao nó-alvo e deixar o menu nativo executar a opção escolhida.
2. **Menu com linhas auxiliares e filtros:** preservar a identidade do item original mesmo que a interface acrescente títulos, esconda itens ou altere a numeração apresentada.
3. **Menu aninhado/condicional:** reproduzir o caminho até o menu-alvo, restaurar flags e pilha corretas e evitar repetir diálogos anteriores ao alvo.
4. **Interface própria baseada em telas:** identificar separadamente chamadas a telas e ações `Jump`; não inferir que são menus AST nem interceptá-las com uma alteração genérica no wrapper.
5. **Rollback comum depois da reescolha:** validar que a escolha executada e os pontos de rollback continuam coerentes, sem replay duplicado ou avanço para outro menu.

A contagem acima é de leitura estática dos arquivos citados, não de execução do jogo com Timeline. Ela orienta os cenários; o resultado PASS/FAIL só pode vir de execução nos SDKs e nos jogos.

## Workflow de compatibilidade já presente

O arquivo `.github/workflows/timeline-sdk-compat.yml` já contém uma matriz para a branch principal:

- **3 SDKs:** 6.99.4, 7.4.11 e 8.5.3;
- **8 destinos de projeto:** fixture `the_question` nos três SDKs e sete jogos reais (Nephilim 0.6.9, Thief of Hearts Part 1, Guilty Pleasure 0.65, MyDorm 0.32.4, Intertwined 0.16, Godson e Him 0.5.0);
- **24 pares SDK × jogo/fixture** no total (3 fixtures do SDK + 7 jogos reais × 3 SDKs);
- compara lint do jogo original com lint de uma cópia descartável contendo o beta;
- remove caches/compilados nas cópias e confirma que scripts do projeto de origem não foram alterados;
- se o jogo original falha no SDK escolhido, marca aquele par como inconclusivo para a compatibilidade do Timeline.

### O que esse workflow comprova

Quando o baseline e o beta passam, ele dá evidência forte de que o conjunto de scripts/screens do beta compila e inicializa no lint desse SDK e projeto, sem regressão detectável pelo lint.

### O que ele não comprova

O workflow não executa `_tl_run_tests()` nem simula abrir o Timeline, selecionar um card, restaurar um snapshot, escolher uma opção, avançar, usar rollback comum, refazer a escolha ou pressionar Shift+R. O arquivo `timeline_tests.rpy` contém verificações de estrutura e de funções com stubs, mas sua execução depende de ser chamada dentro do Ren’Py e não está conectada a esse workflow. Portanto, a matriz CI existente é uma boa barreira de compilação; não fecha o problema de replay/rollback sem testes runtime.

O workflow foi ampliado no commit `16eaaab2fce2583587bed506aee4ec15f82bc721` para incluir os três jogos adicionais. A conexão GitHub não retornou status/check run para os commits desta atualização; portanto, a matriz está configurada e versionada, mas não vou tratar a compilação como executada até haver um resultado de Actions disponível. Mesmo verde, esse workflow continua sendo apenas lint e inicialização, sem execução interativa das escolhas.

## Plano de teste runtime necessário antes de mexer no replay

Usar cópias descartáveis do projeto e executar em cada SDK:

1. **Compilação e inicialização:** baseline vs beta, conservando os resultados do workflow.
2. **Menu simples:** duas opções, registrar índice AST, escolher, voltar pelo Timeline e confirmar menu e ramo.
3. **Menu condicional/aninhado:** condição variável, opção oculta e segundo menu; repetir a escolha e validar o primeiro diálogo após ela.
4. **Estado e contexto:** validar variáveis, objetos rollbackáveis, pilhas de chamada/retorno, label/contexto corrente, cena e roll-forward após a restauração.
5. **Ciclo após reescolha:** avançar alguns diálogos, usar rollback normal, voltar à escolha, refazê-la e comparar com execução nova do jogo.
6. **Reinício de script:** repetir o salto e a reescolha após Shift+R.
7. **Fallback:** remover/inutilizar snapshot de forma controlada e testar o replay de compatibilidade; conferir que ele chega ao menu certo e não pula diálogos.

Cada resultado deve ser marcado como PASS, FAIL ou INCONCLUSIVO, distinguindo falha do baseline do jogo de regressão introduzida pelo Timeline. Um lint verde nunca deve ser relatado como prova de que todos os caminhos de rollback funcionam.

## Conclusão para a próxima mudança

A comparação funcional usa o URM como referência: a escolha é devolvida ao Menu nativo e o Ren’Py continua dono da execução e do histórico. O ponto principal a investigar no Timeline é a restauração por log sintético e sua continuidade após a reescolha. O próximo passo é executar a fixture orientada pelo URM nos três SDKs e comparar o log original com o caminho atual antes de selecionar a menor correção para `wells_beta`. Nenhuma alteração de implementação do Timeline foi feita nesta análise.

## Referências

- [Relatório URM × SDKs × Timeline](COMPARACAO_URM_SDK_TIMELINE.md)
- [Workflow de compatibilidade](../.github/workflows/timeline-sdk-compat.yml)
- [Código atual do Timeline beta](../wells_beta/timeline/)
- SDKs: `laborat-rio_renpy/renpy-6.99.4-sdk`, `renpy-7.4.11-sdk`, `renpy-8.5.3-sdk`.
