# 27 — Freeze em runtime: escrita nativa, edição URM e callback

**Data:** 2026-10-18  
**SDK:** Ren'Py 7.4.11.  
**Fixture:** probe descartável; reproduz o hook e a lógica relevante de freeze do StoreMonitor, sem carregar o pacote completo do URM.

## Resultado

O run [39104245128](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39104245128) concluiu **SUCCESS**, incluindo o passo “Run StoreMonitor freeze native-versus-URM probe”.

O log registra:

```text
FREEZE_PROBE_BEFORE_NATIVE 10 True
FREEZE_PROBE_AFTER_NATIVE 10 True
FREEZE_PROBE_CALLBACK_BEFORE 10 30 True
FREEZE_PROBE_CALLBACK_AFTER 10 True
FREEZE_PROBE_AFTER_URM_EDIT 30 True
FREEZE_PROBE_AFTER_CALLBACK 9 True 10 30 10 True
END StoreMonitor freeze probe ... exit=0
```

Interpretação dos pontos:

1. A variável começa em 10 e está frozen.
2. A ação nativa Ren'Py SetVariable tenta mudar o valor; o helper interceptado mantém 10 e o estado continua frozen.
3. A ação URM reduzida SetVarValue muda o valor para 30. Ao concluir, a marca frozen continua ativa.
4. No callback posterior, o delta do store contém valor antigo 10 e valor corrente 30; o handler reduzido recebe ambos.
5. Com a variável ainda frozen, o handler usa Var.setValue para restaurar 10. O teste confirma que o freeze continua ativo após a restauração.

## O que fica confirmado

- **OBSERVADO EM RUNTIME (fixture reduzida):** uma chamada nativa via helper SetField pode ser impedida pelo handler quando a variável está frozen.
- **OBSERVADO EM RUNTIME (fixture reduzida):** a reprodução do SetVarValue do URM temporariamente remove o freeze, aplica a edição direta e reaplica o freeze.
- **OBSERVADO EM RUNTIME (fixture reduzida):** se o callback posterior ainda recebe o delta antigo 10 e o valor atual 30, o handler restaura 10 e mantém a variável frozen.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** essas rotas correspondem à lógica de StoreMonitor.handleVarChange e Var.setValue examinada no documento 26.

## Limites

- O handler e o estado de freeze são reproduções reduzidas; não foi carregado o pacote completo URM nem inicializado seu StoreMonitor real.
- Este primeiro testcase usou o contexto com rollback desabilitado. A comparação com rollback habilitado foi executada em separado e consta no [documento 28](28_FREEZE_ROLLBACK_RUNTIME.md): o callback não recebeu o delta, o valor permaneceu 30 até rollback e então retornou a 10.
- O probe testa uma variável escalar raiz e o helper nativo encontrado no SDK. Não testa atributos internos, containers, notificações de monitor ou arquivo .urm.
- O comportamento de uma variável frozen após edição URM com rollback habilitado ainda precisa ser observado diretamente: pode haver restauração no callback se o delta estiver disponível, ou apenas rollback nativo em momento posterior.

## Reprodução

- Fixture: **URM_REVERSO/tools/fixtures/urm_choice_runtime_probe.rpy**, testcase **urm_storemonitor_freeze_native_vs_urm**.
- Workflow: **.github/workflows/urm-choice-runtime-probe.yml**, passo “Run StoreMonitor freeze native-versus-URM probe”.
- Run: [39104245128](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39104245128).
- O workflow copia **renpy-7.4.11-sdk/the_question** para diretório temporário e executa a fixture nesse jogo descartável. Nenhuma fonte original do URM, SDK ou Wells é modificada.

## Próxima validação

O cenário com rollback habilitado está no documento 28. Próximos testes: validar notificações de variável monitorada separadamente do freeze e testar se metadados frozen/watch sobrevivem a save/load ou troca de jogo no URM completo.
