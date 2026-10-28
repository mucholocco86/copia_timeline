# 28 — Freeze com rollback habilitado: a edição URM persiste até a restauração

**Data:** 2026-10-18  
**SDK:** Ren'Py 7.4.11.  
**Evidência:** runtime em fixture reduzida; o StoreMonitor original não foi carregado.

## Resultado runtime

O run [39104385145](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39104385145) terminou **SUCCESS**. No testcase **urm_storemonitor_freeze_with_gameplay_rollback**, a fixture executou:

1. Criou o valor 10, marcou a variável como frozen e estabeleceu um checkpoint anterior à edição.
2. Tentou escrita nativa por SetVariable: valor permaneceu 10 e frozen.
3. Aplicou a edição URM reduzida por SetVarValue: o valor passou a 30 e voltou a ficar frozen.
4. O callback Python posterior não encontrou o delta da variável no StoreDict; o valor continuou em 30.
5. Antes do rollback, o log indicava checkpoint pendente. O rollback explícito restaurou o valor a 10.

Trecho do log:

```text
FREEZE_PROBE_BEFORE_NATIVE 10 True
FREEZE_PROBE_AFTER_NATIVE 10 True
FREEZE_PROBE_AFTER_URM_EDIT 30 True
FREEZE_PROBE_AFTER_CALLBACK 9 False None None 30 True
FREEZE_PROBE_BEFORE_ROLLBACK 30 False True
FREEZE_PROBE_AFTER_ROLLBACK 10 True
END StoreMonitor freeze with rollback enabled ... exit=0
```

## Comparação dos dois contextos

| Etapa | Rollback desabilitado | Rollback habilitado |
|---|---|---|
| Escrita nativa em variável frozen | Bloqueada; continua 10 | Bloqueada; continua 10 |
| Edição URM reduzida | 10→30; freeze reaplicado | 10→30; freeze reaplicado |
| Callback posterior | Encontrou delta 10→30 e restaurou 10 | Não encontrou delta; valor ficou 30 |
| Rollback explícito | Não usado nesse caso | Restaurou 30→10 |

O resultado coincide, no escalar testado, com o relato do usuário: a edição pode influenciar a execução enquanto o jogador avança e pode ser desfeita ao retornar a um estado anterior à edição.

## Interpretação e limites

- **OBSERVADO EM RUNTIME (fixture reduzida):** com rollback habilitado, o handler do callback não recebeu o delta; portanto, o caminho de freeze do callback não restaurou imediatamente a edição. O rollback do Ren'Py restaurou o escalar ao valor anterior.
- **CONFIRMADO NO SDK 7.4.11 por inspeção estática:** rollback fecha o estado corrente e restaura deltas/snapshots do histórico; veja documentos 15, 19 e 25.
- A fixture representa metadado frozen em conjunto de teste fora do StoreDict reversível. O valor do jogo participa do rollback, mas a persistência do metadado frozen no URM real não foi testada aqui.
- O StoreMonitor é uma reprodução estreita: hook de SetField, política de bloqueio para frozen e callback simplificado. Não é integração da fonte convertida completa.
- O teste percorre um único checkpoint dirigido e uma variável escalar raiz. Não prova que toda edição e todo rollback em qualquer jogo tenham o mesmo ponto de fronteira.
- Save/load, monitor/notification e containers continuam fora deste caso.

## Fontes e reprodução

- Fixture: **URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy**, testcase **urm_storemonitor_freeze_with_gameplay_rollback**.
- Workflow: **.github/workflows/urm-choice-runtime-probe.yml**, passo “Run StoreMonitor freeze with rollback enabled”.
- Run: [39104385145](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39104385145), conclusão **SUCCESS**.
- Modelo de fonte: URM convertido **classes/vars.rpy**, StoreMonitor/Var.setValue, blob SHA **57482937e14f215dac0ecb22a62da8ad160cba58**.
- SDK: Ren'Py 7.4.11; mecanismo de store/checkpoint/rollback detalhado nos documentos 15, 19, 25.

## Conclusão provisória

Para este circuito reduzido, freeze bloqueia mudanças que passam pelo helper nativo e permite a edição direta do URM. Com rollback habilitado, o callback pode não receber o delta dessa edição, mas o histórico nativo ainda restaurou o valor ao cruzar o checkpoint anterior. A integração com URM completo e a persistência do metadado frozen precisam de prova própria.
