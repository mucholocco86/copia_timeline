# 36 — Choices original do URM abertas durante fixed rollback real

**Data:** 2026-10-23  
**Escopo:** confirmar com o pacote original do URM, seu loader e o Ren'Py SDK 7.4.11 se a notificação normal de Choices abre a tela modal durante fixed rollback e se a ação seleciona outra alternativa.  
**Classificação:** teste de runtime integrado em jogo descartável; fontes originais preservadas sem alteração.

## Resultado

O GitHub Actions run [39903530535](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39903530535) concluiu **SUCCESS** no commit `aadfce0591527e6d32e3f3e3ffe85f59c6e474c6`.

A fixture copiou `the_question` para uma pasta temporária e, sem alterar o material original, copiou todo o conteúdo de:

`URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/`

para:

`<jogo descartável>/game/0x52-URM/`

O loader `x52MF2` carregou o pacote no Ren'Py 7.4.11. A fixture chamou `x52URM.afterLoad()`, instalando overlay e StoreMonitor reais, configurou o aviso de Choices, executou um menu nativo A/B, aplicou `renpy.fix_rollback()` e retornou ao menu por PAGEUP. Não houve modificação em `wells/`, `wells_beta/`, fontes originais ou SDK.

## Sequência efetivamente observada

O log do job `original-loader` (job `120250190304`) contém:

```text
REAL_URM_READY 2.6.2 choice_api False fixed False can False
REAL_URM_BOUNDARY AFTER_FIX route B limit 1 can True fixed False
REAL_URM_ROLLBACK_END True ... forward None
REAL_URM_ROLLBACK_END True ... forward 1
REAL_URM_CHOICES_SCREEN_SHOWN URM_choices fixed True current (..., 58)
REAL_URM_CHOICERETURN fixed_before False label Native route A value 0
REAL_URM_CHOICERETURN_RESULT 0 fixed_after False
REAL_URM_BOUNDARY AFTER_URM_SELECTION route A ... fixed False
```

Interpretação limitada ao percurso testado:

1. A seleção inicial nativa escolheu B e a fixture fixou a fronteira.
2. PAGEUP executou rollback pelo `RollbackLog`; a segunda chamada restaurou o contexto do Menu e deixou `rollback_is_fixed=True`.
3. O atalho `Alt+C`, registrado pela notificação original do URM, chamou `Show('URM_choices')`. O wrapper de observação confirmou a chamada enquanto `rollback_is_fixed=True`.
4. A tela original carregada pelo loader recebeu `Alt+1` e Enter. A ação limpou o fixed flag, chamou `ChoiceReturn` com o valor estrutural `0`, e o Ren'Py executou a rota A.
5. As asserções da fixture confirmaram rota A, chamada da tela `URM_choices` e saída do fixed rollback. O teste terminou com sucesso.

O texto “Choices detected” não foi usado como critério de sucesso: o harness de testes não casou essa inscrição formatada na screen. A evidência direta para a entrada é a chamada instrumentada a `renpy.show_screen('URM_choices')`, após o evento de teclado.

## O que fica confirmado — e o que não fica

- **CONFIRMADO NO URM ORIGINAL EM RUNTIME:** o loader original consegue carregar o pacote copiado sem alteração nesta fixture do SDK 7.4.11.
- **OBSERVADO EM RUNTIME:** a tela original `URM_choices` foi aberta durante `rollback_is_fixed=True`.
- **OBSERVADO EM RUNTIME:** a ação da tela levou à alternativa A e a execução saiu do fixed rollback.
- **CONFIRMADO NA FONTE ORIGINAL:** `screens/watchpanel.rpy.x52` registra `alt_K_c` e o botão da notificação como `Show('URM_choices')`; `screens/choices.rpy.x52` usa `choice.Action`; `classes/choices.rpy` limpa `rollback_is_fixed` antes de retornar o `ChoiceReturn`.
- **LIMITAÇÃO DO HARNESS:** para disponibilizar rollback nesta execução controlada, a fixture definiu `renpy.game.context().rollback=True` e `renpy.store._rollback=True`. O mecanismo de rollback, a fronteira e as telas/ações do URM são reais; não se mediu o comportamento de cada jogo hospedeiro nem o caminho natural de inicialização de outro jogo.
- **NÃO DEMONSTRADO:** se o cartão aparece visualmente em todos os temas/resoluções, ou se a interação funciona com qualquer configuração de painel, idioma, tela modal ou `fix_rollback_without_choice=True`.
- **NÃO DEMONSTRADO:** save/load durante ou após a seleção, alteração manual de variável no mesmo fluxo, persistência em arquivo `.urm`, e rollback que atravessa a reescolha A.
- **NÃO TESTADO AQUI:** botão do watchpanel, modo expandido/recolhido, notificação desativada, Choices condicionais ocultas ou textos substituídos.

## Arquivos reprodutíveis

- Fixture: [`urm_real_loader_choices_boundary_probe.rpy`](../tools/fixtures/urm_real_loader_choices_boundary_probe.rpy)
- Workflow: [`urm-real-loader-choices-boundary-probe.yml`](../../.github/workflows/urm-real-loader-choices-boundary-probe.yml)
- Documento de localização estática da entrada: [35 — Entrada da tela Choices e fixed rollback](35_ENTRADA_DA_TELA_CHOICES_E_FIXED_ROLLBACK.md)
- Fontes originais preservadas: `01_MATERIAL_URM/1_URM_ORIGINAL/screens/watchpanel.rpy.x52`, `screens/choices.rpy.x52`, `classes/choices.rpy` e `classes/main.rpy`.

## Próxima investigação

1. Repetir usando a rota de botão, em vez do atalho `Alt+C`, e capturar presença/visibilidade da notificação independentemente de correspondência de texto no test runner.
2. Comparar `fix_rollback_without_choice=True` e configurações de watchpanel.
3. Testar uma edição real com `Var.setValue`/ação da interface durante fixed rollback; avançar, voltar até antes da edição e inspecionar o valor.
4. Repetir rollback após a reescolha A e verificar qual fronteira é estabelecida.
5. Testar save/load e separar estado nativo do jogo, stores do URM e arquivos `.urm`.

Este resultado fecha somente a dúvida “a interface real de Choices do URM pode ser aberta e usada nesta fronteira de rollback do Ren'Py 7.4.11?”. A resposta, para o percurso reproduzido, é **sim**.
