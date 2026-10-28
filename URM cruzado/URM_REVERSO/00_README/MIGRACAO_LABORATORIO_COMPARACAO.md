# Relatório de migração — `modulos` → `laborat-rio_renpy`

**Data da verificação:** 2026-10-12  
**Repositório canônico a partir desta migração:** [mucholocco86/laborat-rio_renpy](https://github.com/mucholocco86/laborat-rio_renpy)  
**Repositório anterior de comparação:** [mucholocco86/modulos](https://github.com/mucholocco86/modulos)

Este relatório registra uma comparação feita diretamente pela API do GitHub nas branches `main`. Ele não altera nem substitui o SDK. O objetivo é estabelecer uma linha de base verificável para continuar a engenharia reversa no laboratório.

## 1. Resultado de `URM_REVERSO/`

Comparação recursiva de árvore Git:

- entradas no laboratório: **260**;
- entradas no repositório anterior: **260**;
- caminhos presentes somente no laboratório: **0**;
- caminhos presentes somente no repositório anterior: **0**;
- caminhos com SHA diferente: **0**.

Conclusão: a árvore `URM_REVERSO/` está idêntica no nível de caminhos e hashes Git entre os dois repositórios no momento da verificação. Isso inclui os documentos existentes de Choices, o material original e convertido do URM, o manifesto de transferência e o manual interno.

Exemplos de hashes idênticos:
- `04_CHOICES/10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md`: `a649d0cea5a32a4fec63ede2e1bba0cb9ebaf4d4`;
- `04_CHOICES/README.md`: `1ca8dc1bd1e716f09daddba64afe0c1b9e6989d3`;
- `00_README/WELLS_TRANSFER_MANIFEST.md`: `733d0107a184ee3798d6cda0dfaf5849f620ae1c`;
- `01_MATERIAL_URM/1_URM_ORIGINAL/framework/bootstrap.rpy`: `9d72267c2d86c68aa9dac1fee94652c891a611fe`.

## 2. Arquivos centrais do SDK comparados

Os seguintes arquivos centrais possuem SHA Git idêntico nos dois repositórios:

| Arquivo | SHA |
|---|---|
| `renpy/ast.py` | `d81ffc13f28f0b7442ba6905f1745ee838f7b185` |
| `renpy/exports.py` | `781b35b31522dafc6a24e7c3212d206c7bd6dfa5` |
| `renpy/python.py` | `c5eb2819a3e4ee096dbf01130d70a77f9b623484` |
| `renpy/game.py` | `8ca1c771302f106913f7f4dd66172677b14659dc` |
| `renpy/ui.py` | `914a0c4702b7af391e014702a16ccc333e7573de` |
| `renpy/display/core.py` | `14c920f9fe8c95627a698bd56a1e61c7f4b02074` |
| `renpy/loader.py` | `58c11930e0d8e6dac24c42c8a94bddeb567e2137` |
| `renpy/script.py` | `fff38bd03c7fccddff8b81ee141049abaf38f88b` |
| `renpy/common/00action_file.rpy` | `5bd3782bf81d639e48659b756de911f252a6d4e7` |

Esses arquivos cobrem os mecanismos principais que sustentam a análise já feita de AST, Menu, interação, ChoiceReturn, Context, rollback, carregamento e saves.

## 3. Diferenças observadas no SDK

A árvore recursiva do GitHub retornou:

- entradas totais do SDK no laboratório: **2.840**;
- entradas totais no repositório anterior: **2.667**;
- entradas adicionais no laboratório: **175**;
- entradas somente no repositório anterior: **2**;
- caminhos compartilhados com SHA diferente: **151**.

Considerando apenas arquivos (blobs), os números são:

- blobs no laboratório: **2.597**;
- blobs no repositório anterior: **2.448**;
- blobs somente no laboratório: **150**;
- blobs somente no repositório anterior: **1**;
- blobs compartilhados com SHA diferente: **127**.

Esses números brutos incluem arquivos compilados, caches, pastas e projetos de exemplo. **Não devem ser interpretados como 127 mudanças de comportamento no código-fonte do motor.**

### 3.1 Código-fonte textual

Nos arquivos-fonte/textuais que apresentaram SHA diferente — incluindo `EasyDialogsResources.py`, `EasyDialogsWin.py`, os dois arquivos de texto gregos, `tutorial/game/gui.rpy` e `renpy/common/_theme_awt/OFL.txt` — a normalização de finais de linha CRLF/LF torna o conteúdo idêntico. Isso indica diferenças de formatação de linha, não alterações semânticas nesses arquivos.

No filtro de arquivos-fonte/textuais usado nesta comparação, não foram encontradas diferenças de conteúdo em arquivos-fonte do núcleo `renpy/`; as diferenças de hashes nas árvores `renpy/`, `lib/` e em outras pastas são dominadas por arquivos compilados `.pyo` e mudanças de conteúdo de diretório.

### 3.2 Material adicional no laboratório

O laboratório contém itens que não aparecem no SDK do repositório anterior, incluindo:

- `the_question/` — projeto de exemplo Ren'Py completo;
- `tmp/FamilyMatters-v0.14-pc/navigation.json`;
- `log.txt`;
- `launcher/game/saves/persistent`;
- `renpy/common/_tv_unsafe.png`.

O repositório anterior contém apenas um artefato extra em `renpy/__pycache__/pasta vazia ao descompactar o sdk.txt`.

Esses arquivos extras foram preservados. Não foram apagados nem movidos.

## 4. O que podemos concluir — e o que ainda não podemos

### Confirmado

- A documentação e os materiais da engenharia reversa foram migrados sem diferenças de SHA em `URM_REVERSO/`.
- Os principais arquivos-fonte do runtime usados na análise anterior são idênticos.
- Há diferenças substanciais no conjunto de arquivos do SDK, incluindo arquivos compilados e projetos adicionais.
- As diferenças textuais de fonte examinadas foram apenas finais de linha.

### Ainda não confirmado

- Que todos os arquivos compilados `.pyo` no laboratório correspondam exatamente ao mesmo conteúdo-fonte ou tenham sido produzidos pelo mesmo processo.
- Que os itens adicionais do laboratório sejam melhorias do motor; podem ser dados de teste, projetos de exemplo, caches ou artefatos locais.
- Que o SDK do laboratório seja byte a byte idêntico ao SDK anterior.

**Regra de segurança:** considerar o SDK do laboratório como a cópia de referência fornecida pelo usuário, mas não presumir que seus arquivos compilados sejam semanticamente equivalentes apenas porque os arquivos-fonte centrais comparados são iguais. Preservar a cópia e investigar diferenças específicas somente quando forem relevantes para uma pergunta técnica.

## 5. Repositório canônico e proteção

A partir desta migração, novos documentos de R&D devem ser escritos em:

`mucholocco86/laborat-rio_renpy`

O repositório `mucholocco86/modulos` passa a ser a origem de comparação/histórico para esta migração. Não o apagar nem fazer sincronização destrutiva automática.

Continuam protegidos contra modificações não autorizadas:
- `renpy-7.4.11-sdk/`;
- `wells/`;
- `wells_beta/` (exceto quando o usuário solicitar trabalho de laboratório);
- `__urw/`.

Apenas a documentação de engenharia dentro de `URM_REVERSO/` foi atualizada nesta etapa.


## 6. Alterações documentais feitas depois da comparação-base

Os números de igualdade de `URM_REVERSO/` acima descrevem a árvore **antes** de adicionarmos as notas de migração e a análise complementar do loader. Para manter rastreabilidade, depois da comparação foram feitas as seguintes alterações intencionais somente dentro de `URM_REVERSO/` no laboratório:

**Novos arquivos**
- `URM_REVERSO/00_README/MIGRACAO_LABORATORIO_COMPARACAO.md` — este relatório.
- `URM_REVERSO/05_LOADER/01_LOADER_X52MF2_CARGA_E_DEPENDENCIAS.md` — análise detalhada do loader.

**Arquivos atualizados**
- `URM_REVERSO/00_README/README.md` — identifica o laboratório canônico e aponta para os novos documentos.
- `URM_REVERSO/00_README/COMO_CONTINUAR.md` — atualiza o ponto de retomada.
- `URM_REVERSO/00_README/WELLS_TRANSFER_MANIFEST.md` — registra a migração e esclarece que o SHA histórico pertence ao repositório anterior.
- `URM_REVERSO/05_LOADER/README.md` — indexa a nova análise.

Portanto, **após essas alterações**, o repositório canônico contém intencionalmente seis mudanças documentais que não existiam na árvore comparada do repositório anterior. Isso não é uma falha de cópia: é o resultado esperado da continuação da engenharia no novo laboratório. Nenhum arquivo do SDK foi modificado por esta etapa.
