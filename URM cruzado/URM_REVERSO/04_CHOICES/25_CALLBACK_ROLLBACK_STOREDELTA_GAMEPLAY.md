# 25 — Callback, edição por screen e restauração por rollback

**Data:** 2026-10-18  
**Escopo:** comparar o callback reduzido do StoreMonitor após edição por screen com rollback desabilitado e habilitado, e confirmar a restauração da edição no segundo cenário.  
**SDK:** Ren'Py 7.4.11.  
**Evidência:** execução runtime em fixture isolada. A fixture não carrega o pacote completo do URM.

## Resultado principal

No run [39098551052](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098551052), o testcase **urm_storemonitor_callback_with_rollback_enabled** terminou com exit 0 e observou:

1. O valor começou em 10.
2. A ação da screen mudou o valor para 99; nenhum callback foi executado durante a ação.
3. No primeiro nó Python após a interação, o callback viu o valor 99, mas **StoreDict.get_changes(False)** não continha o nome-alvo nem valor anterior.
4. O log estava com **RollbackLog.force_checkpoint=True** quando esse callback ocorreu.
5. Antes do rollback, a fixture confirmou valor 99 e a flag de checkpoint do log ativa.
6. A chamada de rollback direcionada à fronteira anterior restaurou o valor para 10. A label de verificação confirmou o valor e terminou normalmente.

Trecho relevante do log:

```text
CALLBACK_PROBE_BEFORE_SCREEN_ACTION 2 10
CALLBACK_PROBE_AFTER_SCREEN_ACTION 2 99
CALLBACK_PROBE_EVENT 3 (... 'after_edit_python_body', 99, ..., False, True, False, None)
CALLBACK_PROBE_BEFORE_ROLLBACK 99 False True
CALLBACK_PROBE_AFTER_ROLLBACK 10
END StoreMonitor callback with rollback enabled ... exit=0
```

Na tupla instrumentada, os campos finais registram **Context.force_checkpoint**, **RollbackLog.force_checkpoint**, presença do nome-alvo no delta e valor anterior. No evento 3 foram observados, respectivamente, False, True, False e None.

## Comparação com rollback desabilitado

O run [39098269040](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098269040), documentado em [24](24_CALLBACK_SCREEN_EDIT_RUNTIME.md), observou o delta 10→99 no callback posterior quando a fixture rodava com rollback desabilitado.

| Cenário | Callback após a ação | Delta do alvo | Rollback verificado |
|---|---|---|---|
| Rollback desabilitado | Primeiro nó Python posterior | Presente, valor anterior 10 | Não |
| Rollback habilitado | Primeiro nó Python posterior | Ausente; log com checkpoint pendente | Sim; valor restaurado a 10 |

A diferença mostra que a visibilidade do delta para esse callback depende do ciclo do StoreDict antes de sua execução. A ausência do delta nesse instante não demonstra que a edição ficou fora do histórico: nesta fixture, o rollback restaurou a alteração.

## Relação com o SDK 7.4.11

**CONFIRMADO NO SDK 7.4.11 — inspeção estática:** o callback reduzido acompanha os mecanismos já identificados nas fontes:

- **renpy.ast.Python.execute()** chama **renpy.config.python_callbacks** ao final da execução do nó Python.
- **Context.run()** transfere **Context.force_checkpoint** para **RollbackLog.force_checkpoint** quando rollback está habilitado.
- **RollbackLog.begin()** pode completar o registro anterior e chamar **StoreDict.get_changes(True)**, avançando a referência antiga do store.
- **renpy.rollback()** completa o registro corrente antes de restaurar entradas do histórico.
- O checkpoint solicitado por essa flag é soft; não equivale a uma barreira que impeça o rollback.

**OBSERVADO EM RUNTIME — fixture reduzida:** no cenário habilitado, o callback posterior não viu o delta, o log estava com **force_checkpoint=True**, e o rollback restaurou 99→10.

**INTERPRETAÇÃO apoiada pelas duas evidências:** a coleta/ciclagem do delta do StoreDict pode ocorrer antes do callback que a fixture instrumenta, enquanto a mutação ainda permanece representada pelo histórico reversível do Ren'Py. A fixture comprova o resultado de restauração para este escalar raiz, mas não instrumenta diretamente todas as estruturas internas do RollbackLog.

## Limites

- É uma reprodução reduzida de callback e edição por screen, não uma execução integrada do URM completo.
- O teste cobre uma variável escalar raiz; não estende automaticamente a conclusão para propriedades, objetos externos ou todos os containers.
- A fronteira de rollback é controlada no roteiro de teste; o teste não é uma sessão manual de jogo com o URM.
- Não prova que toda edição em qualquer momento seja desfeita pelo rollback, nem define o comportamento de save/load.
- Os resultados do cenário sem rollback e do cenário com rollback não devem ser misturados: diferem justamente no ciclo do StoreDict e na transferência do checkpoint.

## Fontes e reprodução

- Fixture: **URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy**, testcase **urm_storemonitor_callback_with_rollback_enabled**.
- Workflow: **.github/workflows/urm-choice-runtime-probe.yml**, passo “Run StoreMonitor callback with rollback enabled”.
- Resultado: run [39098551052](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098551052), job **choice-runtime**, conclusão **SUCCESS**.
- SDK: **renpy/ast.py**, **Python.execute**, blob SHA **d81ffc13f28f0b7442ba6905f1745ee838f7b185**.
- SDK: **renpy/python.py**, **StoreDict.get_changes** e **RollbackLog**, blob SHA **c5eb2819a3e4ee096dbf01130d70a77f9b623484**.
- SDK: **renpy/execution.py**, **Context.run**, blob SHA **547f73b26dad0fe08fda6333e5f4b60c97cf8772**.
- Fonte URM convertida: **classes/vars.rpy**, **StoreMonitorClass._m1_vars__pythonCallback**, blob SHA **57482937e14f215dac0ecb22a62da8ad160cba58**.

## Próximas questões

1. Executar o caminho com a implementação completa do StoreMonitor, incluindo watched e freeze, em ambiente controlado.
2. Repetir a medição em momentos diferentes: antes do menu, durante a interação, após seleção e após mais de um nó de jogo.
3. Testar edição e rollback para variáveis criadas e para mutações aninhadas, distinguindo o delta do StoreDict dos snapshots de objetos revertíveis.
4. Comparar save/load antes e depois da ciclagem do StoreDict para edição feita pela screen.
