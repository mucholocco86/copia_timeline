# Loader x52MF2 — comportamento confirmado

`framework/bootstrap.rpy` declara módulos e implementa o carregamento. `.x52rpy` e `.x52` são carregados explicitamente. Quando um `.x52rpy` não está disponível como fonte carregável, o loader pode mapear o nome lógico para o `.rpyc` correspondente, por exemplo `modules/01utils.x52rpy` -> `modules/01utils.rpyc`.

O `load()` procura `bootstrap.rpyc`, registra `archivePath` e trata um `.update` pendente. `API.rpy` baixa atualizações para `.tmp`, extrai o primeiro `.rpa` para `.update`, e `applyUpdate` substitui o archive e chama `renpy.reload_script()`.

Questões abertas: trigger da aplicação, estado seguro, UI e reconciliação entre reload, contexto, AST e estado.


# Loader x52MF2

Documentos deste eixo:

- `01_LOADER_X52MF2_CARGA_E_DEPENDENCIAS.md` — catálogo de módulos, expansão de dependências, seleção de `.x52t`, substituição de placeholders, `renpy.load_string()`, fallback `.rpyc` e ciclo de atualização.

Fonte principal: `../01_MATERIAL_URM/1_URM_ORIGINAL/framework/bootstrap.rpy`. A versão convertida foi conferida e tem o mesmo SHA GitHub.

Próximas questões:
1. encontrar o produtor de `.x52t` / `.x52rpyt`, se existir no material disponível;
2. correlacionar a expansão de `availableModules` com a lista de arquivos efetivamente carregados;
3. localizar quem chama `pendingUpdate` e em que estado de jogo;
4. investigar o ajuste de `renpy.game.script.digest` quando o archive não é localizado.

A existência de um loader URM não significa que seus sufixos sejam recursos nativos do Ren'Py. Um futuro loader WF deve ter especificação e testes próprios.


## Limite atual da validação runtime

A fixture de notificações roda no jogo de teste do SDK e não carrega os módulos dinâmicos do URM. O `classes/main.rpy` convertido solicita 18 arquivos `.rpy.x52` em `0x52-URM/` (17 telas em `screens/` e 1 arquivo de estilos), além da expansão do catálogo declarada em `framework/bootstrap.rpy`. Os caminhos presumidos para `01utils.x52rpy`, `URM_styles.rpy.x52` e `screens/watchpanel.rpy.x52` sob a árvore publicada de material original retornaram 404; isso não prova que não exista uma cópia em outro local. Por segurança metodológica, nenhum `.rpy` convertido será renomeado para simular esses assets. Os limites e SHAs consultados estão registrados no [documento 31 de notificações e rollback](../04_CHOICES/31_NOTIFICACOES_E_ROLLBACK_CICLO_DE_VIDA.md#limite-atual-para-integração-runtime-do-urm-integral--inspeção-do-loader).
