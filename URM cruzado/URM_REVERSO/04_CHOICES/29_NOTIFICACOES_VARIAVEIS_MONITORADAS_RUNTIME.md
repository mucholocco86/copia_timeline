# 29 — Notificações de variáveis monitoradas: hook imediato e callback posterior

**Data:** 2026-10-18  
**SDK:** Ren'Py 7.4.11.  
**Evidência:** dois testcases em fixture isolada, com StoreMonitor e Notification reduzidos; não carrega o pacote completo do URM.

## Resultado runtime

O workflow [39148026518](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148026518) concluiu **SUCCESS**, incluindo os passos de notificação por SetVariable nativo e por edição URM.

### Escrita nativa via SetVariable

O log mostra que a notificação do hook ocorreu durante a sequência da ação de screen:

```text
NOTIFY_PROBE_BEFORE_ACTION 0
NOTIFY_PROBE_AFTER_ACTION 1 [(u'Variable changed', u'urm_notify_probe_value', 10, 20)]
```

A ação terminou com o valor 20 e um primeiro registro de notificação com valor anterior 10. Depois, o callback simplificado encontrou o mesmo delta StoreDict 10→20 repetidamente. Em cada chamada, o número de registros cresceu de 1 até 9. Isso demonstra repetição no harness sem rollback; não prova que uma sessão normal do URM mostre nove notificações na interface.

### Edição direta URM reduzida

O log separa a ação e o callback:

```text
NOTIFY_PROBE_BEFORE_ACTION 0
NOTIFY_PROBE_AFTER_ACTION 0 []
NOTIFY_PROBE_URM_FINAL 30 [] False None None 0
NOTIFY_PROBE_CALLBACK_BEFORE 10 30 0
NOTIFY_PROBE_CALLBACK_AFTER 1
NOTIFY_PROBE_CALLBACK_BEFORE 10 30 1
NOTIFY_PROBE_CALLBACK_AFTER 2
...
NOTIFY_PROBE_CALLBACK_BEFORE 10 30 8
NOTIFY_PROBE_CALLBACK_AFTER 9
```

Durante a ação, não houve notificação e o helper nativo não foi chamado. Depois, o callback viu o delta 10→30 e o handler criou registros. Como get_changes(False) não cicla o StoreDict, o callback simplificado voltou a ver o mesmo delta em várias chamadas no contexto testado.

O print URM_FINAL ocorreu dentro do nó Python antes da execução dos callbacks desse nó; portanto, seu array vazio comprova apenas ausência de notificação síncrona na ação, não ausência de notificação posterior.

## Interpretação do circuito

| Caminho de alteração | Momento da detecção no probe | Resultado |
|---|---|---|
| SetVariable nativo | Hook SetField durante a ação | Uma notificação imediata no registro da ação; o callback posterior também recebeu o delta |
| SetVarValue direto | Não passa pelo helper interceptado | Nenhuma notificação durante a ação; callback posterior notificou quando encontrou o delta |

**CONFIRMADO NA FONTE URM CONVERTIDA:** StoreMonitor.handleVarChange cria uma notificação quando a variável é monitored, mudou e a tela URM_modify_value não está aberta. O callback Python percorre os deltas do store e chama o mesmo handler.

**OBSERVADO EM RUNTIME (fixture reduzida):** os caminhos imediato e posterior são distintos; o callback repetiu o processamento do mesmo delta quando o ambiente não avançou o ciclo do StoreDict.

## Repetição de notificações: classificação cuidadosa

- **CONFIRMADO NO SDK 7.4.11 por inspeção estática:** StoreDict.get_changes(False) consulta deltas sem ciclar a referência antiga.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** Notifications.add cria e acrescenta um objeto à lista e reinicia a interação; não há deduplicação visível nesse método.
- **OBSERVADO EM RUNTIME (harness reduzido):** mantendo o mesmo delta disponível, múltiplas chamadas ao handler acrescentaram registros repetidos.
- **HIPÓTESE PENDENTE:** o StoreMonitor integral pode criar notificações repetidas caso receba o mesmo delta em callbacks sucessivos. O número observado no runner não deve ser transferido para gameplay, especialmente porque rollback habilitado pode ciclar o StoreDict antes do callback, como visto no documento 25.
- O próprio UI pode remover notificações por timeout ou por interação do usuário; este probe registra chamadas de add, não o comportamento visual de NotificationsClass.

## Limites do testcase

- A classe de notificação é um coletor simples de tuplas, sem a tela e sem restart_interaction de NotificationsClass.
- O handler reproduz apenas a condição monitored, mudança de valor e ausência da tela de edição.
- Testou um escalar raiz e contexto de test runner sem rollback.
- Não testou a edição pela tela real URM, o timeout, save/load dos metadados ou callbacks com rollback habilitado.
- Os asserts de término verificam o estado síncrono e o primeiro delta; a repetição posterior foi identificada pela sequência de log, não por um assert do número final de registros.

## Fontes e reprodução

- Fixture: **URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy**, testcases **urm_storemonitor_native_notification** e **urm_storemonitor_urm_notification**.
- Workflow: **.github/workflows/urm-choice-runtime-probe.yml**, passos “Run StoreMonitor native monitored notification” e “Run StoreMonitor URM monitored notification”.
- Run: [39148026518](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39148026518), conclusão **SUCCESS**.
- URM convertido: **classes/vars.rpy**, StoreMonitor, blob SHA **57482937e14f215dac0ecb22a62da8ad160cba58**.
- URM convertido: **classes/notifications.rpy**, NotificationsClass.add, blob SHA **3283ec4b1615967a71ad21cc34670bf8158ab96d5**.
- URM convertido: **screens/vars.rpy**, controles de monitor e tela URM_var_changed, blob SHA **7959b2c0e6249df0edbb9ebe683481d46e4537e1**.
- SDK 7.4.11: StoreDict.get_changes descrito nos documentos 18, 20 e 25.

## Próxima validação

Os dois caminhos com rollback habilitado estão no [documento 30](30_MONITOR_ROLLBACK_NOTIFICACAO_URM.md): a escrita nativa gerou aviso imediato antes do rollback; a edição direta URM não notificou no callback sem delta. Ainda falta a NotificationClass/tela verdadeira do URM convertido, se o pacote puder ser inicializado sem alterar fontes protegidas.
