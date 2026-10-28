# 35 — Entrada da tela Choices e fixed rollback

**Data:** 2026-10-23  
**Escopo:** localizar a entrada real para `URM_choices` no URM convertido e avaliar, na fonte, se a entrada é explicitamente bloqueada durante fixed rollback.  
**Status:** circuito de entrada confirmado na fonte convertida e validado em runtime integrado com as fontes originais do URM no SDK 7.4.11; veja o documento 36.

## Pergunta

A tela modal de Choices usada no teste reduzido pode ser aberta pela interface normal do URM quando o jogo está em fixed rollback? Qual ação concreta leva até ela?

## Fontes convertidas examinadas

- `classes/main.rpy`, blob `14f93406d2946eaed664ed72c1d47063984ce24f`, linhas 54–73.
- `classes/choices.rpy`, blob `48fc35f96119189e50f038981795115b3df7b770`, linhas 5–35 e 87–93.
- `classes/settings.rpy`, blob `13fd70596135c4389c9ab01cae982f80bfcad461`, linhas 6–70.
- `screens/main.rpy`, blob `ceb5dc63b3691a4b6244345e1c5a3e3b9d149291`, linhas 20–63 e 77–180.
- `screens/watchpanel.rpy`, blob `8cc83f00838ed409183e85e4ebdb37ddf4433823`, linhas 163–195 e 260–296.
- `screens/choices.rpy`, blob `a78de7e46a5b6230b4871628bfa62708233a07ce`, linhas 2–84.
- `screens/quickmenu.rpy`, blob `e3e4fbcd960c8b14d8869fb291cb40d16b03f73b`, linhas 40–60.

## Circuito de entrada

### 1. O estado reconhecido como Choice atual

`Choices.isDisplayingChoice` consulta `renpy.game.context().current`, procura o nó por `renpy.game.script.lookup` e retorna verdadeiro quando ele é `renpy.ast.Menu`. A leitura de alternativas continua sendo feita por `currentChoices`; não há aqui execução do bloco AST.

### 2. O overlay do URM instala os pontos de entrada

`x52URM.afterLoad()` chama `renpy.show_screen('URM_overlay')` e registra `URM_quickmenu` em `renpy.config.overlay_screens`. `onLabelCalled` chama `afterLoad()` quando o label é `start` (ou mostra o overlay em replay).

Dentro de `URM_overlay`, a tela inclui `URM_notifications`; quando o painel de monitoramento está visível, inclui também `URM_watchpanel`.

### 3. As duas entradas específicas de Choices

- **Notificação flutuante:** `URM_notifications` mostra “Choices detected” quando `showChoicesNotification` é verdadeiro, `Choices.isDisplayingChoice` é verdadeiro, e o watchpanel está desativado ou recolhido. O cartão e a tecla `alt_K_c` executam `Show('URM_choices')`.
- **Watchpanel:** `URM_watchPanelChoiceDetection` oferece botão “Show choices” quando `watchPanelChoiceDetection > 0` e há Menu ativo. O modo compacto usa um botão de painel; o modo expandido mostra contagem e botão. Ambos executam `Show('URM_choices')`.

Os padrões em `SettingsClass.defaultValues` são `showWatchPanel=False`, `watchPanelChoiceDetection=1` e `showChoicesNotification=True`. Portanto, pela fonte convertida, a rota inicial padrão é a notificação flutuante, se o overlay foi instalado e o jogo está num Menu.

### 4. O que o atalho geral do URM faz

O botão opcional do quickmenu e a tecla `Alt+M` chamam `x52URM.Open()`, que abre `URM_main` ou a tela de aviso. A tela principal tem abas Search, Variables, Snapshots, Labels, Renaming, Textboxes, Gamesaves e Options; não tem aba Choices nessa lista.

Assim, **não devemos descrever Alt+M como o caminho direto para Choices**. A fonte aponta para notificação/tecla Alt+C ou para o watchpanel.

### 5. A própria tela de Choices

`URM_choices` declara `modal True`, calcula `choices` a partir de `Choices.currentChoices` ao criar a tela e oferece Select para cada choice incluída. A ação Select declara `sensitive=True` e executa `Hide('URM_choices')`, `Hide('URM_CodeView')` e `choice.Action`. Não há, nesses pontos de entrada examinados, uma condição explícita `in_fixed_rollback()` ou `rollback_is_fixed` para ocultar ou desabilitar o cartão de Choices.

## Classificação das descobertas

- **CONFIRMADO NA FONTE URM CONVERTIDA:** a tela normal de Choices pode ser aberta pela notificação flutuante e pelo watchpanel; ambos usam `Show('URM_choices')`.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** `Alt+M` abre a interface principal, não é por si só uma chamada direta de Choices.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** os padrões favorecem a notificação flutuante; o watchpanel começa escondido.
- **CONFIRMADO NA FONTE URM CONVERTIDA:** as condições explícitas dos dois pontos de entrada verificam Menu atual e configurações, sem bloquear a entrada com base em fixed rollback.
- **OBSERVADO EM RUNTIME:** numa cópia descartável com o pacote original carregado, o wrapper de `renpy.show_screen` registrou `URM_choices` com `rollback_is_fixed=True`; o teste completo selecionou a alternativa A. Ver procedimento e limites no [documento 36](36_CHOICES_ORIGINAL_URM_FIXED_ROLLBACK_RUNTIME.md).
- **CONFIRMADO EM RUNTIME INTEGRADO:** o teste posterior carregou overlay, notificação, classe `Choices`, loader e tela originais do URM. O teste reduzido continua sendo evidência separada, mais estreita.

## Próxima validação

1. **Concluído para Alt+C:** pacote original e loader numa cópia descartável, fronteira real, screen aberta com `rollback_is_fixed=True` e alternativa A executada; ver documento 36.
2. **Pendente:** capturar a visibilidade gráfica do cartão, pois o test runner não casou a inscrição formatada como texto.
3. **Pendente:** repetir com botão do watchpanel, painel expandido/recolhido e `showChoicesNotification=False`.
4. **Pendente:** repetir com `fix_rollback_without_choice=True`.
5. **Pendente:** correlacionar com edição manual de variável e rollback após a reescolha.

O documento 34 permanece limitado ao teste reduzido de reescolha. O teste integrado documentado em 36 fecha a pergunta da entrada normal de Choices neste cenário específico, sem generalizar para toda configuração ou jogo.
