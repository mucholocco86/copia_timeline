# 24 — Callback do StoreMonitor após edição por screen

**Data:** 2026-10-18  
**Escopo:** tempo entre a edição reduzida do URM em uma ação de screen e a observação pelo mecanismo equivalente a `python_callbacks`/ `StoreDict.get_changes(False)`.  
**SDK:** Ren'Py 7.4.11.  
**Evidência:** runtime em fixture isolada; o callback é uma reprodução reduzida, não o pacote completo do URM.

## Resultado runtime

No testcase `urm_storemonitor_callback_after_screen_edit`:

1. Antes do clique: contador de callbacks 2, valor 10.
2. Após o clique que executa a edição reduzida `SetVarValue`: contador ainda 2, valor já 99.
3. Ao terminar o primeiro nó Python do script depois da interação, o callback número 3 registrou:
   - etapa `after_edit_python_body`;
   - valor atual 99;
   - `get_changes(False)` contendo `urm_callback_probe_value`;
   - valor anterior no delta 10.
4. As chamadas seguintes também encontraram o mesmo delta 10→99, coerente com `cycle=False`, que não avança a referência antiga do `StoreDict`.

O teste terminou com exit 0 no run [39098269040](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098269040). Trecho decisivo do log:

```text
CALLBACK_PROBE_BEFORE_SCREEN_ACTION 2 10
CALLBACK_PROBE_AFTER_SCREEN_ACTION 2 99
CALLBACK_PROBE_EVENT 3 (... 'after_edit_python_body', 99, ..., True, False, True, 10)
CALLBACK_PROBE_AFTER_NEXT_PYTHON_NODE 3 99 True 10 99
```

Na tupla instrumentada, os campos finais são, nesta ordem: flag `Context.force_checkpoint` antes do callback defini-la; `RollbackLog.force_checkpoint`; presença do nome-alvo no delta; valor anterior. No evento 3, portanto, o delta 10→99 foi visto, `Context.force_checkpoint` já estava True e a flag do log estava False.

## O que a medição demonstra

- **OBSERVADO EM RUNTIME (fixture reduzida):** o callback não executou durante a ação da screen; o contador ficou em 2 antes e depois da atribuição.
- **OBSERVADO EM RUNTIME (fixture reduzida):** o primeiro callback registrado após o nó Python posterior encontrou o novo valor e o valor anterior no delta.
- **CONFIRMADO NO SDK 7.4.11:** `renpy.ast.Python.execute()` chama `renpy.config.python_callbacks` no bloco `finally`, após `py_exec_bytecode()`, fora de `init_phase`.
- **CONFIRMADO NO SDK 7.4.11:** `StoreDict.get_changes(False)` calcula deltas sem ciclar `old`.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** o callback do StoreMonitor solicita `Context.force_checkpoint=True` e chama `get_changes(False)`.

## Limite desta execução e continuação

Este testcase específico começou no contexto do test runner, onde rollback estava desabilitado. Portanto, seus próprios logs não demonstram a transferência de force_checkpoint ao log nem o rollback da edição.

A continuação com rollback habilitado foi executada separadamente e documentada em [25 — Callback, edição por screen e restauração por rollback](25_CALLBACK_ROLLBACK_STOREDELTA_GAMEPLAY.md). Nessa fixture reduzida, o log recebeu a flag, o callback posterior não encontrou o delta do alvo e o rollback restaurou 99→10. Essa evidência posterior não altera o escopo deste primeiro teste: os dois cenários diferem na configuração de rollback.

## Fixture e fontes

- Fixture: `URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy`, callback reduzido `urm_callback_probe_callback`, tela `urm_callback_probe_screen`, testcase `urm_storemonitor_callback_after_screen_edit`.
- Workflow: `.github/workflows/urm-choice-runtime-probe.yml`, passo “Run StoreMonitor callback after screen edit”.
- SDK: `renpy-7.4.11-sdk/renpy/ast.py`, classe `Python.execute`, blob SHA `d81ffc13f28f0b7442ba6905f1745ee838f7b185`.
- SDK: `renpy-7.4.11-sdk/renpy/python.py`, `StoreDict.get_changes`, blob SHA `c5eb2819a3e4ee096dbf01130d70a77f9b623484`.
- SDK: `renpy-7.4.11-sdk/renpy/execution.py`, `Context.run`, transferência de `force_checkpoint`, blob SHA `547f73b26dad0fe08fda6333e5f4b60c97cf8772`.
- URM convertido: `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/vars.rpy`, `StoreMonitorClass._m1_vars__pythonCallback`, blob SHA `57482937e14f215dac0ecb22a62da8ad160cba58`.

## Próxima etapa

Repetir a edição por screen com rollback habilitado no contexto e coletar, em pontos explícitos, `Context.force_checkpoint`, `RollbackLog.force_checkpoint`, o delta do store e o valor após rollback. Não inferir que o resultado de contexto de teste com rollback desabilitado se aplica automaticamente ao jogo real.
