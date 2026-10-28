# 17 — Edição de itens, mutações de objetos e rollback

**Data:** 2026-10-16  
**Escopo:** URM convertido e SDK Ren'Py 7.4.11.  
**Tipo de evidência:** inspeção estática; nenhuma execução runtime foi realizada nesta etapa.

Este documento continua os documentos 15 e 16. Seu foco é verificar como as ações de criação, edição e exclusão de variáveis do URM chegam aos mecanismos reversíveis nativos do Ren'Py.

## Conclusões resumidas

1. **CONFIRMADO NA FONTE URM:** SetVarValue apenas delega para Var.setValue; a tela de edição também oferece ações diretas para excluir uma variável e adicionar itens em listas/dicionários.
2. **CONFIRMADO NA FONTE URM:** Var.setValue gera uma atribuição para um valor escalar ou chama .append(...) para o operador append. A edição de um filho de lista/dicionário é expressa por um caminho, por exemplo nome[índice] ou nome["chave"].
3. **CONFIRMADO NO SDK 7.4.11:** o compilador Ren'Py converte literais de lista/dicionário presentes no código Python compilado em construtores especiais. RevertableList e RevertableDict registram o estado limpo do objeto na primeira mutação do período corrente de rollback.
4. **CONFIRMADO NO SDK 7.4.11:** RollbackLog.complete() materializa snapshots de objetos mutados e deltas de StoreDict; Rollback.rollback() restaura objetos e depois aplica os valores anteriores do store.
5. **HIPÓTESE LIMITADA:** se o caminho alterado pelo URM aponta para um objeto revertível alcançável e registrado pelo log corrente, a mutação deve poder ser desfeita pelo rollback. A confirmação de que cada objeto encontrado/editado pelo URM satisfaz essas condições depende de runtime.
6. **PENDENTE:** o StoreMonitor não mostra um callback geral de mutações internas de lista/dicionário. A fonte indica detecção de alterações do store após nós Python e interceptação separada de atribuição de campo; não demonstra notificação para .append, __setitem__ de item aninhado ou del em objeto revertível.
7. **CONFIRMADO NA FONTE URM:** CreateVar só aceita string, boolean, int e float no caminho mostrado. Sua verificação if settableValue impede criar valores falsy, incluindo False, 0, 0.0 e string vazia. Esse é um efeito do código convertido e precisa ser validado no URM em execução para confirmar o comportamento do binário original.

## Fontes e versões

### URM convertido

- URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/vars.rpy
  - blob SHA: 57482937e14f215dac0ecb22a62da8ad160cba58
  - Var.setValue: linhas 232–269.
  - Var.delete: linhas 269–318.
  - Var.getChild, children, classificação de tipos: aproximadamente linhas 335–420.
  - SetVarValue: aproximadamente linhas 420–434.
  - CreateVar: linhas 437–477.
  - StoreMonitorClass: linhas 483–577.
- URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/screens/vars.rpy
  - blob SHA: 7959b2c0e6249df0edbb9ebe683481d46e4537e1
  - ações da tela de modificar, adicionar item e criar variável: consultar URM_modify_value, URM_add_item e URM_createVar.

### SDK Ren'Py 7.4.11

- renpy-7.4.11-sdk/renpy/python.py
  - blob SHA: c5eb2819a3e4ee096dbf01130d70a77f9b623484
  - StoreModule e StoreDict: linhas 80–180.
  - WrapNode e compilação: aproximadamente linhas 440–570 e 700–760.
  - mutator, RevertableList, RevertableDict, RevertableObject: aproximadamente linhas 820–1230.
  - Rollback.rollback: aproximadamente linhas 1480–1535.
  - RollbackLog.begin: aproximadamente linhas 1535–1690.
  - RollbackLog.complete: aproximadamente linhas 1690–1760.
- O commit-base consultado para esta inspeção foi c16b975669876cffdf1f5c89059dee58ac9f13eb.

## Caminho de interface para mutação

A tela de variáveis permite editar e adicionar valores por ações Ren'Py. O caminho de edição é:

    ação da tela
      → SetVarValue(var, ...)
      → Var.setValue(...)
      → atribuição sobre renpy.store.<caminho>
         ou chamada .append(...)

A exclusão chama Var.delete diretamente. Para caminhos de filhos, getChild produz acesso por índice para listas/dicionários e por atributo para objetos/store.

A operação afeta o estado do processo do jogo. O código examinado não reescreve os arquivos de script do jogo.

## Criação e exclusão de variáveis no store

CreateVar.__call__ faz a validação do nome, converte o valor e usa setattr(renpy.store, varName, settableValue). A classe não cria diretamente os tipos de lista/dicionário pela interface examinada. Como o teste de validade é por truthiness, valores falsy são rejeitados mesmo quando a conversão foi válida.

Var.delete percorre o caminho do nome. Para um nome raiz, a exclusão ocorre no dicionário do store; para filhos, usa delattr ou exclusão de item/índice. No SDK, StoreModule.__delattr__ delega para o StoreDict. Assim, exclusão de uma raiz passa pelo mecanismo de deltas de store. Já a exclusão de elemento em um container depende do tipo concreto do objeto para ser reversível.

## O que o SDK torna revertível

### Valores raiz do store

StoreDict registra os valores anteriores no início de um período de rollback e get_changes calcula os deltas. Atribuir, criar ou excluir um nome raiz no store participa desse mecanismo nativo.

### Listas, dicionários e objetos mutáveis

WrapNode reescreve literais de lista/dicionário e compreensões no Python compilado pelo Ren'Py para usar construtores especiais. O código registra que os construtores usados pelo compilador são __renpy__list__ e __renpy__dict__; a implementação de RevertableList/RevertableDict está no mesmo módulo.

Os métodos mutadores desses tipos passam por mutator. Na primeira mutação do objeto no período, o wrapper guarda uma referência fraca e self._clean() em renpy.game.log.mutated. Em complete(), o log coleta essas informações e coloca o estado comprimido em current.objects. Em rollback(), o SDK chama obj._rollback(snapshot) nos objetos registrados.

O log também guarda as alterações do store. A rotina de rollback restaura primeiro os objetos registrados e em seguida aplica os valores antigos de cada StoreDict. Isso permite desfazer tanto uma substituição da raiz quanto uma mutação interna, desde que o valor/objeto esteja coberto pelo mecanismo respectivo.

### Limite de generalização

A transformação do compilador confirma o caminho para literais compilados por Ren'Py. Ela não prova que qualquer lista/dicionário recebido de código externo, biblioteca Python, extensão ou objeto desserializado seja automaticamente um tipo revertível. Para uma edição do URM, deve-se inspecionar type(valor) e testar a origem do objeto antes de afirmar reversibilidade.

## Relação do StoreMonitor com o rollback

O callback do StoreMonitor é documentado na própria fonte URM como executado depois de um nó Python. Ele solicita context().force_checkpoint = True, obtém alterações do store e verifica variáveis de nível superior. Em paralelo, o URM injeta código em uma função interna de atribuição de campo para chamar handleVarChange.

Isso sustenta dois caminhos de observação diferentes:

- deltas de nomes de nível superior no store após execução de nós Python;
- interceptação de atribuição de campo compatível com a função interna encontrada pelo URM.

Não se deve inferir que o StoreMonitor observa toda mutação interna. .append, atribuição a um índice/dicionário dentro de um objeto ou remoção de um item podem acionar o mecanismo de rollback do próprio objeto, sem aparecer como substituição da variável raiz no StoreDict. O comportamento exato do callback durante ações de screen e mutações feitas pelo URM continua pendente de execução.

O pedido de checkpoint é uma solicitação ao fluxo nativo; não equivale a o URM possuir ou serializar um rollback independente. A relação temporal entre a ação de screen, o callback Python e o checkpoint efetivo precisa de teste controlado.

## Semântica que a fonte permite afirmar

| Operação URM | Mutação observada na fonte | Mecanismo SDK relevante | Estado da conclusão |
|---|---|---|---|
| Editar valor raiz | atribuição em renpy.store | delta de StoreDict | mecanismo estático confirmado |
| Criar valor raiz | setattr(renpy.store,...) | delta de StoreDict | mecanismo estático confirmado; falsy rejeitado no fluxo observado |
| Excluir valor raiz | del storeDict[key] | delta de StoreDict | mecanismo estático confirmado |
| Editar elemento de lista/dict | atribuição a caminho indexado | RevertableList/Dict, se for esse tipo | condicional ao tipo concreto |
| Acrescentar item à lista | .append(value) | mutator de RevertableList, se for esse tipo | condicional ao tipo concreto |
| Excluir elemento/atributo | del/delattr no objeto | mutator revertível, quando aplicável | condicional ao tipo concreto |
| Notificar monitoramento para mutação interna | não demonstrado no callback de store | separado do snapshot de objetos | pendente de runtime |

## Testes necessários para classificar como OBSERVADO EM RUNTIME

Ainda não foram executados nesta etapa. Um teste isolado no SDK 7.4.11 deve registrar, com valores antes/depois:

1. Mutação raiz via URM antes de um menu e rollback para antes da alteração.
2. Mutação raiz durante o menu, escolha, avanço e rollback.
3. .append, atribuição de índice, edição de chave e exclusão em containers revertíveis.
4. Os mesmos casos com containers de origem não compilada pelo Ren'Py, se possível.
5. Edição de objeto/atributo e remoção de atributo.
6. Repetição de mutação no mesmo objeto dentro de um único intervalo entre checkpoints.
7. Repetição após checkpoint forçado pelo StoreMonitor.
8. Estado do monitor de variável após mutação raiz versus mutação interna.
9. Save/load antes e depois da mutação, seguido de rollback.
10. Seleção de alternativa diferente após retornar a um ponto anterior.

Até esses testes, as conclusões deste documento são estáticas e não demonstram o comportamento do URM em runtime nem a semântica dos arquivos .urm.

## Próximo ponto de investigação

1. Verificar como o URM obtém as referências a containers e se há caminho de criação de listas/dicionários fora de CreateVar.
2. Examinar a implementação exata de __renpy__list__ e __renpy__dict__ nos stores do SDK para completar a cadeia do compilador.
3. Revisar a instrumentação do StoreMonitor contra a versão 7.4.11 e mapear o callback em relação ao ciclo de execução e aos checkpoints.
4. Preparar um fixture mínimo e isolado para runtime sem alterar wells/, wells_beta/, fontes originais ou SDK.
