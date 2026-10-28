# Observação do Wells estável — 2026-10-15

**Escopo:** inspeção estática de arquivos na árvore `wells/` do laboratório canônico; não foi realizado teste de execução, não se modificou o framework.

**Relato do usuário (🟡):** o Walkthrough está concluído e foi testado funcionalmente há semanas. Esse relato é evidência de teste do usuário, não substitui auditoria de runtime feita nesta sessão.

## Fontes consultadas

- `wells/wells_Walkthrough.rpy` — SHA `98cc4d35e9ced386d9d7135936d2a313e017609b`; ~940 linhas.
- `wells/wells_choices.rpy` — SHA `2a0136a7400f85398546cc30a55040dec619f62f`.
- `wells/wells_wt_screen.rpy` — SHA `2dcf7d205c47312cfbbe8d6427cba062b05e43c6`.
- `wells/wells_screen_control.rpy` — SHA `cf58f6feee461ad149351c7c8c90aef419f8b0b5`.
- `wells/wells_settings.rpy` — SHA `e5263fcf4ee70d29b79844ca9c9ede65a45b56d6`.

## Evolução arquitetural observada

O núcleo já dispõe de `WFNonPicklable`, `WFCodeViewClass`, `WFChoicesClass`, `WFChoice`, `WFPathDetectionClass`, `WFPath`, `WFPreviousChoicePathTracker` e `WFWalkthrough`. A UI do Walkthrough é separada em `wells_wt_screen.rpy`. A tela `choice(items)` é declarada em `wells_choices.rpy` e usa as ações disponíveis no objeto recebido da tela, mantendo o fluxo nativo de seleção, em vez de executar diretamente os blocos AST.

A leitura estrutural de Choices utiliza `renpy.game.context().current`, `renpy.game.script.lookup()` e `renpy.ast.Menu`, e cria objetos `WFChoice(i,item)` com o índice original de `Menu.items`. `WFChoice.code` consulta `wf_code_view.nodesToCode(self.block)`; `jumpTo` permanece projeção limitada do primeiro `Jump` direto.

O `WFPreviousChoicePathTracker` percorre caminhos possíveis até limite configurado, mas evita atribuir causalidade quando mais de uma Choice alcança o nó atual. Este comportamento conservador foi identificado no código, não testado por execução nesta inspeção.

## Ponto de atenção para pesquisa posterior

`WFWalkthrough.processar_menu_atual(items_da_screen)` mapeia a posição visual para `WFChoice` primeiro por texto de apresentação, depois texto original, e finalmente por ordem entre alternativas atualmente visíveis. Isso é uma heurística, não uma garantia universal de identidade da alternativa. No SDK 7.4.11, o valor de ChoiceReturn e `Menu.execute()` preserva o índice original da alternativa estrutural.

**Hipótese a testar (🟠):** legendas, rótulos repetidos, traduções, filtros `say_menu_text_filter`, `set` de escolhas e condições poderão criar ambiguidades entre a ordem/texto visual e a identidade estrutural. **Não representa bug confirmado**; não alterar o Wells estável com base nessa hipótese.

## Critério de preservação

A presente nota documenta resultado e perguntas para futuras pesquisas sem editar `wells/`, `wells_beta/`, SDK ou URM original. Não presume equivalência entre inspeção estática e certificação de compatibilidade. Ao investigar as hipóteses, preferir testes no ambiente experimental autorizado e registrar resultados. A meta continua: primeiro entender, depois inspecionar, depois planejar e só então modificar.
