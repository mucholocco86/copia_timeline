## =============================================================================
## WELLS TIMELINE — tl_screens.rpy
## Cartões, sobreposição de depuração, janela modal, rotas e telas de ramos futuros do Timeline.
## As seções consolidadas mantêm a ordem de carregamento anterior.
## =============================================================================

## -----------------------------------------------------------------------------
## Seção 1: ui/tl_cards.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_cards.rpy
## Telas dos cartões: seletor, conteúdo do cartão anterior e conteúdo do cartão atual.
## =============================================================================

## =============================================================================
## Moldura de miniatura compartilhada — usada por tl_card e pelos cartões de ramos futuros.
## img_disp: elemento visual já dimensionado ou None. O chamador é responsável pelo dimensionamento.
## locked/taken/highlighted: estados visuais dos cartões de ramos futuros (todos False/True/False para
## cartões comuns = sem sobreposição).
## fallback_text: exibido quando img_disp é None (somente em cartões comuns).
## =============================================================================

screen tl_thumbnail_frame(cw, th, img_disp=None, locked=False, taken=True, highlighted=False, fallback_text=None):

    frame:
        style "tl_frame_base"
        xsize cw
        ysize th
        background Solid(TL["thumb_bg"])

        if img_disp is not None:
            add img_disp:
                xalign 0.5
                yalign 0.5
        elif fallback_text is not None:
            text fallback_text:
                style "tl_base_bold"
                size TL_SIZE_TITLE
                color "#2a2820"
                xalign 0.5 yalign 0.5

        if locked:
            frame:
                xfill True
                yfill True
                background Solid("#000000bb")
            if _tl_lock_displayable:
                add _tl_lock_displayable:
                    xalign 0.5
                    yalign 0.5
                    xsize 36
                    ysize 36
                    fit "contain"
        elif not taken:
            frame:
                xfill True
                yfill True
                background Solid("#000000aa")

        if highlighted:
            add Solid(TL["accent"]):
                xsize cw
                ysize 3
                yalign 0.0


## =============================================================================
## Tela do cartão
## =============================================================================

screen tl_card(node, cw=300):

    python:
        _tl_is_current = (node["index"] == len(_tl_history) - 1 and
                            node.get("chosen_index") is None)
        _tl_img_name   = node.get("img_name")
        _tl_use_thumb_first = bool(_tl_img_name and _tl_img_name_is_movie(_tl_img_name))
        _tl_thumb      = _tl_node_thumb(node) if (not _tl_img_name or _tl_use_thumb_first) else None
        _tl_has_thumb  = _tl_img_name is not None or _tl_thumb is not None
        _tl_thumb_h    = int(cw * 9 / 16)
        ## Resolve para um único elemento visual já dimensionado para tl_thumbnail_frame.
        _tl_img_disp   = None
        if _tl_img_name and not (_tl_use_thumb_first and _tl_thumb):
            _tl_img_disp = _tl_img_thumb_displayable(_tl_img_name, cw, _tl_thumb_h, "cover")
        elif _tl_thumb:
            _tl_img_disp = Transform(
                _tl_thumb_displayable(_tl_thumb, node["index"]),
                xsize=cw, ysize=_tl_thumb_h, fit="contain")
        _tl_fallback = "#{:02d}".format(node["index"] + 1) if _tl_img_disp is None else None
        _tl_chosen_label = (
            node["options"][node["chosen_index"]]
            if node.get("chosen_index") is not None
            else None)
        _tl_has_new = _tl_node_has_new(node)

    vbox:
        xsize cw
        spacing 0

        use tl_thumbnail_frame(cw, _tl_thumb_h, img_disp=_tl_img_disp, fallback_text=_tl_fallback)

        if _tl_is_current:
            use tl_card_current(node, cw)
        else:
            use tl_card_past(node, _tl_chosen_label, _tl_has_new, cw)


## =============================================================================
## Conteúdo do cartão anterior
## =============================================================================

screen tl_card_past(node, chosen_label, has_new, cw=300):

    vbox:
        xsize cw
        spacing 0

        frame:
            style "tl_frame_base"
            xsize cw
            padding (12, 10, 12, 10)
            background Solid("#00000044")

            hbox:
                xsize cw - 24
                spacing 8
                yalign 0.5

                text (chosen_label or "—"):
                    style "tl_base"
                    size TL_SIZE_BODY
                    color TL["opt_chosen_fg"]
                    xmaximum cw - 28
                    yalign 0.5

        frame:
            style "tl_frame_base"
            xsize cw ysize 1
            background Solid(TL["divider"])

        python:
            _tl_diverged = node.get("_shadow_orig_chosen") is not None

        hbox:
            xsize cw
            spacing 0

            frame:
                style "tl_frame_base"
                xsize cw // 2
                ysize 46
                padding (12, 0, 8, 0)
                background Solid(TL["footer_bg"])

                if _tl_diverged:
                    text "⎇":
                        style "tl_icon"
                        size TL_SIZE_BODY
                        color TL["header_sub"]
                        yalign 0.5
                        italic False
                elif has_new:
                    text "●":
                        style "tl_icon"
                        size TL_SIZE_DOT
                        color TL["new_dot"]
                        yalign 0.5
                        italic False

            button:
                style "tl_frame_base"
                xsize cw // 2
                ysize 46
                padding (0, 0, 0, 0)
                background Solid(TL["footer_bg"])
                hover_background _tl_hover_gradient_wide
                action SetVariable("_tl_modal_node", node)

                text "Todas as opções ▾":
                    style "tl_base"
                    size TL_SIZE_BODY
                    color TL["btn_text"]
                    xalign 0.5 yalign 0.5


## =============================================================================
## Linha de opção individual — usada por tl_card_current.
## =============================================================================

screen tl_card_option_row(node, i, opt, cw, shadow_ci):

    python:
        _tl_show_dot  = not _tl_option_seen(node, i)
        _tl_is_aid    = (shadow_ci is not None and i == shadow_ci)
        _tl_opt_count = len(node["options"])

    vbox:
        xsize cw
        spacing 0

        frame:
            style "tl_frame_base"
            xsize cw
            padding (12, 8, 12, 8)
            background Solid("#00000033")

            vbox:
                xsize cw - 24
                spacing 3

                hbox:
                    xsize cw - 24
                    spacing 8
                    yalign 0.5

                    ## A seta de auxílio à repetição tem prioridade sobre o indicador de item não visto.
                    if _tl_is_aid:
                        text "→":
                            style "tl_icon"
                            size TL_SIZE_BODY
                            color TL["header_sub"]
                            yalign 0.5
                            italic False
                    elif _tl_show_dot:
                        text "●":
                            style "tl_icon"
                            size TL_SIZE_DOT
                            color TL["opt_new_dot"]
                            yalign 0.5
                            italic False
                    else:
                        null xsize 14

                    text opt:
                        style "tl_base"
                        size TL_SIZE_BODY
                        color TL["opt_fg"]
                        xmaximum cw - 44
                        yalign 0.5


        if i < _tl_opt_count - 1:
            frame:
                style "tl_frame_base"
                xsize cw ysize 1
                background Solid(TL["divider"])


## =============================================================================
## Conteúdo do cartão atual — todas as opções em linhas
## =============================================================================

screen tl_card_current(node, cw=300):

    python:
        _shadow_ci = _tl_shadow_match(_tl_shadow_path or [], node)

    vbox:
        xsize cw
        spacing 0

        for _i, _opt in enumerate(node["options"]):
            use tl_card_option_row(node, _i, _opt, cw, _shadow_ci)

        frame:
            style "tl_frame_base"
            xsize cw
            padding (0, 6, 10, 6)
            background None

            frame:
                style "tl_frame_base"
                padding (10, 5, 10, 5)
                background Solid(TL["accent"])
                xalign 0.0

                text "AGORA":
                    style "tl_base_bold"
                    size TL_SIZE_BODY
                    color "#1a1408"
                    italic False

## -----------------------------------------------------------------------------
## Seção 2: ui/tl_debug.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_debug.rpy
## Sobreposição de depuração e linhas de dados de depuração.
## =============================================================================

default _tl_debug_visible = False

screen _tl_debug_overlay():
    if _tl_debug_visible:
        use tl_debug()

screen tl_debug():
    zorder 999
    modal False

    drag:
        drag_name "tl_debug"
        xpos 10 ypos 10

        frame:
            style "tl_frame_base"
            background Solid("#000000dd")
            padding (14, 12, 14, 12)
            xsize 440

            vbox:
                xfill True
                spacing 5

                hbox:
                    xfill True
                    text "TIMELINE — DEPURAÇÃO":
                        style "tl_base_bold"
                        size TL_SIZE_BODY
                        color "#a5b4fc"
                        xfill True
                    button:
                        style "tl_frame_base"
                        background None
                        hover_background None
                        padding (0, 0, 0, 0)
                        yalign 0.0
                        action ToggleVariable("_tl_debug_visible")
                        text "✕":
                            style "tl_icon"
                            size TL_SIZE_BODY
                            color "#64748b"
                            hover_color "#f1f5f9"

                null ysize 4
                use tl_dbrow("RenPy", "{}.{}.{}".format(renpy.version_tuple[0], renpy.version_tuple[1], renpy.version_tuple[2]))
                use tl_dbrow("node_count",  str(_tl_node_count))
                use tl_dbrow("history len", str(len(_tl_history)))
                use tl_dbrow("ast_ready",   str(_tl_ast_ready))
                use tl_dbrow("ast_menus",   str(len(_tl_ast_map)))

                null ysize 4
                if _tl_history:
                    python:
                        _dbnode = _tl_history[-1]
                    text "ÚLTIMO NÓ":
                        style "tl_base_bold"
                        size 16
                        color "#fb923c"
                    use tl_dbrow("prompt",  (_dbnode["prompt"] or "(none)")[:50])
                    use tl_dbrow("chosen",  str(_dbnode.get("chosen_index")))
                    use tl_dbrow("options", str(len(_dbnode["options"])))
                    use tl_dbrow("thumb",   "{}b".format(len(_tl_node_thumb(_dbnode) or b"")) if _tl_node_thumb(_dbnode) else "none")
                    use tl_dbrow("ast_key", str(_dbnode.get("ast_key")))

                null ysize 8
                textbutton "Exportar AST da CFG (tudo)":
                    style "tl_frame_base"
                    background Solid("#1e293b")
                    hover_background Solid("#334155")
                    padding (8, 6, 8, 6)
                    action Function(_tl_cfg_dump_ast)
                    text_style "tl_base"
                    text_size TL_SIZE_DOT
                    text_color "#7dd3fc"
                    text_hover_color "#ffffff"

                null ysize 4
                textbutton "Recuperar ast_keys do histórico":
                    style "tl_frame_base"
                    background Solid("#1e293b")
                    hover_background Solid("#334155")
                    padding (8, 6, 8, 6)
                    action Function(_tl_salvage_history_ast_keys)
                    text_style "tl_base"
                    text_size TL_SIZE_DOT
                    text_color "#7dd3fc"
                    text_hover_color "#ffffff"

                null ysize 4
                text "Use o botão ✕ para ocultar":
                    style "tl_base"
                    size TL_SIZE_DOT
                    color "#334155"

screen tl_dbrow(label, value):
    hbox:
        spacing 8
        text (label + ":"):
            style "tl_base"
            size TL_SIZE_BADGE
            color "#64748b"
            xminimum 120
        text value:
            style "tl_base"
            size TL_SIZE_DOT
            color "#e2e8f0"

## -----------------------------------------------------------------------------
## Seção 3: ui/tl_ghost_cards.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## Cartão de ramo futuro — um ramo de um nó If.
## =============================================================================

screen tl_ghost_card(ghost, bi, cw, th):

    python:
        _gbc_ast    = _tl_ghost_ast(ghost["ast_key"])
        _gbc_taken  = (bi == ghost.get("taken_index"))
        _gbc_sfns   = _gbc_ast.get("seen_fns") or ghost.get("seen_fns") or []
        _gbc_sfn    = _gbc_sfns[bi] if bi < len(_gbc_sfns) else None
        _gbc_eval   = _tl_eval_seen_fn(_gbc_sfn) if _gbc_sfn else False
        _gbc_seen   = _gbc_taken or _gbc_eval
        _gbc_locked = not _gbc_taken and not _gbc_seen
        _gbc_imgs   = ghost.get("branch_imgs") or []
        _gbc_img    = _gbc_imgs[bi] if bi < len(_gbc_imgs) else None
        _gbc_img_disp = Transform(
            _gbc_img, xsize=cw, ysize=th, fit="cover",
        ) if _gbc_img else None
        _gbc_cond   = _tl_prettify_condition((_gbc_ast.get("conditions") or ghost.get("conditions") or ["?"])[bi])

    vbox:
        xsize cw
        spacing 0

        use tl_thumbnail_frame(cw, th,
            img_disp=_gbc_img_disp,
            locked=_gbc_locked,
            taken=_gbc_taken,
            highlighted=False,
        )

        ## Barra inferior: rótulo da condição
        frame:
            style "tl_frame_base"
            xsize cw
            padding (12, 8, 12, 8)
            background Solid("#00000044")

            text _gbc_cond:
                style "tl_base"
                size TL_SIZE_BODY
                color TL["opt_fg"]
                substitute False
                xmaximum cw - 24
                yalign 0.5


## =============================================================================
## Linhas de ramos futuros — exibidas abaixo dos cartões principais do Timeline.
## =============================================================================

screen tl_ghost_rows(ghost_nodes, card_w, cols, spacing, reverse_clusters=False):
    if ghost_nodes:
        vbox:
            spacing spacing
            ## Separador discreto entre a última linha do Timeline e as linhas de ramos futuros
            frame:
                style "tl_frame_base"
                xsize cols * card_w + (cols - 1) * spacing
                ysize 3
                background Solid(TL["divider"])
            python:
                _tl_gbc_th = int(card_w * 9 / 16)
                ## Opcionalmente inverte a ordem dos grupos (mais recente primeiro), mantendo
                ## inalterada a ordem dos cartões dentro de cada grupo.
                if reverse_clusters:
                    _tl_gbc_clusters = []
                    for _gbc_g in ghost_nodes:
                        if not _tl_gbc_clusters or not _gbc_g.get("cluster_with_prev", False):
                            _tl_gbc_clusters.append([])
                        _tl_gbc_clusters[-1].append(_gbc_g)
                    _tl_gbc_ordered = []
                    for _cl in reversed(_tl_gbc_clusters):
                        _tl_gbc_ordered.extend(_cl)
                else:
                    _tl_gbc_ordered = list(ghost_nodes)
                ## Achata para: (ghost, branch_idx, needs_sep)
                ## needs_sep: True = insere um divisor fino antes deste cartão.
                ## Suprimido para o primeiro item de cada linha.
                _tl_gbc_flat = []
                for _gbc_gi, _gbc_g in enumerate(_tl_gbc_ordered):
                    _gbc_cluster_sep = (
                        _gbc_gi > 0 and
                        not _gbc_g.get("cluster_with_prev", False)
                    )
                    for _gbc_bi in range(len(_tl_ghost_ast(_gbc_g["ast_key"]).get("conditions") or _gbc_g.get("conditions") or [])):
                        _tl_gbc_flat.append((
                            _gbc_g, _gbc_bi,
                            _gbc_cluster_sep and _gbc_bi == 0
                        ))
                ## Divide em linhas; cada uma contém uma lista linear de (ghost, bi, is_start).
                ## is_start = True no primeiro cartão da linha ou no primeiro cartão de um novo grupo.
                _tl_gbc_rows = []
                for _gbc_ri in range(0, len(_tl_gbc_flat), cols):
                    _gbc_chunk = _tl_gbc_flat[_gbc_ri:_gbc_ri + cols]
                    _gbc_row   = []
                    for _gbc_ci, (_gbc_g, _gbc_bi, _gbc_sep) in enumerate(_gbc_chunk):
                        _gbc_row.append((_gbc_g, _gbc_bi, _gbc_ci == 0 or _gbc_sep))
                    _tl_gbc_rows.append(_gbc_row)

            vbox:
                spacing spacing
                for _tl_gbc_row in _tl_gbc_rows:
                    hbox:
                        spacing 0
                        for _gbc_ri2, (_gbc_ghost, _gbc_bi, _gbc_start) in enumerate(_tl_gbc_row):

                            ## Espaço antes de cada cartão, exceto o primeiro.
                            ## Preenchido com a cor de destaque quando pertence ao mesmo grupo do cartão anterior.
                            if _gbc_ri2 > 0:
                                if _gbc_start:
                                    ## Moldura transparente — null não é renderizado dentro de if/for aninhados no Ren'Py.
                                    frame:
                                        style "tl_frame_base"
                                        xsize spacing
                                        ysize _tl_gbc_th + 42
                                        background Solid("#00000000")
                                else:
                                    frame:
                                        style "tl_frame_base"
                                        xsize spacing
                                        ysize _tl_gbc_th + 42
                                        background Solid(TL["accent"] + "2a")

                            use tl_ghost_card(_gbc_ghost, _gbc_bi, card_w, _tl_gbc_th)

                        python:
                            _gbc_pad = cols - len(_tl_gbc_row)
                        for _p in range(_gbc_pad):
                            null xsize (spacing + card_w)

## -----------------------------------------------------------------------------
## Seção 4: ui/tl_modal.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_modal.rpy
## Sobreposição modal: lista completa de opções com miniatura, exibida ao selecionar "Todas as opções ▾".
## =============================================================================

## =============================================================================
## Linha de opção individual — usada por tl_modal com ou sem rolagem.
## =============================================================================

screen tl_modal_option_row(node, i, opt, m_w, opt_count):

    python:
        _tl_is_chosen = (node.get("chosen_index") == i)
        _tl_show_dot  = not _tl_option_seen(node, i) and not _tl_is_chosen
        _tl_shadow_ci = node.get("_shadow_orig_chosen")
        if _tl_shadow_ci is None:
            _tl_shadow_ci = _tl_shadow_match(_tl_shadow_path or [], node)
        _tl_is_aid = (_tl_shadow_ci is not None and i == _tl_shadow_ci and not _tl_is_chosen)

    vbox:
        xfill True
        spacing 0

        button:
            xfill True
            padding (16, 12, 16, 12)
            background None
            hover_background _tl_hover_gradient
            action [Function(_tl_jump, node["index"], i), Hide("tl_modal"), Hide("timeline"), Jump("_tl_do_load")]

            hbox:
                xfill True
                spacing 10
                yalign 0.5

                if _tl_is_chosen:
                    text "→":
                        style "tl_icon"
                        size TL_SIZE_BODY
                        color TL["opt_chosen_fg"]
                        yalign 0.5
                elif _tl_is_aid:
                    text "→":
                        style "tl_icon"
                        size TL_SIZE_BODY
                        color TL["header_sub"]
                        yalign 0.5
                        italic False
                elif _tl_show_dot:
                    text "●":
                        style "tl_icon"
                        size TL_SIZE_DOT
                        color TL["opt_new_dot"]
                        yalign 0.5
                        italic False
                else:
                    null xsize 13

                text opt:
                    style "tl_base"
                    size TL_SIZE_BODY
                    color TL["opt_fg"]
                    xmaximum m_w - 60
                    yalign 0.5

        if i < opt_count - 1:
            frame:
                style "tl_frame_base"
                xfill True ysize 2
                padding (20, 0, 20, 0)
                background None

                frame:
                    style "tl_frame_base"
                    xfill True ysize 1
                    background Solid(TL["divider"])


screen tl_modal(node):
    modal True
    zorder 300


    frame:
        style "tl_frame_base"
        xfill True yfill True
        background Solid("#000000aa")

        button:
            style "tl_frame_base"
            xfill True yfill True
            background None
            action SetVariable("_tl_modal_node", None)

    python:
        _tl_m_w         = 500
        _tl_m_pad       = 28
        _tl_m_img_name  = node.get("img_name")
        _tl_m_use_thumb_first = bool(_tl_m_img_name and _tl_img_name_is_movie(_tl_m_img_name))
        _tl_m_thumb     = _tl_node_thumb(node) if (not _tl_m_img_name or _tl_m_use_thumb_first) else None
        _tl_m_has_thumb = _tl_m_img_name is not None or _tl_m_thumb is not None
        _tl_m_thumb_w   = _tl_m_w - (_tl_m_pad * 2)
        _tl_m_thumb_h   = int(_tl_m_thumb_w * 9 / 16)
        _tl_m_img_disp = None
        _tl_m_tdisp = None
        if _tl_m_img_name and not (_tl_m_use_thumb_first and _tl_m_thumb):
            _tl_m_img_disp = _tl_img_thumb_displayable(_tl_m_img_name, _tl_m_thumb_w, _tl_m_thumb_h, "cover")
        elif _tl_m_has_thumb and _tl_m_thumb:
            _tl_m_tdisp = _tl_thumb_displayable(_tl_m_thumb, node["index"])
        _tl_m_row_h        = 52
        _tl_m_opt_count    = len(node.get("options", []))
        _tl_m_list_h       = _tl_m_opt_count * (_tl_m_row_h + 2)
        _tl_m_max_list     = 300
        _tl_m_needs_scroll = _tl_m_list_h > _tl_m_max_list


    frame:
        xsize _tl_m_w + 32
        xalign 0.5
        yalign 0.45
        background None
        padding (0,0,0,0)

        frame:
            style "tl_frame_base"
            xfill True
            background Solid("#111111cc")
            padding (28, 16, 28, 16)

            vbox:
                xfill True
                spacing 0

                frame:
                    style "tl_frame_base"
                    xfill True
                    padding (8, 2, 8, 2)
                    background None

                    button:
                        style "tl_frame_base"
                        xalign 1.0
                        background None
                        hover_background Solid("#ffffff14")
                        padding (12, 6, 12, 6)
                        action SetVariable("_tl_modal_node", None)

                        text "✕":
                            style "tl_icon"
                            size TL_SIZE_BODY
                            color TL["btn_text"]
                            hover_color TL["header_text"]
                            italic False

                frame:
                    style "tl_frame_base"
                    xfill True
                    padding (28, 16, 28, 16)
                    background None

                    vbox:
                        xfill True
                        spacing 0

                        if _tl_m_has_thumb:
                            frame:
                                style "tl_frame_base"
                                xfill True
                                ysize _tl_m_thumb_h
                                background Solid(TL["thumb_bg"])
                                padding (0, 0, 0, 0)

                                if _tl_m_img_disp is not None:
                                    add _tl_m_img_disp
                                elif _tl_m_tdisp is not None:
                                    add _tl_m_tdisp:
                                        ysize _tl_m_thumb_h
                                        fit "cover"
                                        xalign 0.5
                                        yalign 0.5

                        frame:
                            style "tl_frame_base"
                            xfill True
                            padding (0, 28, 0, 12)
                            background None

                            text "Todas as opções":
                                style "tl_base_bold"
                                size TL_SIZE_HEADER
                                color TL["modal_header"]

                        frame:
                            style "tl_frame_base"
                            xfill True ysize 3
                            background Solid(TL["divider"])

                        frame:
                            style "tl_frame_base"
                            xfill True ysize 10
                            background None

                        if _tl_m_needs_scroll:
                            viewport:
                                xfill True
                                ysize _tl_m_max_list
                                mousewheel True
                                draggable True

                                vbox:
                                    xfill True
                                    spacing 0

                                    for _i, _opt in enumerate(node["options"]):
                                        use tl_modal_option_row(node, _i, _opt, _tl_m_w, _tl_m_opt_count)

                        else:
                            vbox:
                                xfill True
                                spacing 0

                                for _i, _opt in enumerate(node["options"]):
                                    use tl_modal_option_row(node, _i, _opt, _tl_m_w, _tl_m_opt_count)

                        null ysize 14

## -----------------------------------------------------------------------------
## Seção 5: ui/tl_route_screen.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_route_screen.rpy
## Tela de rotas: barra de etiquetas com os valores atuais das variáveis acompanhadas no store.
## =============================================================================

## =============================================================================
## Tela de avisos do mod — separada da tela notify do jogo para
## não interferir nos avisos do jogo.
##
## Fonte: grupo de fontes que usa a fonte padrão do jogo para todos os caracteres, com
## DejaVuSans substituindo apenas os caracteres de seta e marcador que talvez faltem na fonte do jogo.
## Isso evita alternâncias de fonte com a tag {font=} (que desalinhavam a linha de base)
## e mantém a renderização correta em jogos cujas fontes já contêm esses glifos.
## =============================================================================


transform _tl_notify_appear:
    on show:
        alpha 0
        linear .25 alpha 1.0
    on hide:
        linear .5 alpha 0.0

screen _tl_notify(message):
    zorder 100
    style_prefix "notify"
    frame at _tl_notify_appear:
        text "[message!t]":
            font _tl_fontgroup
    timer 3.25 action Hide('_tl_notify')


## =============================================================================
## Conteúdo da tela de rotas — barra de etiquetas
## =============================================================================

screen tl_route(tl_route_expanded, tl_route_hover, panel_width=None):
    ## Bloqueia rollback/avanço para que a roda do mouse não feche a tela
    key "rollback"   action NullAction()
    key "rollforward" action NullAction()

    default _tl_route_chips = _tl_build_route_chips()

    python:
        _tl_chip_h      = wells_ui(36)
        _tl_chip_gap    = wells_ui(10)
        _TL_ROUTE_FOLD  = 24
        _tl_side_pad    = wells_ui(40)
        _tl_panel_width = panel_width if panel_width is not None else config.screen_width
        _tl_avail       = max(1, _tl_panel_width - (_tl_side_pad * 2))
        _tl_chip_est    = wells_ui(300)   ## largura estimada da etiqueta para calcular as colunas
        _tl_chips_per_row = _TL_MAX(1, (_tl_avail + _tl_chip_gap) // (_tl_chip_est + _tl_chip_gap))
        _tl_chip_w      = (_tl_avail - _tl_chip_gap * (_tl_chips_per_row - 1)) // _tl_chips_per_row
        _tl_key_w       = _tl_chip_w * 55 // 100
        _tl_val_w       = _tl_chip_w - _tl_key_w
        _tl_ghost_vars  = set()
        for _g in (_tl_ghost_nodes or []):
            _tl_ghost_vars.update(_tl_ghost_ast(_g["ast_key"]).get("affecting_vars") or _g.get("affecting_vars") or [])
        _tl_highlighted = _tl_ghost_vars | (getattr(store, "_tl_recently_changed_vars", None) or set())
        _tl_hl_count    = len([1 for _n, _v in _tl_route_chips if _n in _tl_highlighted])
        _tl_hl_rows     = _TL_MAX(3, -(-_tl_hl_count // _tl_chips_per_row)) if _tl_chips_per_row else 3
        _TL_ROUTE_FOLD  = _tl_hl_rows * _tl_chips_per_row
        _tl_card_spacing = wells_ui(16)
        _tl_min_card = wells_ui(160)
        _tl_max_cols = _TL_MAX(1, (_tl_avail + _tl_card_spacing) // (_tl_min_card + _tl_card_spacing))
        _tl_card_cols = _tl_max_cols if _tl_max_cols < 5 else 5
        _tl_card_w   = (_tl_avail - _tl_card_spacing * (_tl_card_cols - 1)) // _tl_card_cols

    if not _tl_route_chips:
        frame:
            style "tl_frame_base"
            xfill True yfill True
            background None

            vbox:
                xalign 0.5 yalign 0.5
                spacing 10

                text "Nenhuma variável de rota foi rastreada ainda.":
                    style "tl_base_bold"
                    size TL_SIZE_BODY
                    color TL["header_text"]
                    xalign 0.5

                text "As variáveis de rota são detectadas nos scripts do jogo na primeira inicialização.":
                    style "tl_base"
                    size TL_SIZE_BODY
                    color TL["header_sub"]
                    xalign 0.5

    else:
        side "c r":
            xfill True yfill True
            spacing 18

            viewport:
                id "tl_route_vp"
                xfill True yfill True
                mousewheel True
                draggable True

                frame:
                    style "tl_frame_base"
                    xfill True
                    background None
                    padding wells_ui_pad(40, 24)

                    vbox:
                        xfill True
                        spacing 4

                        ## ── Barra de etiquetas — linhas calculadas em Python ─────────────────
                        python:
                            _visible_chips = _tl_route_chips if tl_route_expanded \
                                else _tl_route_chips[:_TL_ROUTE_FOLD]
                            _hidden_count  = len(_tl_route_chips) - len(_visible_chips)
                            _chip_rows = [
                                _visible_chips[_i:_i + _tl_chips_per_row]
                                for _i in range(0, len(_visible_chips), _tl_chips_per_row)
                            ]

                        for _crow in _chip_rows:
                            hbox:
                                spacing _tl_chip_gap

                                for _chip_name, _chip_val in _crow:
                                    python:
                                        _chip_key_label = _tl_prettify_var(_chip_name)
                                        _chip_val_label = _tl_strip_renpy_tags(str(_chip_val))
                                        _chip_key_bg    = (TL["accent"] + "44") if _chip_name in _tl_highlighted else TL["btn_hover_bg"]

                                    button:
                                        background None
                                        hover_background None
                                        padding (0, 0, 0, 0)
                                        xsize _tl_chip_w
                                        yminimum _tl_chip_h

                                        action NullAction()
                                        hovered [SetScreenVariable("tl_route_hover", _chip_name), Function(_tl_capture_hover_pos)]
                                        unhovered SetScreenVariable("tl_route_hover", None)

                                        hbox:
                                            spacing 0
                                            yalign 0.5

                                            ## Metade da chave
                                            frame:
                                                style "tl_frame_base"
                                                background Solid(_chip_key_bg)
                                                padding (10, 6, 10, 6)
                                                xmaximum _tl_key_w
                                                yminimum _tl_chip_h

                                                text _chip_key_label:
                                                    style "tl_base"
                                                    size TL_SIZE_BODY
                                                    color TL["btn_text"]
                                                    yalign 0.5

                                            ## Metade do valor
                                            frame:
                                                style "tl_frame_base"
                                                background Solid(TL["btn_bg"])
                                                padding (10, 6, 10, 6)
                                                xmaximum _tl_val_w
                                                yminimum _tl_chip_h

                                                text _chip_val_label:
                                                    style "tl_base"
                                                    size TL_SIZE_BODY
                                                    color TL["header_text"]
                                                    yalign 0.5

                        if _hidden_count > 0:
                            hbox:
                                spacing _tl_chip_gap
                                button:
                                    background Solid(TL["btn_bg"])
                                    hover_background Solid(TL["btn_hover_bg"])
                                    padding (10, 6, 10, 6)
                                    yminimum _tl_chip_h
                                    action SetScreenVariable("tl_route_expanded", True)

                                    text "Ver mais ({})".format(_hidden_count):
                                        style "tl_base"
                                        size TL_SIZE_BODY
                                        color TL["header_sub"]
                                        yalign 0.5

                        elif tl_route_expanded and _TL_ROUTE_FOLD < len(_tl_route_chips):
                            hbox:
                                spacing _tl_chip_gap
                                button:
                                    background Solid(TL["btn_bg"])
                                    hover_background Solid(TL["btn_hover_bg"])
                                    padding (10, 6, 10, 6)
                                    yminimum _tl_chip_h
                                    action SetScreenVariable("tl_route_expanded", False)

                                    text "Mostrar menos":
                                        style "tl_base"
                                        size TL_SIZE_BODY
                                        color TL["header_sub"]
                                        yalign 0.5

                        frame:
                            background None
                            xfill True
                            ysize 24

                        ## ── Cartões de ramos futuros ───────────────────────────────────────────
                        use tl_ghost_rows(_tl_ghost_nodes, _tl_card_w, _tl_card_cols, _tl_card_spacing, True)

                        frame:
                            background None
                            xfill True
                            ysize 8

            vbar:
                value YScrollValue("tl_route_vp")
                top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)
                bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0)
                thumb Frame("wells/gui/v_pino.png", 10, 0) xsize wells_ui(20)

