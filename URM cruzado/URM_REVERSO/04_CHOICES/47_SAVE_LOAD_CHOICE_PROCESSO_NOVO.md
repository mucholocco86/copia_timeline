# 47 — Save da Choice editada carregado em processo Ren'Py novo

**Data:** 2026-10-25. **SDK:** Ren'Py 7.4.11. **Evidência:** runtime em dois processos Ren'Py independentes dentro de um job GitHub Actions, com URM original e fixture descartável. **Run final:** [40213634448](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213634448), **SUCCESS**.

## Pergunta

A edição numérica feita pelo editor original do URM, junto com o efeito de rota da Choice, sobrevive ao encerramento do primeiro processo e ao carregamento do save por um processo Ren'Py recém-iniciado?

## Procedimento

A fixture [urm_dynamic_condition_fresh_process_probe.rpy](../tools/fixtures/urm_dynamic_condition_fresh_process_probe.rpy) define uma variável inicial 0 e a alternativa C condicionada a `urm_dynamic_fresh_gate == 1`.

### Processo 1

1. Inicia o jogo descartável, seleciona a rota B e volta ao Menu pelo rollback.
2. Abre URM_choices, abre a condição em CodeView e chama o handler `CodeView.handleVarClicked` para abrir a tela original URM_modify_value.
3. Digita 1 e confirma; depois seleciona C, cuja rota torna-se C.
4. Chama `renpy.save` no slot `urm-dynamic-choice-fresh-process`, altera a variável e a rota em memória e encerra o processo.

### Processo 2

1. O workflow inicia outro processo Ren'Py contra o mesmo diretório temporário do jogo e do save.
2. A fixture confirma que o slot existe, define um marcador de reentrada em `renpy.session` e chama `renpy.load` diretamente.
3. Ao retomar no ponto salvo, verifica e afirma que a variável é 1 e a rota é C.

O workflow independente [urm-dynamic-condition-fresh-process-probe.yml](../../.github/workflows/urm-dynamic-condition-fresh-process-probe.yml) mantém o diretório temporário do jogo entre as duas etapas do mesmo job. O SDK, as fontes originais URM e os diretórios Wells não são alterados.

## Resultado runtime

O run 40213634448 terminou SUCCESS e registrou:

~~~text
DYNAMIC_FRESH_BEFORE_SAVE 1 C
DYNAMIC_FRESH_AFTER_SAVE_MUTATION 0 mutated-after-save-process-1
DYNAMIC_FRESH_BEFORE_LOAD 0 None
DYNAMIC_FRESH_AFTER_LOAD 1 C (..., 85)
process 1 exit=0
process 2 exit=0
~~~

Isso demonstra que o segundo processo iniciou com seus valores iniciais, leu o save do primeiro processo e restaurou o valor editado e a rota salva. Asserções foram executadas no processo 2.

## O que a interface Gamesaves faz e o que foi testado

**CONFIRMADO NA FONTE URM ORIGINAL:** `GameSavesClass.load(slot)` verifica `renpy.can_load(slot)` e passa `Function(renpy.load, slot)` para `Confirm`. Portanto o callback confirmado pelo código termina em `renpy.load` após a confirmação.

**NÃO OBSERVADO EM RUNTIME NESTE DOCUMENTO:** a própria tela de confirmação e o clique no slot da interface `URM_gamesaves` não foram usados. O processo 2 chamou diretamente `renpy.load`. A cadeia da fonte sugere que o carregamento confirmado usa a mesma API nativa, mas a tela de Gamesaves e seus controles ainda precisam de prova runtime.

## Classificação e limites

- **OBSERVADO EM RUNTIME EM PROCESSOS SEPARADOS:** `gate=1` e rota C, gravados no primeiro processo, foram restaurados no segundo processo a partir do save nativo.
- **OBSERVADO EM RUNTIME:** antes do load no processo 2, os defaults eram `gate=0` e rota None; depois do load, eram 1 e C.
- **CONFIRMADO NA FONTE URM ORIGINAL:** a ação Gamesaves.load delega a renpy.load através de Confirm.
- **NÃO TESTADO:** clicar na tela URM_gamesaves e confirmar pela tela/modal original; carregamento em outro computador; uso de instalação diferente; o arquivo `.urm`.
- **NÃO CONCLUIR:** o resultado é sobre o save nativo Ren'Py. Não mostra que o arquivo `.urm` guarda o valor da variável ou o estado completo do jogo.
- **LIMITES DO HARNESS:** os dois processos rodam no mesmo runner e compartilham o mesmo diretório descartável, para manter acessível o save. São processos distintos, mas não ambientes/instalações distintos.

## Tentativa de harness e correção

O primeiro run [40213540839](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213540839) ficou preso antes da edição porque o testcase não selecionava a alternativa nativa B. A sequência foi corrigida e o run final 40213634448 passou. O primeiro run não mede save/load.

## Próxima verificação

Exercitar a tela URM_gamesaves: abrir a lista, selecionar o slot salvo, confirmar a ação modal e observar a retomada do estado. Em separado, verificar se algum `.urm` foi criado/alterado e listar exatamente quais stores próprios contém, sem tratar o arquivo como save completo.

## Tentativa de confirmação pela interface Gamesaves

A fonte examinada depois do teste mostra `GameSavesClass.load(slot)` chamando `Confirm(..., Function(renpy.load, slot), ...)`; `Confirm.__call__` mostra `x52URM_Confirm`; o template original associa K_RETURN à ação yes e oculta o modal. O caminho esperado é, portanto, seleção/ação Gamesaves → confirmação original → `renpy.load(slot)`.

Foram feitas duas tentativas de acionar essa interação em runtime dentro do test runner. Nos runs [40213802714](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213802714) e [40213906303](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213906303), o job falhou com `Could not locate the displayable` ao tentar enviar Enter ou localizar a fala sob o modal. Isso é falha de automação do harness; não demonstra falha do callback Gamesaves nem do save. Como o objetivo principal de load em processo novo já passou, a fixture canônica foi restaurada ao caminho direto renpy.load e repetida com sucesso no run [40214014928](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40214014928).

**Status runtime da UI:** pendente. A fonte confirma o callback que Gamesaves passa ao modal, mas ainda não há teste ponta a ponta que selecione o slot visualmente e confirme o diálogo em execução.