# URM — Stores, monitoramento e substituição de texto (primeira validação)

**Data:** 2026-10-15. **Escopo:** inspeção estática do código convertido do URM. **Sem testes de runtime.** Nenhum arquivo protegido foi alterado.

## Fontes verificadas

Prefixo comum: `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/`.

- `classes/vars.rpy` SHA `57482937e14f215dac0ecb22a62da8ad160cba58`: linhas 5–138, 232–269, 437–479, 483–577.
- `classes/labels.rpy` SHA `96713d0297cf1bedeb9232502aa0d631d2a0780e`: linhas 5–32.
- `classes/textrepl.rpy` SHA `70ce9cc40378af1de5092255558659c8512a04f6`: linhas 5–64, 70–122.
- `classes/main.rpy` SHA `14f93406d2946eaed664ed72c1d47063984ce24f`: linhas 18–63 e 194–227.
- `classes/URMFiles.rpy` SHA `888aba28d9d2e7870d8c4e6526417390179cd326`: linhas 78–91, 231–248, 308–372.
- `screens/vars.rpy` SHA `7959b2c0e6249df0edbb9ebe683481d46e4537e1`: referências a `SetVarValue`, `CreateVar`, `VarsStore`, `URMFiles.Save/Load` (linhas 115–168, 192, 270, 370–445, 485, 563).
- `screens/watchpanel.rpy` SHA `8cc83f00838ed409183e85e4ebdb37ddf4433823`: acesso a `VarsStore.watchedStore` (linhas 77–108).

## 1. Quem consome os stores `.urm`?

**Confirmado no código:** `VarsStoreClass.store` acessa `URMFiles.file['vars']` e cria o store se ausente; `watchedStore` faz o mesmo para `'watched'` (`vars.rpy` 5–20). `LabelsStoreClass.store` usa `'labels'` (`labels.rpy` 5–12). `TextReplacementsClass.store` usa `'replacements'` (`textrepl.rpy` 10–16). `URMFile.getStore` carrega sob demanda (`URMFiles.rpy` 231–238).

| Store | Conteúdo demonstrado | Consumidor |
|---|---|---|
| `vars` | nomes lembrados e metadados `name`, `frozen`, `monitor`, `ignored` | `VarsStoreClass` |
| `watched` | nomes de variáveis e nomes de exibição | `VarsStoreClass.watchedStore` |
| `labels` | nomes de labels e nomes de exibição | `LabelsStoreClass` |
| `replacements` | texto original, substituição, `characterVar`, flags de case e palavra parcial | `TextReplacementsClass` |

**Distinção fundamental:** `VarsStore.remember` grava `{'name': ...}` e não uma cópia do valor da variável; `freeze` e `monitor` registram flags. Logo, o arquivo `.urm` armazena **configurações de acompanhamento e substituições** neste circuito, não um snapshot genérico de `renpy.store`.

## 2. Como `freeze` e `monitor` funcionam

**Confirmado no código:** `StoreMonitorClass.init` (`vars.rpy` 492–509) adiciona `_pythonCallback` a `renpy.config.python_callbacks` se o suporte estiver disponível e tenta localizar funções nativas `_m1_00action_data__set_field` ou `_set_field`. Clona a função e substitui seu `__code__` por um interceptador.

O interceptador (`vars.rpy` 521–524) consulta `handleVarChange` antes de chamar o `originalSetField`. Quando a variável está congelada, `handleVarChange` retorna `False`, bloqueando essa rota de atribuição, e tenta restaurar o valor anterior caso haja diferença (`vars.rpy` 526–538). Para variáveis monitoradas, se houver mudança e a tela de edição não estiver aberta, gera uma notificação.

O callback Python (`vars.rpy` 540–563) ativa `renpy.game.context().force_checkpoint = True`, obtém alterações do store via `renpy.store.__dict__.get_changes` e as envia a `handleVarChange`.

**Limites importantes:** a interceptação de `SetField` e o callback Python são **rotas distintas**, não prova de cobertura de todas as mutações possíveis. O comportamento efetivo depende do SDK 7.4.11 e precisa ser conferido, sobretudo `get_changes`, `force_checkpoint`, checkpoints e rollback. A substituição de `__code__` é invasiva; **não transportar para Wells sem análise de compatibilidade e testes**.

## 3. Substituição de texto não é edição de arquivo de script

**Confirmado no código:** `TextRepl.attachFilters` (`textrepl.rpy` 56–64) guarda filtros anteriores e configura `renpy.config.say_menu_text_filter` e `renpy.config.say_arguments_callback`. A instalação ocorre no `init 999` quando não há `pendingUpdate` (`textrepl.rpy` 119–122).

`_textFilter` aplica substituições armazenadas em `replacements` após eventual filtro anterior; `_sayFilter` trata nomes de personagens; `_replace` usa `str.replace` ou regex com opções de sensibilidade a maiúsculas e correspondência parcial (`textrepl.rpy` 70–116).

**Consequência:** o mecanismo demonstrado modifica a **representação de texto exibido**, não o arquivo `.rpy` no disco. Por atuar em `say_menu_text_filter`, também pode interferir na correlação entre texto original do menu e texto exibido: qualquer sistema de Walkthrough deve evitar tratar legenda filtrada como identidade única de Choice.

## 4. Quando o arquivo é carregado

`main.rpy` cria os objetos no `init 52`; `afterLoad` chama `StoreMonitor.init` e `URMFiles.autoLoad` (`main.rpy` 54–63). O `init 999` registra `afterLoad` em `renpy.config.after_load_callbacks` e `onLabelCalled` no monitor de labels (`main.rpy` 194–218). `URMFiles.autoLoad` depende de `Settings.lastLoadedFile` e de condições de `unsaved` (`URMFiles.rpy` 61–64).

**Limite:** o carregamento de stores é lazy e seu uso posterior é demonstrado por propriedades; isso não prova que cada regra foi aplicada em toda interação ou que o rollback preserva o estado desejado.

## 5. Hipóteses e testes pendentes

1. Verificar no SDK 7.4.11 a assinatura de `_set_field` e as versões da API `get_changes`; verificar se `python_callbacks` e `force_checkpoint` operam como suposto.
2. Criar cenários de `freeze` com atribuição direta, `SetField`, mutação de objetos, rollback e load de save; observar o que de fato é bloqueado.
3. Testar `replacements` com Choice, `say`, personagem dinâmico, texto traduzido e labels duplicadas; comparar `Menu.items` e legenda exibida.
4. Verificar se outras stores são adicionadas fora dos consumidores aqui inspecionados; não afirmar inventário global completo.
5. Validar em runtime os metadados carregados de `.urm`, em especial se alterações aninhadas de `freeze`/`monitor` ficam fora da flag `unsaved` e do aviso de troca de arquivo.

**Classificação:** fatos marcados como confirmados referem-se à fonte convertida. **Nenhum resultado de execução nem equivalência entre SDKs foi afirmado.**


## 6. Alterações aninhadas e flag `unsaved` do arquivo URM

A leitura cruzada de `VarsStoreClass` com `URMFileStore` mostra que os metadados de uma variável são mapas aninhados dentro do store externo `vars`:

- Ao abrir um store JSON, `URMFile.load()` converte os objetos JSON aninhados em `OrderedDict` e envolve somente o mapa externo com `URMFileStore` (`classes/URMFiles.rpy`, linha 367).
- `URMFileStore.__setitem__`, `__delitem__`, `update` e `clear` são os métodos que mantêm sua flag `unsaved` (`classes/URMFiles.rpy`, linhas 194–215).
- Para uma variável que já existe em `VarsStore.store`, `freeze`, `unfreeze`, `monitor` e `unmonitor` escrevem/apagam chaves no objeto aninhado `store[varName]` (`classes/vars.rpy`, linhas 46–69). Essas linhas não chamam os métodos de primeiro nível de `URMFileStore` nem atribuem explicitamente `store.unsaved = True`.
- Em contraste, `watch` grava/remova a chave de primeiro nível no store `watched`; `ignore` e `unignore` definem explicitamente `store.unsaved = True` (`classes/vars.rpy`, linhas 79–119).
- A flag agregada `URMFiles.file.unsaved` controla o asterisco da interface e é lida pelos caminhos `clear`, seletor `Load` e `autoLoad` (`classes/URMFiles.rpy`, linhas 61–103 e 260–275; `screens/main.rpy`, linhas 135–137).

**CONFIRMADO NA FONTE URM CONVERTIDA:** quando o registro externo já existe e começa limpo, as quatro alterações aninhadas de freeze/monitor não passam por uma rotina que marque o store externo como alterado. Quando a variável ainda não é lembrada, `freeze`/`monitor` primeiro chamam `remember`, cuja atribuição externa marca `unsaved`; esse cenário não tem o mesmo resultado estático.

**HIPÓTESE de consequência:** uma mudança de freeze/monitor num registro já lembrado pode não acender o indicador de arquivo alterado e pode não acionar proteções que dependem de `file.unsaved`. Isso pode ocultar alterações e permitir descarte/troca sem o aviso esperado em certos caminhos. Não significa que o botão Salvar ignore a alteração: `URMFile.save()` percorre e serializa todos os stores não vazios sem condicionar a escrita a `unsaved`. Portanto, a suspeita diz respeito à detecção de alterações e aos avisos, não à capacidade de uma gravação manual explícita. A validação runtime do aviso de UI permanece pendente.

### Probe reduzida criada

Para separar o comportamento de mapa aninhado do pacote URM integral, foi criada a fixture `tools/fixtures/urm_store_dirty_probe.rpy` e o workflow isolado `.github/workflows/urm-store-dirty-probe.yml`. O testcase compara freeze/unfreeze/monitor/unmonitor sobre registro existente com watch/ignore/unignore e freeze de variável nova. A fixture replica apenas os métodos relevantes; não importa nem executa fontes do pacote URM.

- Fixture commit: `2a080230d69616225744b0461dd2fb263ff65ad3`.
- Workflow commit: `26b747ce272213b39c4b1010b6081379d4e850eb`.
- **PENDENTE DE RUNTIME:** o resultado do testcase precisa ser obtido e revisto antes de classificá-lo como observado no SDK 7.4.11.

| Fonte | Símbolos / linhas | Blob SHA |
|---|---|---|
| URM convertido `classes/vars.rpy` | `freeze`, `unfreeze`, `monitor`, `unmonitor`, `watch`, `ignore`, `unignore` (46–119) | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| URM convertido `classes/URMFiles.rpy` | parsing JSON (124, 367); `URMFileStore` e mutadores (194–215); `autoLoad/clear/Load` (61–103); flag agregada (260–275) | `888aba28d9d2e7870d8c4e6526417390179cd326` |
| URM convertido `screens/main.rpy` | indicador `unsaved` (135–137) | `ceb5dc63b3691a4b6244345e1c5a3e3b9d149291` |
| URM convertido `screens/vars.rpy` | tabela e ações de variáveis (115–178) | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |
| URM convertido `screens/watchpanel.rpy` | leitura da lista assistida e valor atual por `Var(varName)` (89–103) | `8cc83f00838ed409183e85e4ebdb37ddf4433823` |


## 7. Consumidores efetivos de `vars` e `watched`

Esta leitura fecha o circuito entre metadados persistidos no arquivo URM e os pontos que os consultam durante a execução.

### Ciclo de carregamento

**Confirmado na fonte convertida:** `afterLoad()` chama `StoreMonitor.init()` e, depois das configurações visuais, chama `URMFiles.autoLoad()` (`classes/main.rpy`, linhas 54–63). A inicialização do monitor instala o callback Python e tenta substituir o helper de atribuição; ela não percorre os registros de `VarsStore.store` para aplicar flags em lote (`classes/vars.rpy`, linhas 492–509).

As verificações são feitas sob demanda em `handleVarChange`: cada alteração examinada consulta `VarsStore.isFrozen(varName)` ou `VarsStore.isMonitored(varName)` (`vars.rpy`, linhas 521–538). Como as propriedades `store`/ `watchedStore` apontam para os stores do arquivo atual, os metadados carregados pelo `autoLoad` podem ser lidos por essas consultas posteriores. **A fonte não demonstra um replay retroativo de alterações ocorridas antes do carregamento.**

### Mapa de metadado → consumidor

| Metadado em `.urm` | Leitura demonstrada | Efeito descrito pela fonte |
|---|---|---|
| `vars[name].frozen` | `isFrozen` → `StoreMonitor.handleVarChange`; também `Var.setValue` consulta a flag | No helper interceptado, `handleVarChange` retorna falso e não chama o helper original; `Var.setValue` remove temporariamente a flag antes de escrever e a repõe no `finally`. |
| `vars[name].monitor` | `isMonitored` → `handleVarChange` | Se o valor difere e a tela de edição do URM não está aberta, enfileira notificação de variável alterada. |
| `vars[name].ignored` | `strContainsIgnored` alimenta detecção de caminhos e CodeView | Filtra condições de caminho ou trechos Python apresentados pelo CodeView; não altera o valor da variável nem o AST do jogo. |
| `vars[name].name` | Tela de variáveis | Nome de exibição; o valor atual é obtido separadamente com `Var(varName)`. |
| `watched[name].name` | Tela de watch panel | Rótulo exibido; o painel chama `Var(varName).getButtonValue()`, que resolve o valor vivo no store atual. |

**Confirmado na fonte convertida:** `watch` armazena nome e rótulo, não valor histórico. O painel consulta o valor atual em cada renderização (`screens/watchpanel.rpy`, linhas 77–103). Similarmente, a tabela de variáveis lê os metadados e resolve o valor por `Var(varName)` (`screens/vars.rpy`, linhas 115–168).

### Limites para a relação com rollback

- `frozen` e `monitor` são regras/configurações mantidas no arquivo URM; as alterações ao valor do jogo passam por rotas do store Ren'Py. Não se deve confundir persistência da regra com persistência do valor.
- A rota do helper e o callback Python não cobrem necessariamente toda mutação. A fonte convertida de `Var.setValue` usa `exec` para atribuição e `CreateVar` usa `setattr`; a cobertura do monitor nessas ações precisa ser lida em conjunto com a investigação anterior e seu teste reduzido.
- O callback marca `Context.force_checkpoint` e examina `StoreDict.get_changes`; isso descreve uma solicitação de checkpoint e uma observação de deltas, não prova isoladamente que uma alteração específica foi registrada, restaurada ou exibida ao jogador. A semântica do SDK e os resultados runtime já documentados nos documentos 18–24 continuam sendo o suporte necessário para essas afirmações.
- `watched` é somente uma lista persistida para exibição/edição rápida. Não é monitoramento de mudanças: a notificação depende da flag `monitor` em `vars`.
- `ignored` afeta projeções/filtros do URM (PathDetection e CodeView), não seleção de Choice nem execução dos blocos AST, conforme os consumidores examinados.

**Classificação:** consumidores e efeitos acima são **confirmados na fonte URM convertida**. A leitura dinâmica após um `autoLoad` é uma consequência estrutural das referências lazy, ainda não validada numa execução integral do URM. Não se afirma que todos os caminhos de escrita tenham cobertura pelo monitor.

### Fontes verificadas nesta etapa

| Fonte | Símbolos / linhas | Blob SHA |
|---|---|---|
| `classes/main.rpy` | `afterLoad`, ordem `StoreMonitor.init` → configurações → `URMFiles.autoLoad` (54–63) | `14f93406d2946eaed664ed72c1d47063984ce24f` |
| `classes/vars.rpy` | `isFrozen`, `isMonitored`, `watch`, `ignore`; `StoreMonitor.init`, `handleVarChange`, callback (46–119, 492–563) | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| `classes/PathDetection.rpy` | exclusão de condição via `strContainsIgnored(..., 'path')` (em `nextIfStatement`) | `078950513618fe64f6a9961d77230e4c468a3ab4` |
| `classes/codeview.rpy` | exclusão de código via `strContainsIgnored(..., 'code')`; links de variáveis | `508783b02b319f3a34c16730c82ef1de1e9fbb45` |
| `screens/vars.rpy` | metadados/valor, ações freeze/monitor/ignore e edição (115–210) | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |
| `screens/watchpanel.rpy` | rótulo persistido e leitura viva por `Var(varName)` (75–103) | `8cc83f00838ed409183e85e4ebdb37ddf4433823` |
