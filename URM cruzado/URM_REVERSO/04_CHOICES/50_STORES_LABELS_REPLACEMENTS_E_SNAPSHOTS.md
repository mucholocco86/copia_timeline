# 50 — Stores `labels`/`replacements` e snapshots em memória

**Data:** 2026-10-28. **Alvo:** URM X52 convertido/original e Ren'Py 7.4.11. **Evidência:** inspeção estática e runtime em fixtures isoladas; limites de integração visual indicados por caso.

## Fontes consultadas

- URM convertido `classes/labels.rpy`, blob SHA `96713d0297cf1bedeb9232502aa0d631d2a0780e`.
- URM convertido `classes/textrepl.rpy`, blob SHA `70ce9cc40378af1de5092255558659c8512a04f6`.
- URM convertido `classes/snapshots.rpy`, blob SHA `20b45be23df8f12d7f4dfca7a1f401642d6fedba`.
- URM convertido `classes/URMFiles.rpy`, blob SHA `888aba28d9e2d7870d8c4e6526417390179cd326`.
- SDK `renpy/pydict.pyx` e `renpy/python.py`, para a semântica de `DictItems` e o histórico revertível.

## Store `labels`

**CONFIRMADO NA FONTE URM CONVERTIDA:** `LabelsStoreClass.store` cria/usa a entrada `.urm` `labels`. `remember(labelName, displayName)` grava um registro `{labelName: {"name": displayName}}`; `forget`, `changePos`, `sort` e `clear` alteram essa lista.

Essa estrutura registra labels lembrados e nomes de exibição. Não armazena o corpo AST nem as consequências executadas pelo label. `LabelMonClass` é outro objeto: instala `config.label_callback`, acompanha `lastLabel` e notifica callbacks. O código examinado não grava cada execução de label no store `labels`.

**OBSERVADO EM RUNTIME:** no run [40666090480](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40666090480), `remember(...)` produziu uma entrada `labels` no `.urm`; um segundo processo carregou os metadados. Isso valida persistência dos dados lembrados no percurso testado, não a interação visual da tela de labels nem a execução do label.

## Store `replacements`

**CONFIRMADO NA FONTE URM CONVERTIDA:** `TextReplacementsClass.store` cria/usa a entrada `.urm` `replacements`. Cada regra guarda texto original, substituição, referência opcional a variável de personagem e opções de maiúsculas/minúsculas e correspondência parcial.

`attachFilters()` instala callbacks em `renpy.config.say_menu_text_filter` e `renpy.config.say_arguments_callback` quando compatível. Os filtros consultam o store no momento de uso e transformam texto/nome para apresentação; não reescrevem o script `.rpy` nem modificam, por si, o valor narrativo ou variável de gameplay.

**OBSERVADO EM RUNTIME:** no run [40666090480](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40666090480), uma regra foi salva dentro de `.urm`, carregada em processo novo por `URMFiles.load()`, e uma chamada direta a `renpy.config.say_menu_text_filter("WellsProbeChoice")` retornou `URMLoadedChoice`.

**Limite importante:** o probe chamou diretamente o callback. Não demonstrou o texto final renderizado numa screen real de Menu/Choice, nem o encadeamento com todos os filtros de terceiros ou substituições de nome em fala. O efeito visual end-to-end segue pendente.

## Snapshots de variáveis

**CONFIRMADO NA FONTE URM CONVERTIDA:** `SnapshotsClass.create()` mantém snapshots em `self._m1_snapshots__snapshots`, um `OrderedDict` dentro da instância em memória. O método usa `renpy.python.DictItems(renpy.store.__dict__).as_dict()`; não acessa `URMFiles` nem cria store `.urm`.

No SDK 7.4.11, `DictItems` preserva referências a objetos valor; `as_dict()` cria um novo dicionário, mas não cópia profundamente os valores. `Snapshots.findDictChanges()` compara valores no nível superior.

**OBSERVADO EM RUNTIME:** o [documento 51](51_SNAPSHOTS_DIFF_RUNTIME_CONTAINERS.md), run [40658456177](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40658456177), detectou a substituição escalar 10→20. Não listou a lista e o dicionário simples após suas mutações in-place, embora os valores atuais fossem `[9, 2]` e `{"a": 9}`. O primeiro probe, que não alterou valores, foi descartado como evidência.

**Conclusão limitada:** esse resultado é coerente com snapshots rasos/referenciais e não equivale a um histórico profundo de objetos nem a rollback. Não generalizar para todas as classes/coleções.

## Quadro de distinção

| Recurso | Armazenamento observado | Conteúdo | Relação com gameplay |
|---|---|---|---|
| `labels` | Store `.urm` | Labels lembrados e nomes de exibição | Organização/acesso; não guarda execução do label |
| `replacements` | Store `.urm` | Regras de filtro para texto/nome | Altera apresentação ao ser consumida pelo filtro |
| `Snapshots` | Instância `SnapshotsClass` em memória | Referências à tabela do store no instante da captura | Diff superficial; não é rollback nem store `.urm` |
| Save nativo | Persistência Ren'Py | Estado serializado do jogo nos cenários testados | Docs 46–47 validaram variável/rota da Choice |

## Limites e continuidade

- Persistência visual/estado da instância `Snapshots` em save nativo continua não testada.
- O filtro de texto foi chamado diretamente após load; falta validar uma Choice realmente renderizada.
- As telas originais de labels e replacements não foram automatizadas ponta a ponta.
- As fontes convertidas são artefatos de análise; evidência runtime com fontes originais é identificada como tal.
- Os testes são específicos do Ren'Py 7.4.11 e das fixtures documentadas.

Próximo passo: validar o texto final de uma Choice exibida após `.urm` load e, em cenário separado, verificar persistência da instância `Snapshots` através de save/load nativo.

## Relação com o circuito nativo de Choice

O [documento 52](52_TEXTREPL_MENU_AST_FILTER_PATH.md) confirma estaticamente que o SDK chama `say_menu_text_filter` durante `Menu.execute()`, mantendo separadamente o índice estrutural usado para continuar no bloco. O run citado acima valida o callback após load, mas não a renderização final da screen.
