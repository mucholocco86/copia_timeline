# 12 — URM: leitura, edição, pesquisa e persistência — primeiro mapa de circuitos

**Data:** 2026-10-15. **Estado:** 🟢 confirmação por inspeção da fonte convertida do URM; 🔵 dependências do Ren'Py 7.4.11 ainda a cruzar em detalhe; 🟠 perguntas abertas. **Sem teste runtime e sem alteração de Wells ou SDK.**

## Objetivo

Ampliar a pesquisa de Choices para os mecanismos que tornam o URM capaz de **ler, procurar, editar e guardar dados**. Não equiparar edição do estado em memória, arquivos de configuração do URM e saves nativos do jogo. Este documento inicia a árvore, **não a declara completa**.

## Fontes primárias inspecionadas

Todos sob `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/`:

- `vars.rpy` (SHA `57482937e14f215dac0ecb22a62da8ad160cba58`): `Var.value` linhas 197–230; `Var.setValue` 232–269; `VarsStoreClass` e `StoreMonitorClass`.
- `search.rpy` (SHA `0e62656c1d0caf11bc93588ae66ab549db90d479`): `SearchClass.doSearch` linhas 39–79; `matchVarName`, `matchVarValue`.
- `URMFiles.rpy` (SHA `888aba28d9d2e7870d8c4e6526417390179cd326`): `URMFilesClass`, `URMFileStore`, `URMFile`, `save` linhas 308–340 e `load` 356–372.
- `settings.rpy` (SHA `13fd70596135c4389c9ab01cae982f80bfcad461`): `SettingsClass.get/set` linhas 146–185; global ZIP `settings` 187–218.
- `gamesaves.rpy` (SHA `bbedbd08f9ce106c77a12bdb984e11008cf995bf`): `GameSavesClass`, `Save`, `SetPage`, `SetPageName`.
- `snapshots.rpy` (SHA `20b45be23df8f12d7f4dfca7a1f401642d6fedba`): `SnapshotsClass`, diffs de dict/list.
- `states.rpy` (SHA `b787b94fc40183b24165d2844a0f91bc12980626`): `StatesClass`.

## 1. Leitura de valores — Var.value

🟢 `Var.value` inicia em `self.storeDict` e resolve o primeiro segmento de `namePath` como chave. Segmentos seguintes são resolvidos por `getattr` (prefixo `.`), chave textual de coleção (`['...']`) ou índice numérico (`[n]`). Ausência ou exceção retorna `None`.

Isto é leitura de dados do estado do jogo/objetos em runtime; **não é leitura de linhas de script `.rpy`**.

## 2. Edição — Var.setValue

🟢 `Var.setValue(newValue, overruleVarType, operator, varChildKey)` verifica `isEditable`, resolve tipo de valor, formata strings/booleanos/inteiros/floats e executa uma expressão de atribuição sobre `renpy.store.<caminho>` com `exec`. O operador especial `append` chama `.append(...)`. Se a variável estava congelada, descongela temporariamente e volta a congelá-la no `finally`.

```text
ação de interface / SetVarValue
       ↓
Var.setValue
       ↓
resolução de nome + tipo + operador
       ↓
exec('renpy.store.' + caminho + operador + valor)
       ↓
mutação do estado Python/Ren'Py em execução
```

**Limite:** esse código não demonstra edição de arquivo `.rpy` no disco. A persistência de uma alteração de valor através de save/load/rollback deve ser comprovada em circuito separado.

**Cuidado:** `exec` é mecanismo do URM original, não recomendação automática de implementação para Wells. A análise de entradas e segurança será posterior.

## 3. Pesquisa — SearchClass.doSearch

🟢 A origem da coleção depende do modo: para `labels`, `renpy.get_all_labels()`; para variáveis, `renpy.store.__dict__`; se `Settings.searchRecursive` e já houver resultados, usa `self.results` como novo conjunto. Os modos `variable names`, `labels` e `values` encaminham a busca a `matchVarName` ou `matchVarValue`, acumulando resultados e reiniciando a página.

```text
query + tipo
  ├── labels → renpy.get_all_labels()
  └── variáveis → renpy.store.__dict__
        ↓
matchVarName / matchVarValue
        ↓
resultados (possivelmente recursivos)
```

A profundidade, os filtros e o custo de travessia de objetos exigem leitura integral dos métodos de correspondência antes de declarar o mecanismo de pesquisa completamente mapeado.

## 4. Persistência — existem circuitos distintos

🟢 **Arquivos `.urm`**: `URMFile.save` constrói ZIP com `ZIP_DEFLATED`, escreve entradas de stores como JSON, salva primeiro em `.new` e move para o caminho final. Tenta também copiar para o diretório de saves quando disponível. `URMFile.load` abre ZIP e reconstrói `URMFileStore` com `json.loads(..., object_pairs_hook=OrderedDict)`. Há propriedades `urmVersion` e `gameId`.

🟢 **Configurações por jogo**: `SettingsClass.get/set` lê/escreve `renpy.store.persistent.URMSettings`. **Configurações globais**: `_saveGlobalSettings` grava ZIP `settings` com entrada `json` e metadados `id` e `urmVersion`, também usando arquivo `.new` seguido de `shutil.move`.

🟢 **Saves nativos**: `gamesaves.rpy` oferece ações de salvar/carregar/copiar/mover slots do Ren'Py; não é equivalente ao formato `.urm`.

🟢 **Snapshots**: `snapshots.rpy` contém funções para capturar/comparar diferenças de dicionários e listas; não confundir snapshot de análise com save nativo ou arquivo `.urm`.

## 5. Árvore de dependências inicial

```text
URM UI (telas e ações — rastrear)
  ├── CodeView (links interativos — já estudados)
  │    └── Var / SetVarValue → renpy.store
  ├── SearchClass
  │    ├── Var / VarsStore
  │    ├── renpy.store.__dict__
  │    └── renpy.get_all_labels()
  ├── VarsStore / StoreMonitor
  │    └── callbacks Python / rollback (documentos 06, 09 e 10)
  ├── URMFiles / URMFile / URMFileStore
  │    └── ZIP com stores JSON (.urm)
  ├── SettingsClass
  │    ├── persistent.URMSettings
  │    └── ZIP global settings
  ├── GameSavesClass
  │    └── saves nativos Ren'Py
  └── SnapshotsClass
       └── comparação de estado
```

## 6. Próximas perguntas obrigatórias

1. Rastrear a cadeia **tela → Action → Var → store** e distinguir edição de variável, exclusão, criação, congelamento, monitoramento e watch.
2. Ler integralmente `SearchClass.matchVarName/matchVarValue` e relacionar filtros `Settings.searchObjects/searchInternalVars`, profundidade, coleções e ciclos.
3. Identificar **quais stores** são escritos em `.urm`, quem os preenche e **quando** são reaplicados ao jogo após `URMFiles.autoLoad`; rastrear `lastLoadedFile`.
4. Separar `persistent.URMSettings`, configurações globais, arquivos `.urm`, saves nativos e snapshots com evidência de cada produtor/consumidor.
5. Rastrear no SDK 7.4.11 as APIs nativas utilizadas para store, rollback, save/load, `persistent` e labels.
6. Construir tabela de mutações versus rollback e save/load: o que persiste, o que volta, o que é reexecutado, o que é apenas configuração.
7. Identificar todas as chamadas indiretas em telas, `main.rpy`, `codeview.rpy`, `labels.rpy`, `search.rpy` e arquivos auxiliares; preservar mesmo componentes aparentemente secundários.

## 7. Separação de fases

**Fase A:** completar URM + Ren'Py **7.4.11** como fonte de verdade.  
**Fase B (somente depois):** comparar invariantes e mudanças com SDK **6.99.4** e **8.5.3** do laboratório, sem reinterpretar retroativamente o comportamento original.

Método: **primeiro entender → depois inspecionar → depois planejar → só então modificar**. Não alterar `wells/`, `wells_beta/`, SDKs ou fontes originais.
