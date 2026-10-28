# Como continuar a investigação

1. Repositório canônico atual: `mucholocco86/laborat-rio_renpy`.
2. Consultar primeiro `00_README/MIGRACAO_LABORATORIO_COMPARACAO.md` para conhecer o estado da migração.
3. Não alterar `wells/`, `renpy-7.4.11-sdk/` ou `__urw/`. `wells_beta/` é o laboratório do Walkthrough e só deve ser modificado quando o usuário pedir trabalho de implementação.
4. Continuar a extração panorâmica do URM antes de qualquer poda.
5. Para cada mecanismo crítico, separar fato observado de interpretação.
6. Usar `renpy-7.4.11-sdk/` como referência de leitura/comparação; não modificar a cópia do SDK sem autorização explícita.
7. Prioridade de R&D imediata: completar a investigação do loader `x52MF2` — expansão de dependências, produção de `.x52t`, fallback `.rpyc`, localização do archive e ciclo de atualização — e depois conectar esse circuito ao mapa geral do URM.

## Ponto exato de retomada

### Migração

A árvore `URM_REVERSO/` do novo laboratório foi comparada com a árvore do repositório anterior: 260 entradas em cada uma, sem caminho exclusivo e sem SHA diferente. Os arquivos centrais do SDK usados para AST, Menu, interação, ChoiceReturn, Context, rollback e loader também foram comparados e têm SHA igual. As diferenças gerais do SDK são documentadas no relatório de migração; não as apagar nem presumir que os arquivos compilados diferentes sejam equivalentes.

### Loader URM

A função `loadFile()` em `01_MATERIAL_URM/1_URM_ORIGINAL/framework/bootstrap.rpy`:
- aceita extensões `.x52rpy` e `.x52`;
- testa a fonte base e a variante formada por `fullFn + 't'`;
- prioriza a variante terminada em `t`;
- lê com `renpy.loader.load()`, `.read().decode()` e injeta via `renpy.load_string()`;
- substitui `_x52ModName_` e `_x52MFPath_` somente quando a fonte base é carregável;
- só usa fallback `.rpyc` para a extensão `.x52rpy`, não para `.rpy.x52`.

O documento detalhado é `05_LOADER/01_LOADER_X52MF2_CARGA_E_DEPENDENCIAS.md`. O bootstrap original e convertido foram comparados e têm o mesmo SHA GitHub: `9d72267c2d86c68aa9dac1fee94652c891a611fe`.

### Choices

A descoberta arquitetural mais recente continua em `04_CHOICES/10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md`: URMChoice é uma projeção da estrutura nativa, usa ChoiceReturn para retornar à interação Ren'Py e não executa manualmente o bloco AST. Walkthrough deve observar/projetar; Ren'Py executa e controla rollback.

## Método obrigatório

Primeiro entender → depois inspecionar → depois planejar → só então modificar.

Se faltar informação: pesquisar primeiro, nunca inventar. Registrar novas descobertas no GitHub. O objetivo é que o projeto sobreviva à troca de conta, conversa, modelo ou sessão.

## Atualização de retomada — 2026-10-13

A análise complementar mais recente de Choices foi adicionada em `04_CHOICES/11_MENU_CHOICE_SCREEN_CORRELACAO_E_INTEGRIDADE_DA_SELECAO.md` (commit `33f57d548294fc1c6c1d627d3b23f9fd90532aa9`). Ela confirma, no URM e no SDK 7.4.11, a correlação entre o índice original de `Menu.items`, o `value` da alternativa retornado via `ChoiceReturn` e o ramo selecionado por `Menu.execute`. **Não confundir a posição visual com o índice original**, especialmente quando itens sem bloco são omitidos, condições filtram opções ou textos são substituídos.

### Para um novo chat de engenharia reversa

1. Ler este arquivo e `00_README/WELLS_TRANSFER_MANIFEST.md`; depois `00_README/MIGRACAO_LABORATORIO_COMPARACAO.md`.
2. Revisar `04_CHOICES/10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md` e **11** antes de retomar Choices; revisar `05_LOADER/01_LOADER_X52MF2_CARGA_E_DEPENDENCIAS.md` antes de retomar loader.
3. Ler `10_URM_INTERNAL_MANUAL/README.md` e mapas de referências; buscar código primário em `01_MATERIAL_URM/` e comportamento nativo no SDK.
4. Continuar sem resumir/podar a árvore: investigar efeitos de `condition`, entradas sem bloco, `set`, tradução, visibilidade e rollback na correlação Choice→AST; paralelamente, no loader, rastrear o produtor da variante `t`, `pendingUpdate`, `digest` e resolução do archive.
5. Documentar evidência e lacunas com 🟢 URM, 🔵 Ren'Py, 🟡 observação, 🟠 hipótese, 🔴 descartado. Nunca afirmar execução/teste real se houve apenas inspeção estática.
6. Trabalhar exclusivamente em documentos de `URM_REVERSO/` no laboratório canônico, salvo autorização explícita. Não sincronizar nem alterar `modulos`, SDK, `wells/`, `wells_beta/` ou `__urw/`.
7. Método obrigatório: **primeiro entender → depois inspecionar → depois planejar → só então modificar**. Registrar fontes exatas, dúvidas e commit de cada avanço.

**Estado da migração:** o relatório documenta a igualdade de `URM_REVERSO/` **antes** das atualizações documentais posteriores. Os diretórios de documentação alterados desde então são diferenças intencionais, não falhas da clonagem; verificar sempre a linha de base indicada no relatório.

## Atualização — 2026-10-15: nova prioridade da engenharia

O usuário confirmou (🟡 observação de testes) que o Walkthrough do Wells estável já funciona e está testado há semanas. Foi feita inspeção estática de `wells/` e criada a nota `09_WELLS_APPLICATION/OBSERVACAO_WELLS_ESTAVEL_2026_10_15.md` (commit `222e3a6`). **Não modificar Wells estável.**

A pesquisa principal avançou para `04_CHOICES/12_CIRCUITOS_LEITURA_EDICAO_PESQUISA_PERSISTENCIA.md` (commit `ada15fa`): leitura de valores em `Var.value`, edição em `Var.setValue`, pesquisa em `SearchClass`, arquivos `.urm` (ZIP + JSON), configurações `persistent`/globais, saves nativos e snapshots. Trata-se de **mapa inicial, não conclusão**. O próximo passo prioritário é seguir todos os produtores/consumidores de stores e ações de interface, detalhar a recursão da pesquisa, comprovar reaplicação de dados carregados e cruzar APIs com o SDK 7.4.11. Não confundir edição do store com edição física de scripts, nem `.urm` com save nativo.

**Plano de versões:** completar URM usando somente o SDK 7.4.11 como referência nativa; **após** fechar a investigação, comparar mecanismos com os SDKs 6.99.4 e 8.5.3 presentes no laboratório. Preservar versões como fontes separadas e não misturar semânticas.

## Retomada atual — 2026-10-28

Esta atualização substitui como prioridade imediata os próximos passos antigos deste arquivo. O foco continua sendo Choices, edição de estado, rollback e persistência no SDK 7.4.11; o loader permanece documentado, mas não é o próximo eixo.

Estado verificado:
- Choices original do URM conseguiu selecionar alternativa com condição falsa e executar o bloco nas fixtures dos docs 41–42.
- Edição original de variável, rollback e save/load nativo foram observados nos docs 38–47.
- Persistência em `.urm` foi observada para os stores examinados; o valor geral de gameplay não foi restaurado pelo `.urm` nos casos testados (docs 49–50).
- Snapshots demonstraram diff superficial para escalares versus containers simples mutados in-place (doc 51).
- Settings por jogo e globais foram testados em dois processos; substituição de texto foi validada chamando diretamente o callback, sem render final de Menu.

Próximas perguntas: filtro de texto numa Choice renderizada; persistência de Snapshots em save nativo; combinações de ordem entre save/load nativo e `.urm`; lacunas visuais das interfaces. Não comparar SDKs 6.99.4/8.5.3 antes de fechar os contratos do 7.4.11.

O doc 52 confirma pela fonte SDK que `Menu.execute()` chama `say_menu_text_filter` e preserva o índice original como valor; o teste pendente agora é observar a renderização efetiva da Choice.\n\nLeia [REVISAO_DOCUMENTAL_URM_2026-10-28.md](REVISAO_DOCUMENTAL_URM_2026-10-28.md) para inventário dos 77 documentos, correções e limites atuais.
