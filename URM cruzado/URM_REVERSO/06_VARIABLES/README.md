# Variables and URM stores

- [01 — URM stores, monitoramento e substituição de texto](01_URM_STORES_MONITORAMENTO_E_SUBSTITUICAO_DE_TEXTO.md) — análise estática de `vars`, `watched`, `labels` e `replacements`.
- [02 — Persistência e associação por personagem de `textboxCustomizations`](02_TEXTBOX_CUSTOMIZATIONS_URMFILE_RUNTIME.md) — ciclo de settings temporários e runtime em dois processos Ren'Py 7.4.11 (run 40665541175).

- [03 — Mapa dos canais de persistência do URM X52](03_MAPA_CANAIS_PERSISTENCIA_URM.md) — separa save nativo, arquivo `.urm`, `persistent.URMSettings`, arquivo URM `settings` e snapshots, com os testes runtime relacionados.

## Atualização de revisão — 2026-10-28

O mapa `03` foi conferido contra os testes concluídos: persistência em dois processos para `vars`, `watched`, `textboxCustomizations`, `labels` e `replacements); Settings por jogo/global; diff superficial de Snapshots: mutação in-place não detectada; substituição por conteúdo diferente detectada; conteúdo igual não detectado; comparação expõe valor antigo só para leitura e o atual para edição; variáveis removidas retornam `None` no lado novo e não são recriadas por `setValue`; entre snapshots, ambos os lados são somente leitura; chave ausente e valor real `None` podem aparecer iguais como `None/unknown`. Para os detalhes e limites de cada fixture, consulte o mapa e os documentos 49–53 de Choices, em especial a ampliação runtime do doc 51 e o teste de save nativo do doc 53. O doc 53 comprovou em runtime que o singleton Snapshots não foi restaurado por save/load nativo em processo novo. A revisão transversal está em [00_README/REVISAO_DOCUMENTAL_URM_2026-10-28.md](../00_README/REVISAO_DOCUMENTAL_URM_2026-10-28.md).
