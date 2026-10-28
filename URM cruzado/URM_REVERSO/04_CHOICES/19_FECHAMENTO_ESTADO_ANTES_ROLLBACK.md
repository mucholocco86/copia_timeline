# 19 — Fechamento do estado corrente antes do rollback

**Data:** 2026-10-16  
**Escopo:** interação entre ações de edição do URM, checkpoint solicitado pelo StoreMonitor e API de rollback no SDK Ren'Py 7.4.11.  
**Evidência:** inspeção estática das fontes convertidas do URM e do SDK; não houve teste runtime.

## Conclusão

No SDK 7.4.11, a função pública renpy.rollback() chama RollbackLog.complete() imediatamente antes de RollbackLog.rollback(...). O método complete atualiza os deltas de StoreDict e os snapshots dos objetos mutados antes de a restauração percorrer os registros.

Isso fornece uma explicação estática coerente para uma edição feita pelo URM entrar no histórico mesmo que tenha ocorrido após a última conclusão normal de um nó. A afirmação é sobre a implementação do SDK. Ainda não demonstra runtime que todas as ações/tipos de objeto do URM sigam esse caminho nem que todos os jogos permitam o mesmo ponto de rollback.

## Fontes consultadas

- SDK 7.4.11: renpy-7.4.11-sdk/renpy/exports.py, função rollback, linhas 1690–1740, blob SHA 781b35b31522dafc6a24e7c3212d206c7bd6dfa5.
- SDK 7.4.11: renpy-7.4.11-sdk/renpy/python.py:
  - Rollback.rollback, linhas próximas a 1504;
  - RollbackLog.begin, aproximadamente 1535–1610;
  - RollbackLog.complete, aproximadamente 1707–1760;
  - RollbackLog.checkpoint, aproximadamente 1822 em diante;
  - seleção do destino em RollbackLog.rollback, aproximadamente linhas 1930–1995.
  - blob SHA c5eb2819a3e4ee096dbf01130d70a77f9b623484.
- SDK 7.4.11: renpy-7.4.11-sdk/renpy/execution.py, Context.run, linhas 475–550, blob SHA 547f73b26dad0fe08fda6333e5f4b60c97cf8772.
- URM convertido: URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/vars.rpy, SetVarValue/Var.setValue e StoreMonitorClass, blob SHA 57482937e14f215dac0ecb22a62da8ad160cba58.
- URM convertido: URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/screens/vars.rpy, ações das screens de modificar/adicionar/criar, blob SHA 7959b2c0e6249df0edbb9ebe683481d46e4537e1.

## Ordem no SDK

### 1. Edição do estado

As ações da screen URM podem chamar SetVarValue/Var.setValue, CreateVar ou Var.delete. As operações resultantes podem alterar uma raiz no StoreDict ou mutar um container/objeto. Essa chamada, por si só, não é um checkpoint.

### 2. Captura de mudanças

RollbackLog.complete() é responsável por:

- consumir force_checkpoint quando a flag interna do log está ativa, criando checkpoint com hard=False;
- coletar os deltas dos StoreDicts por get_changes(...);
- materializar em current.objects os snapshots dos objetos mutados conhecidos pelo log.

O método documenta que pode ser chamado após execução de nó, antes de save ou imediatamente antes de rollback, e que deve ocorrer depois de uma atualização do store e antes da restauração.

### 3. Entrada na API de rollback

exports.rollback() primeiro verifica as condições de permissão/configuração, limpa o estado de skipping e então executa, nesta ordem:

    renpy.game.log.complete()
    renpy.game.log.rollback(...)

Assim, o registro corrente é atualizado imediatamente antes de o log restaurar checkpoints. No Rollback.rollback(), os snapshots de objetos e os valores antigos do StoreDict são reaplicados.

## Checkpoint do StoreMonitor: caminho e semântica

O StoreMonitor do URM define context().force_checkpoint = True em seu python callback. O SDK Context.run() transfere essa solicitação para RollbackLog.force_checkpoint em uma passagem posterior, quando a execução do nó satisfaz as condições para iniciar/atualizar rollback.

RollbackLog.complete() consome a flag interna chamando checkpoint(hard=False). Pelo SDK, esse é um checkpoint soft: marca o registro como checkpoint, mas não como hard_checkpoint. Na seleção de destino de RollbackLog.rollback, a contagem checkpoints é decrementada por hard_checkpoint; checkpoint soft só é contado no ramo on_load. Em rollback interativo normal, o log pode portanto percorrer registros que tenham apenas checkpoint soft até encontrar um hard checkpoint/estado de parada válido. hard=False não cria uma fronteira intransponível nem conta como uma chamada hard para o limite interativo.

Duas distinções:

- O callback do StoreMonitor não executa renpy.rollback() nem chama RollbackLog.complete() diretamente.
- Uma edição por ação de screen não executa por si só o callback ast.Python.execute do StoreMonitor.

Ainda assim, quando a operação nativa de rollback é efetivamente chamada, exports.rollback faz complete() antes da restauração. Esse fechamento captura deltas/snapshots pendentes independentemente de a screen ter acionado o callback do monitor.

## O que isso explica — e o que não prova

- **CONFIRMADO NO SDK 7.4.11:** a API renpy.rollback fecha o registro corrente com complete() imediatamente antes da restauração.
- **CONFIRMADO NO SDK 7.4.11:** complete coleta deltas de StoreDict e snapshots de objetos mutados; rollback reaplica esses estados anteriores.
- **CONFIRMADO NO SDK 7.4.11:** o checkpoint solicitado pelo StoreMonitor é soft, quando a flag chega ao RollbackLog e é consumida; a seleção de rollback interativo conta hard checkpoints, não checkpoints soft.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** edição pela screen chama ações próprias de edição e não a callback python_callbacks por meio de ast.Python.execute.
- **RELATADO PELO USUÁRIO:** após editar uma variável, avançar e voltar antes da edição, o valor pode retornar ao valor original.
- **HIPÓTESE MECÂNICA:** o relatório do usuário é consistente com a coleta final de deltas/snapshots antes do rollback.
- **PENDENTE:** identificar qual registro/checkpoint é escolhido em cada percurso específico, especialmente quando a edição ocorre durante uma interação/menu.
- **PENDENTE:** observar em runtime se o patch de atribuição do StoreMonitor intercepta algum caso de ação de screen e que notificação resulta.
- **PENDENTE:** verificar save/load e variações de fixed rollback com as mesmas ações.

## Limite do termo “checkpoint”

Neste circuito, checkpoint não significa salvar um arquivo persistente em disco. A chamada de RollbackLog.complete() atualiza o histórico reversível em memória. Save nativo é outra operação, também analisada no documento 02 da área de compatibilidade. Um checkpoint soft também não deve ser confundido com uma barreira hard que bloqueia rollback.

## Continuação recomendada

A próxima etapa é um teste runtime isolado no SDK 7.4.11, registrando a sequência de valores e posições AST para edição raiz, edição de item revertível, edição durante menu, avanço e rollback até antes da alteração. A matriz e as variáveis observadas devem ser anotadas sem alterar o SDK, o Wells ou as fontes originais do URM.
