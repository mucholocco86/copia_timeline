# 42 — Rollback após selecionar Choice com condição falsa

**Data:** 2026-10-23. **SDK:** Ren'Py 7.4.11. **Tipo de evidência:** runtime integrado com URM original, loader original e fixture descartável. **Workflow final:** [39924626643](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39924626643), **SUCCESS**.

## Pergunta

Depois de o URM forçar uma alternativa com condição False e seu bloco executar, quantos passos de rollback no cenário testado são necessários para restaurar a rota anterior? O que o log mantém para roll-forward, e o URM permite selecionar outra rota quando o limite normal de rollback chega a zero?

## Preparação da fixture

A fixture executa um Menu com A/B normais e C, cujo predicado é literalmente False. O jogador escolhe B, retorna ao Menu pela fronteira fixed rollback, abre a tela original URM_choices e seleciona C via Alt+3/Enter. A fixture confirma que:

- o URM mostra C com isVisible=False e índice estrutural 2;
- ChoiceReturn recebe C e devolve 2;
- o bloco C executa;
- renpy.fix_rollback() é executado no fluxo depois da escolha;
- quatro eventos PAGEUP depois da continuação registram estado de rota, contexto, limite, fixed rollback e forward info;
- Choices do URM reabre no Menu restaurado e a rota B pode ser selecionada de novo.

O pacote original URM não foi alterado; somente a fixture/workflow isolados foram usados.

## Resultado observado no runtime

O primeiro e o segundo PAGEUP não desfizeram o bloco C: a rota ainda era C, rollback_is_fixed permanecia False e havia dados de roll-forward.

No terceiro PAGEUP, o log restaurou a rota para None e o contexto chegou de volta ao nó Menu. rollback_is_fixed ficou True e o rollback_limit ainda era 1.

No quarto PAGEUP, a rota permaneceu None e no Menu. O registro preservou roll_forward_info()==2, correspondente ao índice da alternativa C; rollback_limit passou a zero, portanto can_rollback() ficou False.

Apesar do limite zero, a tela original URM_choices abriu novamente com fixed rollback ativo. A ação selecionou B, limpou rollback_is_fixed e devolveu índice 1; a execução seguiu pela rota B. A fixture terminou **SUCCESS**.

| Evento no cenário desta fixture | Rota | Contexto relevante | Fixed | Limite | Roll-forward |
|---|---|---|---|---:|---|
| Depois de selecionar C | C | bloco C executado | False | — | — |
| PAGEUP 1 | C | fluxo anterior à continuação | False | 3 | nenhum |
| PAGEUP 2 | C | continuação | False | 2 | presente |
| PAGEUP 3 | None | Menu restaurado | True | 1 | nenhum |
| PAGEUP 4 | None | Menu na fronteira | True | 0 | índice 2 (C) |
| Nova escolha B pelo URM | B | bloco B executado | False | — | consumido/alterado pelo fluxo |

Os valores intermediários de limite/contexto vêm do trace HIDDEN_POST_ROLLBACK_*. São contagens da fixture específica; não são uma regra universal de PAGEUP para qualquer jogo.

## O que foi confirmado

- **OBSERVADO EM RUNTIME INTEGRADO:** a alternativa C com condição literal False pode ser forçada pelo URM; sua rota fica ativa após a seleção.
- **OBSERVADO EM RUNTIME INTEGRADO:** o terceiro PAGEUP no percurso da fixture restaura a variável da rota para None e retorna a execução ao Menu.
- **OBSERVADO EM RUNTIME INTEGRADO:** após o quarto PAGEUP, o estado continua no Menu, fixed rollback está ativo, o limite de rollback é zero e roll-forward informa índice 2 (C).
- **OBSERVADO EM RUNTIME INTEGRADO:** a tela original do URM abre nesse estado e permite selecionar B; a rota B executa mesmo com can_rollback() falso antes da reescolha.
- **CONFIRMADO NO SDK 7.4.11:** o rollback restaura o estado e o Context a partir dos registros; a reescolha retorna à execução do índice de Menu selecionado. O valor de roll-forward é mecanismo separado de can_rollback/rollback_limit.
- **CONFIRMADO NA FONTE URM:** URMChoice.Action limpa rollback_is_fixed e devolve o índice original via ChoiceReturn.
- **NÃO CONFIRMADO:** que o URM apague a fronteira de fixed rollback permanentemente. A sequência mostra que o motor mantém a fronteira e pode entrar novamente em fixed rollback conforme o percurso.
- **NÃO CONFIRMADO:** que o mesmo número de PAGEUPs ou os mesmos valores de limite se apliquem a outros jogos, quantidades de interação, políticas ou versões.

## Importância da ordem do evento

O experimento fecha uma distinção útil:

1. O bloco forçado pode executar mesmo que o predicado da Choice seja False.
2. Seus efeitos ainda entram no estado reversível do jogo e podem ser desfeitos.
3. Ao desfazer a rota, o Ren'Py retorna ao Menu com informação de roll-forward sobre a escolha anterior.
4. O URM pode então fornecer outro índice e continuar por outro bloco, inclusive quando can_rollback() já é False.

Portanto, “o URM executa uma Choice invisível” não significa que a escolha vira permanente, e “rollback_limit chegou a zero” não significa que o URM não possa iniciar outra rota. São mecanismos diferentes.

## Limitações

- C usa condição literal False; não foram testados predicados variáveis ou com efeitos laterais.
- A fixture habilitou rollback no Context e no store.
- A seleção foi pela notificação Alt+C e teclas Alt+3/Enter e, na segunda entrada, Alt+2/Enter.
- O resultado se aplica ao Ren'Py 7.4.11 e a este fluxo controlado.
- Save/load e persistência em arquivo .urm continuam fora do teste.
- Uma variável contador de chamadas da tela foi revertida pelo rollback; o marcador final foi baseado no roll-forward, e não em tratar store reversível como histórico append-only.
- Execuções intermediárias falharam por expectativa/contador da fixture depois da restauração; elas não contradizem os dados do trace. A versão final, com o marcador baseado em roll_forward_info()==2, passou.

## Artefatos

- Fixture: [urm_hidden_postrollback_probe.rpy](../tools/fixtures/urm_hidden_postrollback_probe.rpy)
- Workflow: [urm-hidden-postrollback-probe.yml](../../.github/workflows/urm-hidden-postrollback-probe.yml)
- Execução final: [39924626643](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39924626643)
- Resultado anterior sobre execução de C: [41 — Choice com condição falsa executada pelo URM](41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md)
- Cruzamento estático: [40 — Menu, condições e force_checkpoint](40_MENU_CONDICOES_FORCE_CHECKPOINT_RUNTIME.md)

## Próximas verificações

1. Repetir com condição C dependente de variável e registrar edição dessa variável durante a tela Choices.
2. Medir como mudanças de condição afetam a tela já aberta versus a próxima execução de Menu.
3. Testar save/load depois de C e depois de rollback para antes de C.
4. Comparar o mesmo circuito com fix_rollback_without_choice=True.
5. Depois de fechar esses casos, verificar o comportamento em outro jogo Ren'Py da fixture, sem generalizar a partir de the_question.
