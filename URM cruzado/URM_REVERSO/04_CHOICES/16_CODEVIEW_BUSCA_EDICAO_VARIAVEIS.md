# 16 — CodeView, busca e edição de variáveis ligadas a Choices

**Data:** 2026-10-16  
**Escopo:** rastrear a cadeia da Choice lida pelo URM até CodeView, pesquisa de variáveis, tela de edição e escrita no store ativo.  
**Estado:** 🟢 cadeia confirmada por inspeção estática da fonte convertida do URM; 🔵 mecanismo do store e rollback nativo confirmado no SDK conforme documentos 15 e 02; 🟠 limites de cobertura e efeitos de runtime permanecem pendentes.  
**Proteções:** nenhuma fonte original do URM, SDK, wells/ ou wells_beta/ foi modificada.

## 1. Fontes

Repositório mucholocco86/laborat-rio_renpy, branch main, árvore consultada em 2026-10-16, tree SHA 63362742ecdbc7d9ff9c04ad08e924f22c309a76.

| Fonte convertida | Blob SHA Git | Símbolos/intervalos |
|---|---|---|
| classes/choices.rpy | 48fc35f96119189e50f038981795115b3df7b770 | URMChoice.code 57–66 |
| classes/codeview.rpy | 508783b02b319f3a34c16730c82ef1de1e9fbb45 | CodeViewClass 5–228; nodesToCode, colorize, hyperlinks |
| screens/choices.rpy | a78de7e46a5b6230b4871628bfa62708233a07ce | Choice → OpenCodeView, 37–50 |
| screens/codeview.rpy | 1a6df61ce45842de6e88212116f84333a1314479 | URM_CodeView, 101–123 |
| classes/vars.rpy | 57482937e14f215dac0ecb22a62da8ad160cba58 | Var.value/setValue 140–269; SetVarValue 421–435 |
| screens/vars.rpy | 7959b2c0e6249df0edbb9ebe683481d46e4537e1 | URM_modify_value 181–255; URM_remember_var 326–362 |
| classes/search.rpy | 0e62656c1d0caf11bc93588ae66ab549db90d479 | doSearch 39–79; matchVarValue 104–166; matchVarName 168–230 |
| screens/search.rpy | 39de91697419e691f18100ca0c468b9cd699accd | Results and variable actions 1–180 |

Os intervalos são linhas da cópia convertida no laboratório. A conversão é instrumento de inspeção e não garantia de equivalência perfeita com a distribuição original do URM.

## 2. Circuito: Choice → CodeView → variável

1. URMChoice.code passa o bloco da alternativa a CodeView.nodesToCode.
2. nodesToCode converte certos nós AST em texto: fonte de nós Python, condições e blocos If, chamadas, jumps e alguns UserStatement. Pode omitir trechos marcados como ignorados e pode remover código Ren'Py considerado pouco relevante conforme a configuração.
3. A tela de Choices abre URM_CodeView com choice.code.
4. URM_CodeView chama CodeView.colorize e exibe o texto como rich text, com substituição de texto desabilitada.
5. O CodeView adiciona hyperlinks URMVarDialog a tokens que reconheceu e coloriu como variáveis.
6. handleVarClicked recebe o nome, instancia Var(varName), abre URM_modify_value e reinicia a interação.
7. A tela de edição lê var.value. A ação Change/Enter chama SetVarValue, que chama Var.setValue.
8. Var.setValue compõe e executa uma atribuição sobre renpy.store ou chama append em um valor de coleção. Isso altera o store ativo do jogo; não reescreve o arquivo de script.

**Conclusão:** o CodeView é uma representação inspecionável do bloco AST e uma porta de navegação para ferramentas de variável. Não executa aquele bloco AST, e seus hyperlinks não demonstram que o URM encontrou todas as variáveis ou consequências possíveis.

## 3. O que o CodeView consegue tornar clicável

**Confirmado no código convertido:**

- A coloração e a identificação de links são feitas por padrões regex, não por uma resolução semântica de cada expressão no AST.
- interactiveVariables só envolve em hyperlink texto que já está dentro da marcação de cor de variável e cujo token corresponde a [\w\.]+.
- Os padrões de tokens de variável reconhecem identificadores e nomes pontuados em contextos como operadores, argumentos, comparações e return.
- O link abre Var(varName), que por padrão lê o store principal.
- O CodeView pode comentar uma condição If como satisfeita, não satisfeita ou impossível de avaliar. Isso é avaliação da condição para apresentação; não executa o bloco da condição.

**Limite:** indexação de lista/dicionário, expressões complexas, variáveis interpoladas, nomes que o regex não coloriu e texto omitido não são cobertos por uma resolução completa de símbolos. Não tratar a ausência de link como prova de que a expressão não dependa de uma variável.

A própria tela de CodeView explica ao usuário que o código gerado provavelmente não é exatamente o texto escrito pelo desenvolvedor. Esse aviso corresponde aos filtros e reconstrução observados no método nodesToCode.

## 4. A tela de edição modifica valor do jogo ou metadado do URM?

São dois circuitos independentes.

### Editar o valor corrente

- URM_modify_value mostra o valor obtido por Var.value.
- A entrada é configurada com var.isEditable.
- A ação onEnter e o botão Change usam SetVarValue.
- SetVarValue chama Var.setValue.
- Var.setValue escreve no store ativo por meio de uma atribuição ou append.

Esta é uma mutação do estado atual do jogo. Conforme a inspeção do SDK em 15 e 02, uma escrita no StoreDict participante pode ser registrada pelo RollbackLog e incluída no save nativo. O momento e o resultado concreto em runtime continuam pendentes de teste.

### Lembrar, monitorar e observar

As ações Remember/Forget, Watch/Unwatch, Freeze/Unfreeze e Ignore alteram registros do VarsStore/URMFile associados ao arquivo .urm. Esses registros descrevem nomes e preferências das ferramentas do URM. Não são, por si, a gravação do valor corrente da variável.

A tela de variável pode oferecer edição e metadados lado a lado, mas não se deve agrupá-los como uma única persistência.

## 5. Pesquisa também conduz à edição

SearchClass.doSearch começa, conforme o modo, em renpy.store.__dict__ ou renpy.get_all_labels(). Para busca por valor, matchVarValue avalia valores e cria objetos Var para resultados; para busca por nome, matchVarName cria Var para correspondências. A tela de resultados apresenta os valores e permite abrir URM_modify_value, expandir uma estrutura, lembrar uma variável ou adicioná-la ao watchpanel.

A pesquisa, portanto, é outra entrada para o mesmo circuito Var → SetVarValue → store. Ela não é uma fonte separada de mutação.

### Limites estruturais observados

- A busca por valores trata tipos escalares e tem ramos especiais para persistent, dicionários e objetos, conforme flags de configuração.
- A busca por nomes percorre persistent, dicionários e atributos de certos objetos quando as opções correspondentes estão habilitadas.
- Não há ramo explícito de recursão sobre elementos de lista nos métodos examinados; uma lista pode aparecer como variável editável/expansível em outras partes da UI, mas não concluir que Search percorre seus membros por valor/nome.
- A busca recursiva pode usar a coleção de resultados anterior como próxima coleção, em vez de reiniciar no store inteiro.
- Há filtros para variáveis internas, objetos, persistent e tipos não suportados; logo, o conjunto de resultados depende da configuração.

Isto documenta o circuito e seus limites, não a completude da pesquisa do URM.

## 6. Relação com python_callbacks e StoreMonitor

O botão Change chama um objeto de ação SetVarValue a partir da interação de tela; o fluxo examinado não executa um nó ast.Python do script só por causa dessa ação. No SDK 7.4.11, python_callbacks são chamados por ast.Python.execute. Portanto, não há evidência de que essa edição de UI dispare o callback do StoreMonitor.

O hook de atribuição do StoreMonitor é outro caminho: a fonte URM substitui um método interno de atribuição e usa handleVarChange para notificação/congelamento. Separadamente, o StoreDict/RollbackLog do SDK captura mudanças de store para rollback. Esses mecanismos não devem ser tratados como sinônimos.

Esta conclusão é estática, baseada no fluxo da tela/action e no ponto de chamada do SDK. Instrumentação runtime ainda pode revelar efeitos adicionais de integração.

## 7. Classificação

| Afirmação | Classificação |
|---|---|
| A Choice passa código derivado do bloco AST para CodeView | CONFIRMADO NA FONTE URM CONVERTIDA |
| CodeView reconstrói texto parcialmente e aplica regex para colorir/linkar variáveis | CONFIRMADO NA FONTE URM CONVERTIDA |
| Clique em variável abre tela que encaminha edição a SetVarValue/Var.setValue | CONFIRMADO NA FONTE URM CONVERTIDA |
| Var.setValue escreve no store ativo do jogo | CONFIRMADO NA FONTE URM CONVERTIDA |
| A edição desse valor é um registro do arquivo .urm | CONTRADITO: o registro .urm é outro circuito de metadados |
| Toda variável usada pelo bloco é reconhecida e linkada | PENDENTE; regex não é resolução semântica completa |
| A ação de tela dispara python_callbacks | NÃO DEMONSTRADO pelo circuito estático |
| A edição é revertida em um ponto exato do menu ou save | PENDENTE DE RUNTIME |

## 8. Próximas verificações

1. Seguir a ação de edição de valor para dict/list/atributo e comparar com Var.delete, URM_add_item e CreateVar.
2. Rastrear CodeView links para labels e as operações replay/jump separadamente das variáveis.
3. Cruzar Stores Vars/Watched/Labels/Replacements/Snapshots com seus produtores e consumidores.
4. Montar fixture Ren'Py 7.4.11 para registrar atribuições feitas em tela, callback, deltas de store, checkpoint e rollback.
5. Só depois considerar quais mecanismos seriam relevantes a uma futura extensão Wells.

Este documento não recomenda transplante ou implementação. O objetivo é descrever o circuito observado e preservar o que ainda depende de runtime.
