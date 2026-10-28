# 33 — Fixed rollback e escolha acionada pelo URM

**Data:** 2026-10-23  
**Escopo:** cruzamento estático entre a ação de Choice do URM convertido e o SDK Ren'Py 7.4.11.  
**Status:** fonte URM e fonte SDK confirmadas; integração ponta a ponta em runtime permanece pendente.

## Pergunta

Por que `URMChoice.Action` define `renpy.game.log.rollback_is_fixed = False` antes de devolver o índice da alternativa por `ChoiceReturn`? Essa atribuição remove a decisão fixada, libera uma nova seleção, ou altera o histórico de rollback?

## Evidências

### Fonte URM convertida

- `URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/choices.rpy`, blob `48fc35f96119189e50f038981795115b3df7b770`, propriedade `URMChoice.Action` (linhas 87–93 no snapshot examinado):
  - define `renpy.game.log.rollback_is_fixed = False`;
  - chama `renpy.ui.ChoiceReturn(choice[0], index)()`;
  - retorna o valor produzido por essa ação.
- `.../screens/choices.rpy`, blob `a78de7e46a5b6230b4871628bfa62708233a07ce`, linhas 79–84:
  - o botão Select executa a ação URM em uma lista de ações;
  - declara `sensitive=True`;
  - não consulta `choice.isVisible` para desabilitar esse botão.

### SDK Ren'Py 7.4.11

- `renpy/config.py`, blob `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`, linha 75: `fix_rollback_without_choice = False` por padrão. O comentário descreve que, quando ativada, menus em fixed rollback não têm opções clicáveis e um clique/roda do mouse avança o roll-forward.
- `renpy/ui.py`, blob `914a0c4702b7af391e014702a16ccc333e7573de`, `ChoiceActionBase.get_sensitive()` (696–703): a sensibilidade nativa depende de `in_fixed_rollback()`, `block_all` e `get_selected()`. `block_all` assume o valor de `config.fix_rollback_without_choice` quando não especificado. Com o padrão `False`, a alternativa já selecionada no roll-forward pode continuar sensível; alternativas diferentes ficam bloqueadas enquanto fixed rollback estiver ativo.
- No mesmo arquivo, `ChoiceReturn.__call__()` (aprox. 758–762) retorna `self.value`; só registra `chosen` se a ação tiver localização e store de escolhas disponível.
- `renpy/exports.py`, blob `781b35b31522dafc6a24e7c3212d206c7bd6dfa5`, `display_menu` (1127 em diante, em especial 1205–1206 e 1296–1300): em fixed rollback, chama `saybehavior()` quando a configuração correspondente está ligada; a interação retorna `rv`, que é então processado pelo fluxo do menu e pelo checkpoint (linha 1476 no caminho de menu examinado).
- `renpy/ast.py`, blob `d81ffc13f28f0b7442ba6905f1745ee838f7b185`, `Menu.execute()` (1639–1698): depois de `renpy.exports.menu(...)`, se o resultado não for `None`, usa `self.items[choice][2][0]` como próximo nó. O valor retornado precisa corresponder ao índice estrutural em `Menu.items`.
- `renpy/exports.py`, `in_fixed_rollback()` (aprox. 245–255): delega a `renpy.game.log.in_fixed_rollback()`.
- `renpy/python.py`, blob `c5eb2819a3e4ee096dbf01130d70a77f9b623484`:
  - `RollbackLog.in_fixed_rollback()` (aprox. 1805–1806) retorna `rollback_is_fixed`;
  - `fix_rollback()` (1911–1913) define `fixed_rollback_boundary` se ainda não estiver em fixed rollback e houver histórico;
  - `rollback()` (aprox. 2064–2067) liga `rollback_is_fixed` quando um registro restaurado alcança a fronteira;
  - `begin()` (1673–1685) encerra o estado fixo ao alcançar a fronteira durante a continuação ou atualiza a fronteira quando termina o dado de replay.

## Circuito e interpretação delimitada

O motor mantém a fronteira (`fixed_rollback_boundary`) separada do indicador consultado pela UI (`rollback_is_fixed`). A ação do URM altera somente o indicador booleano; ela não apaga a fronteira, não altera diretamente os registros do log e não regrava uma decisão no AST.

Na fonte, a ação está desenhada para limpar o estado que faz as ações nativas restringirem alternativas durante fixed rollback e, em seguida, devolver o índice original à interação de menu. O Ren'Py continua responsável por consumir o resultado e direcionar `Menu.execute()` ao bloco correspondente.

Isto permite uma conclusão estática sobre a intenção e o caminho de dados: **o URM abre uma rota programática para escolher uma alternativa durante a janela de fixed rollback, contornando a restrição de sensibilidade do botão nativo**. Não permite concluir, sem runtime, que todos os contextos/telas do jogo aceitam a troca, nem que a fronteira de fixed rollback foi removida. Como `begin()` também controla o ciclo de vida do indicador, o estado pode ser recalculado em uma fronteira posterior.

A configuração `fix_rollback_without_choice=False` é apenas o padrão do SDK; jogos podem sobrescrevê-la. Quando ela é `True`, `display_menu` também aciona `saybehavior()`. O alcance dessa interação sobre a tela modal do URM exige teste integrado antes de afirmar o comportamento final.

## Classificação

- **CONFIRMADO NA FONTE URM CONVERTIDA:** a ação limpa `rollback_is_fixed` antes de invocar `ChoiceReturn`; botão Select do URM declara `sensitive=True`.
- **CONFIRMADO NO SDK 7.4.11:** fixed rollback é representado pela combinação do estado `rollback_is_fixed` e da fronteira; as ações nativas consultam fixed rollback para limitar seleção; `ChoiceReturn` retorna seu valor; `Menu.execute` usa o resultado como índice estrutural.
- **HIPÓTESE FORTE a partir do fluxo:** limpar o indicador tem como efeito operacional pretendido liberar a seleção via URM durante a janela fixa. A ponte passa por ação de screen e interação ativa, então a integração precisa ser exercitada em runtime.
- **NÃO DEMONSTRADO:** a atribuição não prova que o URM remova a fronteira, altere o histórico, preserve a alternativa nova após outro rollback ou funcione da mesma forma quando `fix_rollback_without_choice=True`.
- **PENDENTE:** teste de runtime que crie uma decisão com `renpy.fix_rollback()`, faça rollback até antes dela, compare a seleção nativa e a seleção via URM, observe o bloco executado e repita com ambos os valores da configuração. Depois, testar novo rollback e save/load.

## Runtime reduzido — screen → Menu AST com a flag ativa

A fixture independente `URM_REVERSO/tools/fixtures/urm_fixed_rollback_choice_probe.rpy` foi executada pelo workflow [39895890714](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39895890714), concluído **SUCCESS** no Ren'Py 7.4.11.

O testcase define deliberadamente `renpy.game.log.rollback_is_fixed = True`, consulta a sensibilidade de dois `ChoiceReturn` nativos sem valor de roll-forward disponível e, em seguida, escolhe a rota A pelo botão modal que reproduz a ação do URM. A tela devolve o índice 0 à interação do menu. O log registrou:

```text
FIXED_CHOICE_PRE False True False False
FIXED_CHOICE_POST False A False
FIXED_CHOICE_PRE True True False False
FIXED_CHOICE_POST True A False
```

Os dois pares correspondem a `config.fix_rollback_without_choice=False` e `True`. Em ambos, as ações nativas consultadas estavam insensíveis; a ação modal selecionou a rota A, o bloco correspondente do AST foi executado e o indicador ficou falso após a ação.

- **OBSERVADO EM RUNTIME — fixture reduzida:** com a flag fixed ativa artificialmente, a ação de screen análoga ao URM devolve o índice e o motor executa a alternativa correspondente; o caminho passou com ambos os valores da configuração.
- **CONFIRMADO NO SDK 7.4.11 — runtime sintético:** a consulta `ChoiceReturn.get_sensitive()` retornou falso para as duas opções quando `rollback_is_fixed=True` e não havia dado de roll-forward.
- **Limite explícito:** a fixture **atribui a flag diretamente**. Ela não executa `renpy.fix_rollback()`, não atravessa uma fronteira real via rollback, não instala a tela/código integral do URM e não mede o papel do roll-forward nativo. Portanto, não confirma ainda a sequência natural rollback → fixed boundary → escolha alternativa.
- **Arquivos do experimento:** [fixture](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/URM_REVERSO/tools/fixtures/urm_fixed_rollback_choice_probe.rpy) e [workflow isolado](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/.github/workflows/urm-fixed-rollback-choice-probe.yml).

## Próximo experimento isolado

Usar uma fixture temporária fora de `wells/`, `wells_beta/`, das fontes originais do URM e do SDK:

1. Criar duas alternativas A/B com efeitos distintos no store e em labels.
2. Executar `renpy.fix_rollback()` em ponto conhecido, avançar e fazer rollback até a decisão fixada.
3. Registrar `in_fixed_rollback()`, `roll_forward_info()`, alternativa disponível e label/bloco efetivamente alcançado.
4. Repetir com ação nativa, ação de seleção URM reduzida e `fix_rollback_without_choice` igual a `False` e `True`.
5. Após a escolha forçada, avançar, aplicar outro rollback e observar a fronteira, o estado e o roll-forward.
6. Manter a evidência de runtime separada da conclusão estática e remover/arquivar a fixture de acordo com o fluxo de experimentação do laboratório.

Nenhum código protegido foi alterado nesta etapa.

## Atualização — fronteira real atravessada em runtime (2026-10-23)

A fixture foi estendida para executar uma escolha nativa, chamar `renpy.fix_rollback()` depois dela, avançar até uma fala e acionar rollback pelo evento de teclado `PAGEUP`. O workflow [39897163458](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39897163458) concluiu **SUCCESS** no SDK 7.4.11.

O log do ciclo reproduzido mostra:

1. O jogador escolhe B; a fixture alcança o ponto após o menu.
2. O primeiro `PAGEUP` retorna a um estado anterior, mas ainda não alcança a fronteira fixa (`rollback_is_fixed=False`, sem roll-forward).
3. O segundo `PAGEUP` atravessa a fronteira: o rollback termina com `rollback_is_fixed=True`, e `roll_forward_info()==1`, que corresponde à escolha B.
4. No menu reaberto, a medição das ações nativas dá A insensível e B sensível. A tela URM reduzida oferece A; ao escolhê-la, registra fixed=True/forward=1, limpa a flag, retorna o índice 0 e o Ren'Py executa o bloco A. O testcase confirma a rota observada.

Trecho do log:

```text
BOUNDARY_ROLLBACK_END True ... 1
BOUNDARY_URM_ACTION True 1 False True ... 0 False
BOUNDARY_AFTER_MENU A False None ...
```

### Conclusão atualizada

- **OBSERVADO EM RUNTIME — fixture reduzida com fronteira real:** após `renpy.fix_rollback()` e rollback efetivo até a decisão, a alternativa previamente escolhida B permanece como roll-forward e a ação nativa a distingue das demais.
- **OBSERVADO EM RUNTIME — fixture reduzida:** a ação análoga a `URMChoice.Action` limpa a flag fixed, devolve outra posição estrutural (A, índice 0) e o motor executa o bloco A.
- **CONFIRMADO NO SDK 7.4.11 — fonte + runtime:** `rollback_is_fixed` não impede por si só que uma ação programática retorne outro índice; as ações nativas consultam fixed rollback para sensibilidade, enquanto `ChoiceReturn.__call__` retorna o valor.
- **Limite:** o fixture reproduz a ação e a tela, mas não carrega o URM integral pelo loader. O teste cobre `fix_rollback_without_choice=False); o cenário `True` só foi exercitado no probe sintético anterior.
- **PENDENTE:** testar novo rollback depois da troca A, para confirmar como a nova decisão se comporta após o script alcançar novamente `renpy.fix_rollback()`; testar também `fix_rollback_without_choice=True` com uma fronteira real, e save/load.
- **Tentativa inconclusiva:** a extensão que tentou executar A→rollback→B ficou parada esperando o botão B (runs [39896929205](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39896929205) e [39897042594](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39897042594)). Não houve segundo trace de rollback; portanto, ela não demonstra que o segundo rollback ou a segunda troca falhe no jogo. A fixture foi retornada ao caso de um ciclo validado, cujo run verde é 39897163458.

A fixture final e o workflow dedicado permanecem em [`urm_fixed_rollback_boundary_probe.rpy`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/URM_REVERSO/tools/fixtures/urm_fixed_rollback_boundary_probe.rpy) e [`urm-fixed-rollback-boundary-probe.yml`](https://github.com/mucholocco86/laborat-rio_renpy/blob/main/.github/workflows/urm-fixed-rollback-boundary-probe.yml). Nenhum SDK, fonte original do URM ou arquivo do Wells foi alterado.
