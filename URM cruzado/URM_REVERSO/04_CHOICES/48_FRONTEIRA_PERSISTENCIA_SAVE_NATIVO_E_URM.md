# 48 — Fronteira de persistência: save nativo Ren'Py e arquivo .urm

**Data:** 2026-10-27. **Alvo:** fontes convertidas do URM X52 e SDK Ren'Py 7.4.11. **Status:** inspeção estática; teste runtime de gravação e comparação de arquivos .urm pendente.

## Pergunta

A edição de uma variável de jogo feita por Var.setValue é persistida pelo arquivo próprio .urm, ou pelo save nativo Ren'Py? Quais dados a fonte atribui ao formato .urm?

## Evidência da fonte URM

Fonte consultada: URM_REVERSO/01_MATERIAL_URM/2_URM_X52_CONVERTIDO/classes/URMFiles.rpy, blob SHA 888aba28d9d2e7870d8c4e6526417390179cd326.

- URMFile.save() inicializa o store properties com urmVersion e gameId, serializa cada store carregado como JSON dentro de um ZIP e grava o arquivo .urm.
- O arquivo também pode ser copiado para o diretório de saves do jogo. Isso é uma cópia do mesmo arquivo URM, não uma chamada a renpy.save.
- URMFiles.save() delega a URMFile.save(filename); URMFiles.load() reconstrói stores URM de entradas ZIP/JSON (ou tenta o leitor legado JSON).
- A fonte não percorre renpy.store para capturar todas as variáveis do jogo durante URMFile.save(). Ela serializa os stores que foram associados ao objeto URMFile.
- O código de variáveis define stores próprios vars e watched para metadados de freeze/monitor e observação. A gravação de um valor do jogo por Var.setValue é uma atribuição em renpy.store; esse método não chama URMFiles.save nem adiciona o valor editado a um store URM.

## Conclusão estática

**CONFIRMADO NA FONTE URM CONVERTIDA:** o .urm é um contêiner de stores de dados próprios do URM, com serialização ZIP + JSON. Sua implementação de save não faz snapshot geral do estado de jogo.

**CONFIRMADO NA FONTE URM CONVERTIDA:** editar uma variável de jogo por Var.setValue e salvar o arquivo .urm são rotas distintas no código examinado. Os metadados URM podem descrever variáveis monitoradas/congeladas/observadas; isso não equivale ao valor atual de cada variável.

**CONFIRMADO EM RUNTIME NOS DOCUMENTOS 46–47:** o save nativo Ren'Py conservou a variável editada e a rota da Choice, inclusive após load em processo Ren'Py novo, nas fixtures documentadas.

**HIPÓTESE AINDA NÃO TESTADA:** um .urm pode preservar referências/nome/configuração de uma variável que depois é localizada novamente no jogo, mas não o valor atual da variável como snapshot. É preciso seguir os consumidores de cada store e testar a gravação/carregamento do arquivo.

## Limites

A fonte consultada é uma conversão por unrpyc, não uma prova de equivalência byte a byte com o original. Esta etapa não executou o modal de salvar/carregar .urm, não inspecionou um artefato produzido em runtime e não prova a lista exaustiva de stores criados em todos os fluxos.

O teste de save nativo dos documentos 46–47 não testa .urm. Não se deve inferir uma coisa a partir da outra.

## Próximo experimento isolado

Em fixture descartável no Ren'Py 7.4.11:

1. Abrir e salvar um arquivo .urm pelas ações originais do URM.
2. Registrar stores/nomes/valores antes e depois de salvar.
3. Abrir o ZIP resultante e inspecionar entradas JSON.
4. Editar uma variável do jogo, salvar novamente o .urm e comparar entradas.
5. Reiniciar processo, carregar .urm pela API original e verificar se o valor do jogo muda ou se apenas metadados/configuração são restaurados.
6. Repetir com stores vars e watched, separando configuração e estado de gameplay.

Nenhuma fonte original, SDK ou diretório Wells deve ser alterado para esse teste.

## Atualização posterior — runtime do arquivo `.urm` (2026-10-28)

O status acima descreve corretamente a etapa estática de 2026-10-27. A pendência foi parcialmente resolvida por testes posteriores:

- [Documento 49](49_PERSISTENCIA_URM_RUNTIME_STORES_E_ESTADO.md), run [40657558715](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40657558715): `URMFiles.save/load` foi executado em dois processos com o URM original. O valor de gameplay editado para 7 não apareceu nos stores do `.urm`; após load em processo novo, a variável permaneceu em 0 enquanto `vars`/`watched` foram restaurados.
- [Documento 50](50_STORES_LABELS_REPLACEMENTS_E_SNAPSHOTS.md), run [40666090480](https://github.com/mucholocco86/laborat-rio_renpy/actions/runs/40666090480): `labels` e `replacements` também foram serializados e recarregados; uma regra carregada foi aplicada quando o callback de filtro foi chamado diretamente.
- [Mapa dos canais](../06_VARIABLES/03_MAPA_CANAIS_PERSISTENCIA_URM.md): registra também o teste de `textboxCustomizations` e os canais distintos de Settings.

**Conclusão atual:** há runtime observado para esses stores e para o cenário de variável escalar testado. Isso fortalece a conclusão de que o `.urm` armazena dados operacionais/configurações das ferramentas, não um snapshot geral do gameplay. Não prova a exaustividade de stores em arquivos de todas as versões nem a integração visual dos modais.
