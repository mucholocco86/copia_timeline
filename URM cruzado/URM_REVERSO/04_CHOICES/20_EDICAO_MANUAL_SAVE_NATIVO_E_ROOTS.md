# 20 — Edição manual e save nativo: raízes e ciclos do StoreDict

**Data:** 2026-10-16  
**Escopo:** relação estática entre mutações feitas pelo URM, a rotina nativa de save/load do Ren'Py 7.4.11 e o arquivo próprio .urm.  
**Evidência:** inspeção estática; nenhum save/load runtime foi executado.

## Conclusões

- **CONFIRMADO NO SDK 7.4.11:** renpy.save chama RollbackLog.freeze(), serializa o par (roots, RollbackLog) no save nativo; freeze chama complete(False), calcula roots e filtra objetos não alcançáveis.
- **CONFIRMADO NO SDK 7.4.11:** get_roots() monta roots a partir de StoreDict.ever_been_changed; para cada nome marcado, inclui seu valor atual ou o marcador deleted.
- **CONFIRMADO NO SDK 7.4.11:** complete(False) solicita StoreDict.get_changes(cycle=False). Essa leitura não atualiza ever_been_changed; a atualização ocorre no ramo cycle=True.
- **HIPÓTESE DE COBERTURA A TESTAR:** um valor alterado pela ação de screen imediatamente antes de save pode depender de o nome já estar em ever_been_changed ou de uma captura normal anterior. Não se pode afirmar só pela fonte que um nome recém-criado/até então não alterado será incluído nos roots do save apenas por complete(False).
- **PENDENTE:** observar se o log/contexto e o ciclo de load cobrem todos os casos de edição manual recente, sobretudo nome recém-criado, variável raiz anteriormente alterada, container mutado in-place, e save a partir de uma interação aberta.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** o circuito de Gamesaves chama renpy.save/renpy.load. Os arquivos .urm são carregados/salvos como estrutura própria do URM; a evidência examinada não mostra a escrita do valor arbitrário do jogo no .urm.

## Fontes

- SDK renpy-7.4.11-sdk/renpy/loadsave.py, blob SHA c8b831ebfd5487f11a1d4dde8c87cde7f7ed93e3:
  - save(): linhas 373–420; chama renpy.game.log.freeze(None) e serializa (roots, log);
  - load(): linhas 762–771; lê roots/log e chama log.unfreeze(roots, label="_after_load").
- SDK renpy-7.4.11-sdk/renpy/python.py, blob SHA c5eb2819a3e4ee096dbf01130d70a77f9b623484:
  - StoreDict.get_changes(): linhas 120–165;
  - RollbackLog.complete(): linhas 1707–1755;
  - RollbackLog.get_roots(): linhas 1757 em diante;
  - RollbackLog.freeze(): linha 2133 em diante;
  - RollbackLog.unfreeze(): em seguida.
- URM convertido:
  - classes/gamesaves.rpy, blob SHA bbedbd08f9ce106c77a12bdb984e11008cf995bf, Gamesaves.save/load aproximadamente linhas 24–50;
  - classes/URMFiles.rpy, blob SHA 888aba28d9d2e7870d8c4e6526417390179cd326, autoLoad/load aproximadamente linhas 61–90;
  - para produtores/consumidores dos stores .urm, veja também ../06_RENPY_COMPATIBILITY/02_SDK_SAVELOAD_URM_PERSISTENCIA.md.

## Caminho nativo de save

A implementação de loadsave.save() obtém o estado com:

    roots = renpy.game.log.freeze(None)

Depois serializa roots junto com RollbackLog. freeze() chama complete(False), executa get_roots() e purga do log objetos que não sejam alcançáveis a partir dos roots. A operação é distinta de salvar um arquivo .urm.

loadsave.load() desserializa roots e log, então chama log.unfreeze(...). A rotina unfreeze reinstala o log, limpa os stores para sua base limpa, aplica roots e entra no caminho nativo de rollback/on_load para retomar em um ponto aceitável. Isso confirma que save/load inclui estado nativo e histórico; não prova sozinho como uma edição específica é retomada.

## O detalhe de cycle=False

StoreDict.get_changes(cycle) compara a captura antiga (old) com o estado atual. Só quando cycle=True:

1. substitui old pela captura atual;
2. adiciona nomes novos ao conjunto ever_been_changed;
3. retorna os nomes adicionados no delta de ebc.

RollbackLog.complete(begin) passa begin como o argumento cycle de get_changes(begin). Em freeze(), complete(False) é chamado. Portanto, a conclusão de save coleta mudanças para o registro corrente sem avançar esse conjunto de nomes nesse mesmo passo.

Separadamente, get_roots() percorre ever_been_changed para construir o mapa serializado. Essa diferença torna relevante saber se a variável já havia sido marcada por um ciclo anterior. Um nome raiz alterado durante execução de script e já marcado aparece com seu valor atual nos roots; uma edição recente em nome não marcado não pode ser presumida coberta por essa lista apenas pelo caminho complete(False).

## Containers mutados in-place

Para RevertableList/RevertableDict, o histórico de objetos registra snapshots distintos dos deltas de raiz. complete(False) ainda coleta snapshots do RollbackLog.current.objects. O save serializa o próprio log, que contém esses registros. A preservação e a ligação da referência do container após clean_stores()/unfreeze dependem da alcançabilidade e do estado do store; a fonte estática consultada não basta para declarar todos os casos de container garantidos.

StoreDict.get_changes não copia o conteúdo interno do container. Para objetos revertíveis, os snapshots de mutação seguem a rota de objetos; não confundir essa rota com a inclusão da variável raiz em roots.

## Arquivo .urm versus save do jogo

A interface Gamesaves do URM delega a renpy.save e renpy.load, portanto usa o formato e o ciclo nativos do Ren'Py.

URMFiles mantém outro artefato: um arquivo ZIP próprio com stores/metadados das ferramentas. autoLoad chama URMFiles.load para selecionar esse arquivo ativo. O código examinado não mostra autoLoad copiando para o .urm qualquer variável arbitrária modificada no store do jogo.

Logo, a formulação segura é:

- save nativo do Ren'Py: serializa roots do jogo e RollbackLog;
- arquivo .urm: guarda estruturas próprias do URM identificadas em seus stores;
- a inclusão e recuperação de cada edição manual específica em um save nativo ainda exige teste controlado.

## Matriz mínima para runtime

| Caso | O que medir no instante do save | Questão |
|---|---|---|
| Variável já alterada pelo script e depois editada pelo URM | ever_been_changed, roots, valor antes/depois do load | o save preserva o valor editado |
| Variável criada pelo URM e save imediato | presença do nome em ever_been_changed e roots | o nome recém-criado entra no save |
| Nome existente nunca alterado pelo script, editado e salvo imediatamente | StoreDict.old, current.stores, roots | a edição recente aparece após load |
| Container revertível atribuído antes e depois mutado | identidade, snapshot de objeto, raiz em roots | conteúdo e referência permanecem consistentes |
| Container recebido externamente ou não revertível | tipo concreto, snapshots, resultado do load | não presumir suporte a rollback/save |
| Salvar com a tela/modal URM aberta | contexto atual, save callback, estado ao carregar | efeito da interação e da tela sobre o ciclo |

Para cada cenário, registrar SDK exato, procedimento, log antes/depois, variáveis e resultado. Até isso ser feito, esta seção identifica uma dependência de cobertura; não declara perda de dados nem comportamento de runtime.

## Próxima etapa

Rastrear quem marca nomes em ever_been_changed no jogo real e testar os casos de edição imediata antes de save/load em fixture isolado do SDK 7.4.11. Em paralelo, continuar a pesquisa das ações de edição disparadas por CodeView/Search e suas fontes de dados, mantendo a separação entre estado do jogo e metadados .urm.
