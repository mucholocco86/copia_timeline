# 53 — Persistência de Snapshots no save nativo Ren'Py

**Data:** 2026-10-28  
**Alvo:** URM X52 original com Ren'Py 7.4.11  
**Classificação:** fonte URM + SDK confirmados; comportamento observado em runtime isolado  
**Workflow:** [run 40670191468](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40670191468)

## Pergunta

Um snapshot criado por `x52URM.Snapshots.create()` sobrevive ao save nativo e ao load em um processo Ren'Py novo?

## Resultado observado

O workflow executou duas sessões de teste independentes, usando o SDK Ren'Py 7.4.11 e uma cópia descartável do jogo de teste `the_question`, com o pacote original do URM copiado sem alterações.

- **Processo 1:** o fixture confirmou que o snapshot ainda não existia, chamou `Snapshots.create("native-save-probe")`, confirmou sua existência, registrou `URM_SNAPSHOT_SAVE_BEFORE [u'native-save-probe']` e gravou o slot nativo. Após retornar ao runner, o snapshot continuou listado.
- **Processo 2:** uma nova execução confirmou que o singleton começou vazio (`URM_SNAPSHOT_NEW_PROCESS_BEFORE_LOAD []`), carregou o slot e registrou `URM_SNAPSHOT_AFTER_FRESH_PROCESS_LOAD [] False 17`. A asserção de que o snapshot não foi restaurado passou.

**Conclusão runtime delimitada:** no percurso testado, criar um objeto de snapshot e gravar depois um save nativo não fez com que a instância `x52URM.Snapshots` fosse restaurada no processo novo. O valor de gameplay 17 foi carregado, mostrando que o slot foi efetivamente carregado; o resultado não veio de uma falha do load.

As três tentativas anteriores (runs 40669566495, 40669769275 e 40669957168) falharam por configuração/controle inadequado do harness e são excluídas como evidência sobre persistência. A correção do quarto percurso habilitou rollback no fixture; só o run 40670191468 sustenta o resultado acima.

## Caminho na fonte do URM

Na fonte original:

- `classes/main.rpy`, blob SHA `14f93406d2946eaed664ed72c1d47063984ce24f`: o módulo `x52URM` é marcado `_constant = True` e cria o singleton `Snapshots = SnapshotsClass()`.
- `classes/snapshots.rpy`, blob SHA `20b45be23df8f12d7f4dfca7a1f401642d6fedba`: `SnapshotsClass.__init__` cria dicionários para snapshots e horários; `create()` preenche esses atributos. A classe não chama `URMFiles.save()` nesse caminho.
- `classes/ConstantStoreHandler.rpy`, blob SHA `0464cff856d2c03b79cada452fa55216e627dacd`: para versões Ren'Py abaixo de 7.6, o URM substitui `StoreDict.get_changes` para devolver deltas vazios a stores marcados `_constant`. Também remove esses stores de `rollbackLog.current.stores` e `delta_ebc` após `RollbackLog.complete`.

Isso confirma que o URM deliberadamente tira o store `x52URM` do delta normal de rollback nessa faixa de versões. A conclusão sobre save/load é corroborada pela execução em processo novo, em vez de depender apenas dessa intenção observada no código.

## Cruzamento com Ren'Py 7.4.11

Na implementação SDK examinada:

1. `RollbackLog.freeze()` fecha o registro com `complete(False)`, obtém raízes com `get_roots()` e prepara o estado serializável.
2. `get_roots()` seleciona stores registrados como alterados no histórico.
3. `renpy.loadsave.save()` serializa `(roots, log)`; o caminho de load restaura esses objetos e o log.

A adaptação do URM faz `x52URM` produzir deltas vazios e remove entradas desse store do registro corrente. A observação em runtime é compatível com o singleton não integrar as raízes restauradas nesse caso. O teste prova o resultado para este objeto, esta versão, este fixture e este percurso; não prova que todo objeto guardado em qualquer store marcado constante seja sempre omitido, nem que isso seja igual em outras versões.

## Distinções

- **Snapshot URM:** mapa de valores da tabela do store capturado pela classe `SnapshotsClass`, mantido em atributos do singleton `x52URM.Snapshots`.
- **Save nativo:** serialização de raízes e histórico do Ren'Py que restaurou o estado de gameplay do fixture.
- **Arquivo `.urm`:** stores próprios serializados pelo `URMFiles`; a classe Snapshots não foi encontrada como store registrado nesse fluxo.

Portanto, o nome “snapshot” do URM não significa que ele seja um slot de save nativo nem um arquivo persistente próprio.

## Inspeção da interface original

A tela original `screens/snapshots.rpy.x52`, blob SHA `5766c7f74987738de8d14cbe407f66e8c49b9871`, oferece criar, comparar, mostrar mudanças e remover. O diálogo `URM_snapshot_create` chama `Snapshots.create`. Não foi encontrado, nessa tela, botão ou caminho de exportação/salvamento do conjunto de snapshots. Isso é uma conclusão da interface examinada; não exclui funções externas ou módulos adicionais.

## Limites e pendências

- Teste integrado em runtime com o URM original e SDK 7.4.11, executado em cópia descartável.
- O harness cobre criação de snapshot, save nativo e load em processo novo; não cobre salvar e carregar dentro do mesmo processo, comparar snapshots após load, ou o fluxo visual da tela de Snapshots.
- A tela original examinada não apresenta ação de exportação. Não foi feita busca exaustiva por módulos externos ao URM ou por extensões de terceiros que exportem dados.
- Não extrapolar o comportamento para Ren'Py 6.99.4, 8.5.3 ou versões >= 7.6, nas quais o URM não instala essa adaptação conforme a condição da fonte.
- A frase da tela original de que snapshots se perdem ao fechar o jogo é uma declaração de interface; o teste acima é a evidência runtime do percurso de save/load.

## Fontes

- URM original `classes/main.rpy`, SHA `14f93406d2946eaed664ed72c1d47063984ce24f`.
- URM original `classes/snapshots.rpy`, SHA `20b45be23df8f12d7f4dfca7a1f401642d6fedba`.
- URM original `classes/ConstantStoreHandler.rpy`, SHA `0464cff856d2c03b79cada452fa55216e627dacd`.
- URM original `screens/snapshots.rpy.x52`, SHA `5766c7f74987738de8d14cbe407f66e8c49b9871`.
- SDK Ren'Py 7.4.11: `renpy/python.py` (`RollbackLog.complete/get_roots/freeze`) e `renpy/loadsave.py` (`save/load`), conforme inspeção do SDK e fontes registradas na revisão de persistência.
- Fixture isolada: `URM_REVERSO/tools/fixtures/urm_snapshot_save_persistence_probe.rpy`, blob SHA `063fc1d8e0436abc9807f99e37ce172d22f3c55d`.
- Workflow isolado: `.github/workflows/urm-snapshot-save-persistence-probe.yml`.
- Run runtime: [40670191468](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40670191468).
