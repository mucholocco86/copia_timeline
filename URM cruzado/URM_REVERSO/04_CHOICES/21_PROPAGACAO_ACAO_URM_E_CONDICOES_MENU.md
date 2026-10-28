# 21 — Propagação da ação do URM e condições do Menu

**Data:** 2026-10-16  
**Escopo:** seguir o retorno da ação Select da tela URM através da interação Ren'Py 7.4.11 até o índice usado por `ast.Menu.execute`, com atenção a alternativas cuja condição é falsa.  
**Estado:** cadeia de retorno confirmada por leitura estática do SDK e da fonte convertida do URM; seleção efetiva de alternativa invisível permanece pendente de runtime.  
**Proteções:** não foram alterados Wells, SDK ou fontes originais do URM.

## Fontes e evidências

Repositório `mucholocco86/laborat-rio_renpy`, branch `main`, consultado em 2026-10-16.

| Fonte | Blob SHA | Símbolos/intervalos relevantes |
|---|---|---|
| URM convertido: `classes/choices.rpy` | `48fc35f96119189e50f038981795115b3df7b770` | `URMChoice.Action`, linhas 87–93 |
| URM convertido: `screens/choices.rpy` | `a78de7e46a5b6230b4871628bfa62708233a07ce` | ação Select e atalhos, linhas 79–84 |
| SDK: `renpy/display/behavior.py` | `bd71ca989695444a7bf1317c878137a93318614a` | `run(action)`, aproximadamente 303–328; retorno do evento de botão, aproximadamente 914–925 |
| SDK: `renpy/ui.py` | `914a0c4702b7af391e014702a16ccc333e7573de` | `ChoiceActionBase`, `ChoiceReturn.__call__`, linhas 680–759 |
| SDK: `renpy/exports.py` | `781b35b31522dafc6a24e7c3212d206c7bd6dfa5` | `menu`, linhas 966–1055; `display_menu`, linhas 1127–1319 |
| SDK: `renpy/ast.py` | `d81ffc13f28f0b7442ba6905f1745ee838f7b185` | `Menu.execute`, linhas 1639–1693 |

## Cadeia confirmada no código

1. A ação Select da tela URM é uma lista: oculta as telas do URM e, por último, executa `choice.Action`. Os atalhos de teclado reutilizam a mesma ação.
2. `URMChoice.Action` atribui `False` a `renpy.game.log.rollback_is_fixed` e chama `renpy.ui.ChoiceReturn(label, índice_original)()`.
3. `ChoiceReturn.__call__` devolve seu `value`; neste caso, o índice estrutural original da alternativa.
4. `renpy.display.behavior.run` executa os elementos de uma lista em ordem e conserva o último resultado não-None. O evento do botão propaga esse resultado quando ele não é None. Assim, o índice não é apenas calculado: o caminho de ação da tela o devolve à interação.
5. No fluxo nativo, `display_menu` recebe o resultado de `renpy.ui.interact`, chama `checkpoint(rv)` e retorna `rv`. `renpy.exports.menu` devolve esse valor ao chamador.
6. `Menu.execute` trata qualquer resultado não-None como índice e define o próximo nó com `self.items[choice][2][0]`. Nesse trecho não reavalia a condição da alternativa escolhida.

## Condições e alternativa invisível

**Confirmado no SDK 7.4.11:** antes da interação normal, `renpy.exports.menu` avalia a condição. Conforme `config.menu_actions` e `config.menu_include_disabled`, a opção falsa é filtrada ou fica representada por uma ação cuja sensibilidade corresponde à condição.

**Confirmado na fonte convertida do URM:** a tela Choices lista as entradas estruturais recuperadas por `currentChoices`; o botão Select declara `sensitive=True` e sua construção não consulta `choice.isVisible`.

**Inferência estática, ainda sem runtime:** se a ação Select do URM ocorrer dentro da mesma interação que aguarda o resultado do menu e devolver o índice válido de uma alternativa com bloco e condição falsa, os trechos examinados não mostram uma validação posterior que rejeite esse índice antes de `Menu.execute` acessar o bloco. Isso é compatível com a possibilidade de o URM selecionar alternativa que o menu nativo filtraria ou desabilitaria.

A inferência depende da integração efetiva entre a tela modal do URM e a interação ativa do menu. A leitura dos trechos prova a propagação de resultados de ações e a falta de revalidação no trecho de `Menu.execute`; ela não substitui um teste da tela URM em runtime.

## Relação com fixed rollback

`rollback_is_fixed=False` altera a flag consultada por `renpy.exports.in_fixed_rollback()`. Essa flag participa de `ChoiceActionBase.get_sensitive()` e do comportamento de escolha durante fixed rollback. A atribuição não apaga registros do `RollbackLog`, não cria checkpoint e não determina por si só qual estado será restaurado.

O checkpoint que aparece no fluxo de menu é chamado em `display_menu` depois que a interação retorna. Portanto, ele pertence à conclusão da interação de escolha. Não se deve concluir que esse checkpoint marca ou persiste uma edição de variável feita anteriormente por outra ação de tela.

## Classificação

| Afirmação | Classificação |
|---|---|
| `behavior.run` propaga o último retorno não-None da lista de ações | **CONFIRMADO NO SDK 7.4.11** |
| O evento do botão propaga um retorno não-None para a interação | **CONFIRMADO NO SDK 7.4.11** |
| `URMChoice.Action` devolve o índice original através de `ChoiceReturn` | **CONFIRMADO NA FONTE URM CONVERTIDA** e **CONFIRMADO NO SDK 7.4.11** |
| A condição é avaliada antes do menu nativo e pode filtrar/desabilitar a entrada | **CONFIRMADO NO SDK 7.4.11** |
| `Menu.execute` usa o índice recebido sem reavaliar a condição | **CONFIRMADO NO SDK 7.4.11** |
| O URM consegue selecionar uma opção invisível em execução em qualquer contexto | **PENDENTE DE RUNTIME** |
| `rollback_is_fixed=False` remove checkpoints ou apaga histórico de rollback | **CONTRADITO** pela distinção entre flag de fixed rollback e operações do RollbackLog |

## Próximo teste isolado

Em uma fixture descartável no Ren'Py 7.4.11, sem alterar Wells, SDK ou fonte original URM:

1. Criar menu com alternativas indexadas, incluindo uma com condição falsa e bloco identificável.
2. Executar primeiro com `menu_actions` e `menu_include_disabled` nos valores padrão do fixture; registrar o que a tela nativa exibe.
3. Abrir a tela Choices do URM durante a interação e selecionar a alternativa falsa.
4. Registrar o valor recebido pelo menu, o nó AST executado e o checkpoint resultante.
5. Repetir com textos duplicados e com filtro de texto, para separar identidade estrutural de rótulo.
6. Repetir em fixed rollback, comparando a ação com e sem a atribuição URM a `rollback_is_fixed`.

Até esse teste, a seleção de alternativa invisível permanece hipótese de comportamento ponta a ponta, não resultado observado.

## Atualização runtime posterior — 2026-10-28

A pendência indicada acima para alternativa de condição falsa foi resolvida em percursos limitados com o URM original: o doc [41](41_CHOICE_CONDICAO_FALSA_EXECUTADA_PELO_URM.md) observou Choice C com condição literal `False` ser devolvida por ChoiceReturn e seu bloco executar; o doc [42](42_ROLLBACK_APOS_CHOICE_CONDICAO_FALSA.md) observou rollback posterior e reabertura para reescolha.

A conclusão não é “condições sempre ignoradas”. Trata-se da ação direta da tela do URM no contexto/fixture descrito. As variantes de configuração não foram todas cobertas.
