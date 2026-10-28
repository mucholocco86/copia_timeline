# 41 — Choice com condição falsa selecionada pela tela original do URM

**Data:** 2026-10-23. **SDK:** Ren'Py 7.4.11. **Tipo de evidência:** teste de runtime integrado, com loader e pacote original do URM copiado sem alterações para uma instância descartável de the_question. Nenhum arquivo protegido foi modificado.

## Pergunta investigada

Quando uma alternativa de Menu tem condição falsa, a tela original de Choices do URM apenas a mostra como indisponível ou consegue devolvê-la ao Menu AST e fazer o bloco executar?

## Resultado observado

O workflow [39913014343](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39913014343) terminou **SUCCESS**.

A fixture apresentou três alternativas: Native route A e Native route B, sem condição falsa; e Hidden route C, com condição literal False e bloco AST não vazio.

O percurso foi:

1. O menu nativo foi iniciado e a rota B foi selecionada.
2. A fixture estabeleceu a fronteira de fixed rollback e executou PAGEUP até retornar ao Menu.
3. A tela original URM_choices foi aberta pela notificação/atalho Alt+C enquanto o log indicava fixed rollback.
4. A instrumentação de show_screen confirmou que a lista do URM continha A, B e C, preservando índices 0, 1 e 2. Para C, isVisible era False.
5. Alt+3 e Enter acionaram a ação original Select da terceira linha.
6. ChoiceReturn recebeu label “Hidden route C” e value 2. A ação URM havia limpado rollback_is_fixed antes da chamada.
7. Menu.execute continuou pela rota C; a fixture alcançou “Hidden probe route C.” e a asserção route == "C" passou.

O log registrou: URM_choices abriu com fixed=True e false_item_seen=True; a lista tinha C com isVisible=False e índice 2; ChoiceReturn recebeu value 2 com fixed=False; o resultado foi 2; a rota final foi C; e o processo saiu com exit=0.

## Conclusão delimitada

- **OBSERVADO EM RUNTIME INTEGRADO:** na fixture do SDK 7.4.11, o URM mostra a alternativa cuja condição é False e sua tela original devolve o índice 2; o bloco da alternativa C é executado.
- **CONFIRMADO NA FONTE URM:** currentChoices inclui itens com bloco AST sem filtrar por isVisible; a tela mostra o valor isVisible e mantém a ação Select sensível; URMChoice.Action limpa rollback_is_fixed e chama ChoiceReturn com o índice original.
- **CONFIRMADO NO SDK 7.4.11:** Menu.execute usa o índice retornado para obter self.items[choice] e não reavalia ali a condição do item.
- **CONSEQUÊNCIA:** nesse circuito, a condição que normalmente governa a apresentação da alternativa no menu não impediu que a ação programática do URM alcançasse o bloco. Isso demonstra capacidade de forçar a execução daquela alternativa no cenário testado; não equivale a alterar a condição no script nem o arquivo .rpy.

## Limites do teste

- A condição era a expressão literal False; variáveis dinâmicas, efeitos colaterais da avaliação e mudanças da condição durante a tela não foram testados.
- O harness habilitou rollback no contexto e no store para tornar reproduzível a fronteira. A tela, loader, ação e interação do URM eram os originais.
- O teste demonstra o caminho de notificação Alt+C e seleção por Alt+3/Enter. Não cobre o botão do watchpanel, outros temas/telas, mais de nove alternativas ou jogos com políticas de menu distintas.
- Não mede consequências posteriores que dependam da condição falsa, estado salvo antes/depois, save/load ou outro rollback após a rota C.
- O resultado é específico do SDK 7.4.11; não se transfere automaticamente para outras versões.

## Arquivos reprodutíveis

- Fixture isolada: [urm_hidden_condition_probe.rpy](../tools/fixtures/urm_hidden_condition_probe.rpy)
- Workflow independente: [urm-hidden-condition-probe.yml](../../.github/workflows/urm-hidden-condition-probe.yml)
- Workflow run: [39913014343](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39913014343)
- Código original consultado: classes/choices.rpy e screens/choices.rpy.x52 em URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/
- Fontes do SDK: renpy/ast.py (Menu.execute), renpy/exports.py (menu/display_menu), renpy/ui.py (ChoiceReturn.__call__).

## Relevância para a análise de Choices e rollback

A tela original do URM não é apenas um visualizador de alternativas indisponíveis. Ao selecionar uma alternativa falsa neste cenário, a cadeia retorna o índice AST e o Ren'Py executa seu bloco. A ação também altera o estado de fixed rollback antes de devolver esse índice. Isso torna ainda mais importante tratar seleção via URM como modificação de fluxo, separada de leitura/projeção da Choice, edição de variáveis que condicionam a Choice, modificação do script ou da condição, e avanço/retorno do estado pelo rollback nativo.

## Próximas questões

1. Repetir com uma condição dependente de variável e editar essa variável pelo próprio URM enquanto a tela está aberta.
2. Medir o que ocorre se a condição mudar de False para True durante a tela.
3. Fazer rollback depois que o bloco forçado executou; verificar valor, contexto, fronteira e roll-forward.
4. Repetir com fix_rollback_without_choice=True e com menu_actions/menu_include_disabled alterados.
5. Testar save/load após a rota forçada.

## Proveniência

Fixture e workflow adicionados no commit 405098b091acf0a8f305069387e7eca53ad13736. O run acima concluiu com sucesso e registrou as chamadas e as asserções no job hidden-choice.
