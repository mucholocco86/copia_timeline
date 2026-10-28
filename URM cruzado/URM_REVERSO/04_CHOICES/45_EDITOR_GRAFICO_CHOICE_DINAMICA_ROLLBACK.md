# 45 — Editor gráfico do URM, Choice dinâmica e rollback

**Data:** 2026-10-25. **SDK:** Ren'Py 7.4.11. **Evidência:** runtime integrado com loader e telas originais do URM, em fixture isolada. **Run:** [40200078200](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40200078200), **SUCCESS**.

## Pergunta

O fluxo da tela original URM_modify_value consegue editar a variável numérica que controla a condição de uma Choice, fazer a alternativa ficar selecionável, executar seu bloco e depois ter edição e rota revertidas pelo rollback?

## Fontes e fixture

- `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/classes/codeview.rpy`: `CodeView.handleVarClicked` abre URM_modify_value para a variável e reinicia a interação.
- `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/screens/vars.rpy.x52`: a tela URM_modify_value recebe `Var`, mantém `newValue` como variável local de tela, e o botão Change chama `valueInput.onEnter`; esse callback usa `SetVarValue` e, em sucesso, fecha a tela.
- `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/classes/vars.rpy`: `Var.setValue` converte o valor numérico e atribui ao store; `SetVarValue.__call__` chama esse método e executa `onSuccess` quando ele retorna sucesso.
- `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/screens/choices.rpy.x52`: a tela de Choices lê `choice.isVisible` e oferece a ação Select para a alternativa.

A fixture [urm_dynamic_condition_editor_probe.rpy](../tools/fixtures/urm_dynamic_condition_editor_probe.rpy) usa uma variável inteira começando em 0 e uma Choice C cuja condição é `urm_dynamic_editor_gate == 1`. O workflow independente [urm-dynamic-condition-editor-probe.yml](../../.github/workflows/urm-dynamic-condition-editor-probe.yml) prepara uma cópia descartável do jogo de teste, do SDK 7.4.11 e do pacote URM original.

## Percurso observado

1. Seleciona rota B e retorna ao Menu.
2. Abre a tela original URM_choices; C está inicialmente invisível no índice estrutural 2.
3. Seleciona C e abre a visualização original da condição em URM_CodeView.
4. O harness invoca `CodeView.handleVarClicked("urm_dynamic_editor_gate")`, o handler que a CodeView usa para abrir URM_modify_value.
5. A tela original URM_modify_value recebe o foco; o teste digita 1 e pressiona Enter. A ação original de entrada submete SetVarValue e fecha a tela de edição.
6. A CodeView é fechada para revelar novamente a tela Choices; a ação original Select escolhe C e o bloco da rota executa.
7. Após avançar para a continuação, quatro PAGEUP são enviados e os valores são registrados após cada um.

## Resultado runtime

O run terminou SUCCESS. Trechos do log:

~~~text
DYNAMIC_EDITOR_CHOICES 0 [(False, 2)]
DYNAMIC_EDITOR_SCREEN URM_CodeView
DYNAMIC_EDITOR_SCREEN URM_modify_value urm_dynamic_editor_gate
DYNAMIC_EDITOR_AFTER_INPUT 1 None ScreenDisplayable
DYNAMIC_EDITOR_RB_1 1 C ... limit 2
DYNAMIC_EDITOR_RB_2 1 C ... limit 1
DYNAMIC_EDITOR_RB_3 0 None ... limit 0
DYNAMIC_EDITOR_RB_4 0 None ... limit 0
DYNAMIC_EDITOR_RESULT 0 None [(False, 2)]
... exit=0
~~~

`URM_modify_value` estava fechada após a entrada, enquanto URM_CodeView ainda existia. O fluxo então selecionou C com o valor 1 e executou sua rota. No terceiro PAGEUP desta fixture, rollback restaurou a variável para 0, a rota para None e a condição de C para falsa; o quarto não mudou o estado.

## Classificação

- **OBSERVADO EM RUNTIME INTEGRADO:** o teste abriu as telas URM_CodeView e URM_modify_value originais, submeteu valor numérico por entrada de teclado e confirmou o fechamento da tela de edição.
- **OBSERVADO EM RUNTIME INTEGRADO:** a variável foi alterada para 1; a Choice C foi selecionada e sua rota executou.
- **OBSERVADO EM RUNTIME INTEGRADO:** no terceiro PAGEUP deste roteiro, valor, rota e visibilidade da Choice voltaram a 0, None e False, respectivamente.
- **CONFIRMADO NA FONTE URM ORIGINAL:** o submit de entrada/Change passa por `SetVarValue → Var.setValue`; o sucesso chama a ação que fecha URM_modify_value.
- **LIMITAÇÃO DO HARNESS:** o teste chamou o handler CodeView.handleVarClicked diretamente em vez de clicar fisicamente no hyperlink colorido do texto da condição. As telas originais, a edição por teclado, o submit original, a ação Select e o rollback do motor foram usados.
- **LIMITADO À FIXTURE:** o terceiro PAGEUP observado depende do roteiro, interações e política do teste; não generalizar a contagem para outros jogos.
- **NÃO TESTADO:** tipo boolean no controle gráfico de toggle, condições compostas, save/load após essa edição, ou integração com uma busca de variável iniciada por outra tela.

## Conclusão delimitada

Agora há evidência runtime para o caminho de edição numérica pela tela original do URM, ligada à condição de uma Choice. O valor editado influenciou disponibilidade e seleção em seguida, e o rollback nativo restaurou o estado anterior nesse cenário. A prova não altera script/AST nem demonstra persistência em `.urm`; também não substitui testes de save/load ou de outras telas de entrada.

## Próxima etapa

Investigar save/load nativo depois da edição feita por URM_modify_value, separando a serialização do estado do jogo dos metadados `.urm` e verificando se a condição e a rota restauradas acompanham o slot salvo.