# 13 — Revisão independente: busca, criação de variáveis e carga de arquivos URM

**Data:** 2026-10-15. **Estado:** inspeção estática confirmada no código convertido URM; **sem teste de execução**. Complementa o documento 12. Não altera Wells, SDK ou fontes URM.

## Evidência do primeiro workflow

GitHub Actions `URM Reverse Engineering Inventory`, execução [38695473315](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/38695473315), job **success**, artefato `urm-inventory-38695473315` (ID 11954022878, SHA256 publicado pelo GitHub `4ed2bd2e7ca71ce6424cd94f0abd239bb502ea7e7441d10a0d11a6440ab4ecb1`). O ZIP contém `urm_declarations.csv`, `sdk_declarations.csv`, `urm_references.csv`, `urm_imports.csv`, `summary.json`, `README.md`. Resumo: 771 declarações URM, 3732 SDK, 2133 referências URM, 38 imports. **São correspondências regex, não 771 funcionalidades, nem ligações semânticas validadas.**

## Fontes examinadas independentemente

Todos sob `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/`:

- `search.rpy` SHA `0e62656c1d0caf11bc93588ae66ab549db90d479`, linhas 39–79 e 94–230.
- `vars.rpy` SHA `57482937e14f215dac0ecb22a62da8ad160cba58`, linhas 197–269 e 437–479.
- `URMFiles.rpy` SHA `888aba28d9d2e7870d8c4e6526417390179cd326`, linhas 61–64, 78–162, 225–305 e 308–372.

## 1 — Busca de valores: limites da recursão

**Confirmado na fonte:** `SearchClass.doSearch` escolhe `renpy.get_all_labels()` para labels e `renpy.store.__dict__` para variáveis, ou restringe a coleção aos resultados anteriores quando `Settings.searchRecursive` estiver ativo (39–79).

**Confirmado na fonte:** `matchVarValue` (104–166) consulta `Var.getVarType`, exclui nomes iniciados por `_` conforme `Settings.searchInternalVars`, e compara valores string, boolean, int e float com o termo buscado. Para `persistent`, percorre atributos se `Settings.searchPersistent`. Para dict e objetos com `__dict__`, só entra quando `not parentVarName and Settings.searchObjects`.

**Consequência verificável no código:** a expansão genérica de dict/objeto está condicionada a estar no nível inicial; portanto **não se pode afirmar busca recursiva irrestrita em profundidade**. A opção `searchRecursive` de `doSearch` significa também pesquisar *sobre os resultados anteriores*, mecanismo diferente de expansão aninhada de objetos. Há exceção especial para o tipo `persistent`, que requer análise separada.

**Limite:** não foi demonstrada proteção explícita contra ciclos nesse trecho; a restrição `not parentVarName` limita parte da expansão, mas não prova segurança universal. `eval` é utilizado na leitura de valores; avaliar risco, efeitos e exceções em testes isolados.

## 2 — Busca de nomes e labels

**Confirmado na fonte:** `matchVarName` (168–229) filtra `store`, nomes internos, tipos desconhecidos e não suportados segundo as configurações. `persistent` recebe tratamento especial. Para dict e objetos com `__dict__`, há expansão de primeiro nível condicionada a `not parentVarName`. Para os demais casos, corresponde o nome por `_matchStringValue`.

**Pendente:** leitura completa de `_matchStringValue` (231–241) e testes de wildcard/case; a existência de `Settings.useWildcardSearch` não é prova de sintaxe ou semântica de busca até essa leitura.

## 3 — Criação de variáveis não usa exatamente o mesmo caminho da edição

**Confirmado na fonte:** `CreateVar.__call__` (437–479) resolve parâmetros, verifica se a variável já existe com `hasattr(renpy.store, varName)` quando não há overwrite, converte valores por tipo e usa `setattr(renpy.store, varName, settableValue)` (470). Se estiver congelada, descongela antes e restaura o estado ao final.

**Distinção importante:** `Var.setValue` (232–269) usa `exec` para atribuições ou append; `CreateVar` usa `setattr` diretamente.

**Possível comportamento-limite a testar:** `CreateVar` condiciona a atribuição a `if settableValue:` (468), o que impede valores falsy como `0`, `0.0`, `False` e string vazia de chegar ao `setattr` nesse caminho. Isso é **consequência do ramo de código inspecionado**, mas não foi testado em execução. `Var.setValue` verifica uma *string de expressão* não vazia, distinção relevante.

## 4 — Carregamento `.urm` não equivale automaticamente a restaurar variáveis do jogo

**Confirmado na fonte:** `URMFilesClass.load(filename)` (78–91) cria `URMFile`, seleciona o caminho disponível mais recente, tenta leitura do formato legado e registra `self.file` e `Settings.lastLoadedFile`. A versão legada aceita JSON começando com `{` e transforma `replacements` em mapa por `original` (116–142).

**Confirmado na fonte:** `URMFile.getStore` (231–238) carrega stores sob demanda; `URMFile.load` (356–372) abre ZIP e reconstrói stores JSON; `URMFile.save` (308–340) grava ZIP em `.new` e move para o destino.

**Consequência:** os métodos examinados carregam **dados do URM**. Não demonstram por si só a reaplicação de cada variável ou substituição ao estado de jogo. Para afirmar essa etapa é obrigatório localizar **todos os consumidores de `URMFiles.file.getStore`, `URMFiles.file[...]` e `addStore`**.

**Confirmado na fonte:** `URMFile.lastModifiedPath` (289–303) compara `mtime` do arquivo no diretório do jogo e no diretório de saves, preferindo o do jogo em empate.

## 5 — Pontos a validar no SDK 7.4.11

- Semântica de `renpy.store`, `setattr` e `exec` durante interações e rollback.
- Como `persistent` é persistido e recuperado, separado do save de slots.
- Se `renpy.get_all_labels()` cobre os labels pretendidos.
- Como `renpy.restart_interaction()` interage com as ações da interface.
- Compatibilidade de `basestring`, `eval`, acesso `__dict__` e objetos especiais no ambiente Python do Ren'Py 7.4.11.

## Próxima revisão

Rastrear consumidores das stores `.urm`, telas e ações de criação/edição, filtros da busca e hooks de `StoreMonitorClass`; em seguida cruzar métodos nativos do SDK. **Nenhuma conclusão de runtime deve ser adicionada sem teste.**
