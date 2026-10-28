# 03 — Mapa dos canais de persistência do URM X52

**Data:** 2026-10-28. **Alvo:** fontes URM X52 convertidas e Ren'Py 7.4.11. **Evidência:** inspeção estática e fixtures runtime isoladas. Testes relevantes: `.urm` de vars/watch [40657558715](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40657558715), customização de textbox [40665541175](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40665541175), labels/replacements [40666090480](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40666090480), Settings por jogo/global [40666289110](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40666289110), save nativo de Choice [40213634448](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40213634448).

## Pergunta

Quais mecanismos diferentes guardam dados de gameplay, configurações de ferramenta, listas do URM e preferências globais? O formato `.urm` é o único arquivo persistente próprio do URM?

## Resumo dos canais

| Canal | Dados observados | Escopo/comportamento demonstrado | Evidência |
|---|---|---|---|
| Save nativo de slot Ren'Py | Estado serializado do jogo, inclusive variável editada e rota Choice da fixture | Carregado via API nativa; processo novo restaurou estado salvo | Docs 46–47; run 40213634448 |
| Arquivo `.urm` | Stores de configurações/dados das ferramentas URM | ZIP com JSON por store; `URMFiles.load()` restaura os stores sem restaurar snapshot geral do jogo | Runs 40657558715, 40665541175 e 40666090480 |
| `persistent.URMSettings` | Preferências por jogo do URM | Usa o store persistent do Ren'Py; fixture chamou `renpy.persistent.save()` e processo novo leu a configuração | Run 40666289110 |
| Arquivo URM `settings` | Dicionário classificado pelo URM como configuração global | ZIP fora do `.urm`, sob `Settings.saveDir`; contém `json`, `id` opcional e `urmVersion` | Código `settings.rpy`; run 40666289110 leu o JSON e o segundo processo recuperou a opção |
| `SnapshotsClass` | Mapeamento da tabela `renpy.store` capturado em memória | Não foi restaurado pelo save nativo no teste em dois processos; não usa o circuito `.urm` examinado | Docs 51 e 53; run 40670191468 |

Esses canais não devem ser tratados como intercambiáveis. Em particular, “configuração global” é o nome do parâmetro `globalSetting=True` no código; este documento não infere que o mesmo arquivo atravesse instalações de jogos diferentes.

## Stores `.urm` definidos pelas classes analisadas

A busca por `URMFiles.file`, `addStore()` e `clearStore()` em todos os `classes/*.rpy` do URM convertido encontrou estes stores criados diretamente pelas classes:

| Store | Classe responsável | Conteúdo identificado |
|---|---|---|
| `properties` | `URMFile._m1_URMFiles__initProperties()` | `urmVersion` e `gameId`; adicionado durante o save |
| `vars` | `VarsStoreClass` | Nomes lembrados e metadados como nome de exibição, freeze, monitor e ignore |
| `watched` | `VarsStoreClass` | Variáveis observadas e nomes de exibição |
| `labels` | `LabelsStoreClass` | Labels lembrados e nomes de exibição |
| `replacements` | `TextReplacementsClass` | Regras de substituição de texto/personagem e suas opções |
| `textboxCustomizations` | `TextBoxSettings` | Preferências da caixa de diálogo por personagem ou chave `None` |

**Limite da enumeração:** esta lista cobre nomes encontrados nas classes convertidas examinadas. O carregador percorre e aceita genericamente entradas presentes num ZIP/arquivo legado; logo, arquivos antigos, externos ou produzidos por outra versão podem conter outros nomes. A lista não afirma que todo `.urm` real contém todos os seis stores: vários são criados sob demanda, e stores vazios não são gravados.

## Settings: prioridade de leitura

`SettingsClass.get(name, globalSetting=None)` possui três modos:

- `globalSetting=True`: consulta apenas o dicionário `_globalSettings` carregado do arquivo `settings`.
- `globalSetting=False`: consulta apenas `persistent.URMSettings` e, se ausente, usa o valor padrão.
- `globalSetting=None`: primeiro consulta `persistent.URMSettings`; se a chave não existir, consulta `_globalSettings`; por fim usa o padrão.

Portanto uma configuração explicitamente guardada por jogo pode sobrepor a configuração global para essa preferência.

`SettingsClass.set()` segue o modo informado:

- modo global altera `_globalSettings` e grava o arquivo ZIP `settings`;
- modo normal cria/atualiza `persistent.URMSettings`.

No runtime, `textboxesEnabled=True` foi salvo em persistent e `quickmenuEnabled=True` no ZIP global. Em um processo novo, os três acessos (normal, somente global, e global via lookup normal) retornaram os valores esperados.

## Evidência runtime por stores `.urm`

- `vars` e `watched`: doc 49; JSON guardou nome/freeze/monitor/watch e `URMFiles.load()` recuperou isso em processo novo. A variável de gameplay ficou no default.
- `textboxCustomizations`: doc 02; JSON guardou configurações por nome de personagem; `TextBoxSettings(Character)` resolveu esses valores após load no segundo processo.
- `labels` e `replacements`: run 40666090480; JSON conservou o label lembrado e a regra. Depois do load em processo novo, `renpy.config.say_menu_text_filter()` aplicou a regra e transformou `WellsProbeChoice` em `URMLoadedChoice`.
- `properties`: aparece em cada arquivo gerado pelos probes porque `URMFile.save()` adiciona versão e `save_directory`.

## Classificação das conclusões

- **CONFIRMADO NA FONTE URM CONVERTIDA:** os seis nomes listados são criados/referenciados pelas classes examinadas; SettingsClass usa canais distintos para persistent e seu ZIP global; snapshots não usam `URMFiles` no caminho examinado.
- **OBSERVADO EM RUNTIME:** `.urm` restaurou metadados dos quatro stores `vars`, `watched`, `labels`, `replacements` e `textboxCustomizations` em fixtures isoladas; a regra de substituição foi chamada após load.
- **OBSERVADO EM RUNTIME:** dois modos de Settings, persistent por jogo e arquivo global, foram recuperados em processo Ren'Py novo.
- **OBSERVADO EM RUNTIME:** save nativo restaurou condição dinâmica/rota de Choice nas fixtures dos docs 46–47.
- **OBSERVADO EM RUNTIME:** diff superficial detecta escalares e substituição de containers por conteúdo diferente; mutações in-place e substituições de conteúdo igual não aparecem como alterações. O valor `Var` antigo é somente leitura; o atual altera o store sem alterar o snapshot. Variáveis ausentes aparecem como `None`; `setValue` não recria uma variável removida. Em comparação entre dois snapshots, ambos os lados são somente leitura; chave ausente e valor armazenado `None` aparecem como `None/unknown` nos objetos `Var`, embora o diff registre a diferença de presença. Doc 51, runs 40658456177, 40676323550, 40676920686, 40677490829, 40677934414 e 40678157016.
- **OBSERVADO EM RUNTIME:** após criar um Snapshots e gravar/carregar save nativo em processo novo, o singleton começou e permaneceu vazio após load, enquanto um valor de gameplay foi restaurado. Doc 53/run 40670191468.
- **PENDENTE:** integração visual de todas as telas de salvar/carregar `.urm`; renderização final do customizer; interação completa com stores `labels`/`replacements` via interface; comparação desses detalhes em outros SDKs.

## Fontes principais

- URM convertido `classes/URMFiles.rpy`, blob SHA `888aba28d9d2e7870d8c4e6526417390179cd326`.
- URM convertido `classes/settings.rpy`, blob SHA `13fd70596135c4389c9ab01cae982f80bfcad461`.
- URM convertido `classes/vars.rpy`, blob SHA `57482937e14f215dac0ecb22a62da8ad160cba58`.
- URM convertido `classes/labels.rpy`, blob SHA `96713d0297cf1bedeb9232502aa0d631d2a0780e`.
- URM convertido `classes/textrepl.rpy`, blob SHA `70ce9cc40378af1de5092255558659c8512a04f6`.
- URM convertido `classes/textbox.rpy`, blob SHA `33cbf0440c09715be1bbc2789296f5e252ba88c6`.
- URM convertido `classes/snapshots.rpy`, blob SHA `20b45be23df8f12d7f4dfca7a1f401642d6fedba`.

## Atualização — texto da Choice e identidade (2026-10-28)

O doc [04_CHOICES/52](../04_CHOICES/52_TEXTREPL_MENU_AST_FILTER_PATH.md) complementa o mapa: a regra `replacements` carregada participa do filtro de rótulo chamado por `Menu.execute()`; o SDK mantém o índice AST original como valor estrutural. O runtime atual chamou o callback diretamente após load; falta validar o texto final renderizado numa Choice real.
