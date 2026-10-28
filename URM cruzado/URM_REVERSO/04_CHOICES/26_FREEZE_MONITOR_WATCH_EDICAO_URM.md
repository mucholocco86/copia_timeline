# 26 — Freeze, monitor e watch: estados diferentes e edição própria do URM

**Data:** 2026-10-18  
**Escopo:** leitura estática dos stores de variáveis, do StoreMonitor e da tela de variáveis convertida do URM.  
**Referência:** código convertido URM X52; não é prova integral do runtime original.

## Achado principal

A interface e a fonte distinguem três estados:

| Estado | Estrutura registrada | Efeito pretendido |
|---|---|---|
| Freeze | store `vars`, atributo `frozen` | Interceptar/reverter mudança de variável simples |
| Monitor | store `vars`, atributo `monitor` | Notificar mudança detectada |
| Watch | store `watched`, metadado `name` | Exibir variável no painel de observação para consulta/edição |

Esses estados não são sinônimos. Watch não ativa por si só o bloqueio de freeze nem o mecanismo de notificação de monitor. Os metadados fazem parte dos stores próprios do URM, não de um snapshot do estado do jogo.

## Elegibilidade

**CONFIRMADO NA FONTE URM CONVERTIDA:** `VarsStore.isFreezable(varName)` recusa nomes que contenham ponto ou colchete. Para nomes de raiz, permite tipos retornados como `string`, `boolean`, `int` ou `float`.

`isMonitorable` delega para `isFreezable`; portanto, os dois controles têm a mesma restrição de tipo e caminho na tela examinada.

A interface da tabela desabilita freeze e monitor quando a variável não é elegível. Já a ação Watch usa uma lista separada e não consulta esses mesmos predicados naquele trecho da tela.

## Como o StoreMonitor atua

A classe convertida tem dois caminhos de observação:

1. **Hook de SetField:** ao inicializar, procura um helper de atribuição no store, guarda uma cópia da função e substitui o código do helper. O wrapper chama `handleVarChange(name, valor_atual, novo_valor)`. Se a variável estiver frozen, o método tenta restaurar o valor anterior e retorna False para impedir a atribuição original. Se estiver monitorada, pode criar uma notificação quando os valores diferem e a tela de edição URM não está aberta.
2. **Callback Python:** ao fim de nós Python, solicita `Context.force_checkpoint = True`, consulta `StoreDict.get_changes(False)` e chama `handleVarChange` para cada delta detectado, comparando o valor anterior do delta com o valor atual.

O segundo caminho é temporal e depende de quais deltas ainda estão disponíveis quando o callback roda. O runtime reduzido anterior demonstrou que a visibilidade do delta pode diferir com rollback habilitado/desabilitado; ver [documento 25](25_CALLBACK_ROLLBACK_STOREDELTA_GAMEPLAY.md).

## A edição do URM quando a variável está frozen

**CONFIRMADO NA FONTE URM CONVERTIDA:** `Var.setValue` verifica se a variável raiz está frozen. Se estiver, remove temporariamente a marca, aplica a atribuição direta com `exec('renpy.store.' + caminho + operador + valor)` ou executa o append, e no bloco `finally` volta a marcar a variável como frozen.

Isso significa que freeze não é apresentado pelo código como “nem o URM pode editar”. A tela avisa que a variável frozen não pode mudar pelo jogo, mas pode ser mudada pelo próprio URM. O código implementa essa exceção com unfreeze → escrita → freeze.

Para uma variável monitorada, a atribuição direta por `Var.setValue` não passa necessariamente pelo helper SetField interceptado. A detecção depende então do callback Python posterior e do delta ainda estar visível. A fonte não basta para afirmar quando a notificação aparece em toda situação.

## Persistência e alcance

- `remember`, `freeze`, `monitor` guardam metadados no store `vars`; freeze e monitor criam/atualizam o registro lembrado.
- `watch` guarda nome de exibição separado em `watched` e ativa `Settings.showWatchPanel`.
- `ignore` registra filtros por contexto (`path`, `code`) no store `vars`.
- Esses metadados descrevem preferências e comportamento das ferramentas URM; não são o valor corrente completo do jogo.
- O circuito exato de gravação desses stores no arquivo `.urm` continua remetido à análise de URMFiles e aos documentos de persistência.

## Classificação

- **CONFIRMADO NA FONTE URM CONVERTIDA:** freeze, monitor e watch usam flags/stores diferentes.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** freeze e monitor se restringem a variáveis raiz escalares simples pela checagem examinada.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** `Var.setValue` temporariamente remove e restaura freeze ao escrever por ação URM.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** o hook SetField bloqueia mudança detectada em variável frozen e o callback Python usa deltas do store.
- **OBSERVADO EM RUNTIME (fixture reduzida; doc 25):** uma edição por screen pode ser restaurada por rollback mesmo quando o callback posterior não encontrou o delta.
- **OBSERVADO EM RUNTIME (fixture reduzida; doc 27):** escrita nativa via helper foi bloqueada em variável frozen; SetVarValue mudou 10→30 e reaplicou freeze; callback posterior, recebendo o delta, restaurou 30→10 e manteve freeze. Foi em contexto com rollback desabilitado.
- **OBSERVADO EM RUNTIME (fixture reduzida; doc 28):** com rollback habilitado, o callback não viu o delta; o valor editado ficou em 30 até rollback, que restaurou 10. Isso não verifica o StoreMonitor ou a persistência dos metadados do URM completo.
- **OBSERVADO EM RUNTIME (fixtures reduzidas; docs 29 e 30):** sem rollback, edição direta não notifica durante a ação e callback pode processar o delta disponível; com rollback habilitado, callback não recebeu o delta e não houve notificação antes da restauração. Não é integração do URM completo.
- **PENDENTE:** verificar no URM completo como o ciclo de StoreMonitor é instalado e como os metadados freeze/monitor/watch sobrevivem a reinício e carregamento de outro jogo.

## Fontes consultadas

| Arquivo convertido | Símbolos / trechos | Blob SHA |
|---|---|---|
| `classes/vars.rpy` | `VarsStoreClass` (freeze/monitor/watch/ignore); `Var.setValue`; `StoreMonitorClass.init`, hook, `handleVarChange` e callback | `57482937e14f215dac0ecb22a62da8ad160cba58` |
| `screens/vars.rpy` | tabela de variáveis, ações Watch/Freeze/Monitor e `URM_var_changed` | `7959b2c0e6249df0edbb9ebe683481d46e4537e1` |

