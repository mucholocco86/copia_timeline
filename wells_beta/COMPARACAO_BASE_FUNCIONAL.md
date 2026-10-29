# Comparação de Wells Beta com a base funcional

Data: 29/10/2026  
Base comparada: `wells/` e `wells_beta/` no HEAD `d10299588cc69ae1c1b2fcf41d5eaa4074439721`.

## Resultado antes da cópia

- `wells/`: 134 arquivos.
- `wells_beta/`: 124 arquivos.
- 109 arquivos comuns eram idênticos.
- 15 arquivos comuns tinham conteúdo diferente.
- 10 arquivos existiam em `wells/` e faltavam em `wells_beta/`.
- Não havia arquivos exclusivos de `wells_beta/`.

## Diferença comprovadamente ligada à falha de retorno do Timeline

No Beta, `timeline/backend/tl_state.rpy` define a função `_tl_native_rollback_checkpoints(node)` e também usa `store._tl_native_rollback_checkpoints` para guardar o valor dos checkpoints. A própria função de limpeza e o retorno reatribuem esse mesmo nome a `None` ou a um número. Isso faz o nome global deixar de apontar para a função original. O erro registrado no jogo — “Can't pickle <function _tl_native_rollback_checkpoints ...>: it's not the same object as store._tl_native_rollback_checkpoints” — é compatível diretamente com essa colisão.

O Beta também tenta salvar a recuperação antes do retorno e, em `timeline/timeline_screen.rpy`, prioriza o rollback nativo antes do snapshot. No teste físico, a gravação falhou com o erro acima e o log terminou sem despachar snapshot ou slot. A base funcional não contém esse caminho de rollback nativo: restaura o snapshot da choice, o que corresponde ao teste em que o retorno funcionou.

O Beta também guarda identificadores/âncoras de rollback em `timeline/timeline_runtime.rpy`; esse mecanismo faz parte da estratégia nativa acima. A comparação e o teste apontam a colisão de nomes como causa concreta da falha de gravação/retorno. Não é necessário reutilizar esse caminho para preservar o comportamento funcional.

## Diferença ligada ao traceback do painel

Em `timeline/ui/tl_screens.rpy`, o Beta procura o card de histórico com uma expressão geradora que referencia `_tl_graph_index`. No Ren'Py 7.4.11 testado, essa expressão gerou `NameError: global name '_tl_graph_index' is not defined`. A versão em `wells/` usa um loop explícito no mesmo ponto, evitando a falha. O usuário testou essa correção em vários jogos e confirmou que funcionou.

## Outras diferenças

- `timeline/timeline_tests.rpy` também difere; é o módulo de testes do Timeline.
- `wells_wt_screen.rpy` e seis imagens de barra/pino diferem visualmente.
- Dez arquivos da base funcional estavam ausentes do Beta: quatro fontes, dois ícones de aviso e quatro recursos do Timeline.
- Os demais arquivos comuns que diferiam incluem módulos e imagens acima; os outros 109 arquivos comparados eram idênticos.

O aumento de CPU e RAM observado no Beta não ficou atribuído com segurança a uma diferença específica nesta comparação. Não registrar uma causa sem medição que a confirme.

## Resultado da sincronização

Após este registro, os arquivos de `wells/` serão copiados para os caminhos correspondentes em `wells_beta/`. A base `wells/` permanece intacta. Este documento fica em `wells_beta/` como histórico da comparação; portanto, o conteúdo funcional espelhado será igual, com este registro adicional no diretório Beta.
