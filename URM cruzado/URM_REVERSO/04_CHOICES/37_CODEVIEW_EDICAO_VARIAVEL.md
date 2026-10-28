# 37 — Da CodeView de Choice à edição de variável

**Data:** 2026-10-23  
**Escopo:** traçar estaticamente, nas fontes originais preservadas do URM, o caminho entre o código/condição de uma alternativa, o hyperlink de variável e a tela de edição.  
**Status:** circuito de fonte confirmado e fluxo de tela/edição/rollback observado em runtime integrado; o clique visual automatizado no hyperlink permanece pendente. Ver [documento 38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md).

## Circuito de navegação

### 1. Choice abre o CodeView

Em `screens/choices.rpy.x52`, a coluna Code oferece o ícone de Show e o atalho `Alt+S` quando uma alternativa está selecionada. Ambos usam `choice.OpenCodeView` (linha 61–64).

Na classe `URMChoice`, `OpenCodeView` cria uma ação que chama:

```python
renpy.show_screen('URM_CodeView',
    code=self.choice.code,
    title='Choice code',
    ...)
renpy.restart_interaction()
```

O campo `choice.code` é produzido por `CodeView.nodesToCode` a partir dos nós no bloco AST. A tela afirma que o código exibido é gerado pelo URM e pode não reproduzir a escrita original do desenvolvedor.

### 2. CodeView converte alguns identificadores em hyperlinks

A inicialização de `CodeViewClass` registra `handleVarClicked` em `renpy.config.hyperlink_handlers['URMVarDialog']`.

Durante `colorize`, a etapa `interactiveVariables` procura tokens coloridos pelo padrão `([w.]+)` e os envolve como `{a=URMVarDialog:<nome>}...{/a}`. A tela `URM_CodeView` mostra o resultado em um `text colorized`, portanto a origem do clique é o identificador renderizado, não um objeto AST de variável ligado à atribuição original.

Ao receber o hyperlink, `handleVarClicked(varName)` chama:

```python
renpy.show_screen('URM_modify_value', Var(varName), allowRemember=True)
renpy.restart_interaction()
```

As condições também passam pela mesma tela CodeView via `choice.OpenConditionView`; por padrão, `colorize` mantém `interactiveVariables=True`. Isso oferece uma rota de inspeção/edição de variáveis citadas em condições, quando elas correspondem ao padrão de token reconhecido.

### 3. A tela de edição escreve no store

`URM_modify_value` inicializa `newValue` com `var.value` e um objeto `Input`. A ação Enter e o botão Change constroem `SetVarValue(var, ..., newValue=...)`.

`SetVarValue.__call__` invoca `Var.setValue`; se retornar sucesso, executa o callback `Hide('URM_modify_value')`. Para os tipos string, boolean, int e float, `Var.setValue` converte/valida o texto, então usa `exec` para atribuir em `renpy.store.<nome>`. Se a variável estiver congelada, descongela antes da escrita e congela novamente no bloco `finally`.

O objeto `Var` considera editável uma variável resolvida contra o store global (seu `_storeDict` está vazio/ausente). A visualização de atributos/elementos pode usar outros nomes e caminhos; não se deve generalizar que todo valor aninhado aceita edição com as mesmas regras.

## O que este circuito demonstra

- **CONFIRMADO NA FONTE URM ORIGINAL:** a tela Choices pode abrir CodeView de código gerado e de condição.
- **CONFIRMADO NA FONTE URM ORIGINAL:** identificadores que o colorizador reconhece viram hyperlinks `URMVarDialog`.
- **CONFIRMADO NA FONTE URM ORIGINAL:** o hyperlink cria `Var(varName)` e abre `URM_modify_value`.
- **CONFIRMADO NA FONTE URM ORIGINAL:** o editor chama `SetVarValue` e, por fim, `Var.setValue`, que escreve no store.
- **OBSERVADO EM RUNTIME INTEGRADO:** a tela Choices original abre e seleciona uma alternativa em fixed rollback, documento [36](36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md).
- **OBSERVADO EM RUNTIME INTEGRADO:** o CodeView e a tela original de edição foram abertos; a variável foi alterada 1→7 e lida pelo bloco da rota; após uma sequência de rollback o valor retornou a 1. O handler foi chamado diretamente pelo test runner, sem clique visual do hyperlink. Detalhes e limites no [documento 38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md).
- **PENDENTE:** automatizar o clique visual do hyperlink e testar save/load.

## Limites que afetam a interpretação

1. A lista de identificadores reconhecidos é baseada em regex após o colorizador. Não equivale a uma análise semântica de dependências nem garante que todo nome clicável corresponda a uma variável editável.
2. O texto do CodeView vem da conversão de nós AST pelo URM; comentários, atributos dinâmicos, subscritos, expressões e construções não cobertas por `nodesToCode` podem ficar diferentes do script executável.
3. A escrita em `Var.setValue` é distinta do mecanismo monitorado de `SetField`. O monitor também usa callback de execução de nós Python e `get_changes`; a fonte consultada ainda não demonstra exatamente quando uma edição disparada por ação de screen passa por esse callback.
4. Rollback nativo pode registrar alterações de store independentemente de o URM emitir uma notificação de monitoramento. Não concluir, sem runtime, em qual checkpoint uma alteração feita pela tela passa a ser revertível.
5. Não há evidência aqui de que editar uma condição ou valor altere o AST do jogo. A fonte examinada aponta para edição de dados do store, enquanto Choice/AST permanece separado.

## Fontes

| Fonte original no repositório | Símbolos / linhas | Blob SHA |
|---|---|---|
| `classes/choices.rpy` | `URMChoice.code`, `OpenCodeView`, `OpenConditionView` (aprox. 43–94) | `48fc35f96119189e50f038981795115b3df7b770` |
| `classes/codeview.rpy` | registro de hyperlink, `handleVarClicked`, `colorize`, `interactiveVariables` (aprox. 5–165) | `508783b02b319f3a34c16730c82ef1de1e9fbb45` |
| `screens/choices.rpy.x52` | atalho/botão Show code e seleção (61–84) | `a78de7e46a5b6230b4871628bfa62708233a07ce` |
| `screens/codeview.rpy.x52` | `URM_CodeView`, renderização de `colorized` (91–104) | `1a6df61ce45842de6e88212116f84333a1314479` |
| `screens/vars.rpy.x52` | `URM_modify_value`, input, Enter, Change (181–254) | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |
| `classes/vars.rpy` | `Var.setValue`, `SetVarValue`, monitor (aprox. 232–269, 421–439, 492–577) | `57482937e14f215dac0ecb22a62da8ad160cba58` |

## Próximos probes de runtime

A sequência integrada de edição e rollback já foi executada; ver [documento 38](38_EDICAO_VARIAVEL_URM_ROLLBACK_RUNTIME.md). Restam:

1. Automatizar ou observar manualmente o clique no token hyperlink renderizado, pois o runner atual chamou o handler diretamente.
2. Instrumentar cada retorno de `RollbackLog.rollback()` para localizar em qual PAGEUP o estado da edição é restaurado.
3. Testar save/load em casos separados e comparar com o estado da sessão.
4. Comparar a callback e as notificações do StoreMonitor com variável comum, monitorada e congelada.

A fixture deve manter observabilidade por logs e asserts; não deve alterar o pacote original do URM nem os diretórios Wells/SDK.
