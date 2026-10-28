# 43 — Condição dinâmica de Choice após edição pelo URM

**Data:** 2026-10-23. **SDK:** Ren'Py 7.4.11. **Evidência:** inspeção da fonte URM original e teste runtime integrado com o pacote original, em fixture descartável. **Workflow:** [39992488601](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/39992488601), **SUCCESS**.

## Pergunta

Se a condição de uma Choice depende de uma variável do store e essa variável é editada enquanto a tela original URM_choices está aberta, o URM reavalia a visibilidade? A alternativa pode então ser selecionada e executada?

## Fonte examinada

- URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/classes/choices.rpy: URMChoice.isVisible chama eval(self.condition, renpy.store.__dict__) quando a propriedade é consultada. A condição não é armazenada como resultado booleano no objeto.
- URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/screens/choices.rpy.x52: a screen inicializa default choices = x52URM.Choices.currentChoices or []; dentro do for, consulta choice.isVisible para exibir True/False. O botão Select mantém a ação sensível e chama choice.Action.
- classes/vars.rpy: Var.setValue converte o valor conforme tipo da variável e executa atribuição ao renpy.store; para tipo boolean, constrói a expressão str(bool(newValue)).

Isso separa duas coisas: a lista choices da screen é inicializada uma vez durante a vida daquela instância; a propriedade isVisible de cada objeto é consultada no momento de renderização da linha e lê a condição atual do store.

## Fixture e procedimento

A fixture [urm_dynamic_condition_probe.rpy](../tools/fixtures/urm_dynamic_condition_probe.rpy) define um Menu com A e B e uma terceira alternativa C condicionada por urm_dynamic_probe_enabled, inicialmente False.

O teste:

1. escolhe a rota nativa B;
2. retorna ao Menu pelo percurso de rollback e abre a screen original URM_choices com Alt+C;
3. confirma que a screen abriu e que C está com isVisible=False;
4. chama o setter original x52URM.Var('urm_dynamic_probe_enabled').setValue(True) enquanto a screen está aberta;
5. consulta x52URM.Choices.currentChoices e confirma que o objeto de C agora retorna isVisible=True;
6. chama renpy.restart_interaction(), seleciona a terceira linha por Alt+3/Enter e confirma que o bloco C executou.

O workflow [urm-dynamic-condition-probe.yml](../../.github/workflows/urm-dynamic-condition-probe.yml) copia the_question, o SDK 7.4.11 e o pacote URM original para um diretório temporário. O pacote original, SDK, Wells estável e beta não foram modificados.

## Resultado

O log do workflow registra:

~~~text
DYNAMIC_PROBE_SCREEN URM_choices enabled False target [(False, 2)]
DYNAMIC_PROBE_AFTER_EDIT True True [(True, 2)]
DYNAMIC_PROBE_RESULT True C
... exit=0
~~~

A chamada a Var.setValue teve sucesso; o mesmo índice estrutural 2 passou de falso para verdadeiro na consulta seguinte; depois do reinício da interação, o bloco da rota C executou e a fixture terminou com exit 0.

## Conclusões classificadas

- **CONFIRMADO NA FONTE URM ORIGINAL:** URMChoice.isVisible avalia a expressão de condição contra o store atual a cada consulta.
- **CONFIRMADO NA FONTE URM ORIGINAL:** a tela armazena uma lista de objetos Choice em default choices, mas consulta a propriedade isVisible nas linhas renderizadas. Não foi encontrado cache do resultado booleano dentro de URMChoice.
- **OBSERVADO EM RUNTIME INTEGRADO:** com a screen original aberta, a edição via método original Var.setValue mudou a condição de False para True para a alternativa estrutural 2.
- **OBSERVADO EM RUNTIME INTEGRADO:** após renpy.restart_interaction(), a seleção da alternativa C alcançou seu bloco AST e a variável de rota ficou C.
- **CONFIRMADO NO SDK 7.4.11:** a execução do bloco ocorre pelo circuito nativo Menu/ChoiceReturn descrito nos documentos 15 e 40; este teste acrescenta o predicado dinâmico e a mutação durante a screen.
- **NÃO TESTADO:** o teste chamou diretamente Var.setValue dentro do testcase. Ele usa o setter original do URM, mas não percorre as ações de digitação/clique da screen URM_modify_value, nem o fluxo de hyperlink da CodeView.
- **NÃO TESTADO:** se a screen redesenha imediatamente após uma edição feita por qualquer controle externo sem reiniciar a interação; a fixture solicitou explicitamente renpy.restart_interaction().
- **NÃO TESTADO:** rollback da variável booleana editada neste mesmo cenário, save/load, expressões com efeitos colaterais, valor ausente, erros de avaliação ou condições compostas.
- **NÃO GENERALIZAR:** o resultado refere-se ao URM original convertido/carregado e ao Ren'Py 7.4.11 do laboratório. Não prova comportamento em qualquer jogo, outro SDK ou toda forma de edição.

## Significado para o circuito investigado

A fixture demonstra que uma Choice pode mudar de disponibilidade durante a execução sem alteração do AST do jogo: o código de condição permanece ligado ao Menu, enquanto a avaliação lê o valor corrente do store. Quando a variável muda e a interação é reiniciada, a screen do URM mostra o novo resultado. A seleção posterior devolve o índice estrutural e o Ren'Py executa o bloco da alternativa.

Isso não altera o texto/condição no arquivo .rpy nem persiste, por si só, a edição. A relação da edição com rollback foi demonstrada separadamente para uma variável escalar raiz no documento 39, mas ainda falta repetir rollback da variável-condição no mesmo circuito.

## Próximas verificações

1. Fazer a edição pelo fluxo gráfico URM_modify_value enquanto URM_choices estiver aberta e observar se o editor fecha/oculta a tela ou provoca reinício de interação.
2. Após tornar C visível e executá-la, usar rollback e medir em que ponto o valor booleano, o nó Menu e a rota são restaurados.
3. Reabrir a tela depois da restauração e verificar se C volta a isVisible=False.
4. Salvar após a edição, mudar o valor e carregar; separar estado serializado do save de metadados .urm.