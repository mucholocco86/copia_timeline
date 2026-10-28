# 02 — Persistência e associação por personagem do store `textboxCustomizations`

**Data:** 2026-10-28. **SDK:** Ren'Py 7.4.11. **Evidência:** inspeção do URM convertido e runtime em dois processos usando as fontes originais. **Run:** [40665541175 — SUCCESS](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40665541175).

## Fontes examinadas

- `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/textbox.rpy`, blob SHA `33cbf0440c09715be1bbc2789296f5e252ba88c6`: `TextBoxClass` (linhas 5–265), `TextBoxSettings` (267–405) e instalação no init 999 (414–419).
- `classes/URMFiles.rpy`, blob SHA `888aba28d9d2e7870d8c4e6526417390179cd326`: serialização dos stores no arquivo ZIP/JSON.
- Fixture isolada `URM_REVERSO/tools/fixtures/urm_textbox_customization_probe.rpy` e workflow `.github/workflows/urm-textbox-customization-probe.yml`.

## Modelo estático

**CONFIRMADO NA FONTE URM CONVERTIDA:** `TextBoxSettings.store` acessa/cria a entrada `textboxCustomizations` dentro de `URMFiles.file`. Cada entrada é indexada por string de variável de personagem ou pela chave `None` para configurações globais. O registro contém propriedades de apresentação, como tamanhos e cores para nome e fala, outline, fundo, alinhamento, side image e fonte.

`TextBoxSettings._getSettingsForChar(char)` resolve os dados por estes caminhos:

1. Se `char` é string e está no store, usa a entrada diretamente.
2. Se `char` é um `ADVCharacter`, percorre as chaves guardadas, resolve os nomes no `renpy.store` e compara o objeto encontrado com `char`.
3. Se não encontrou configuração específica, tenta a chave global `None`.

`TextBoxClass._sayReplace` atualiza `TextBox.Settings` para o personagem atual, a menos que a tela de customização esteja aberta. Quando a integração de caixa do URM está habilitada, o callback deriva os argumentos visuais de fala/personagem desses settings e encaminha a fala à screen `URM_say` quando `customSayScreen` está habilitado.

No editor, `enableTemp()` faz uma cópia temporária dos settings; as alterações passam por `set()` para essa cópia. `commitTemp()` grava o dicionário temporário no store; cancelar usa `dismissTemp()` e descarta o temporário. A fonte assim separa edição em andamento de preferência aplicada. O efeito visual em tela é uma questão distinta da persistência do store.

## Teste runtime

O workflow criou um jogo descartável e executou dois processos Ren'Py independentes.

### Processo de gravação

A fixture iniciou a cópia temporária para `urm_textbox_probe_character`, alterou `whoSize=44`, `whoColor="#12AB34"` e `whatBold=True`, aplicou com `commitTemp()` e salvou por `URMFiles.save()` original.

O passo externo abriu o ZIP e validou a entrada:

~~~json
{
  "urm_textbox_probe_character": {
    "whatBold": true,
    "whoColor": "#12AB34",
    "whoSize": 44
  }
}
~~~

### Processo de carregamento

Um processo Ren'Py novo carregou o arquivo com `URMFiles.load()`, criou `TextBoxSettings(urm_textbox_probe_character)` passando o objeto Character (não apenas seu nome), e confirmou os três valores. Criou também settings para outro personagem sem entrada específica e confirmou o fallback aos valores default.

Log resumido:

~~~text
URM_TEXTBOX_SAVED urm-textbox-customization-probe.urm ['properties', 'vars', 'textboxCustomizations']
URM_TEXTBOX_CUSTOMIZATION_JSON {"urm_textbox_probe_character": {"whatBold": true, "whoColor": "#12AB34", "whoSize": 44}}
URM_TEXTBOX_AFTER_LOAD ... 44 #12AB34 True
~~~

## Classificação

- **OBSERVADO EM RUNTIME:** `.urm` serializou `textboxCustomizations` e recuperou esses valores em outro processo Ren'Py.
- **OBSERVADO EM RUNTIME:** o lookup por objeto Character encontrou as preferências indexadas pelo nome da variável do personagem.
- **OBSERVADO EM RUNTIME:** personagem sem entrada própria recebeu o valor default consultado no teste.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** customização em edição é temporária até `commitTemp()`; a aplicação escreve os settings no store do `.urm`.
- **PENDENTE:** verificar visualmente a renderização da screen `URM_say`; este probe verificou persistência e resolução de settings, não pixels/render final. A UI original do customizer também não foi automatizada por clique.

## Limitação do log

A fixture imprimiu `TextBoxSettings.store` como atributo da classe durante uma tentativa de diagnóstico; isso exibiu um objeto `property`, pois `store` é propriedade de instância. Esse print não é evidência do conteúdo. A evidência vem do JSON extraído do ZIP e da leitura por `TextBoxSettings` em runtime após load.

## Relação com outros stores

`textboxCustomizations` é um store de preferências de apresentação do URM. Não guarda o texto original da fala, não altera scripts e não é estado narrativo do jogo. Distingue-se de:

- `replacements`: regras que transformam texto/nome durante os filtros de apresentação;
- `vars` e `watched`: metadados de variáveis lembradas/congeladas/monitoradas e lista observada;
- save nativo Ren'Py: mecanismo já validado para estado do jogo editado e rota da Choice nos documentos 46–47.
