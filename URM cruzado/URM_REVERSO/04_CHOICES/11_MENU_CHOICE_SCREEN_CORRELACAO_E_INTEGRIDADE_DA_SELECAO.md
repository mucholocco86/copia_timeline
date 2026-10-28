# 11 — Correlação entre Menu.items, MenuEntry e seleção nativa

**Data:** 2026-10-13  
**Estado:** 🟢 comprovado na fonte convertida do URM disponibilizada no laboratório; 🔵 comprovado no SDK Ren'Py 7.4.11; 🟠 limites ainda exigem teste de runtime.

## Objetivo

Aprofundar o ponto de parada do documento [10 — URM Choices como projeção da interação nativa](10_URM_CHOICES_COMO_PROJECAO_DA_INTERACAO_NATIVA.md). A pergunta central é: **qual identificador percorre a interação nativa e como se relaciona com o índice de `Menu.items` preservado por `URMChoice`?**

## Fontes verificadas no novo laboratório

- `01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/choices.rpy` — `ChoicesClass.currentChoices`, `URMChoice.Action`, `text` e `isVisible`.
- `01_MATERIAL_URM/2_URM_X52_CONVERTIDO/screens/choices.rpy` — tela modal `URM_choices` e `choice.Action`.
- `renpy-7.4.11-sdk/renpy/ast.py` — `Menu.execute` e `Menu.chain`.
- `renpy-7.4.11-sdk/renpy/exports.py` — `display_menu`, `MenuEntry`, `checkpoint(rv)`.
- `renpy-7.4.11-sdk/renpy/ui.py` — `ChoiceReturn.__call__`.

## 1. A identidade estrutural da alternativa

🟢 `ChoicesClass.currentChoices` faz `enumerate(script.items)` e cria `URMChoice(i, item)` **somente** se `len(item) >= 3 and item[2]`. O `i` é o índice original na lista `Menu.items`, **não** a posição na lista filtrada `currentChoices`.

Isso é uma distinção operacional: uma entrada sem bloco pode ser omitida da lista do URM sem mudar o valor de índice associado aos demais itens.

🔵 No `Menu.execute` do SDK, a construção de `choices` também usa `enumerate(self.items)`; quando há bloco, o valor da alternativa é `i`. Após `renpy.exports.menu(...)`, o retorno `choice` indexa `self.items[choice][2][0]`.

Fluxo estrutural:

```text
Menu.items[i] ───> URMChoice(index=i, tuple=Menu.items[i])
      │
      └──────────> Menu.execute(): choices.append((label, condition, i))
                                      │
                                      └──> escolha retorna i
                                            │
                                            └──> self.items[i][2][0]
```

**Invariante confirmado:** para a alternativa com bloco, o valor `i` referencia a posição original de `Menu.items`; não se deve remapear para a posição visual da alternativa.

## 2. A Choice Screen nativa recebe outro tipo de objeto

🔵 `display_menu` instancia `MenuEntry((label, action, chosen))` ou `MenuEntry((label, action))`, conforme configuração, e acrescenta propriedades `caption`, `action`, `chosen`, `args` e `kwargs`.

Se o valor recebido não for um `ChoiceReturn` existente, a função cria `renpy.ui.ChoiceReturn(label, value, location)`. Esse `value` vem da seleção nativa; para o `Menu` analisado, é o índice original `i`.

A tela padrão **não recebe automaticamente** o bloco AST inteiro; o URM consulta o `Menu` pelo contexto/script em um ramo separado.

## 3. A alternativa selecionada retorna um valor, não executa o bloco

🟢 `URMChoice.Action` executa:

```python
renpy.game.log.rollback_is_fixed = False
return renpy.ui.ChoiceReturn(self._m1_choices__choice[0], self._m1_choices__index)()
```

🔵 `ChoiceReturn.__call__` atualiza o estado de `chosen` quando disponível e retorna `self.value`. `display_menu` recebe o resultado de `renpy.ui.interact(...)`, chama `checkpoint(rv)` e retorna `rv`.

Depois, `Menu.execute` decide o primeiro nó do bloco com `self.items[choice][2][0]`. O executor continua sendo Ren'Py. É importante **não confundir o valor devolvido pela escolha com o texto de exibição**.

## 4. Implicação: correspondência por texto é frágil

🟢 `URMChoice.text` chama `renpy.exports.substitute`, com fallback para o texto original. Já `URMChoice.Action` fornece a string original `choice[0]` ao construtor `ChoiceReturn` e o índice original como valor.

🔵 `Menu.execute` também pode aplicar `renpy.config.say_menu_text_filter` ao rótulo antes do caminho nativo.

**Conclusão de engenharia:** uma futura camada Wells não deve identificar alternativas unicamente pelo texto mostrado, que pode ter substituições/filtros e não é garantidamente único. A correspondência mais sólida nessa arquitetura é baseada no `Menu` atual e no índice original `Menu.items[i]`, preservando distinção entre itens com bloco, entradas de legenda, condições e estado de visibilidade.

## 5. Limites / perguntas ainda abertas

- 🟠 A coincidência entre a alternativa associada ao `Menu` atual e o objeto recebido pela Choice Screen deve ser validada com casos de `condition` falso, menus com legendas, rótulos repetidos, `set` de escolhas e argumentos por item.
- 🟠 A posição de apresentação na tela pode diferir do índice de `Menu.items`; não assumir `enumerate(items)` da tela = índice de AST sem teste.
- 🟠 A correlação exata de estado durante tradução, substituição de texto, screen re-render, rollback e outros contextos precisa de instrumentação de leitura.
- 🟠 A intervenção `rollback_is_fixed=False` do URM está comprovada, mas a intenção original do autor e os resultados em outras versões não devem ser extrapolados.
- 🟠 A inspeção estrutural não equivale à previsão dos efeitos de executar um bloco com `If`, `Call`, `Jump` e código Python. Não executar um bloco para inferir efeitos.

## 6. Próxima experiência controlada

Sem modificar SDK, URM original ou Wells estável:

1. Criar em um projeto **experimental autorizado** menus com A/B, condição `False`, rótulos repetidos e entradas de legenda.
2. Registrar de modo somente-leitura: identidade do `Menu`, índices de `Menu.items`, valor da ação nativa, dados preparados para a Choice Screen e retorno de seleção.
3. Confirmar índices e condições **antes e depois** do rollback com `A → rollback → B`.
4. Documentar resultados como observação de runtime separada dos fatos já demonstrados por fonte.

## 7. Relação com a pesquisa anterior

Esta análise **estende** o documento 10; não o substitui. Mantém-se a conclusão arquitetural:

```text
URM = leitura/projeção + intervenção pontual na seleção
Ren'Py = execução de Menu e blocos + checkpoint/rollback
Wells futuro = camada de análise/apresentação sem segundo executor
```

A conclusão acima é restrita aos mecanismos verificados; não declara concluída a árvore inteira de engenharia reversa.
