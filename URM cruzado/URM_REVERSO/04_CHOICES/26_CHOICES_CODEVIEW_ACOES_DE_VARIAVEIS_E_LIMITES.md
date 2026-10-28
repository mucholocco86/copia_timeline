# 26 — Choices, CodeView e ações de variáveis: fronteiras da interface

**Data:** 2026-10-19  
**Escopo:** rastrear quais operações de variáveis são alcançáveis diretamente da tela de Choices e do CodeView, e separar edição de estado de metadados do URM.  
**Fontes URM:** versão convertida no laboratório; não equivale necessariamente em todos os detalhes ao pacote original.  
**SDK:** Ren'Py 7.4.11 para a semântica de rollback já verificada nos documentos 15, 22 e 25.  
**Proteções:** nenhum arquivo do Wells, SDK ou fonte original do URM foi alterado.

## Resultado em uma frase

A tela de Choices oferece inspeção da condição/código, substituição do texto exibido e seleção estrutural. A partir do CodeView, um identificador de variável reconhecido pode abrir a edição do valor corrente e os controles **Remember/Forget** e **Watch/Unwatch**. Essa tela contextual não apresenta os controles **Freeze/Monitor/Ignore**; eles aparecem na tabela completa de variáveis.

## Caminho confirmado na fonte convertida

1. `URM_choices` monta linhas a partir de `Choices.currentChoices`.
2. O comando de condição abre `URM_CodeView` com `choice.condition`; o comando de código abre a mesma tela com `choice.code`.
3. `choice.code` é texto reconstruído de parte do bloco AST por `CodeView.nodesToCode`; não é execução do bloco.
4. `CodeView.colorize` identifica tokens com padrões e adiciona links de variável aos tokens reconhecidos.
5. O handler `URMVarDialog` cria `Var(varName)` e abre `URM_modify_value(..., allowRemember=True)`.
6. A tela de edição permite alterar o valor escalar corrente via `SetVarValue → Var.setValue`; também oferece excluir a variável. Com `allowRemember=True`, oferece Remember/Forget e Watch/Unwatch.
7. A tabela geral de variáveis expõe separadamente os controles de Watch, Freeze, Monitor e Ignore. Esses controles alteram os metadados do arquivo URM.

Esse caminho de interface não mantém um vínculo semântico entre a variável clicada e a Choice além de ter vindo do texto de código projetado. O handler recebe somente o nome reconhecido pelo CodeView e abre uma `Var` para esse nome no store ativo. A tela de edição não recebe índice/objeto da Choice.

## Matriz das ações acessíveis

| Entrada / ação | O que a fonte mostra | Tipo de efeito |
|---|---|---|
| Ver condição da Choice | Exibe a condição em CodeView | Inspeção/apresentação |
| Ver código da Choice | Reconstrói e exibe parte dos nós do bloco | Inspeção/apresentação |
| Clicar variável reconhecida | Abre `URM_modify_value` para `Var(nome)` | Navegação para ferramenta de variável |
| Change no diálogo | `SetVarValue` chama `Var.setValue` e escreve no store ativo | Mutação do estado de jogo em execução |
| Remember/Forget | Atualiza registro de `vars` no arquivo URM | Metadado próprio do URM |
| Watch/Unwatch | Atualiza registro `watched` no arquivo URM | Lista/rótulo de observação do painel |
| Freeze/Unfreeze | Disponível na tabela geral de variáveis; muda flag `frozen` | Metadado URM que o StoreMonitor consulta |
| Monitor/Unmonitor | Disponível na tabela geral; muda flag `monitor` | Metadado URM que o StoreMonitor consulta |
| Ignore/Unignore | Disponível na tabela geral; muda flag `ignored` | Metadado URM usado por PathDetection/CodeView |
| Trocar texto da Choice | Abre `URM_add_textrepl` para a representação textual | Regra de filtro de texto, não alteração do AST |

## Edição de variável congelada e monitorada

**Confirmado na fonte URM convertida:** antes de escrever, `Var.setValue` consulta se o nome raiz está congelado. Se estiver, chama `VarsStore.unfreeze`; faz a atribuição ou o append; e, no bloco `finally`, chama `VarsStore.freeze` novamente. Isso indica que a própria edição manual tenta permitir a escrita apesar do estado congelado e restaurar a flag depois. Não prova que qualquer rota externa de escrita seja bloqueada, nem que a ação sempre consiga alterar o valor.

A edição por CodeView não desativa explicitamente a flag `monitor`. A fonte do `StoreMonitor` usa `isMonitored` ao processar alterações. Porém, a ação de tela de edição não chama um nó `ast.Python` e não percorre o helper `SetVariable` no circuito estático examinado. A observação pode ocorrer em callback posterior, conforme o ciclo do jogo; não se deve descrever isso como notificação síncrona no clique.

## Relação com rollback: evidência e limite

- **CONFIRMADO NA FONTE URM CONVERTIDA:** a tela contextual escreve no store do jogo via `Var.setValue`; metadados Remember/Watch são stores separados do arquivo URM.
- **OBSERVADO EM RUNTIME — fixture reduzida:** a ação reduzida de edição por screen alterou um escalar raiz de 10 para 99; com rollback habilitado, o rollback restaurou 99 para 10 (run [39098551052](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39098551052), descrito no documento 25).
- **CONFIRMADO NO SDK 7.4.11:** o histórico nativo restaura deltas de store e estado de execução nos cenários documentados nos documentos 15, 19, 22 e 25.
- **PENDENTE:** executar a integração com as telas e classes completas do URM convertido, incluindo congelamento, monitoramento, escolha do jogo e rollback acionado em sessão.
- **PENDENTE:** estabelecer comportamento para variáveis que sejam filhos de objetos/containers externos e para todas as condições temporais de edição.

A fixture de rollback prova o contrato do caso reduzido testado, não a integração integral do URM nem todos os tipos de variável.

## Limites de identificação de variáveis no CodeView

CodeView usa regex sobre o texto gerado. Um token não reconhecido ou trecho omitido não implica ausência de dependência real no AST. O link também não resolve escopo/identidade no AST: ele recebe um nome e resolve `Var(name)` no store principal. Portanto, a ferramenta oferece navegação prática, não uma análise completa de dependências entre Choice, símbolos e efeitos.

## Fontes consultadas

| Arquivo convertido | Símbolos / linhas aproximadas | Blob SHA |
|---|---|---|
| `classes/choices.rpy` | `URMChoice.code`, `Action`, `OpenCodeView` | `48fc35f96119189e50f038981795115b3df7b770` |
| `screens/choices.rpy` | botões de condição, código, substituição e seleção | `a78de7e46a5b6230b4871628bfa62708233a07ce` |
| `classes/codeview.rpy` | hyperlinks, `handleVarClicked`, `nodesToCode` | `508783b02b319f3a34c16730c82ef1de1e9fbb45` |
| `screens/codeview.rpy` | exibição de texto colorizado em `URM_CodeView` | `1a6df61ce45842de6e88212116f84333a1314479` |
| `classes/vars.rpy` | `Var.setValue`, `SetVarValue`, `VarsStore`, `StoreMonitor` | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| `screens/vars.rpy` | `URM_modify_value` e tabela geral com controles de metadados | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |
| Runtime reduzido | callback posterior e rollback de escalar raiz | run `39098551052`; análise no documento 25 |

## Continuação recomendada

O próximo teste controlado deve combinar os dois lados do circuito sem alterar as fontes protegidas: fixture isolada que reproduza a entrada CodeView → variável → edição de screen, inicie com a flag frozen e depois com monitor, avance por uma Choice, faça rollback e registre separadamente o valor do jogo, as flags URM e as notificações. Até esse teste, as conclusões de integração permanecem pendentes.
