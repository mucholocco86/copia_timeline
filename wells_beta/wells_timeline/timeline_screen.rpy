## =============================================================================
## WELLS TIMELINE — timeline_screen.rpy
## =============================================================================

## Atalhos de teclado
init python:
    config.overlay_screens.append("_tl_debug_overlay")

init:
    transform tl_layer_blur:
        blur 48
        matrixcolor SaturationMatrix(0.6)


init python:
    def _tl_capture_hover_pos():
        store._tl_route_hover_pos = renpy.get_mouse_pos()

## =============================================================================
## Timeline — labels auxiliares de salto
## Chamados pela ação Jump() para sair do contexto da tela antes de executar o salto.
## As telas são ocultadas pela lista de ações antes da execução destes labels, para que nenhuma tela modal
## ou sobreposta esteja ativa quando o descongelamento ou carregamento ocorrer.
## Ordem alternativa: snapshot -> pré-save -> save Wells wf_* (aceita o legado _ch_*).
## =============================================================================

label _tl_do_load:
    if getattr(renpy.game, "_tl_pending_snap", None) is not None:
        $ _tl_log("TL do_load: dispatching snapshot unfreeze")
        $ _snap = renpy.game._tl_pending_snap
        $ renpy.game._tl_pending_snap = None
        $ _tl_unfreeze_from_snapshot(_snap)
    elif _tl_load_slot:
        $ _tl_log("TL do_load: dispatching load slot={}".format(_tl_load_slot))
        $ renpy.load(_tl_load_slot)
    else:
        $ _tl_log("TL do_load: nothing to dispatch (no snap, no slot)")
    return

## =============================================================================
## Tela principal do Timeline
## =============================================================================

screen timeline():
    modal True
    zorder 200

    default tl_view            = "cards"   ## valores da tela: "cards" (cartões) | "route" (rotas)
    default tl_route_expanded  = False
    default tl_route_hover     = None
    default _tl_locked_count   = _tl_count_locked_branches()


    add tl_layer_blur
    add Solid("#111111cc")
    add _tl_noise_bg()

    python:
        _tl_window_small = renpy.variant("small")
        _tl_window_w = wells_ui(1800 if _tl_window_small else 1650)
        _tl_window_h = wells_ui(1150 if _tl_window_small else 920)
        _tl_window_padding = (wells_ui_pad(60, 50) if _tl_window_small
                              else wells_ui_pad(50, 40))
        _tl_content_w = max(1, _tl_window_w - wells_ui(120 if _tl_window_small else 100))

    frame:
        xalign 0.5
        yalign 0.4
        xsize _tl_window_w
        ysize _tl_window_h
        padding _tl_window_padding
        background Frame("wells/timeline/gui/frame.png", 10, 10)

        vbox:
            xfill True yfill True
            spacing 0

            frame:
                style "tl_frame_base"
                xfill True
                background Solid(TL["header_bg"])
                padding wells_ui_pad(40, 20)

                hbox:
                    xfill True
                    spacing 0
                    yalign 0.5

                    vbox:
                        spacing 4
                        text "TIMELINE":
                            style "tl_base_bold"
                            size TL_SIZE_TITLE
                            color TL["header_text"]
                        text ("Rastreamento de Rotas" if tl_view == "route" else "Histórico de Escolhas"):
                            style "tl_base"
                            size TL_SIZE_BODY
                            color TL["header_sub"]

                    null xfill True

                    ## ── Alternância entre rotas e cartões ───────────────────────────────
                    python:
                        _tl_btn_cards_color = TL["header_text"] if tl_view == "cards" else TL["header_sub"]
                        _tl_btn_route_color = TL["header_text"] if tl_view == "route" else TL["header_sub"]

                    hbox:
                        spacing 8
                        yalign 0.5

                        button:
                            idle_background Frame("wells/timeline/gui/Button-idle.png", 5, 5)
                            hover_background Frame("wells/timeline/gui/Button-hover.png", 5, 5)
                            padding wells_ui_pad(18, 9, 18,9)
                            action SetScreenVariable("tl_view", "cards")

                            text "Histórico":
                                style "tl_base"
                                size TL_SIZE_SUBTITLE
                                color _tl_btn_cards_color
                                hover_color TL["header_text"]
                                yalign 0.5

                        button:
                            idle_background Frame("wells/timeline/gui/Button-idle.png", 5, 5)
                            hover_background Frame("wells/timeline/gui/Button-hover.png", 5, 5)
                            padding wells_ui_pad(18, 9, 18,9)
                            action SetScreenVariable("tl_view", "route")

                            text "Rotas":
                                style "tl_base"
                                size TL_SIZE_SUBTITLE
                                color _tl_btn_route_color
                                hover_color TL["header_text"]
                                yalign 0.5

                    null xsize 16

                    if tl_view == "route":
                        python:
                            _tl_notifs_on    = getattr(persistent, "_tl_var_notifs_enabled", True)
                            _tl_notifs_label = "Avisos de mudanças ✓" if _tl_notifs_on else "Avisos de mudanças ✗"
                            _tl_notifs_color = TL["header_text"] if _tl_notifs_on else TL["header_sub"]
                        hbox:
                            spacing 8
                            yalign 0.5

                            button:
                                idle_background Frame("wells/timeline/gui/Button-idle.png", 5, 5)
                                hover_background Frame("wells/timeline/gui/Button-hover.png", 5, 5)
                                padding wells_ui_pad(18, 9, 18,9)
                                action ToggleField(persistent, "_tl_var_notifs_enabled")

                                text _tl_notifs_label:
                                    style "tl_base"
                                    size TL_SIZE_SUBTITLE
                                    color _tl_notifs_color
                                    hover_color TL["header_text"]
                                    yalign 0.5

                        null xsize 16

                    python:
                        _tl_playthrough_new = sum(
                            1 for _n in _tl_history if _tl_node_has_new(_n))
                        _tl_show_locked  = _tl_locked_count > 0 or _tl_playthrough_new > 0

                    if _tl_show_locked:
                        null xsize 20
                        vbox:
                            spacing 4
                            yalign 0.5

                            if _tl_playthrough_new > 0:
                                hbox:
                                    spacing 10
                                    yalign 0.5
                                    text "●":
                                        style "tl_icon"
                                        size TL_SIZE_DOT
                                        color "#FFFFFF"
                                        yalign 0.5
                                        italic False
                                    text "{} {} com novos caminhos.".format(
                                            _tl_playthrough_new,
                                            "escolha" if _tl_playthrough_new == 1 else "escolhas"): 
                                        style "tl_base"
                                        size TL_SIZE_BODY
                                        color "#FFFFFF"
                                        yalign 0.5

                            if _tl_locked_count > 0:
                                hbox:
                                    spacing 10
                                    yalign 0.5
                                    text "●":
                                        style "tl_icon"
                                        size TL_SIZE_DOT
                                        color "#FFFFFF"
                                        yalign 0.5
                                        italic False
                                    text "{} {} restante{} para desbloquear.".format(
                                            _tl_locked_count,
                                            "ramo" if _tl_locked_count == 1 else "ramos",
                                            "" if _tl_locked_count == 1 else "s"): 
                                        style "tl_base"
                                        size TL_SIZE_BODY
                                        color "#FFFFFF"
                                        yalign 0.5
                        null xsize 20

                    if persistent._tl_recovery_slot:
                        hbox:
                            spacing 8
                            yalign 0.5
                            button:
                                idle_background Frame("wells/timeline/gui/Button-idle.png", 5, 5)
                                hover_background Frame("wells/timeline/gui/Button-hover.png", 5, 5)
                                padding wells_ui_pad(18, 9, 18,9)
                                action [Function(_tl_cancel_jump), Hide("timeline"), Jump("_tl_do_load")]

                                text "Reverter":
                                    style "tl_base"
                                    size TL_SIZE_BODY
                                    color TL["header_sub"]
                                    hover_color TL["accent"]
                                    yalign 0.5

                    null xsize wells_ui(14)

                    hbox:
                        spacing 8
                        yalign 0.5
                        button:
                            padding wells_ui_pad(0, 0, 0, 0)
                            xysize (wells_ui(100), wells_ui(40))
                            idle_background Frame("wells/timeline/gui/Button-idle.png", 5, 5)
                            hover_background Frame("wells/timeline/gui/Button-hover.png", 5, 5)
                            action [Function(renpy.layer_at_list, [], layer="master"), Hide("timeline")]
                            text _("Fechar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

            frame:
                style "tl_frame_base"
                xfill True ysize 3
                background Solid("#FFFFFF")

            if tl_view == "route":
                use tl_route(tl_route_expanded, tl_route_hover, _tl_content_w)

            elif not _tl_history:
                frame:
                    style "tl_frame_base"
                    xfill True yfill True
                    background None

                    vbox:
                        xalign 0.5 yalign 0.5
                        spacing 12
                        text "Nenhuma escolha foi registrada ainda.":
                            style "tl_base_bold"
                            size TL_SIZE_BODY
                            color TL["header_text"]
                            xalign 0.5
                        text "O Timeline registra as escolhas a partir do momento em que foi instalado.":
                            style "tl_base"
                            size TL_SIZE_BODY
                            color TL["header_sub"]
                            xalign 0.5
                        text "Continue jogando para ver suas escolhas aqui.":
                            style "tl_base"
                            size TL_SIZE_BODY
                            color TL["header_sub"]
                            xalign 0.5
            else:
                side "c r":
                    xfill True yfill True
                    spacing 18

                    viewport:
                        id "tl_history_vp"
                        xfill True yfill True
                        mousewheel True
                        draggable True
                        yadjustment ui.adjustment(value=999999)

                        python:
                            _tl_side_pad = wells_ui(40)
                            _tl_spacing  = wells_ui(16)
                            _tl_avail    = max(1, _tl_content_w - (_tl_side_pad * 2))
                            _tl_min_card = wells_ui(160)
                            _tl_max_cols = (_tl_avail + _tl_spacing) // (_tl_min_card + _tl_spacing)
                            if _tl_max_cols < 1: _tl_max_cols = 1
                            _tl_cols     = _tl_max_cols if _tl_max_cols < 5 else 5
                            _tl_card_w   = (_tl_avail - (_tl_spacing * (_tl_cols - 1))) // _tl_cols
                            ## Agrupa o histórico em linhas de cartões.
                            _tl_items = []
                            _tl_cur_row = []
                            try:
                                for _n in _tl_history:
                                    _tl_cur_row.append(_n)
                                    if len(_tl_cur_row) == _tl_cols:
                                        _tl_items.append(list(_tl_cur_row))
                                        _tl_cur_row = []
                                if _tl_cur_row:
                                    _tl_items.append(list(_tl_cur_row))
                            except Exception as _build_err:
                                _tl_log("TL screen ERROR building items: {}".format(_build_err))

                        frame:
                            style "tl_frame_base"
                            xfill True
                            padding wells_ui_pad(40, 30)
                            background None

                            vbox:
                                xfill True
                                spacing _tl_spacing

                                for _row in _tl_items:
                                    hbox:
                                        spacing _tl_spacing

                                        for _node in _row:
                                            use tl_card(_node, _tl_card_w)

                                        python:
                                            _tl_pad_count = _tl_cols - len(_row)
                                        for _p in range(_tl_pad_count):
                                            null xsize _tl_card_w
                    vbar:
                        value YScrollValue("tl_history_vp")
                        top_bar Frame("wells/timeline/gui/vertical_cheia.png", 0, 0)
                        bottom_bar Frame("wells/timeline/gui/vertical_vazia.png", 0, 0)
                        thumb Frame("wells/timeline/gui/v_pino.png", 10, 0) xsize wells_ui(20)


    if _tl_modal_node is not None:
        use tl_modal(_tl_modal_node)

    ## ── Dica de rota — acompanha o cursor; fica no nível da tela para xpos/ypos funcionar
    if tl_view == "route" and tl_route_hover is not None:
        python:
            _tt_hx, _tt_hy = getattr(store, "_tl_route_hover_pos", (0, 0))
            _tt_x  = _TL_MIN(_tt_hx + 14, config.screen_width  - 240)
            _tt_y  = _TL_MIN(_tt_hy + 14, config.screen_height - 160)
            _tt_numeric = tl_route_hover in (getattr(persistent, "_tl_var_is_numeric", None) or set())
            _tt_domain  = [] if _tt_numeric else (
                (getattr(persistent, "_tl_var_domain", None) or {}).get(tl_route_hover) or []
            )
            _tt_cur    = str(getattr(store, tl_route_hover, ""))

        if _tt_domain:
            frame:
                style "tl_frame_base"
                background Solid(TL["modal_bg"])
                xpos _tt_x
                ypos _tt_y
                padding (14, 12, 14, 12)
                xsize 220

                vbox:
                    xfill True
                    spacing 10

                    text "Rotas possíveis":
                        style "tl_base_bold"
                        size TL_SIZE_BODY
                        color TL["header_text"]

                    frame:
                        style "tl_frame_base"
                        xfill True
                        ysize 1
                        background Solid(TL["header_sub"] + "44")

                    vbox:
                        xfill True
                        spacing 4
                        for _tt_val in _tt_domain:
                            python:
                                _tt_is_cur    = (_tt_val == _tt_cur)
                                _tt_val_color = TL["header_text"] if _tt_is_cur else TL["header_sub"]

                            hbox:
                                xfill True
                                spacing 6
                                xalign 0.5
                                yalign 0.5

                                if _tt_is_cur:
                                    text "→":
                                        style "tl_base"
                                        size TL_SIZE_BODY
                                        color _tt_val_color
                                        yalign 0.5
                                else:
                                    null xsize 14

                                text _tl_strip_renpy_tags(_tt_val):
                                    style "tl_base"
                                    size TL_SIZE_BODY
                                    color _tt_val_color
                                    yalign 0.5



## Os cartões ficam em ui/tl_screens.rpy.
## A janela modal fica em ui/tl_screens.rpy.

