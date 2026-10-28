# 15 — Validação no SDK 7.4.11: Menu, ChoiceReturn e checkpoint

**Data:** 2026-10-15. **Estado:** confronto de fontes URM e SDK 7.4.11, confirmado estaticamente; rollback dinâmico não testado. Continua documentos 11 e 14.

## Fontes e versões

- `renpy-7.4.11-sdk/renpy/ast.py`, SHA `d81ffc13f28f0b7442ba6905f1745ee838f7b185`, `Menu.execute` linhas 1639–1693.
- `renpy-7.4.11-sdk/renpy/exports.py`, SHA `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`, `checkpoint` linhas 267–293 e `display_menu` linhas 1127–1319.
- `renpy-7.4.11-sdk/renpy/ui.py`, SHA `914a0c4702b7af391e014702a16ccc333e7573de`, `ChoiceReturn` linhas 718–759.
- `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/choices.rpy`, SHA `48fc35f96119189e50f038981795115b3df7b770`, linhas 16–25 e 87–93.
- `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/screens/choices.rpy`, SHA `a78de7e46a5b6230b4871628bfa62708233a07ce`, linhas 28–84.

## Circuito confirmado

1. `Menu.execute` percorre `enumerate(self.items)` e, para entradas com bloco, passa `i` como valor de escolha em `choices.append((label, condition, i))` (ast.py 1657–1675).
2. Aplica `renpy.config.say_menu_text_filter` ao **label** antes de apresentar o menu (1659–1660). O índice `i` continua ligado à posição original em `self.items`.
3. `renpy.exports.menu(...)` recebe as escolhas (1688). `display_menu` monta `MenuEntry` com `ChoiceReturn(label, value, location)` para entradas selecionáveis (exports.py 1222–1256).
4. `ChoiceReturn.__call__` marca `chosen[(location,label)]` se aplicável e **retorna `self.value`** (ui.py 755–759). O próprio URM cria `ChoiceReturn(choice[0], original_index)` e chama a ação (choices.rpy 87–93).
5. `display_menu` recebe o resultado de `renpy.ui.interact`, chama `checkpoint(rv)` (exports.py 1294–1311) e retorna o valor (1319).
6. `Menu.execute` usa o valor retornado como índice estrutural: `next_node(self.items[choice][2][0])` (ast.py 1690–1693). **A execução do bloco permanece com o motor**, não com o URM.

## Implicações

- **Confirmado:** o URM pode selecionar a alternativa por índice original sem executar diretamente seu bloco AST. Isso preserva a identidade estrutural em menus com textos duplicados.
- **Confirmado:** há uma etapa de checkpoint no fluxo nativo de `display_menu`. `checkpoint` delega a `renpy.game.log.checkpoint` e leva em conta `renpy.store._rollback` (exports.py 267–293).
- **Confirmado:** a marcação nativa de escolhas usa o par `(location,label)` para `chosen` (ui.py 755–759), **não** a mesma identidade usada pelo URM para selecionar o bloco. Textos iguais no mesmo local podem afetar essa marcação; não afirmar colisão prática sem teste.
- **Confirmado:** `say_menu_text_filter` atua no texto passado ao menu, enquanto o URM usa o texto original da tupla para `ChoiceReturn`. O resultado por índice não depende da igualdade textual, mas a marcação `chosen` pode depender.
- **Não confirmado:** que `rollback_is_fixed=False` garanta rollback a um ponto arbitrário, ou que edições em `renpy.store` sejam revertidas exatamente no momento relatado pelo usuário. Isso exige seguir o log de rollback e testes isolados.

## Questões a continuar

1. Inspecionar `renpy/python.py` e a implementação do log de rollback (`renpy/game.py`, `renpy/rollback.py` se presente em outra árvore, ou `renpy/rollback.py` ausente nesta árvore): identificar o arquivo **real**, sem presumir caminho.
2. Examinar `renpy.exports.menu` entre `Menu.execute` e `display_menu`, especialmente `set`, filtragem de condições, `item_arguments` e interações com alternativas invisíveis.
3. Construir testes runtime para escolha invisível, labels duplicados, filtro de texto e retorno por índice.
4. Seguir `Var.setValue` e `StoreMonitor` através de checkpoints, rollback e save/load; não confundir seleção de menu com edição manual do estado.

**Proteções:** sem alterações no Wells estável, SDKs ou fontes originais URM.
