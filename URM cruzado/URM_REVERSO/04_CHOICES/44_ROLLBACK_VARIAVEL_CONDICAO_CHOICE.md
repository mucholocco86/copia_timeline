# 44 — Rollback da variável que controla uma Choice dinâmica

**Data:** 2026-10-25. **SDK:** Ren'Py 7.4.11. **Evidência:** runtime integrado com URM original e fixture isolada. **Run final:** [40198340290](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40198340290), **SUCCESS**.

## Pergunta

Quando a variável que controla a condição de uma Choice é editada pelo setter original do URM, a alternativa é selecionada, e o jogo avança, o rollback restaura a variável, a rota e a disponibilidade da Choice?

## Fixture e execução

A fixture [urm_dynamic_condition_rollback_probe.rpy](../tools/fixtures/urm_dynamic_condition_rollback_probe.rpy) usa o URM original e o SDK 7.4.11 em uma cópia descartável de the_question. Ela define a alternativa C com condição `urm_dynamic_rb_enabled`, inicialmente False.

O cenário seleciona B, retorna ao Menu, abre URM_choices, altera a variável pelo método `x52URM.Var(...).setValue(True)`, reinicia a interação e escolhe C. Depois avança para a continuação e envia quatro PAGEUP, registrando variável, rota, nó corrente e limite do log depois de cada evento.

O workflow independente é [urm-dynamic-condition-rollback-probe.yml](../../.github/workflows/urm-dynamic-condition-rollback-probe.yml). Nenhuma fonte original do URM, arquivo do SDK, `wells/` ou `wells_beta/` foi alterado.

## Resultado runtime

O run 40198340290 terminou SUCCESS e registrou:

~~~text
DYNAMIC_RB_SCREEN False [(False, 2)]
DYNAMIC_RB_AFTER_EDIT True [(True, 2)]
DYNAMIC_RB_STEP_1 True C ... limit 2
DYNAMIC_RB_STEP_2 True C ... limit 1
DYNAMIC_RB_STEP_3 False None ... limit 0
DYNAMIC_RB_STEP_4 False None ... limit 0
DYNAMIC_RB_RESULT False None [(False, 2)]
... exit=0
~~~

Assim, neste percurso:

1. A edição tornou a condição verdadeira e C executou.
2. PAGEUP 1 e 2 mantiveram a variável True e a rota C.
3. PAGEUP 3 restaurou a variável para False e a rota para None, retornando o contexto ao Menu.
4. PAGEUP 4 não mudou o estado observado.
5. A consulta da Choice restaurada retornou `isVisible=False` para o índice estrutural 2.

## Classificação

- **OBSERVADO EM RUNTIME INTEGRADO:** o setter original do URM alterou a variável que dirige a condição; a Choice passou de invisível para visível, e a seleção pelo URM executou seu bloco.
- **OBSERVADO EM RUNTIME INTEGRADO:** o terceiro PAGEUP deste roteiro restaurou em conjunto o valor booleano False, a rota None e o contexto no Menu; a condição da mesma alternativa foi então avaliada como falsa.
- **CONFIRMADO NO SDK 7.4.11:** o rollback restaura estado do store e Context a partir do histórico nativo, conforme os documentos 15, 19, 39 e 40. Este teste mostra esse efeito na variável-condição dentro do percurso integrado.
- **LIMITADO À FIXTURE:** o número de PAGEUPs depende das interações, do roteiro, da política de rollback e da versão. Não é uma regra geral de jogos.
- **NÃO TESTADO:** a edição foi realizada chamando diretamente `Var.setValue`, não digitando no editor gráfico `URM_modify_value`; save/load e outros tipos de variável também não foram cobertos.

## Tentativa inicial e correção do probe

O primeiro run, [40198189336](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40198189336), chegou a observar o mesmo estado final, mas falhou numa asserção auxiliar que esperava que flags de instrumentação continuassem True depois do rollback. O próprio rollback restaurou essas flags junto com o restante do store, invalidando a asserção, não o mecanismo investigado. A fixture foi corrigida para validar os valores restaurados diretamente; o run final 40198340290 passou.

## Conclusão para o circuito

Neste cenário, a edição de uma variável que condiciona uma Choice é uma mutação do estado corrente do jogo. Ela alterou a disponibilidade observada pelo URM e permitiu executar C; depois, rollback restaurou tanto a variável como o efeito de rota e a condição voltou a False. Isso não modifica a condição no AST ou no arquivo `.rpy` e não demonstra persistência fora do histórico/save nativo.

## Próximos pontos

1. Repetir pelo fluxo gráfico completo de URM_modify_value, mantendo a screen de Choices aberta.
2. Salvar depois da edição e verificar load do estado booleano e da rota.
3. Comparar edição antes da abertura da screen, durante a screen e depois da escolha.
4. Examinar condições compostas ou com objetos mutáveis sem extrapolar o resultado deste escalar booleano.