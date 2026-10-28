# 15 — Validação no SDK 7.4.11: ChoiceReturn, checkpoint, store e rollback

**Data:** 2026-10-16  
**Escopo:** confronto estático da leitura de Choices do URM com o SDK Ren'Py 7.4.11 no laboratório canônico.  
**Estado:** fluxo nativo de Menu, retorno da seleção, checkpoint e armazenamento reversível confirmados no código do SDK; edição confirmada na fonte convertida do URM; relato de rollback do usuário não reproduzido nesta investigação; save/load e testes runtime pendentes.  
**Proteções respeitadas:** nenhum arquivo de wells/, wells_beta/, do SDK ou das fontes URM foi alterado.

## 1. Retomada e localização do rollback

O documento 14 deixou a validação nativa pendente. A árvore atual do SDK não contém renpy/rollback.py. As classes Rollback e RollbackLog estão implementadas em renpy/python.py. A busca foi feita na árvore real do SDK, não por um caminho presumido.

Este documento complementa os documentos 14 e 06. Não os substitui nem transforma inspeção estática em teste runtime.

## 2. Fontes consultadas

Repositório mucholocco86/laborat-rio_renpy, branch main, árvore consultada em 2026-10-16, tree SHA eb9a50b0d3947940fb7ac7ba102d0b9a3eb520d7.

| Fonte | Blob SHA Git | Símbolos e intervalos |
|---|---|---|
| renpy-7.4.11-sdk/renpy/ast.py | d81ffc13f28f0b7442ba6905f1745ee838f7b185 | Menu.execute, linhas 1580–1705 |
| renpy-7.4.11-sdk/renpy/exports.py | 781b35b31522dafc6a24e7c3212d206c7bd6dfa5 | checkpoint 267–293; menu 966–1065; display_menu 1120–1300 |
| renpy-7.4.11-sdk/renpy/ui.py | 914a0c4702b7af391e014702a16ccc333e7573de | ChoiceActionBase 680–710; ChoiceReturn.__call__ 718–752 |
| renpy-7.4.11-sdk/renpy/python.py | c5eb2819a3e4ee096dbf01130d70a77f9b623484 | StoreDict 125–195; Rollback 1353–1551; RollbackLog 1550–2157 |
| renpy-7.4.11-sdk/renpy/execution.py | 547f73b26dad0fe08fda6333e5f4b60c97cf8772 | Context.run 475–620; rollback_copy 728–750; run_context 907–945 |
| URM convertido classes/choices.rpy | 48fc35f96119189e50f038981795115b3df7b770 | URMChoice.Action 87–93 |
| URM convertido classes/vars.rpy | 57482937e14f215dac0ecb22a62da8ad160cba58 | Var.setValue 232–269; SetVarValue 421–435; CreateVar 437–477; StoreMonitorClass 483–577 |

## 3. Fluxo nativo: Menu até o bloco selecionado

### 3.1 Preparação estrutural

**Confirmado no SDK 7.4.11 — ast.Menu.execute:**

1. Define inicialmente next_node(self.next), a continuação caso não haja resultado de Choice.
2. Enumera self.items com o índice estrutural original i.
3. Para item com bloco, acrescenta (label, condition, i) à lista de interação e aponta provisoriamente next_node ao primeiro nó do bloco.
4. Passa a lista para renpy.exports.menu.
5. Se o retorno não for None, usa esse valor como índice em self.items[choice] e define o próximo nó como o primeiro nó do bloco escolhido.

O valor da seleção é, portanto, o índice estrutural original em Menu.items. Filtros de condição ou menuset podem mudar quais alternativas aparecem, mas não renumeram o valor associado à alternativa. O Ren'Py recebe esse valor de volta e o usa para selecionar o bloco AST.

### 3.2 Condições e apresentação

**Confirmado no SDK — exports.menu e display_menu:**

- exports.menu avalia cada condition com renpy.python.py_eval.
- Com config.menu_actions, uma condição falsa pode ser omitida conforme menu_include_disabled; se for mostrada desabilitada, sua condição é transportada em ChoiceReturn.sensitive.
- Sem menu_actions, são mantidos apenas itens cuja condição é verdadeira. Nos dois caminhos, o valor associado continua sendo o valor original fornecido por Menu.execute.
- display_menu cria MenuEntry e associa ChoiceReturn à alternativa selecionável.
- Quando ui.interact termina, display_menu registra a alternativa escolhida, chama checkpoint(rv) e devolve rv a exports.menu. Menu.execute usa o valor para entrar no bloco correspondente.

### 3.3 ChoiceReturn

**Confirmado no SDK — ui.ChoiceReturn.__call__:** se houver um mapa chosen, marca nele (location, label); depois retorna self.value. A marcação da alternativa e o valor que encaminha a execução são operações distintas.

A ação do URM constrói ChoiceReturn(label, index) sem location. Pela implementação nativa, chosen é None, então essa chamada não grava persistent._chosen; ela retorna o índice.

## 4. Checkpoint e captura de mudanças do store

**Confirmado no SDK — exports.checkpoint e RollbackLog:**

- Depois da interação de menu, display_menu chama checkpoint(rv).
- O checkpoint marca o registro corrente como ponto de retorno. Se for hard, também pode incrementar rollback_limit; os dados de forward são tratados separadamente.
- RollbackLog.begin abre um novo período antes de executar um nó elegível. Quando já existe registro corrente, chama complete(True) antes de abrir o próximo.
- RollbackLog.complete coleta as mudanças de cada StoreDict em current.stores por meio de get_changes(begin), além de capturar dados de objetos revertíveis.
- StoreDict.get_changes compara o estado atual ao snapshot guardado no início do período e devolve, por chave, o valor anterior ou o marcador de remoção.
- Rollback.rollback reaplica os valores anteriores, remove chaves que ainda não existiam e restaura o Context associado ao registro.
- RollbackLog.rollback cria um registro corrente com cópia rollback do contexto e lança RestartContext ou RestartTopContext. run_context captura a exceção e executa novamente o contexto restaurado.

O armazenamento do valor anterior não depende de StoreMonitor: o SDK mantém deltas via StoreDict e RollbackLog para stores participantes do rollback. O período exato que contém uma edição acionada pela UI depende do estado do log naquele momento; isso ainda exige runtime.

## 5. Edição manual do URM

**Confirmado na fonte convertida do URM:** Var.setValue gera atribuição ou append direcionados a renpy.store; CreateVar usa setattr(renpy.store, ...). São escritas no store ativo do jogo, não edições do arquivo .rpy. Se a escrita atinge o StoreDict participante do log, o SDK tem o mecanismo de captura e reversão descrito acima.

**Conclusão limitada:** o código do SDK torna coerente o relato do usuário de que uma edição em execução pode afetar acontecimentos posteriores e ser desfeita ao voltar além do período que a contém. O relato continua classificado como RELATADO PELO USUÁRIO; não foi reproduzido nesta investigação e o registro/checkpoint exato ainda não está determinado para cada momento de edição.

### 5.1 StoreMonitor é uma camada distinta

O URM instala StoreMonitorClass, que tenta substituir o código de um método interno de atribuição do store, adiciona um callback em renpy.config.python_callbacks, e nesse callback define context().force_checkpoint = True e consulta get_changes(False). O monitor usa essas informações para notificar alterações ou restaurar valores congelados.

Isso é observação/congelamento do URM, separada do registro delta nativo. A fonte URM mostra que o callback pede um checkpoint futuro durante o tratamento de um nó Python. Ela não prova que toda edição feita por uma ação de tela passe por esse callback, nem que o callback seja o mecanismo que torna a atribuição reversível.

No SDK, Context.run transfere force_checkpoint ao RollbackLog antes da execução de um nó. RollbackLog.complete consome o sinal com checkpoint(hard=False). Esse checkpoint forçado é soft; não apaga o histórico nem cria necessariamente um novo limite hard para o contador de rollback.

## 6. rollback_is_fixed e a seleção do URM

**Confirmado na fonte URM:** antes de devolver o índice, URMChoice.Action atribui False diretamente a renpy.game.log.rollback_is_fixed.

**Confirmado no SDK:**

- in_fixed_rollback consulta esse booleano.
- ChoiceActionBase.get_sensitive usa o estado fixed e block_all para calcular a sensibilidade da ação.
- fix_rollback calcula fixed_rollback_boundary; durante a restauração, RollbackLog.rollback ativa rollback_is_fixed ao alcançar essa fronteira.
- Atribuir False ao booleano pode limpar o estado fixed naquele instante. Essa atribuição não remove entradas do log, não apaga a fronteira e não escolhe outro bloco AST.

**Pendente de runtime:** por que o URM limpa o estado nesse ponto, como isso se manifesta na tela modal sobreposta ao menu e como se comportam os casos de fixed rollback. Não inferir que essa linha desativa toda proteção de rollback.

## 7. Detalhe de CreateVar

CreateVar.__call__ testa if settableValue antes de atribuir. Nesse caminho, valores falsy como False, 0 e string vazia não são atribuídos. Essa conclusão estática é específica de CreateVar; não deve ser generalizada para Var.setValue, que converte os valores tipados em representações textuais antes do teste.

## 8. Classificação

| Afirmação | Classificação |
|---|---|
| Menu.execute usa o índice original de Menu.items e seleciona o bloco por esse índice | CONFIRMADO NO SDK 7.4.11 |
| Condições são avaliadas antes da interação e podem filtrar/desabilitar opções sem renumerar o valor estrutural | CONFIRMADO NO SDK 7.4.11 |
| display_menu registra checkpoint após a interação e retorna o valor da ação | CONFIRMADO NO SDK 7.4.11 |
| ChoiceReturn devolve o valor e só marca chosen quando há localização/mapa | CONFIRMADO NO SDK 7.4.11 |
| Rollback registra valores anteriores de StoreDict e restaura stores e Context | CONFIRMADO NO SDK 7.4.11 |
| A edição manual relatada afeta o jogo e pode ser revertida ao cruzar seu período | RELATADO PELO USUÁRIO; coerente com o modelo estático, runtime pendente |
| StoreMonitor é o mecanismo nativo que grava alterações para rollback | CONTRADITO: o SDK registra deltas via StoreDict/RollbackLog; o monitor é uma camada adicional URM |
| Toda edição acionada pela interface é capturada imediatamente pelo callback Python do URM | PENDENTE |
| O instante exato em que rollback de uma edição ocorre em cada posição relativa ao menu | PENDENTE |
| Semântica completa de save/load e stores próprios .urm | PENDENTE |

## 9. Testes necessários para fechar o circuito

Executar em fixture isolado de Ren'Py 7.4.11, sem alterar SDK ou Wells:

1. Criar duas alternativas com efeitos distintos; selecionar a segunda pelo URM e verificar índice e bloco executado.
2. Variar condição falsa, menu_actions e menu_include_disabled; registrar índice estrutural, ordem visual e sensibilidade.
3. Editar variável pela interface antes, durante e depois da tela de Choice; avançar e anotar valor, current, checkpoints e rollback_limit.
4. Aplicar rollback em passos e até antes da edição; verificar valor e alternativa reexecutada.
5. Repetir com variável congelada/monitorada para separar interceptação do URM da reversão nativa.
6. Salvar e carregar depois da edição, acompanhando save nativo, rollback log e stores .urm separadamente.
7. Testar fixed rollback com e sem a atribuição URM rollback_is_fixed = False, registrando sensibilidade e resultado.

Até esses testes, não atribuir um checkpoint específico à edição feita durante a interação, nem declarar concluído o circuito de save/load.


## Continuação — inspeção estática de save/load (2026-10-16)

O fluxo nativo de serialização e restauração do RollbackLog foi examinado em seguida, junto ao callback de Python do SDK e ao autoLoad dos arquivos URM. Consulte [02 — Save/load do SDK e persistência própria do URM](../06_RENPY_COMPATIBILITY/02_SDK_SAVELOAD_URM_PERSISTENCIA.md). A distinção entre save nativo e arquivo .urm está documentada; testes runtime e o ciclo completo de persistent/settings continuam pendentes.

## Atualização runtime posterior — 2026-10-28

Este documento registra corretamente a etapa estática inicial. A integração original do URM com o SDK 7.4.11 foi testada depois: docs [36](36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md), [38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md), [41](41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md) e [42](42_ROLLBACK_APOS_CHOICE_CONDICAO_FALSA.md) cobrem abertura da tela durante fixed rollback, seleção de condição falsa, execução do bloco e rollback nos roteiros descritos. Docs [46–47](47_SAVE_LOAD_CHOICE_PROCESSO_NOVO.md) cobrem save/load nativo.

Esses resultados resolvem somente os casos executados. Não demonstram todas as combinações de configuração, nem equivalência com outros SDKs.
