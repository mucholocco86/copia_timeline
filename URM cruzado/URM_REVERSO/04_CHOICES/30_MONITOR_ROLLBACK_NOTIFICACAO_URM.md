# 30 — Monitor de edição URM com rollback habilitado

**Data:** 2026-10-18  
**SDK:** Ren'Py 7.4.11.  
**Evidência:** runtime em fixture reduzida, com monitor/callback de teste. O URM completo não foi carregado.

## Resultado

O run [39148219484](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148219484) terminou **SUCCESS**. No testcase **urm_storemonitor_urm_notification_with_rollback**, houve uma edição direta monitorada por SetVarValue:

```text
NOTIFY_PROBE_URM_FINAL 30 [] False None None 0
NOTIFY_PROBE_URM_BEFORE_ROLLBACK 30 [] False True
NOTIFY_PROBE_URM_AFTER_ROLLBACK 10 [] False
END URM notification with rollback probe ... exit=0
```

- Valor após ação: 30.
- Notificações registradas durante a ação: nenhuma.
- Hook SetField: nenhuma chamada (contador 0).
- Callback posterior: não registrou o delta do alvo (False, valor anterior None).
- Antes de rollback: valor 30, sem aviso e log com checkpoint pendente.
- Após rollback explícito: valor 10.

## Interpretação

**OBSERVADO EM RUNTIME (fixture reduzida):** quando a edição direta URM ocorre com rollback habilitado no contexto testado, o callback instrumentado não encontra o delta e não gera notificação. A mudança ainda é restaurada pelo rollback nativo.

Isso é coerente com o mecanismo de StoreDict.get_changes(False) e com as observações de edição/freeze no documento 28. Não demonstra que o URM completo sempre deixe de notificar: a integração real, o timing dos callbacks do jogo e o estado de NotificationsClass não foram executados.

## Comparação dos resultados disponíveis

| Caminho/teste | Hook imediato | Callback encontrou delta | Notificação no probe |
|---|---:|---:|---|
| SetVariable nativo, rollback desabilitado (doc 29) | Sim | Sim, repetidamente no harness | Uma imediata; callbacks posteriores repetiram chamadas |
| SetVarValue direto, rollback desabilitado (doc 29) | Não | Sim, repetidamente no harness | Nenhuma durante a ação; callback posterior adicionou registros |
| SetVarValue direto, rollback habilitado (doc 30) | Não | Não | Nenhuma até o rollback |
| SetVariable nativo, rollback habilitado (run 39148594202) | Sim | Não observado no callback | Uma imediata antes do rollback; o coletor revertível foi limpo pelo rollback |

### Contraponto: SetVariable nativo com rollback habilitado

O testcase **urm_storemonitor_native_notification_with_rollback** passou no run [39148594202](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148594202). Antes do rollback, o hook produziu a notificação imediata para 10→20; após rollback, o valor voltou a 10.

```text
NOTIFY_PROBE_NATIVE_BEFORE_ROLLBACK 20 [(u'Variable changed', u'urm_notify_probe_value', 10, 20)] False True
NOTIFY_PROBE_NATIVE_AFTER_ROLLBACK 10 [] False
END native notification with rollback probe ... exit=0
```

A lista coletora do harness é um valor do store revertível; por isso o rollback também limpou seu registro. Isso é característica da fixture e não demonstra o ciclo de vida da lista interna de NotificationsClass do URM. A observação sólida é que o hook emitiu aviso imediatamente antes do rollback, enquanto a variável foi restaurada.

Uma primeira versão desse testcase falhou porque exigia que a lista de registros continuasse preenchida depois do rollback. O assert foi removido e o run corrigido passou; a falha era da expectativa sobre o coletor reversível, não do comportamento do hook.

## Limitações

- O registro de notificações é uma lista simples no store de teste, não a Notification/overlay completa do URM; por ser revertível, o rollback limpa esse coletor.
- O handler reduzido usa o estado monitorado simulado e consulta deltas do store.
- Testou uma variável escalar raiz e uma fronteira explícita de rollback.
- Não testa a aparência, timeout, remoção ou persistência do aviso; nem efeitos em save/load.
- A fixture mantém metadados de monitor fora do estado reversível do jogo; isso não comprova ciclo de vida de flags no URM real.

## Reprodução

- Fixture: **URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy**, testcase **urm_storemonitor_urm_notification_with_rollback**.
- Workflow: **.github/workflows/urm-choice-runtime-probe.yml**, passo “Run StoreMonitor URM notification with rollback”.
- Run [39148219484](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148219484), edição URM monitorada com rollback, **SUCCESS**.
- Run [39148594202](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148594202), SetVariable monitorado com rollback, **SUCCESS**.
- Leitura fonte convertida: **classes/vars.rpy**, StoreMonitor.handleVarChange e callback; SHA **57482937e14f215dac0ecb22a62da8ad160cba58**.

## Próxima etapa

Testar a escrita nativa monitorada com rollback habilitado para separar aviso síncrono do hook e aviso posterior do callback. Depois, tentar a NotificationClass/tela verdadeira em ambiente isolado, ou marcar essa integração como não reproduzida se o pacote exigir dependências externas difíceis de carregar.
