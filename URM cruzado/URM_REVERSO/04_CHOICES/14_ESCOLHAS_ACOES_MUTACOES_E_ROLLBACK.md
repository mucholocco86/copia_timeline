# 14 — Choices: leitura, ações, mutações e rollback

**Data:** 2026-10-15. **Prioridade:** circuito de escolhas e Walkthrough. **Status:** confirmado por leitura estática da fonte convertida URM; observação de rollback relatada pelo usuário; validação SDK 7.4.11 e runtime pendentes. Nenhum arquivo protegido alterado.

## Evidências URM inspecionadas

Prefixo: `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/`.

- `classes/choices.rpy` SHA `48fc35f96119189e50f038981795115b3df7b770`, linhas 5–35, 37–93, 95–127.
- `screens/choices.rpy` SHA `a78de7e46a5b6230b4871628bfa62708233a07ce`, linhas 2–84.
- `classes/PathDetection.rpy` SHA `078950513618fe64f6a9961d77230e4c468a3ab4`, linhas 145–185.
- `classes/vars.rpy` SHA `57482937e14f215dac0ecb22a62da8ad160cba58`, linhas 232–269, 421–435, 483–563.
- `classes/textrepl.rpy` SHA `70ce9cc40378af1de5092255558659c8512a04f6`, linhas 56–116.
- `classes/main.rpy` SHA `14f93406d2946eaed664ed72c1d47063984ce24f`, linhas 54–63, 194–218.

## A — Leitura da Choice

`Choices.currentChoices` usa `renpy.game.context().current`, `renpy.game.script.lookup`, verifica `renpy.ast.Menu` e enumera `script.items`, conservando o índice estrutural original quando `item[2]` existe. `URMChoice` expõe `condition`, `text`, `isVisible`, `code` e `jumpTo`. `code` é projeção de AST via `CodeView.nodesToCode`, não execução; `jumpTo` procura `Jump` direto, não necessariamente saltos aninhados.

`URMChoice.text` usa `renpy.exports.substitute`; `isVisible` usa `eval` no store. A tela `URM_choices` exibe **todas as escolhas estruturais incluídas na coleção**, com indicação de visibilidade, código e label. O índice `i` exibido pela tela não é necessariamente o índice original `Menu.items`; `URMChoice.Action` preserva o índice original. Não usar texto exibido como identidade única.

## B — Selecionar uma alternativa pelo URM

`URMChoice.Action` cria `choose()`, executa `renpy.game.log.rollback_is_fixed = False` e retorna `renpy.ui.ChoiceReturn(choice[0], index)()` (`choices.rpy` 87–93). A tela usa `[Hide('URM_choices'), Hide('URM_CodeView'), choice.Action]` (`screens/choices.rpy` 79–84).

**Distinção:** a ação devolve ao menu um resultado de escolha por índice; o URM não executa diretamente os comandos do bloco AST nessa função. A sequência posterior de execução é responsabilidade do Ren'Py. A alteração de `rollback_is_fixed` merece estudo específico, mas não prova, isoladamente, que o URM salva ou fixa escolhas.

A tela permite selecionar inclusive uma alternativa marcada como não visível: `sensitive=True` na ação Select, sem teste de `choice.isVisible` nesse botão. **Isto é evidência de ausência de bloqueio na UI do URM, não confirmação de comportamento runtime para cada versão.**

## C — Alterar o estado de variáveis não é selecionar outra Choice

`SetVarValue.__call__` encaminha a `Var.setValue`; `Var.setValue` altera o store em execução por atribuição/append. Esse circuito é independente de `URMChoice.Action`. Modificar `josylove` antes ou depois de um menu pode mudar o que os próximos condicionais enxergam, mas **não reexecuta automaticamente uma alternativa passada**.

`StoreMonitorClass` intercepta algumas atribuições e observa mudanças em callback Python; registra `force_checkpoint`, consulta `get_changes` e pode impedir alterações em variáveis congeladas. A relação com rollback exige validação do SDK e testes.

## D — Outro mecanismo: forçar caminho sem estar em Choice

`PathDetection.Path.Action` (`PathDetection.rpy` 145–185) atua quando `forceable` e não está sendo exibida Choice. Pode substituir `renpy.game.context().next_node` ou reconstruir uma cadeia de nós por cópias até alcançar o `If` alvo, então retorna. **Isso é alteração do fluxo em memória**, não escrita de `.rpy` no disco. Não confundir com seleção via `ChoiceReturn` ou edição de variável.

## E — Alteração visual do texto da Choice

A tela oferece botão para `URM_add_textrepl` associado a `choice.text` (`screens/choices.rpy` 37–44). `TextRepl` guarda substituições no store `replacements` e instala filtro `renpy.config.say_menu_text_filter` (`textrepl.rpy` 56–77). Esse recurso **edita a representação textual** que o jogador vê, não demonstra alteração de bloco AST nem regravação do script original.

## F — Modelo de rollback a comprovar

**Observação do usuário, não teste do assistente:** após uma edição manual de valor, os efeitos podem continuar ao avançar; ao voltar até antes do ponto da alteração, o valor pode retornar ao estado original.

**Hipótese a testar:** atribuições do URM ao estado de jogo participam do histórico de estado/rollback do Ren'Py, enquanto os stores próprios `.urm` representam metadados/configurações persistidos separadamente. A presença de `rollback_is_fixed=False` e `force_checkpoint=True` é relevante, mas não demonstra sozinha quando a alteração entra no histórico ou como volta.

### Matriz mínima de experimentos isolados

| Experimento | Verificar |
|---|---|
| Menu A/B, selecionar B via URM | Resultado `ChoiceReturn`, índice AST e bloco realmente executado |
| Escolha condicionada `False` | Ação Select do URM e tratamento pelo motor |
| Duas legendas idênticas | Identidade estrutural versus texto |
| Modificar variável após Choice, avançar, rollback parcial | Valor, checkpoint e histórico |
| Rollback até antes da modificação | Se e quando retorna ao valor anterior |
| Editar valor, salvar slot, carregar | Persistência no save nativo versus `.urm` |
| Editar substituição de texto e rollback | Separação de filtro/store `.urm` e estado de jogo |
| Forçar PathDetection | `next_node`, AST compartilhado e rollback |

## G — Próxima validação obrigatória no SDK 7.4.11

1. `renpy/ast.py`: `Menu.execute`, `Menu.items`, chamada a `renpy.exports.menu` e `next_node`.
2. `renpy/exports.py`: `display_menu`, `checkpoint`, retorno de menu.
3. `renpy/ui.py`: `ChoiceReturn.__call__` e valor devolvido.
4. `renpy/rollback.py` e `renpy/python.py`: checkpoint, mutação de store, `rollback_is_fixed`, `get_changes`, `force_checkpoint`.
5. Identificar os hooks de `after_load_callbacks` e as condições de rollback ao carregar saves.

**Regra:** somente após esse cruzamento e testes afirmar quais edições sobrevivem ao avanço, quais são desfeitas por rollback e quais são persistidas por arquivos `.urm`.

## Revisão posterior — estado comprovado até 2026-10-28

O cabeçalho acima descreve o estado em 2026-10-15. As pendências de runtime então abertas foram cobertas em percursos posteriores: a tela original do URM selecionou Choice com condição falsa e executou seu bloco (docs [41](41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md) e [42](42_ROLLBACK_APOS_CHOICE_CONDICAO_FALSA.md)); edição via tela original e reversão por rollback foram observadas (docs [38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md), [44](44_ROLLBACK_VARIAVEL_CONDICAO_CHOICE.md) e [45](45_EDITOR_GRAFICO_CHOICE_DINAMICA_ROLLBACK.md)); save/load nativo foi validado nos docs [46](46_SAVE_LOAD_NATIVO_APOS_EDICAO_CHOICE.md) e [47](47_SAVE_LOAD_CHOICE_PROCESSO_NOVO.md).

A relação entre edição e callback de monitor continua dependente do ponto do ciclo: no cenário integrado do doc [39](39_STOREMONITOR_DELTA_E_EDICAO_POR_SCREEN.md), rollback capturou o delta, mas o callback não recebeu aquela chave após a ciclagem. Não generalizar para todas as mutações/telas. O arquivo `.urm` e os stores atuais são revisados nos docs [49](49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md) e [50](50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md).
