# Compatibilidade com Ren'Py 7.4.11

Esta área registra os mecanismos do SDK usados pelo URM. O SDK em `renpy-7.4.11-sdk/` é referência somente-leitura e permanece intocado.

## Estado atualizado em 2026-10-28

A investigação estática e parte dos testes runtime estão concluídos para o circuito prioritário de Choices, estado, rollback e persistência:

- Menu/ChoiceReturn, checkpoint, deltas de StoreDict, rollback e Context: fonte do SDK examinada; runtime reduzido documentado em `04_CHOICES/22`.
- URM original selecionando Choice sob fixed rollback, inclusive condição falsa: runtime integrado nos docs `04_CHOICES/36`, `41` e `42`.
- Edição de variável pela interface original, leitura do valor pelo fluxo do jogo e reversão por rollback: docs `04_CHOICES/38–45`.
- Save/load nativo da edição e da rota, inclusive em processo novo: docs `04_CHOICES/46–47`.
- `.urm`, Settings e snapshots: docs `04_CHOICES/49–51` e `06_VARIABLES/02–03`.

Esses resultados são específicos do Ren'Py 7.4.11 e dos roteiros documentados. Não cobrem todos os tipos de objeto, estados de UI, combinações de configuração ou outros SDKs.

## Continuidade

1. Validar filtro de texto numa Choice realmente renderizada e a ordem entre filtros.
2. Completar save/load nativo combinado com load `.urm`, registrando ordem e precedência.
3. Testar persistência nativa da instância Snapshots e interações visuais ainda pendentes.
4. Depois de fechar os comportamentos no 7.4.11, comparar com SDKs 6.99.4 e 8.5.3.

Para a revisão consolidada dos documentos, consulte [Revisão documental URM — 2026-10-28](../00_README/REVISAO_DOCUMENTAL_URM_2026-10-28.md).

## Atualização — filtro de texto de Menu

O doc [04_CHOICES/52](../04_CHOICES/52_TEXTREPL_MENU_AST_FILTER_PATH.md) confirma em `ast.Menu.execute()` que `say_menu_text_filter` recebe o rótulo e que o índice original `i` é mantido como valor estrutural. `exports.menu()` processa condição e substituição depois. O callback de regra restaurada também foi chamado em runtime (doc 50), mas o texto visual final continua sem teste end-to-end.
