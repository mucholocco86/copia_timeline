# Missão delegável — Engenharia reversa investigativa do URM

**Criado em:** 2026-10-15. **Estado:** plano preparado; **nenhuma execução de Workflow/Work iniciada por este documento**.

## Propósito

Conduzir uma primeira investigação extensa e independente do Universal Ren'Py Mod, produzindo relatórios auditáveis. A segunda linha, coordenada por ChatGPT com o usuário, fará a verificação de cada conclusão contra as fontes primárias e o SDK Ren'Py 7.4.11 antes de consolidá-la como comprovada.

## Fonte de verdade e repositório

Repositório canônico: `mucholocco86/laborat-rio_renpy`.

Ler antes de começar:
- `URM_REVERSO/00_README/WELLS_TRANSFER_MANIFEST.md`
- `URM_REVERSO/00_README/COMO_CONTINUAR.md`
- `URM_REVERSO/04_CHOICES/10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md`
- `URM_REVERSO/04_CHOICES/11_MENU_CHOICE_SCREEN_CORRELACAO_E_INTEGRIDADE_DA_SELECAO.md`
- `URM_REVERSO/04_CHOICES/12_CIRCUITOS_LEITURA_EDICAO_PESQUISA_PERSISTENCIA.md`
- `URM_REVERSO/05_LOADER/01_LOADER_X52MF2_CARGA_E_DEPENDENCIAS.md`
- `URM_REVERSO/10_URM_INTERNAL_MANUAL/README.md`

Fontes primárias:
- `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/`
- `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/`
- `renpy-7.4.11-sdk/`

Os SDKs 6.99.4 e 8.5.3 **não** devem ser usados para justificar conclusões sobre o comportamento do URM no 7.4.11; a comparação entre gerações ocorrerá somente após a conclusão da pesquisa-base.

## Proteções e permissão

- **Não modificar** `wells/`, `wells_beta/`, SDKs, URM original/convertido ou outros projetos.
- **Não modificar** documentos consolidados existentes para substituir conclusões.
- Produzir inicialmente resultados **em relatório de resposta ou arquivo para revisão**, sem commits automáticos. O revisor humano/assistente integrará somente evidências verificadas. Se houver autorização explícita para gravar relatórios no repositório, criar somente novos arquivos na área de pesquisa provisória previamente acordada.
- Não executar scripts de jogos desconhecidos como parte da inspeção estática; não alterar saves.
- Não declarar runtime comprovado quando houver apenas leitura estática.
- Registrar fontes com caminho, símbolo, linhas ou trechos e commit/SHA quando possível.

## Pacotes de investigação — ordem de prioridade

### P1 — Edição de variáveis e ações
Rastrear `classes/vars.rpy`: `VarsStoreClass`, `Var`, `SetVarValue`, `CreateVar`, `StoreMonitorClass`. Identificar chamadas em screens, pages, main, CodeView, actions. Separar atribuição, append, criação, exclusão, freeze, watch, monitor, callbacks e rollback.

### P2 — Pesquisa e leitura
Rastrear `classes/search.rpy`, `labels.rpy`, `Characters.rpy`, `codeview.rpy` e todas as telas consumidoras. Documentar busca por nome, valor, labels, recursão, filtros, tratamento de ciclos, paginação, tipos e limites. Distinguir busca no store de busca em script AST.

### P3 — Persistência e restauração
Rastrear `classes/URMFiles.rpy`, `settings.rpy`, `gamesaves.rpy`, `snapshots.rpy`, `states.rpy`. Mapear cada formato de arquivo, estrutura ZIP/JSON, stores escritos, leitores, produtores, gatilhos de autoLoad, aplicação de valores ao jogo, diferenças de saves nativos e rollback.

### P4 — Choices e edição do fluxo
Rastrear `classes/choices.rpy`, `PathDetection.rpy`, `codeview.rpy`, `screens/choices.rpy`, módulos de interface e SDK. Determinar o que URM **lê**, o que permite **selecionar**, o que permite **alterar** e o que não modifica; registrar os caminhos exatos de ação, efeitos, limites e rollback. Verificar `Menu.items`, índices estruturais, `MenuEntry`, `ChoiceReturn`, condições e alternativas repetidas.

### P5 — Loader, API e componentes indiretos
Completar `framework/bootstrap.rpy`, `classes/API.rpy`, `ConstantStoreHandler.rpy`, `ExceptionHandler.rpy`, `utils.rpy`, `textrepl.rpy` e dependências. Identificar como se produzem/consomem variantes `x52t`, ordem de init, archives, `digest`, updates e pontos de injeção.

### P6 — Cobertura completa
Construir inventário de **todos** os arquivos URM, dependências e telas, marcando investigado, parcialmente investigado, não investigado e não aplicável, com justificativa. Evitar declarar conclusão apenas por ausência de achados.

## Contrato de entrega por pacote

Cada relatório deve conter:
1. Objetivo e fronteiras.
2. Arquivos inspecionados (path, SHA/commit, função/classe).
3. Diagrama de chamadas e fluxo de dados.
4. Tabela de afirmações atômicas com evidência exata.
5. Classificação: confirmado na fonte URM; confirmado no SDK 7.4.11; observado em runtime; hipótese; contradito; desconhecido.
6. Diferenças entre o que o URM **faz** e o que a API nativa do Ren'Py **garante**.
7. Dependências ainda não rastreadas e casos-limite.
8. Sugestão de testes isolados sem modificar fontes protegidas.
9. Lista de perguntas para a segunda investigação.

## Critérios de aceitação da revisão

O revisor deve refazer, independentemente, cada percurso de código de alto impacto; validar afirmações contra o SDK 7.4.11; marcar explicitamente confirmações, refutações e dúvidas; exigir evidência de runtime quando a afirmação for dinâmica; e somente então transferir descobertas para a documentação canônica. Resultados não verificados permanecem como hipóteses.

## Regra de continuidade

Método obrigatório: **primeiro entender → depois inspecionar → depois planejar → só então modificar**. Não pular componentes, não confundir arquivo `.urm` com save Ren'Py, nem alteração de `renpy.store` com edição de script no disco.

**Este documento é um plano pronto para execução em Work, não uma confirmação de que Work foi iniciado.**
