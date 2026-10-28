# 49 — Persistência runtime do arquivo .urm: stores URM versus estado do jogo

**Data:** 2026-10-28. **SDK:** Ren'Py 7.4.11. **Evidência:** runtime em dois processos, fixture descartável contendo o pacote original do URM. **Run:** [40657558715 — SUCCESS](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40657558715). **Commit do workflow:** 205a592ca1f7c6e5b08e53fcdc651f5d965dde83.

## Pergunta

O que o método original do URM grava no arquivo .urm quando uma variável de gameplay é editada, e o que `URMFiles.load()` restaura em um processo novo?

## Procedimento

O workflow isolado [urm-file-persistence-probe.yml](../../.github/workflows/urm-file-persistence-probe.yml) copia o jogo `the_question` para diretório temporário, instala nele as fontes originais do URM e injeta a fixture [urm_file_persistence_probe.rpy](../tools/fixtures/urm_file_persistence_probe.rpy). SDK, fontes e Wells do repositório não são modificados pelo teste.

### Processo 1 — editar e gravar

1. Inicializa o URM pela sua rotina `afterLoad()`.
2. Muda `urm_file_probe_value` de 0 para 7 pelo método original `Var.setValue`.
3. Registra a variável em `VarsStore` com nome, freeze e monitor; adiciona-a à lista `watched`.
4. Chama `URMFiles.save("urm-runtime-persistence-probe", overwrite=True)`.
5. Um passo Python independente abre o arquivo `.urm` como ZIP, lê os JSONs e verifica o conteúdo.

### Processo 2 — carregar

Um segundo processo Ren'Py inicia com `urm_file_probe_value == 0`, chama `URMFiles.load("urm-runtime-persistence-probe.urm")` e verifica que o valor de gameplay continua 0, enquanto os metadados lembrados, congelados, monitorados e observados foram carregados.

## Resultado observado

O run terminou **SUCCESS**. Logs relevantes:

~~~text
URM_FILE_PROBE_BEFORE_SAVE 7 ...
URM_FILE_PROBE_SAVED True urm-runtime-persistence-probe.urm ['watched', 'properties', 'vars']
URM_ZIP_ENTRIES ['watched', 'properties', 'vars']
URM_JSON_STORES {"properties":{"gameId":"the_question-7","urmVersion":"2.6.2"},"vars":{"urm_file_probe_value":{"frozen":true,"monitor":true,"name":"Runtime probe value"}},"watched":{"urm_file_probe_value":{"name":"Runtime probe watch"}}}
URM_FILE_PROBE_AFTER_LOAD 0 ['watched', 'properties', 'vars'] ...
~~~

As asserções passaram em ambos os processos. O JSON de `vars` guardou o nome exibido e as flags `frozen`/`monitor`; `watched` guardou o nome de exibição. O número 7 editado não aparece como valor em nenhuma entrada do arquivo. No segundo processo, `URMFiles.load()` recuperou esses metadados, mas a variável do jogo permaneceu no default 0.

## Classificação

- **OBSERVADO EM RUNTIME:** o método original `Var.setValue` mudou a variável de jogo para 7 no processo que salvou.
- **OBSERVADO EM RUNTIME:** `URMFiles.save()` produziu ZIP com entradas `watched`, `properties` e `vars`; os JSONs continham metadados de URM descritos acima.
- **OBSERVADO EM RUNTIME:** em processo Ren'Py separado, `URMFiles.load()` restaurou stores/metadados do URM sem restaurar o valor de gameplay, que permaneceu 0.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** `URMFiles.load()` atribui um novo `URMFile` a `URMFiles.file`; `VarsStore` lê suas listas nos stores `vars` e `watched`.
- **CORROBORADO:** para esse percurso e esses stores, o `.urm` persiste organização/configuração de ferramentas do URM, enquanto o save nativo Ren'Py é o mecanismo observado nos documentos 46–47 para restaurar o estado editado de gameplay.

## Limites

Este teste cobre os stores `properties`, `vars` e `watched` e as operações `remember`, `freeze`, `monitor`, `watch`, `Var.setValue`, `URMFiles.save` e `URMFiles.load`. Não cobre todos os stores URM (labels, substituições de texto, snapshots ou outros), nem todas as opções da interface visual de arquivos. O save/load nativo do jogo foi testado separadamente nos documentos 46–47; este workflow não testa como os dois formatos interagem quando ambos são carregados em sequência numa sessão real.

A edição foi realizada pela classe original `Var.setValue`; a digitação no modal gráfico `URM_modify_value` não fez parte deste teste específico. A tela de salvar/carregar `.urm` não foi automatizada aqui; o percurso usa os métodos originais `URMFiles.save/load` diretamente.

## Próxima etapa

Seguir os consumidores dos demais stores e validar `labels`/PathDetection, `replacements`/TextRepl e snapshots, identificando em cada caso se são metadados do URM, conteúdo derivado de análise ou estado de gameplay. Também testar a sequência save nativo → load `.urm` e load nativo → load `.urm` sem presumir que sejam equivalentes.
