# 23 — StoreMonitor: interceptação de atribuições e edição do URM

**Data:** 2026-10-18  
**Escopo:** distinção entre o callback Python do StoreMonitor, o helper de atribuição das ações nativas do Ren'Py e as ações de edição próprias do URM.  
**Referência principal:** Ren'Py SDK 7.4.11.  
**Evidência:** leitura estática e teste runtime concluído com sucesso na fixture reduzida do SDK 7.4.11; isso não é uma integração completa do URM.

## Resultado

A frase “a edição por screen não aciona o StoreMonitor” precisa de qualificação. Há dois circuitos independentes:

1. **Callback `renpy.config.python_callbacks`:** chamado ao final de `renpy.ast.Python.execute()`, fora de `init_phase`. Uma ação de screen não é, por si só, um nó `ast.Python`.
2. **Interceptação do helper de ações de campo:** o StoreMonitor tenta localizar no store `_m1_00action_data__set_field` ou `_set_field`, clona a função e substitui o `func_code` da original por `_m1_vars__injectableSetField`. Isso intercepta atribuições que passam por esse helper.
3. **Edição URM reduzida:** `Var.setValue` executa uma expressão `renpy.store.<caminho> = valor` (ou a mutação de container correspondente); `CreateVar` chama `setattr(renpy.store, ...)`; `Var.delete` usa `delattr`, `del` de item ou exclusão de raiz. Esses caminhos não chamam `_set_field` por sua implementação.

Portanto, o hook pode observar as ações nativas `SetVariable/SetField`, mas a fonte convertida não indica que ele intercepte diretamente as atribuições próprias de `SetVarValue` ou `CreateVar`. Isso **não** significa que o StoreMonitor jamais observe uma edição URM: o callback posterior consulta deltas do `StoreDict` após outro nó Python, enquanto o log de rollback também coleta estado em `RollbackLog.complete()`.

## Fontes e símbolos

| Fonte | Símbolo / trecho | SHA do blob |
|---|---|---|
| SDK 7.4.11 `renpy/python.py` | `StoreModule.__setattr__`: delega para `self.__dict__[key] = value`; `StoreDict` é o dicionário do módulo | `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| SDK 7.4.11 `renpy/common/00action_data.rpy` | `__set_field` resolve o objeto e chama `setattr(obj, attr, value)`; `SetVariable.__call__` percorre esse helper por `SetField` | `9cc515b3938d5db6128f68c1403b33a82d85cb72` |
| URM convertido `classes/vars.rpy` | `Var.setValue`, `CreateVar`, `StoreMonitorClass.init`, `injectableSetField`, `pythonCallback` | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| URM convertido `screens/vars.rpy` | ações ligadas à edição, criação e exclusão | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |
| SDK 7.4.11 `renpy/ast.py` | `Python.execute`, callback no `finally` | `d81ffc13f28f0b7442ba6905f1745ee838f7b185` |
| SDK 7.4.11 `renpy/execution.py` | `Context.run`, transferência de `Context.force_checkpoint` | `547f73b26dad0fe08fda6333e5f4b60c97cf8772` |

## Caminho das ações nativas

No SDK, `StoreModule.__setattr__` grava no `StoreDict`. A função nativa `SetVariable` devolve uma ação `SetField`; ao executá-la, `SetField.__call__` chama `__set_field`, que usa `setattr` sobre o objeto alvo. O URM tenta substituir a função desse helper por um wrapper que chama `StoreMonitor.handleVarChange` antes de encaminhar para a função original.

Quando o atributo alvo é o store raiz, a rota nativa passa então pelo helper observado pelo hook.

## Caminho próprio do URM

Na fonte convertida, `SetVarValue.__call__` delega a `Var.setValue`. Para o valor raiz, `Var.setValue` constrói código textual e executa `renpy.store.<nome> = valor`. Para propriedades internas e containers, a expressão pode mutar o atributo/item diretamente. `CreateVar` usa `setattr(renpy.store, nome, valor)`. Nenhum desses trechos chama a ação `SetVariable` ou o helper `__set_field`.

Essa leitura explica por que a interceptação de `__set_field` não deve ser atribuída automaticamente às ações de edição do próprio URM.

## Relação com callback e rollback

A ausência do helper não elimina os mecanismos seguintes:

- O callback de `python_callbacks` é executado ao final do nó Python e consulta `StoreDict.get_changes(False)`; uma edição feita antes desse nó pode aparecer como delta, embora o callback não seja síncrono com o clique da screen.
- O executor transfere `Context.force_checkpoint` ao log durante uma passagem subsequente de `Context.run`.
- `renpy.rollback()` chama `RollbackLog.complete()` antes de restaurar o histórico, o que atualiza deltas de store e snapshots de objetos mutados.

A sequência temporal para uma edição feita com o URM enquanto uma interação está aberta ainda depende do fluxo de execução específico do jogo e precisa ser verificada na fixture/runtime. Ver também os documentos 18, 19 e 22.

## Classificação

- **CONFIRMADO NO SDK 7.4.11:** `StoreModule.__setattr__` grava no dicionário do store; `SetVariable` percorre `__set_field`.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** StoreMonitor troca o código da função helper quando encontra um dos nomes previstos; `Var.setValue` e `CreateVar` usam atribuição direta.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** callback e hook de atribuição são mecanismos separados.
- **HIPÓTESE:** hookeando o helper, o URM observa chamadas nativas de `SetVariable/SetField` em atribuições ao store raiz.
- **OBSERVADO EM RUNTIME (fixture reduzida):** o helper disponível foi `_m1_00action_data__set_field`; após `SetVariable`, contador do hook=1 e valor=20; após `SetVarValue` reduzido, contador permaneceu 1 e valor=30. O testcase terminou com exit 0 no run 39098070978.
- **OBSERVADO EM RUNTIME (fixture reduzida):** sem rollback, callback posterior encontrou delta 10→99; com rollback habilitado, callback posterior não encontrou o delta, o log estava com checkpoint pendente e rollback restaurou 99→10. Ver documentos 24 e 25. Isso ainda não testa notificação/freeze do StoreMonitor completo.
- **PENDENTE:** repetir com URM completo, caso seja possível carregar o pacote convertido em ambiente controlado. A fixture atual só reproduz os métodos relevantes; não é uma integração do URM original.

## Prova runtime preparada

Fixture: `URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy`, testcase `urm_storemonitor_assignment_hook`.  
Workflow isolado: `.github/workflows/urm-choice-runtime-probe.yml`, passo “Run StoreMonitor assignment-hook contrast”.

A prova clona e instrumenta temporariamente o helper em uma cópia descartável, executa `SetVariable` nativo e, em seguida, a ação reduzida `SetVarValue`; asserts comparam contagem do hook e valor final. Não modifica o SDK versionado, o Wells, nem as fontes originais do URM.

A execução final [39098070978](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098070978) concluiu **SUCCESS**. O log traz `STOREMONITOR_HOOK_METHOD _m1_00action_data__set_field`, `STOREMONITOR_AFTER_NATIVE_SETVARIABLE 1 20`, `STOREMONITOR_AFTER_URM_SET 1 30` e `STOREMONITOR_ASSERTIONS _m1_00action_data__set_field 1 30`. As execuções anteriores [39093314766](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39093314766) e [39097924784](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39097924784) imprimiram os mesmos valores, mas falharam ao sincronizar a label do test runner; a versão corrigida encerra e valida os asserts na própria label de verificação. O run [39093312665](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39093312665) foi cancelado pela concorrência.

## Próximos passos

1. Testar em runtime o callback Python posterior, separadamente da interceptação síncrona.
2. Retomar o circuito da interação/menu: edição URM → seleção Choice → nó Python seguinte → callback → checkpoint soft → rollback.
3. Atualizar o documento 19 com referência cruzada a esta validação.
