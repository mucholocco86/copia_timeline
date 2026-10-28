# 40 — Menu, filtro de condições e trilha de force_checkpoint

**Data:** 2026-10-23. **Escopo:** cruzamento estático entre URM convertido/original e Ren'Py SDK 7.4.11, com repetição runtime da edição de variável pelo URM. **Fixture:** jogo descartável the_question, pacote original URM copiado sem alteração. Nenhum arquivo de wells/, wells_beta/, SDK ou fonte original do URM foi modificado.

## Resultado principal

A investigação fecha mais uma parte do circuito, sem confundir três coisas:

1. **O Menu AST atribui à alternativa o índice estrutural original.**
2. **O menu nativo avalia as condições antes de apresentar seus itens.**
3. **O URM emite um ChoiceReturn diretamente pela sua interface; a seleção de uma Choice invisível ainda exige teste isolado.**

A edição feita pelo editor do URM continua participando do histórico reversível nativo no cenário testado. A repetição corrigida confirmou que o valor 1→7 permanece após avançar e retorna a 1 no terceiro PAGEUP. O novo trace de RollbackLog.begin não rastreia cada escrita de Context.force_checkpoint; portanto, a autoria do valor observado dentro de Var.setValue continua sem prova runtime direta.

## 1. Índice e execução do bloco

**CONFIRMADO NO SDK 7.4.11.** Em renpy/ast.py, Menu.execute() percorre self.items com enumerate. Para uma alternativa com bloco, acrescenta (label, condition, i) às escolhas. Depois de renpy.exports.menu(...), se o retorno não é None, busca self.items[choice] e agenda o primeiro nó do bloco por next_node(...).

Assim, o valor devolvido pela interação tem de identificar a entrada estrutural original, mesmo que uma tela apresente os itens em outro formato. A tela visual e seu índice local não substituem esse índice AST.

## 2. Condições no menu nativo

**CONFIRMADO NO SDK 7.4.11.** Em renpy/exports.py, a função menu() avalia cada condição usando renpy.python.py_eval(condition). Com menu_actions desligado, inclui somente as entradas cuja condição é verdadeira. Com menu_actions ligado, a fonte também pode descartar condições falsas se menu_include_disabled estiver desligado; quando itens desabilitados são incluídos, a condição é passada como sensitive do ChoiceReturn nativo.

A função display_menu() cria as ações da tela para os itens filtrados e, após ui.interact(), chama checkpoint(rv) e retorna o valor. checkpoint() recebe hard=True por padrão, mas só encaminha hard=True quando renpy.store._rollback também está verdadeiro; a existência/força efetiva do checkpoint depende ainda do estado do log. Menu.execute() usa o valor para entrar no bloco correspondente.

**PENDENTE:** a tela do URM mostra alternativas marcadas como invisíveis e sua ação chama ChoiceReturn com o índice original. A leitura da tela demonstra que o botão de seleção do URM não bloqueia pelo próprio predicado isVisible; ainda não foi isolado em runtime se o caminho direto do URM efetivamente contorna o filtro/condição do menu nativo em todas as configurações. Não generalizar a partir do teste com Choice visível.

## 3. Semântica do ChoiceReturn usado pelo URM

**CONFIRMADO NO SDK 7.4.11.** renpy.ui.ChoiceReturn.__call__() registra a opção em chosen somente se esse mapa foi fornecido e retorna self.value. O URM constrói/aciona a ação com o índice original como valor; a continuação do bloco é resolvida depois pelo Menu.execute().

Isso confirma o circuito estrutural já descrito nos docs 14–15, sem afirmar que a ação execute o bloco AST. A avaliação normal de condições pertence ao caminho de renpy.exports.menu(); uma invocação programática de ChoiceReturn não executa essa avaliação por conta própria.

## 4. Trilha estática de force_checkpoint

### URM

**CONFIRMADO NA FONTE URM CONVERTIDA.** StoreMonitorClass._m1_vars__pythonCallback (classes/vars.rpy, aproximadamente linhas 540–563) atribui renpy.game.context().force_checkpoint = True e em seguida chama renpy.store.__dict__.get_changes(False). A atribuição não está dentro de Var.setValue; portanto, a linha de log de Var.setValue que registra force_checkpoint=True não prova que o setter pediu o checkpoint.

### SDK

**CONFIRMADO NO SDK 7.4.11.** Context.run() examina a flag antes de executar o próximo nó. Se self.force_checkpoint estiver verdadeira, a política escolhe atualização forçada de rollback e chama RollbackLog.begin(force=True). Depois da chamada, transfere o pedido a renpy.game.log.force_checkpoint e limpa Context.force_checkpoint.

**CONFIRMADO NO SDK 7.4.11.** RollbackLog.begin() decide se começa um registro; quando começa e já existe current, chama complete(True). RollbackLog.complete() primeiro consome self.force_checkpoint chamando checkpoint(hard=False) e limpando a flag, depois percorre os stores e grava os deltas devolvidos por StoreDict.get_changes(begin) no registro corrente.

**CONFIRMADO NO SDK 7.4.11.** StoreDict.get_changes(True) devolve os valores anteriores ao ciclo e atualiza sua base de comparação. Rollback.rollback() seleciona registros, chama rb.rollback() e reaplica os dados reversíveis dos stores/contextos.

A distinção importante é que Context.force_checkpoint provoca uma passagem forçada pela abertura/ciclo de rollback; o flag RollbackLog.force_checkpoint leva complete() a solicitar um checkpoint com hard=False. Isso não é o mesmo que o checkpoint do menu, que chama checkpoint(rv) com hard=True por padrão (a efetividade depende de renpy.store._rollback), e nenhum desses flags, isoladamente, explica a reversão de 1→7.

## 5. Runtime da edição integrada

O workflow [39912696436](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912696436) terminou **SUCCESS** após remover a interceptação recursiva de Context.__setattr__. O cenário manteve o loader e telas originais do URM, editou a variável monitorada pelo CodeView e passou as asserções.

| Evento | Valor | Rota | Evidência |
|---|---:|---:|---|
| Editor do URM | 7 | ainda não avaliada | URM_EDIT_VAR_SET registra 1→7 |
| Após avançar | 7 | 7 | URM_EDIT_RUNTIME_RESULT 7 7 |
| PAGEUP 1 | 7 | 7 | histórico recua, estado não muda |
| PAGEUP 2 | 7 | 7 | fixed rollback ativo, valor não muda |
| PAGEUP 3 | 1 | None | RollbackLog.rollback() reaplica valor e estado anteriores |
| PAGEUP 4 | 1 | None | sem estado adicional restaurado |

Isso reproduz o resultado já confirmado nos runs 39907164916 e 39910519723; não amplia o conjunto de cenários funcionais. O logger de begin observou a relação temporal entre context_force e log_force, mas não interceptou cada atribuição da flag.

## 6. Instrumentação que falhou e limites

O workflow [39912551615](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39912551615) falhou com recursão depois que a fixture tentou substituir Context.__setattr__. Essa execução é **inválida como evidência de comportamento do Ren'Py/URM**. A interceptação foi removida do fixture no commit a20f2dc5d9c8763e5895dae2c39cb78dec2c9abe; o teste seguinte passou. A falha não deve ser usada para inferir defeito no SDK ou no URM.

## Classificação

- **CONFIRMADO NO SDK 7.4.11:** Menu.execute conserva i e usa o retorno para selecionar o bloco AST.
- **CONFIRMADO NO SDK 7.4.11:** renpy.exports.menu avalia condições e display_menu retorna o valor selecionado após checkpoint(rv).
- **CONFIRMADO NO SDK 7.4.11:** ChoiceReturn.__call__ devolve value; não executa o bloco AST.
- **CONFIRMADO NA FONTE URM:** o callback define Context.force_checkpoint; Var.setValue não é a origem demonstrada dessa atribuição.
- **CONFIRMADO NO SDK 7.4.11:** o pedido é transferido por Context.run(); RollbackLog.complete() trata o flag do log por checkpoint soft e captura deltas.
- **OBSERVADO EM RUNTIME:** a edição original do URM continuou reversível no cenário fixado, com retorno a 1 no terceiro PAGEUP.
- **PENDENTE:** rastrear por método seguro a escrita/limpeza de cada flag no runtime; testar Choice com condição falsa acionada pela tela do URM; save/load; variações de menu_actions, menu_include_disabled e rollback.
- **INVÁLIDO COMO EVIDÊNCIA:** run 39912551615, por recursão introduzida pela instrumentação da fixture.

## Fontes

Prefixo SDK: renpy-7.4.11-sdk/.

| Arquivo | Símbolos / linhas aproximadas | Blob SHA |
|---|---|---|
| renpy/ast.py | Menu.__new__, Menu.execute, ~1580–1690 | d81ffc13f28f0b7442ba6905f1745ee838f7b185 |
| renpy/exports.py | menu, display_menu, checkpoint, ~1000–1290 | 781b35b31522dafc6a24e7c3212d206c7bd6dfa5 |
| renpy/ui.py | ChoiceReturn.__call__, ~718–749 | 914a0c4702b7af391e014702a16ccc333e7573de |
| renpy/execution.py | Context.run, ~500–565 | 547f73b26dad0fe08fda6333e5f4b60c97cf8772 |
| renpy/python.py | StoreDict.get_changes, RollbackLog.begin/complete/checkpoint/rollback, ~150–210, 1630–2020 | c5eb2819a3e4ee096dbf01130d70a77f9b623484 |
| URM convertido classes/vars.rpy | _m1_vars__pythonCallback, ~540–563 | 57482937e14f215dac0ecb22a62da8ad160cba58 |
| Fixture | tools/fixtures/urm_real_loader_variable_edit_probe.rpy | commit a20f2dc5d9c8763e5895dae2c39cb78dec2c9abe |

## Continuação recomendada

1. Substituir a interceptação de Context.__setattr__ por um trace localizado no callback URM e no ponto de transferência em Context.run(), sem alterar o SDK original.
2. Criar um caso isolado de Choice com condição falsa: comparar a seleção pelo menu nativo e pelo botão da tela do URM.
3. Depois, executar save/load antes e depois da edição para separar reversibilidade de rollback e persistência nativa.
