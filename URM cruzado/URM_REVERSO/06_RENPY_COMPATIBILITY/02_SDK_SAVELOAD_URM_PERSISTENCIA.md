# 02 — Save/load do SDK e persistência própria do URM

**Data:** 2026-10-16  
**Escopo:** leitura estática do save/load nativo Ren'Py 7.4.11 e comparação com arquivos e stores próprios do URM convertido.  
**Estado:** 🔵 save/load nativo e callbacks de Python confirmados no código do SDK; 🟢 carregamento e conteúdo dos arquivos .urm confirmados na fonte convertida; 🟡 comportamento observado pelo usuário continua sem reprodução nesta investigação; 🔴 não houve execução runtime.  
**Isolamento:** somente documentação em URM_REVERSO foi alterada.

## 1. Fontes e revisão

Repositório mucholocco86/laborat-rio_renpy, branch main, árvore consultada em 2026-10-16, tree SHA b0ba131534657d8ea5e6b39846e571b0ef80d64f.

| Fonte | Blob SHA Git | Símbolos/intervalos |
|---|---|---|
| SDK renpy/ast.py | d81ffc13f28f0b7442ba6905f1745ee838f7b185 | Python.execute, linhas 907–936 |
| SDK renpy/config.py | dea7cbd33fb6826e6dbd3ed2026ccbed63177060 | python_callbacks, linha 485 |
| SDK renpy/loadsave.py | c8b831ebfd5487f11a1d4dde8c87cde7f7ed93e3 | save, 373–425; load, 762–772 |
| SDK renpy/python.py | c5eb2819a3e4ee096dbf01130d70a77f9b623484 | StoreDict 125–195; RollbackLog.freeze 2133–2156; unfreeze 2157–2206; rollback 1945–2115 |
| URM convertido classes/URMFiles.rpy | 888aba28d9d2e7870d8c4e6526417390179cd326 | URMFilesClass.load/autoLoad 5–94; URMFileStore/URMFile 194–372 |
| URM convertido classes/vars.rpy | 57482937e14f215dac0ecb22a62da8ad160cba58 | VarsStore.store/watchedStore e flags 5–80 |
| URM convertido classes/settings.rpy | 13fd70596135c4389c9ab01cae982f80bfcad461 | Settings.get/set e arquivo global 120–225 |
| URM convertido classes/main.rpy | 14f93406d2946eaed664ed72c1d47063984ce24f | afterLoad 38–68; callbacks/load de módulos 194–208 |
| URM convertido classes/gamesaves.rpy | bbedbd08f9ce106c77a12bdb984e11008cf995bf | GameSavesClass.load/save 5–52 |

## 2. Callback Python do Ren'Py

**Confirmado no SDK 7.4.11:** ast.Python.execute executa py_exec_bytecode e, em um bloco finally, percorre renpy.config.python_callbacks quando o contexto não está em init_phase. Portanto, esse callback está associado à execução de um nó Python do script; não é um observador global chamado automaticamente após qualquer mudança em qualquer tela.

A fonte convertida do URM descreve StoreMonitor._m1_vars__pythonCallback como chamado após nó Python. O código desse callback define context().force_checkpoint = True e consulta StoreDict.get_changes(False).

O SDK Context.run lê force_checkpoint no início do próximo nó elegível, chama RollbackLog.begin e transfere o sinal para RollbackLog.force_checkpoint. RollbackLog.complete consome esse sinal ao completar o registro e chama checkpoint(hard=False). A sequência comprova um pedido de checkpoint soft relacionado à execução de nós Python; não comprova que toda ação de botão passe pelo callback nem que o checkpoint aconteça no mesmo instante da atribuição.

**Consequência para a análise anterior:** o StoreMonitor do URM tem duas atividades distintas: o hook de atribuição tenta interceptar escritas; o callback de Python examina deltas depois de nós Python e sinaliza checkpoint. O registro de deltas reversíveis continua sendo fornecido pelo SDK via StoreDict/RollbackLog.

## 3. Save nativo: estado atual e histórico de rollback

**Confirmado no SDK 7.4.11:**

1. renpy.loadsave.save chama renpy.game.log.freeze(None).
2. RollbackLog.freeze chama complete(False), determina roots do estado do jogo e remove informações de objetos inalcançáveis do histórico.
3. O save serializa, via pickle configurável do Ren'Py, o par (roots, renpy.game.log).
4. Cada Rollback contém Context, alterações anteriores de stores, alterações de objetos reversíveis, checkpoints e dados auxiliares; o RollbackLog também mantém limites e sequência de rollback.
5. renpy.loadsave.load deserializa roots e log e chama log.unfreeze(roots, label="_after_load").
6. RollbackLog.unfreeze instala o log como log ativo, limpa os stores, restaura as raízes serializadas e chama rollback(0, force=True, on_load=True). O fluxo então reinicia o contexto; o load não é simplesmente uma atribuição isolada do store atual.

Assim, o save nativo inclui o estado serializado necessário para restaurar o jogo e o histórico de rollback mantido pelo log. Isso é distinto de um arquivo .urm. O quanto do histórico fica disponível depende dos checkpoints e limites preservados no log; a configuração e os casos runtime não foram testados aqui.

## 4. Arquivos .urm: dados do URM, não snapshot geral do jogo

### 4.1 O que URMFiles.load e autoLoad fazem

**Confirmado na fonte URM convertida:**

- URMFiles.autoLoad consulta Settings.lastLoadedFile e chama URMFiles.load quando há um arquivo anterior e nenhum arquivo URM diferente está ativo/alterado.
- URMFiles.load cria um URMFile, verifica seu lastModifiedPath, opcionalmente converte formato legado, atribui o objeto a URMFiles.file e atualiza Settings.lastLoadedFile.
- Essa função não percorre as variáveis do jogo nem executa Var.setValue. Ela carrega o objeto de dados do URM.
- afterLoad é chamado na inicialização do label start e também é registrado em renpy.config.after_load_callbacks; ele instala a interface/monitor e chama URMFiles.autoLoad.

Logo, autoLoad reabre as informações próprias do URM após início/carregamento. A edição de uma variável em jogo é uma ação separada de interface que passa por Var.setValue; não é produzida pela mera leitura do ZIP .urm.

### 4.2 O que os stores do arquivo guardam

VarsStoreClass acessa URMFiles.file['vars'] para nomes lembrados e metadados como nome de exibição, frozen e monitor. watchedStore usa URMFiles.file['watched'] para a lista do painel de observação. Esses dados descrevem a configuração e organização das ferramentas do URM; não constituem, por si, valores correntes das variáveis do jogo.

O código da classe URMFile lê e grava stores como entradas ZIP codificadas em JSON. URMFile.save grava primeiro em um caminho temporário .new e move para o arquivo final; se houver caminho de saves, tenta copiar o arquivo para lá. lastModifiedPath escolhe a cópia mais recente entre gameDir e saveDir.

Essa leitura suporta o limite já registrado no documento 12: não tratar .urm como cópia integral do estado do jogo. A fonte examinada mostra stores de metadados/configuração. Outros consumidores e stores devem continuar a ser mapeados módulo por módulo.

## 5. Persistências separadas identificadas

| Mecanismo | Conteúdo confirmado | Carregamento |
|---|---|---|
| Save nativo Ren'Py | roots do estado e RollbackLog serializados | load deserializa e chama RollbackLog.unfreeze |
| Arquivo .urm do URM | stores do URM serializados como entradas JSON em ZIP | URMFiles.load recupera um URMFile e o define como ativo |
| Settings por jogo | Settings.get/set usa persistent.URMSettings | lido pelo objeto Settings |
| Settings global do URM | ZIP próprio chamado settings, entradas json/id/urmVersion | Settings._loadGlobalSettings |
| Slots nativos oferecidos pelo URM | Gamesaves chama renpy.save/renpy.load | usa o save/load do motor |

A interação interna do Ren'Py com persistent e o momento completo em que settings globais são carregados devem ser rastreados separadamente antes de afirmar seus detalhes de ciclo de vida.

## 6. Conclusões classificadas

| Afirmação | Classificação |
|---|---|
| Save nativo serializa roots do jogo junto com RollbackLog | CONFIRMADO NO SDK 7.4.11 |
| Load nativo restaura roots, reinstala log e reinicia via rotina de unfreeze/rollback | CONFIRMADO NO SDK 7.4.11 |
| python_callbacks são chamados no finally de execução de nó Python fora de init_phase | CONFIRMADO NO SDK 7.4.11 |
| O callback do StoreMonitor do URM observa mudanças após nó Python e sinaliza force_checkpoint | CONFIRMADO NA FONTE URM |
| URMFiles.autoLoad restaura um URMFile ativo, sem aplicar valores de variáveis do jogo por conta própria | CONFIRMADO NA FONTE URM examinada |
| Stores vars/watched guardam metadados/listas do URM, não um snapshot geral dos valores de jogo | CONFIRMADO NA FONTE URM examinada |
| Edição por ação de tela sempre aciona python_callbacks | NÃO DEMONSTRADO; não presumir |
| O usuário observou que rollback pode desfazer edição manual | RELATADO PELO USUÁRIO; sem reprodução runtime nesta investigação |
| Ciclo completo de persistent/global settings entre início, load e saves | PENDENTE |
| Duração e limites efetivos de rollback após load em jogo real | PENDENTE DE RUNTIME |

## 7. Próxima etapa recomendada

Continuar a árvore de pesquisa e edição seguindo as telas que acionam as classes, preservando a distinção entre dados de jogo e metadados URM:

1. Rastrear CodeView → link de variável → tela de edição → SetVarValue/CreateVar → store.
2. Rastrear Search → resultados → ações disponíveis para cada tipo de variável/objeto.
3. Identificar quais stores URM são preenchidos por Choices, Labels, TextRepl, Snapshots e States.
4. Inspecionar carregamento de persistent/global settings e callback after_load no SDK.
5. Depois montar uma matriz runtime isolada para edição antes/durante/depois de menus, rollback, save e load.

O documento 15 valida o circuito estático Menu/ChoiceReturn/checkpoint/store/rollback. Este documento fecha a inspeção estática do caminho nativo de save/load e distingue sua persistência da carga dos dados próprios do URM; os efeitos em execução continuam pendentes de teste.

## Revisão posterior — testes runtime até 2026-10-28

O status acima é histórico e descreve a inspeção de 2026-10-16; testes posteriores atualizaram partes que estavam pendentes:

- Edição de variável pelo URM e rollback foram observados no doc [38](../04_CHOICES/38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md); o callback do StoreMonitor não recebeu aquela chave no cenário rastreado, enquanto o delta nativo permitiu restaurar o valor (doc [39](../04_CHOICES/39_STOREMONITOR_DELTA_E_EDICAO_POR_SCREEN.md)).
- Save/load nativo foi observado na mesma sessão e em processo Ren'Py novo (docs [46](../04_CHOICES/46_SAVE_LOAD_NATIVO_APOS_EDICAO_CHOICE.md) e [47](../04_CHOICES/47_SAVE_LOAD_CHOICE_PROCESSO_NOVO.md)).
- Stores `.urm` foram salvos/carregados em dois processos (docs [49](../04_CHOICES/49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md), [50](../04_CHOICES/50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md) e [06_VARIABLES/03](../06_VARIABLES/03_MAPA_CANAIS_PERSISTENCIA_URM.md)).
- Settings por jogo e globais foram recuperados em processo novo, conforme run 40666289110 e o mapa de persistência.

**Ainda pendente:** interação visual completa de Gamesaves/Confirm; persistência de Snapshots no save nativo; matriz ampla de combinações entre save nativo e load `.urm`; comparação com outros SDKs. Os testes acima não provam equivalência fora do Ren'Py 7.4.11.
