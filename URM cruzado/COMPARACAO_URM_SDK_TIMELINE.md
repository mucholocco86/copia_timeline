# URM cruzado: comparação documental e de SDKs

**Data:** 2026-10-28  
**Repositório:** `mucholocco86/timeline`  
**Objetivo:** preparar a revisão futura da leitura de Choices, rollback e replay do Timeline com base na documentação do URM e na comparação dos SDKs do laboratório.

## Proveniência e limites

A documentação de referência foi copiada do repositório `mucholocco86/laborat-rio_renpy`, pasta `URM_REVERSO/`, no commit `05ceffdece80f9039328f8ccf5b921b0574bc982`. A revisão documental de 28/10 informa 90 arquivos Markdown no inventário corrente; os 90 foram copiados para `URM cruzado/URM_REVERSO/` preservando os caminhos relativos. Os SHAs Git dos 90 blobs de destino conferem com os originais.

O conteúdo do laboratório permanece a fonte canônica e não foi alterado. A cópia aqui é um retrato daquele commit: atualizações futuras na pasta canônica não serão refletidas automaticamente nesta pasta.

A documentação descreve inspeção estática do URM e testes integrados delimitados ao Ren’Py 7.4.11. A comparação abaixo usa os arquivos-fonte do SDK 6.99.4 e 8.5.3 guardados no laboratório. Ela confirma contratos visíveis no código, não uma execução runtime do URM nem do Timeline nessas duas versões. O SDK 6.99.4 não contém um `renpy/rollback.py` separado: o `RollbackLog` está em `renpy/python.py`; sua ausência como arquivo separado não significa ausência do mecanismo.

## Comparação dos mecanismos do Ren’Py

| Área | SDK 6.99.4 | SDK 7.4.11 (referência da documentação URM) | SDK 8.5.3 |
|---|---|---|---|
| AST do menu | `renpy/ast.py: Menu.execute` constrói as opções e usa o índice original de `Menu.items` como valor da alternativa com bloco; após o retorno, encaminha para o primeiro nó do bloco escolhido. | Os documentos 11, 36 e 42 correlacionam índice original, `ChoiceReturn`, seleção de ramo e rollback; há testes runtime delimitados. | `renpy/ast.py: Menu.execute` preserva a mesma ligação estrutural: cada alternativa com bloco carrega o índice AST original e o retorno encaminha a `self.items[index]`. A versão acrescenta caption, argumentos e filtros de texto. |
| Registro de rollback | `RollbackLog` está em `renpy/python.py`, versão serializada 4; inclui log, limite, roll-forward e fixed rollback. `begin()`, `complete()`, `checkpoint()`, `rollback()`, `freeze()` e `unfreeze()` estão nesse módulo. | A documentação examina o ciclo Context/RollbackLog e separa `did_interaction`, checkpoint, limite e `rollback_is_fixed`; docs 34, 36 e 42 mostram casos runtime específicos. | `RollbackLog` está em `renpy/rollback.py`, versão serializada 7. Mantém o ciclo de registros, stores, objetos reversíveis, checkpoints e roll-forward, com assinaturas e estados ampliados. |
| Contexto | `Context.rollback_copy()` copia pilhas de chamada/retorno/dinâmica e o nó atual, entre outros campos. | Os docs 6 e 15 descrevem o contexto restaurado pelo log; os resultados de runtime são específicos à fixture 7.4.11. | `Context.rollback_copy()` mantém a cópia de pilhas e nó, e inclui campos adicionais de estado anormal e interação. |
| Reescolha | O AST do menu continua sendo o dono da execução do bloco: o motor recebe um valor de retorno e seleciona o ramo correspondente. | O URM abre sua interface durante fixed rollback e devolve um `ChoiceReturn`; o Ren’Py executa o bloco. A interface do URM é uma projeção da escolha nativa, não um executor próprio do bloco. | O código continua a separar a interação que retorna o índice e a execução posterior do bloco AST; opções de rollback do menu e argumentos são mais ricos. |

### Consequências para o Timeline

1. **A identidade da opção é estrutural.** Índice de linha visível ou texto não é uma âncora confiável. Condições, itens sem bloco, filtros/tradução e argumentos podem alterar o conjunto apresentado. O Timeline deve correlacionar a opção com a posição original do nó AST, preservando a mesma semântica que o menu do jogo usa.
2. **Ren’Py deve executar a escolha.** A evidência do URM favorece retornar o jogador ao menu real e deixar que a interação nativa devolva a escolha. Selecionar um card pode escolher qual menu revisitar; o card não deve simular a ação como se fosse dono do bloco da história.
3. **Rollback não equivale a restaurar variáveis apenas.** O fluxo nativo coordena contexto de execução, pilhas, alterações de stores, objetos reversíveis, checkpoints, limite e dados de roll-forward. Pular nós de diálogo ou reconstruir só uma parte desse estado pode levar a cena/diálogo desalinhados.
4. **Checkpoint e interação são sinais diferentes.** A documentação do URM destaca que `did_interaction` não é o próprio checkpoint e que o callback do StoreMonitor apenas solicita checkpoint em determinados caminhos Python. Não se deve inferir um ponto de rollback exato contando cliques, diálogos ou PAGEUPs.
5. **Fixed rollback é um estado próprio.** Limite de rollback zero, dados de roll-forward e `rollback_is_fixed` não são equivalentes. O URM demonstrou que uma nova alternativa pode ser escolhida durante fixed rollback em testes delimitados no 7.4.11.

## Leitura do Timeline beta atual

O código inspecionado é o beta em `wells_beta/timeline/` no commit `fb754300a85adfec458a0519f92198856b0f12b8`.

- `timeline_runtime.rpy` registra os menus e associa as opções ao índice AST original; o wrapper de menu também sustenta o caminho de replay automático.
- `backend/tl_state.rpy` tenta restaurar o snapshot capturado imediatamente antes do menu-alvo. Se não houver snapshot utilizável, prepara uma reprodução compatível que refaz escolhas anteriores e deixa a escolha-alvo para a tela nativa do jogo.
- `backend/tl_state.rpy` monta um `RollbackLog` e chama `unfreeze(..., label="_after_load")` para restaurar o snapshot. Esse caminho usa estruturas internas do Ren’Py e precisa ser validado por versão; a inspeção estática não comprova compatibilidade universal.
- O objetivo funcional mais seguro continua sendo chegar ao menu alvo com o contexto e o store daquele ponto, exibir a escolha original e deixar o motor executar o ramo selecionado. O fallback de replay deve ser avaliado contra esse contrato, especialmente em menus condicionais/aninhados e scripts que intercalam diálogo, chamadas e efeitos de estado.

## Direção de investigação antes de qualquer alteração

1. Construir testes equivalentes para 6.99.4 e 8.5.3 que observem: nó Menu atual, índice AST retornado, variáveis/objetos, pilhas de contexto, checkpoints, roll-forward, fixed rollback e continuação após uma nova escolha.
2. Comparar esses traces com os cenários URM 34–42 e com os casos do Timeline/MyDorm já relatados. Registrar cada divergência separando inspeção de fonte e execução real.
3. Validar o caminho de snapshot/unfreeze do Timeline em cada geração, incluindo restauração imediata no menu, escolha nativa, avanço, rollback comum e nova reescolha. Incluir SHIFT+R, que já causou problemas anteriormente.
4. Somente após fechar esse mapa, propor uma alteração pequena e localizada no beta. Não modificar o Wells estável, a documentação canônica do URM ou os SDKs do laboratório nesta etapa.

## Arquivos-fonte consultados

- URM: commit `05ceffdece80f9039328f8ccf5b921b0574bc982`; revisão documental `URM_REVERSO/00_README/REVISAO_DOCUMENTAL_URM_2026-10-28.md`; docs 34–42, 52–53 e manual interno de Choices/replay.
- Ren’Py 6.99.4: `renpy-6.99.4-sdk/renpy/ast.py`, `renpy/execution.py`, `renpy/python.py`, `renpy/loadsave.py`.
- Ren’Py 8.5.3: `renpy-8.5.3-sdk/renpy/ast.py`, `renpy/execution.py`, `renpy/rollback.py`.
- Ren’Py 7.4.11: análise e evidência conforme documentado no snapshot URM acima.
- Timeline beta: commit `fb754300a85adfec458a0519f92198856b0f12b8`; `timeline_runtime.rpy`, `backend/tl_state.rpy`, `backend/tl_route_logic.rpy`.

## O que esta etapa não fez

Nenhum arquivo de implementação do Timeline foi alterado. Nenhum arquivo do Wells estável, do URM canônico ou dos SDKs do laboratório foi alterado. Esta pasta contém a cópia de referência e a análise comparativa para orientar a próxima etapa.
