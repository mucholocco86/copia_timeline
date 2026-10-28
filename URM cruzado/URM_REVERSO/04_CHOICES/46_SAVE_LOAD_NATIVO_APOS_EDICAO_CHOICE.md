# 46 — Save/load nativo após editar condição e executar Choice

**Data:** 2026-10-25. **SDK:** Ren'Py 7.4.11. **Evidência:** runtime integrado com as telas e o setter original do URM, em fixture descartável. **Run final:** [40212821209](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40212821209), **SUCCESS**.

## Pergunta

Depois de a tela original do URM editar a variável que controla uma Choice dinâmica e a rota C executar, o save nativo do Ren'Py preserva esse valor e essa rota? O load restaura os dois após terem sido mudados em memória?

## Procedimento

A fixture [urm_dynamic_condition_save_probe.rpy](../tools/fixtures/urm_dynamic_condition_save_probe.rpy) inicia `urm_dynamic_save_gate` em 0. A Choice C requer `urm_dynamic_save_gate == 1`.

O percurso integra a tela original URM_choices, o CodeView e URM_modify_value. O harness chama o handler `CodeView.handleVarClicked`, digita 1 no editor e submete a entrada pelo caminho original `SetVarValue → Var.setValue`. Em seguida seleciona C, cuja rota define `urm_dynamic_save_route = "C"`.

No ponto de save, a fixture imprime valores e contexto, chama `renpy.save("urm-dynamic-choice-edit-roundtrip", ...)`, depois altera a variável para 0 e a rota para `"mutated-after-save"`, e chama `renpy.load` no mesmo processo. O marcador para distinguir reentrada fica em `renpy.test.testexecution`, fora do estado serializado pelo save do jogo.

O workflow [urm-dynamic-condition-save-probe.yml](../../.github/workflows/urm-dynamic-condition-save-probe.yml) cria jogo temporário com o SDK 7.4.11 e o URM original. Nenhuma fonte original, SDK, `wells/` ou `wells_beta/` foi alterado.

## Resultado runtime

O run 40212821209 terminou SUCCESS e registrou:

~~~text
DYNAMIC_SAVE_BEFORE_SAVE 1 C (..., 73)
DYNAMIC_SAVE_MUTATED_AFTER_SAVE 0 mutated-after-save
DYNAMIC_SAVE_AFTER_LOAD 1 C (..., 84)
... exit=0
~~~

O log demonstra que o estado salvo continha `gate=1` e rota C; depois da mutação em memória para `0` e `mutated-after-save`, o load retornou `gate=1` e rota C. A fixture verifica esses valores com asserções e encerra com exit 0.

## Classificação

- **OBSERVADO EM RUNTIME INTEGRADO:** após a edição gráfica original e a execução da rota C, `renpy.save` e `renpy.load` na mesma sessão restauraram a variável da condição e a rota do estado salvo.
- **CONFIRMADO NO SDK 7.4.11:** o caminho nativo de save/load serializa estado e RollbackLog conforme o documento 20; esta fixture observa o resultado específico no estado de Choice e rota.
- **LIMITAÇÃO:** o marcador de reentrada é mantido no módulo do runner de teste para impedir repetição do save/load; não é parte dos stores salvos pelo jogo.
- **NÃO TESTADO:** encerramento e reabertura do processo, outro slot/interface de save, carregamento através da screen Gamesaves do URM, condição boolean, containers, variável recém-criada ou comparação do arquivo `.urm` antes/depois.
- **NÃO CONCLUIR:** este resultado não demonstra que o arquivo `.urm` persiste a variável do jogo. A operação testada foi o save nativo `renpy.save`; o conteúdo próprio `.urm` continua sendo tratado separadamente nos documentos de persistência.

## Tentativas do harness e correções

- [40212497903](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40212497903) salvou antes da edição, no estado B; não serve como evidência do estado editado.
- [40212617374](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40212617374) falhou ao localizar um displayable porque a sequência do test runner divergia do roteiro de interação validado.
- [40212690066](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40212690066) repetiu a mutação porque faltava a guarda de reentrada imediatamente depois da instrução save. A fixture foi corrigida; o run final 40212821209 passou.

Esses runs anteriores são diagnósticos de sequência/instrumentação, não evidência contra a persistência observada no run final.

## Conclusão delimitada

No cenário testado, uma variável escalar raiz alterada pelo editor original do URM e o valor de rota produzido pela Choice foram preservados pelo save nativo; carregar o slot restaurou o par de valores após mutações posteriores. Isso confirma a persistência nesse save do Ren'Py 7.4.11. Não prova persistência no arquivo `.urm` nem comportamento em um processo novo.

## Próximas verificações

1. Abrir o mesmo slot pela tela original Gamesaves do URM, em vez de chamar renpy.load diretamente.
2. Repetir em processo novo para remover a dependência de sessão/runtime atual.
3. Comparar o arquivo `.urm` e os stores do URM antes/depois, separando metadados de estado do jogo.
4. Verificar se save/load reabre a Choice no Menu ou retoma de um ponto posterior, e como a condição reavaliada aparece na tela.