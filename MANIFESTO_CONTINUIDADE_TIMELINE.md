# MANIFESTO DE CONTINUIDADE — WELLS TIMELINE

Atualizado em 28/10/2026. Repositório mucholocco86/copia_timeline, branch main. Código de desenvolvimento em wells_beta/. Validação física pendente.

> Ao retomar em novo chat: leia primeiro a memória externa e este manifesto, confira os repositórios em modo de leitura e discuta o plano com o usuário. Não modifique arquivos, não crie commits e não inicie trabalho de correção até receber autorização explícita depois dessa conversa.

## 1. Leitura obrigatória

Memória externa mucholocco86/WELLS-PROJECT-MEMORY:
1. MEMORIA/COMO-TRABALHAMOS.md
2. MEMORIA/CONTINUIDADE-ENTRE-CHATS.md
3. PROJETOS/WELLS-TIMELINE.md
4. MANIFESTOS/RETOMADA-WELLS-TIMELINE-2026-10-28.md

Neste repositório:
1. este manifesto;
2. URM cruzado/README.md;
3. URM cruzado/COMPARACAO_URM_SDK_TIMELINE.md;
4. URM cruzado/MATRIZ_COMPATIBILIDADE_RENPY_TIMELINE.md;
5. código relevante em wells_beta/timeline/, lido no HEAD atual.

URM_REVERSO é referência somente de leitura. Não modificar documentação ou arquivos originais do URM.

## 2. Escopo e limites

- Trabalhar apenas em wells_beta/.
- wells/ é base estável; não editar durante o trabalho no Beta.
- Preservar a interface atual; não adicionar botões/telas/funções não pedidas.
- Nunca adicionar salvamento automático no fechamento do jogo.
- Corrigir somente causa comprovada, sem refatoração ampla.
- SDKs do laboratório: 6.99.4, 7.4.11, 8.5.3. Casos reais adicionais: 7.3.5, 8.1.3 e 8.3.4.
- Workflow/lint não equivale a teste de gameplay; o usuário faz validação física.
- Conversar e obter autorização explícita antes de alterar qualquer coisa nesta retomada.

## 3. Comportamento desejado

Timeline mostra choices e rotas sem criar saves ramificados. Mantém o sistema normal de saves do jogo e usa um JSON leve em game/wells_cache/ para o mapa/histórico.

Ao chegar a uma choice:
- registrar o card com a miniatura da tela real e as opções;
- após selecionar, desenhar o caminho percorrido;
- ao clicar no card, retornar à choice nativa para que o usuário escolha novamente;
- não escolher automaticamente uma opção pelo card;
- não capturar uma cena antes de a choice estar desenhada nem depois da seleção.

JASON é referência apenas para o desenho de rotas. O usuário rejeita sua lógica de ramificações de saves e a criação de muitos arquivos de save.

Debug e cache ficam em wells_cache. Não criar auto-save na saída.

## 4. Estado técnico conhecido em 28/10/2026

HEAD conhecido: 5ff40966613cce3edbf6549195776a951aa3a8ad — “fix: keep choice snapshots out of serialized rollback log”.

A correção move o cache de snapshots para memória runtime renpy.game._tl_snapshot_cache e remove o atributo legado do RollbackLog. Ela busca evitar RecursionError no save/load, onde Ren’Py serializa roots e renpy.game.log. Workflow informado: SUCCESS, 25 jobs; artifact fonte ID 12826261359, link expirável.

No arquivo backend/tl_state.rpy há comentários antigos afirmando que o cache fica em renpy.game.log. O código atual usa renpy.game. Corrigir a documentação interna apenas com autorização para mudanças.

## 5. Problemas físicos atuais

### Save/Load e RecursionError
MyDorm Ren’Py 8.1.3 apresentou RecursionError no pickle ao abrir Save/Load durante uma choice. Ainda falta confirmação física separada de que o patch de cache resolveu esse erro.

### Reentrada na choice, salto e loop
Relato mais recente: depois de chegar à segunda choice, escolher e clicar no retorno do Timeline, o jogo salta para uma cena/diálogos adiante; tentar retornar novamente pode entrar em loop. O usuário espera que o card tenha imagem e opções quando a choice aparece, o caminho seja desenhado após seleção e o retorno caia exatamente na choice nativa.

O arquivo mais importante pendente é wells_cache/debug.txt gerado depois dessa reprodução. Identificar qual caminho foi usado:
- Timeline native rollback: menu=... checkpoints=...
- Timeline do_load: dispatching snapshot unfreeze
- Timeline do_load: dispatching load slot=...

Não corrigir sem distinguir esses caminhos.

## 6. Google IA

Google_IA.zip foi analisado como pista secundária. Sua teoria de auto-recursão dos wrappers é possível de examinar, mas não provada pelo traceback: a falha mostrada ocorre em pickle e os wrappers aparecem uma vez na cadeia normal exports → store → menu. A referência original capturada em vez de renpy.store.menu pode ser avaliada como hardening, não como causa confirmada.

Outras alegações sobre deepcopy, testes contaminando saves, ast.Str/ast.Num e listas revertíveis também precisam ser verificadas contra código/SDK; não aplicar patches em lote. Separar fatos, hipóteses e inferências.

## 7. Histórico breve de decisões e correções

- Timeline de terceiro Chronology foi traduzido, renomeado, integrado à aparência Wells e reorganizado.
- Interface e rotas visuais foram testadas pelo usuário; alguns alinhamentos foram ajustados manualmente.
- Fontes/cores ficaram mais simples; remover camada de tema excessivamente complexa.
- Scrollbars foram aplicadas às abas História e Rota.
- Debug/cache foram encaminhados a wells_cache; chapters.json deixou de participar da lógica.
- Miniaturas devem capturar a choice real.
- O retorno passou por estratégias nativas, snapshots e fallback de replay/save.
- Ocorreram e foram corrigidos tracebacks de Shift+R, syntax/API em Ren’Py 7.3.5 e snapshot not_greedy em 8.1; não assumir que novas alterações não reintroduziram regressões.
- Usuário confirmou formação de rotas visualmente, mas o retorno de choices segue sob investigação.

## 8. Processo sugerido depois da autorização

1. Receber debug.txt e passos exatos.
2. Ler o estado/diff real no HEAD.
3. Determinar caminho executado e estado do nó alvo.
4. Comparar com SDK aplicável e referências URM sem editar URM.
5. Propor correção pequena e pedir/receber autorização do usuário.
6. Testar em MyDorm e depois nos outros casos de compatibilidade; registrar o que workflow e teste físico realmente provam.
7. Promover Beta para a base estável somente após confirmação do usuário.

## 9. Wells Manager

Wells Manager está pausado até Timeline ser concluído. Retomar depois consultando os manifestos na memória externa. A continuação se limita às funções atuais do Translator e Revisor; nenhum botão/função extra. Wells SDK, Wells Extractor e funções RPA são protegidos e fora do escopo sem autorização específica.
