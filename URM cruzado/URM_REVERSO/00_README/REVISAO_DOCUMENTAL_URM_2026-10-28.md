# Revisão documental do URM — estado em 2026-10-28

**Repositório:** [mucholocco86/laborat-rio_renpy](https://github.com/mucholocco86/laborat-rio_renpy)  
**Escopo auditado:** 79 documentos Markdown nas áreas de documentação de `URM_REVERSO` listadas abaixo.  
**Método:** conferência do inventário, dos índices, das classificações de evidência e das afirmações de pendência contra os documentos e execuções posteriores até 2026-10-28. Os registros de cada experimento permanecem cronológicos; quando uma conclusão antiga foi superada, a atualização aponta para a evidência posterior em vez de apagar o histórico.

## Resultado da revisão

**Adições após a primeira auditoria:** o doc 53 testa save/load nativo de Snapshots em processo novo: o slot carregou, mas o singleton URM permaneceu vazio. O doc 52 examina no SDK como `Menu.execute()` aplica `say_menu_text_filter` antes de passar o índice AST como valor da alternativa. Isso confirma estaticamente que alterações de texto e identidade estrutural são camadas separadas; o texto final renderizado continua pendente de validação runtime.

A análise atual confirma que o núcleo prioritário já tem evidência bem além da inspeção estática inicial:

- **Choice e execução:** o URM original pode selecionar uma alternativa com condição falsa e fazer o Ren'Py executar seu bloco AST na fixture testada; rollback posterior e reescolha foram observados em testes integrados (docs 36, 41 e 42).
- **Edição e rollback:** o editor original do URM alterou uma variável de gameplay; o bloco seguinte leu o novo valor e rollback restaurou o valor e o estado da rota nos cenários documentados (docs 38, 39, 44 e 45). Isso vale para as sequências e SDK testados, não para toda ação/posição possível.
- **Save nativo:** o valor editado e a rota sobreviveram ao save/load e ao carregamento por um segundo processo Ren'Py (docs 46 e 47).
- **Arquivo `.urm`:** testes em dois processos mostraram que `vars`, `watched`, `textboxCustomizations`, `labels` e `replacements` guardam dados/configurações próprios do URM; os probes não restauraram um snapshot geral das variáveis de gameplay (docs 49, 50 e `06_VARIABLES/02–03`).
- **Configurações:** `persistent.URMSettings` e o ZIP global `settings` são canais separados e foram recuperados em processo novo no run 40666289110, descrito em `06_VARIABLES/03_MAPA_CANAIS_PERSISTENCIA_URM.md`.
- **Snapshots:** o diff do URM detectou escalares e substituição de containers por conteúdo diferente; não detectou mutação in-place nem novas listas/dicionários de conteúdo igual. O teste adicional mostrou que o `Var` antigo na comparação é somente leitura e o atual edita o store, preservando o snapshot; variáveis ausentes aparecem como `None` e não são recriadas pela edição do diff; em comparação entre dois snapshots, ambos os lados são somente leitura; `None` real e chave ausente podem ter a mesma projeção no diff, embora a presença seja detectada (doc 51). Snapshots não é rollback.

## Correções de status aplicadas nesta revisão

1. **Doc 48:** a pendência de teste de `.urm` foi atualizada com os resultados posteriores dos docs 49–50. O documento continua registrando que sua própria etapa foi estática.
2. **Doc 50:** passou de “runtime pendente” a um relatório de inspeção mais runtime para `labels`/`replacements` e Snapshots, com limites explícitos.
9. **Doc 51:** ampliação runtime com substituição de containers e comparação de conteúdo igual/diferente; fixture usa checagens explícitas.
10. **Doc 53:** teste runtime em dois processos encerrou a pendência sobre restauração do singleton Snapshots por save nativo no cenário coberto; outras rotas de exportação permanecem fora do teste.
3. **Doc 14:** recebeu uma nota de atualização que encaminha os casos inicialmente pendentes para os testes integrados 36–47.
4. **Doc 15 duplicado (ChoiceReturn/checkpoint/rollback):** recebeu referências aos testes posteriores que comprovaram runtime em cenários delimitados.
5. **Doc 21:** a pendência de seleção de condição falsa foi atualizada com os resultados 41–42.
6. **Doc 22:** os contratos sintéticos permanecem válidos como testes reduzidos; a integração com o URM original, antes pendente, é complementada pelos docs 36–47.
7. **Compatibilidade Ren'Py:** README e doc 02 foram atualizados para distinguir o que já foi testado em runtime do que continua pendente.
8. **Índices de continuidade:** README geral, README de Choices, README de Variables, `COMO_CONTINUAR` e manifesto foram atualizados para apontar ao estado de 28/10 e a este relatório.

## Limites que continuam explícitos

- O teste de `TextRepl` após load chamou diretamente `renpy.config.say_menu_text_filter`; não demonstrou o texto final renderizado numa screen real de Choice.
- A interação visual automatizada com o modal de Gamesaves e o clique físico no hyperlink de CodeView continuam pendentes; alguns testes usam o handler original diretamente, com os limites indicados nos respectivos documentos.
- A o teste runtime do doc 53 mostrou que a instância Snapshots não foi restaurada após save/load nativo em processo novo, no percurso específico da fixture.
- As conclusões runtime são específicas do Ren'Py 7.4.11, das fixtures e dos percursos descritos. Não há comparação validada com SDK 6.99.4 ou 8.5.3.
- A fonte convertida por unrpyc é uma representação de análise; quando a conclusão depende de runtime, os testes integrados com fontes originais são identificados separadamente.
- A enumeração dos seis stores `.urm` conhecidos deriva das classes convertidas examinadas; o loader aceita entradas genéricas, então ela não prova que arquivos históricos/externos contenham somente esses nomes.

## Continuidade recomendada

1. Fechar a validação end-to-end do filtro de texto numa Choice realmente exibida, separando texto AST, filtro de menu e texto final renderizado.
2. A tela original de Snapshots foi inspecionada no doc 53 e não mostra ação de exportação; uma busca mais ampla por extensões externas não faz parte desta etapa.
3. Completar a matriz de save/load `.urm` + save nativo em ordens diferentes, sem tratar os formatos como equivalentes.
4. Revisar os módulos restantes do URM por produtor, consumidor, estado, persistência e dependências do SDK.
5. Comparar outras versões do SDK somente após fechar cada comportamento no 7.4.11.

## Inventário revisado

O inventário abaixo identifica os 79 documentos Markdown incluídos nesta revisão. As notas em si permanecem como registros técnicos cronológicos; os índices e correções acima indicam quando evidência posterior amplia ou substitui uma pendência antiga.


### 00_README

- `COMO_CONTINUAR.md`
- `MIGRACAO_LABORATORIO_COMPARACAO.md`
- `README.md`
- `WELLS_TRANSFER_MANIFEST.md`
- `WORKFLOW_MISSAO_ENGENHARIA_REVERSA.md`

### 03_ARCHITECTURE

- `ARQUITETURA_ATUAL.md`

### 04_CHOICES

- `53_PERSISTENCIA_SNAPSHOTS_SAVE_NATIVO.md`
- `52_TEXTREPL_MENU_AST_FILTER_PATH.md`
- `01_FLUXO_CHOICE_ROLLBACK.md`
- `02_LIMITES_E_CASOS_ESPECIAIS.md`
- `03_AST_MENU_BLOCOS_CALL_IF_JUMP.md`
- `04_CHOICE_RETURN_ROLLBACK_7_4_11.md`
- `05_MICROCICLO_INTERACAO_ROLLFORWARD.md`
- `06_CONTEXT_ROLLBACK_EXECUTION_7_4_11.md`
- `06_DID_INTERACTION_CIRCUITO_INTERACAO_ROLLBACK.md`
- `06_FIXED_ROLLBACK_E_FIX_ROLLBACK_WITHOUT_CHOICE.md`
- `07_CODEVIEW_INTERATIVO_E_EDICAO.md`
- `07_URM_CHOICE_INFORMATION_PROJECTION.md`
- `08_FLUXO_EXECUCAO_BLOCO_CHOICE_IF_CALL_JUMP.md`
- `09_MENU_ROLLBACK_FORCE_E_CONTINUIDADE_BLOCO.md`
- `10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md`
- `11_MENU_CHOICE_SCREEN_CORRELACAO_E_INTEGRIDADE_DA_SELECAO.md`
- `12_CIRCUITOS_LEITURA_EDICAO_PESQUISA_PERSISTENCIA.md`
- `13_REVISAO_INDEPENDENTE_BUSCA_CRIACAO_CARGA_URM.md`
- `14_ESCOLHAS_ACOES_MUTACOES_E_ROLLBACK.md`
- `15_VALIDACAO_SDK_7411_MENU_CHOICE_RETURN_CHECKPOINT.md`
- `15_VALIDACAO_SDK_CHOICERETURN_CHECKPOINT_ROLLBACK.md`
- `16_CODEVIEW_BUSCA_EDICAO_VARIAVEIS.md`
- `17_EDICAO_ITENS_MUTACOES_OBJETOS_ROLLBACK.md`
- `18_CALLBACK_PYTHON_E_CHECKPOINTS_URM.md`
- `19_FECHAMENTO_ESTADO_ANTES_ROLLBACK.md`
- `20_EDICAO_MANUAL_SAVE_NATIVO_E_ROOTS.md`
- `21_PROPAGACAO_ACAO_URM_E_CONDICOES_MENU.md`
- `22_RUNNER_TESTE_RENPY_ENCERRAMENTO_E_EVIDENCIA_RUNTIME.md`
- `23_STOREMONITOR_INTERCEPTACAO_E_EDICAO_URM.md`
- `24_CALLBACK_SCREEN_EDIT_RUNTIME.md`
- `25_CALLBACK_ROLLBACK_STOREDELTA_GAMEPLAY.md`
- `26_CHOICES_CODEVIEW_ACOES_DE_VARIAVEIS_E_LIMITES.md`
- `26_FREEZE_MONITOR_WATCH_EDICAO_URM.md`
- `27_FREEZE_RUNTIME_EDICAO_E_CALLBACK.md`
- `27_NOTIFICACAO_REVERT_E_PERSISTENCIA.md`
- `28_FREEZE_ROLLBACK_RUNTIME.md`
- `29_NOTIFICACOES_VARIAVEIS_MONITORADAS_RUNTIME.md`
- `30_MONITOR_ROLLBACK_NOTIFICACAO_URM.md`
- `31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md`
- `32_CICLAGEM_STOREDELTA_ANTES_CALLBACK_REVERT.md`
- `33_ROLLBACK_FIXO_E_ESCOLHA_URM.md`
- `34_SEGUNDO_ROLLBACK_APOS_REESCOLHA_URM.md`
- `35_ENTRADA_DA_TELA_CHOICES_E_FIXED_ROLLBACK.md`
- `36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md`
- `37_CODEVIEW_EDICAO_VARIAVEL.md`
- `38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md`
- `39_STOREMONITOR_DELTA_E_EDICAO_POR_SCREEN.md`
- `40_MENU_CONDICOES_FORCE_CHECKPOINT_RUNTIME.md`
- `41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md`
- `42_ROLLBACK_APOS_CHOICE_CONDICAO_FALSA.md`
- `43_CONDICAO_DINAMICA_CHOICE_EDITADA_PELO_URM.md`
- `44_ROLLBACK_VARIAVEL_CONDICAO_CHOICE.md`
- `45_EDITOR_GRAFICO_CHOICE_DINAMICA_ROLLBACK.md`
- `46_SAVE_LOAD_NATIVO_APOS_EDICAO_CHOICE.md`
- `47_SAVE_LOAD_CHOICE_PROCESSO_NOVO.md`
- `48_FRONTEIRA_PERSISTENCIA_SAVE_NATIVO_E_URM.md`
- `49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md`
- `50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md`
- `51_SNAPSHOTS_DIFF_RUNTIME_CONTAINERS.md`
- `README.md`

### 05_LOADER

- `01_LOADER_X52MF2_CARGA_E_DEPENDENCIAS.md`
- `README.md`

### 06_RENPY_COMPATIBILITY

- `02_SDK_SAVELOAD_URM_PERSISTENCIA.md`
- `README.md`

### 06_VARIABLES

- `01_URM_STORES_MONITORAMENTO_E_SUBSTITUICAO_DE_TEXTO.md`
- `02_TEXTBOX_CUSTOMIZATIONS_URMFILE_RUNTIME.md`
- `03_MAPA_CANAIS_PERSISTENCIA_URM.md`
- `README.md`

### 07_EVIDENCE

- `README.md`

### 08_CROSS_REFERENCE

- `MAPA_CRUZADO.md`

### 09_WELLS_APPLICATION

- `OBSERVACAO_WELLS_ESTAVEL_2026_10_15.md`
- `README.md`

### 10_URM_INTERNAL_MANUAL

- `README.md`

