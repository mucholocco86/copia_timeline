# 52 — TextRepl, rótulo exibido e índice estrutural da Choice

**Data:** 2026-10-28. **SDK:** Ren'Py 7.4.11. **Evidência:** inspeção estática do circuito Menu/exports e runtime do callback restaurado de `.urm` (run 40666090480). **Renderização final ponta a ponta:** ainda não testada.

## Pergunta

Quando o URM carrega uma regra de substituição de texto, como ela chega a uma Choice nativa? A mudança no rótulo altera a identidade/índice usado pelo AST?

## Fontes e evidências

- SDK `renpy/ast.py`, blob SHA `d81ffc13f28f0b7442ba6905f1745ee838f7b185`, `Menu.execute()`, linhas 1639–1697.
- SDK `renpy/exports.py`, blob SHA `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`, processamento de `menu()`, linhas 1000–1065, e `display_menu()`, linhas 1127–aprox. 1319.
- URM convertido `classes/textrepl.rpy`, blob SHA `70ce9cc40378af1de5092255558659c8512a04f6`.
- URM `URMFiles.save/load` e runtime de dois processos: doc [50](50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md), run [40666090480](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40666090480).

## Circuito no SDK

Em `Menu.execute()`, o Ren'Py enumera `self.items`:

1. Para cada tupla `(label, condition, block)`, chama `renpy.config.say_menu_text_filter(label)` quando existe filtro.
2. Se o item tem bloco, adiciona `(label_filtrado, condition, i)` à lista; `i` é a posição original daquele item em `Menu.items`.
3. Passa as tuplas para `renpy.exports.menu()`.
4. A rotina de menu avalia a condição, aplica `substitute(label)` e cria a interação. Com `menu_actions`, cria `ChoiceReturn(label, value, location, sensitive=condition, ...)`; sem esse modo, envia pares substituídos à screen/menu nativa.
5. Depois da interação, o valor devolvido é usado por `Menu.execute()` como índice: `self.items[choice][2][0]`.

## Consequência para identidade

**CONFIRMADO NO SDK 7.4.11:** o filtro pode alterar o texto local usado na apresentação, mas o ramo AST de um item com bloco continua associado ao valor estrutural `i`. A identidade para continuação não deve ser reconstruída a partir do texto final.

Assim, regras de TextRepl, substituição/interpolação, traduções, textos duplicados e outras transformações de apresentação não substituem o índice estrutural. Uma ferramenta que correlacione Choices deve carregar identidade e texto como campos separados. O texto pode ser uma chave auxiliar com colisões; não é uma chave universal.

Isso também distingue dois momentos:
- `say_menu_text_filter` é chamado durante a execução de `Menu.execute()`, antes de construir a lista de alternativas.
- `substitute(label)` é aplicado depois, durante o processamento de menu. O resultado visual exato ainda depende da screen e de seus filtros/renderização.

## Ligação com TextRepl e runtime

**CONFIRMADO NA FONTE URM CONVERTIDA:** `TextReplacementsClass.attachFilters()` instala o callback em `renpy.config.say_menu_text_filter`; o callback consulta `replacements` e aplica regras sem escrever no AST ou no arquivo `.rpy`.

**OBSERVADO EM RUNTIME:** no run 40666090480, o URM original salvou a regra em `.urm`; outro processo carregou o arquivo e uma chamada direta ao callback converteu `WellsProbeChoice` em `URMLoadedChoice`.

**Limite:** o runtime chamou diretamente o filtro. A cadeia estática do SDK mostra onde uma Choice nativa consulta o callback, mas ainda não foi feita captura/asserção do texto efetivamente renderizado pela screen `choice` com regra carregada.

## Relação com seleção direta do URM

A seleção programática do URM usa `ChoiceReturn` com o índice original da alternativa. O teste integrado de condição falsa (docs 41–42) confirma que o valor estrutural chega ao bloco escolhido no percurso testado. Não deduzir o rótulo visível da ação de seleção: o índice seleciona o bloco; o texto pertence à camada de apresentação/log.

## Classificação

- **CONFIRMADO NO SDK 7.4.11:** filtro aplicado em `Menu.execute()`; índice original `i` conservado como valor estrutural; menu consome esse valor para continuar no bloco AST.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** TextRepl instala e consulta o callback, armazenando regras no store próprio `replacements`.
- **OBSERVADO EM RUNTIME:** regra `replacements` carregada de `.urm` transforma o texto quando o callback é chamado diretamente (run 40666090480).
- **PENDENTE:** validar a renderização final na screen nativa/real; ordem e interação com filtros adicionais; casos de traduções, interpolação e rótulos duplicados em runtime.

## Próximo teste

Em fixture descartável, carregar regra via `URMFiles.load()`, exibir um Menu com duas alternativas de rótulo parecido/repetido e um caminho condicionado, capturar o texto efetivamente fornecido à screen e confirmar separadamente que `ChoiceReturn` ainda encaminha o índice AST correto. Registrar a tela/trace sem usar texto como único identificador.
