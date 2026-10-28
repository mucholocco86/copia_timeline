init python:
    def wells_saveload_initial_page():
        page = getattr(persistent, "wells_saveload_page", None)
        if page is None:
            page = persistent._file_page

        if page in ("auto", "quick"):
            return page

        try:
            return str(max(1, int(page)))
        except (TypeError, ValueError):
            return "1"

    def wells_saveload_page_step(page, amount):
        """Change the Wells screen page without touching Ren'Py's global page."""
        if page == "auto":
            if amount > 0:
                return "quick" if config.has_quicksave else "1"
            return page

        if page == "quick":
            if amount > 0:
                return "1"
            return "auto" if config.has_autosave else page

        try:
            page_number = int(page)
        except (TypeError, ValueError):
            page_number = 1

        if amount < 0 and page_number == 1:
            if config.has_quicksave:
                return "quick"
            if config.has_autosave:
                return "auto"

        return str(max(1, page_number + amount))


################################################################################
## MODULE: wells_saveload.rpy (PARTE 1: TELA DE SALVAMENTO EXCLUSIVA)
################################################################################

screen wells_custom_save():
    modal True
    zorder 199 
    tag menu
    add Solid("#000000aa")

    default wells_page = wells_saveload_initial_page()

    frame:
        xalign 0.5 yalign 0.4
        background Frame("wells/gui/frame_menu.png", 10, 10)
        xsize wells_ui(1450) ysize wells_ui(820) xpadding wells_ui(50) ypadding wells_ui(40)

        fixed:
            xfill True yfill True

            frame:
                xpos wells_ui_signed(0) ypos wells_ui_signed(10)
                background Frame("wells/gui/label_frame.png", 10, 10)
                xpadding wells_ui(30) ypadding wells_ui(8)
                text "SALVAR" size wells_ui(32) color "#ff4444"

            hbox:
                xalign 0.5 ypos wells_ui_signed(10) 
                spacing wells_ui(12)

                # Atalho para Salvamento Automático (A)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_auto_idle.png"
                    hover "wells/gui/button/p_auto_hover.png"
                    selected_idle "wells/gui/button/p_auto_hover.png" # Mantém aceso se for a página atual
                    action [SetScreenVariable("wells_page", "auto"), SetField(persistent, "wells_saveload_page", "auto")]

                # Atalho para Salvamento Rápido (Q)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_quick_idle.png"
                    hover "wells/gui/button/p_quick_hover.png"
                    selected_idle "wells/gui/button/p_quick_hover.png" # Mantém aceso se for a página atual
                    action [SetScreenVariable("wells_page", "quick"), SetField(persistent, "wells_saveload_page", "quick")]

                # Botão Voltar 10 Páginas (<<<)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_menos10_idle.png"
                    hover "wells/gui/button/p_menos10_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, -10)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, -10))]

                # Botão Voltar 1 Página (<<)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_voltar_idle.png"
                    hover "wells/gui/button/p_voltar_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, -1)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, -1))]

                # [MANTIDO] Contador de Página Centralizado (Caixa de texto estilizada que mostra o número)
                frame:
                    yalign 0.5
                    background Frame("wells/gui/button/Button-hover.png", 5, 5)
                    xpadding wells_ui(20) ypadding wells_ui(8)
                    minimum (wells_ui(70), wells_ui(55))
                    if wells_page == "auto":
                        text "A" xalign 0.5 yalign 0.5 size wells_ui(32) color "#2bff00"
                    elif wells_page == "quick":
                        text "Q" xalign 0.5 yalign 0.5 size wells_ui(32) color "#2bff00"
                    else:
                        text " [wells_page]" xalign 0.5 yalign 0.5 size wells_ui(32) color "#2bff00"

                # Botão Avançar 1 Página (>>)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_avancar_idle.png"
                    hover "wells/gui/button/p_avancar_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, 1)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, 1))]

                # Botão Avançar 10 Páginas (>>>)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_mais10_idle.png"
                    hover "wells/gui/button/p_mais10_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, 10)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, 10))]

            side "c r":
                xalign 0.5 ypos wells_ui_signed(95) spacing wells_ui(25) 

                viewport:
                    id "wells_save_slots_vp"
                    xsize wells_ui(1250) ysize wells_ui(565)
                    mousewheel True draggable True

                    grid 3 5:
                        spacing wells_ui(35)

                        for slot in range(1, 16):
                            vbox:
                                xysize (wells_ui(360), wells_ui(262)) spacing wells_ui(5)

                                fixed:
                                    xysize (wells_ui(360), wells_ui(230)) 

                                    button:
                                        xfill True yfill True background Solid("#00000066")
                                        action FileSave(slot, page=wells_page)

                                        if FileLoadable(slot, page=wells_page):
                                            fixed:
                                                xfill True yfill True
                                                frame:
                                                    xfill True yfill True
                                                    background Frame(FileScreenshot(slot, page=wells_page), 0, 0)
                                        else:
                                            frame:
                                                xfill True yfill True
                                                background Frame("wells/gui/slot_vazio.png", 0, 0)

                                    if FileLoadable(slot, page=wells_page):
                                        button:
                                            xpadding 0 ypadding 0 xysize (wells_ui(72), wells_ui(28)) 
                                            idle_background Frame("wells/gui/Button-idle.png", 3, 3)
                                            hover_background Frame("wells/gui/Button-hover.png", 3, 3)
                                            action FileDelete(slot, page=wells_page) 
                                            text _("Delete") xalign 0.5 yalign 0.5 size wells_ui(20) hover_color "#2bff00"

                                if FileLoadable(slot, page=wells_page):
                                    text FileTime(slot, format=_("{#file_time}%d.%m.%Y - %H:%M"), empty=_("Vazio"), page=wells_page) xalign 0.5 size wells_ui(22) color "#2bff00"
                                else:
                                    text "Vazio" xalign 0.5 size wells_ui(22) color "#ffffff"

                vbar:
                    value YScrollValue("wells_save_slots_vp")
                    top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)   
                    bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0) 
                    thumb Frame("wells/gui/v_pino.png", 10, 0) xsize wells_ui(20)                                               

        button:
            xpadding 0 ypadding 0 xysize (wells_ui(180), wells_ui(45)) xalign 0.5 yalign 0.985 
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action [Hide("wells_custom_save")]
            text _("Voltar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

################################################################################
## MODULE: wells_saveload.rpy (PARTE 2: TELA DE CARREGAMENTO EXCLUSIVA)
################################################################################

screen wells_custom_load():
    modal True
    zorder 199 
    tag menu
    add Solid("#000000aa")

    default wells_page = wells_saveload_initial_page()

    frame:
        xalign 0.5 yalign 0.4
        background Frame("wells/gui/frame_menu.png", 10, 10)
        xsize wells_ui(1450) ysize wells_ui(820) xpadding wells_ui(50) ypadding wells_ui(40)

        fixed:
            xfill True yfill True

            frame:
                xpos wells_ui_signed(0) ypos wells_ui_signed(10)
                background Frame("wells/gui/label_frame.png", 10, 10)
                xpadding wells_ui(30) ypadding wells_ui(8)
                text "CARREGAR" size wells_ui(32) color "#ff4444"

            hbox:
                xalign 0.5 ypos wells_ui_signed(10) 
                spacing wells_ui(12)

                # Atalho para Salvamento Automático (A)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_auto_idle.png"
                    hover "wells/gui/button/p_auto_hover.png"
                    selected_idle "wells/gui/button/p_auto_hover.png" # Mantém aceso se for a página atual
                    action [SetScreenVariable("wells_page", "auto"), SetField(persistent, "wells_saveload_page", "auto")]

                # Atalho para Salvamento Rápido (Q)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_quick_idle.png"
                    hover "wells/gui/button/p_quick_hover.png"
                    selected_idle "wells/gui/button/p_quick_hover.png" # Mantém aceso se for a página atual
                    action [SetScreenVariable("wells_page", "quick"), SetField(persistent, "wells_saveload_page", "quick")]

                # Botão Voltar 10 Páginas (<<<)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_menos10_idle.png"
                    hover "wells/gui/button/p_menos10_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, -10)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, -10))]

                # Botão Voltar 1 Página (<<)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_voltar_idle.png"
                    hover "wells/gui/button/p_voltar_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, -1)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, -1))]

                # [MANTIDO] Contador de Página Centralizado (Caixa de texto estilizada que mostra o número)
                frame:
                    yalign 0.5
                    background Frame("wells/gui/button/Button-hover.png", 5, 5)
                    xpadding wells_ui(20) ypadding wells_ui(8)
                    minimum (wells_ui(70), wells_ui(55))
                    if wells_page == "auto":
                        text "A" xalign 0.5 yalign 0.5 size wells_ui(32) color "#2bff00"
                    elif wells_page == "quick":
                        text "Q" xalign 0.5 yalign 0.5 size wells_ui(32) color "#2bff00"
                    else:
                        text " [wells_page]" xalign 0.5 yalign 0.5 size wells_ui(32) color "#2bff00"

                # Botão Avançar 1 Página (>>)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_avancar_idle.png"
                    hover "wells/gui/button/p_avancar_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, 1)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, 1))]

                # Botão Avançar 10 Páginas (>>>)
                imagebutton:
                    yalign 0.5
                    idle "wells/gui/button/p_mais10_idle.png"
                    hover "wells/gui/button/p_mais10_hover.png"
                    action [SetScreenVariable("wells_page", wells_saveload_page_step(wells_page, 10)), SetField(persistent, "wells_saveload_page", wells_saveload_page_step(wells_page, 10))]

            side "c r":
                xalign 0.5 ypos wells_ui_signed(95) spacing wells_ui(25) 

                viewport:
                    id "wells_load_slots_vp"
                    xsize wells_ui(1250) ysize wells_ui(565)
                    mousewheel True draggable True

                    grid 3 5:
                        spacing wells_ui(35)

                        for slot in range(1, 16):
                            vbox:
                                xysize (wells_ui(360), wells_ui(262)) spacing wells_ui(5)

                                fixed:
                                    xysize (wells_ui(360), wells_ui(230)) 

                                    button:
                                        xfill True yfill True background Solid("#00000066")
                                        action FileLoad(slot, page=wells_page)

                                        if FileLoadable(slot, page=wells_page):
                                            fixed:
                                                xfill True yfill True
                                                frame:
                                                    xfill True yfill True
                                                    background Frame(FileScreenshot(slot, page=wells_page), 0, 0)
                                        else:
                                            frame:
                                                xfill True yfill True
                                                background Frame("wells/gui/slot_vazio.png", 0, 0)

                                    if FileLoadable(slot, page=wells_page):
                                        button:
                                            xpadding 0 ypadding 0 xysize (wells_ui(72), wells_ui(28)) 
                                            idle_background Frame("wells/gui/Button-idle.png", 3, 3)
                                            hover_background Frame("wells/gui/Button-hover.png", 3, 3)
                                            action FileDelete(slot, page=wells_page) 
                                            text _("Delete") xalign 0.5 yalign 0.5 size wells_ui(20) hover_color "#2bff00"

                                if FileLoadable(slot, page=wells_page):
                                    text FileTime(slot, format=_("{#file_time}%d.%m.%Y - %H:%M"), empty=_("Vazio"), page=wells_page) xalign 0.5 size wells_ui(22) color "#2bff00"
                                else:
                                    text "Vazio" xalign 0.5 size wells_ui(22) color "#ffffff"

                vbar:
                    value YScrollValue("wells_load_slots_vp")
                    top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)   
                    bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0) 
                    thumb Frame("wells/gui/v_pino.png", 10, 0) xsize wells_ui(20)                                               

        button:
            xpadding 0 ypadding 0 xysize (wells_ui(180), wells_ui(45)) xalign 0.5 yalign 0.985 
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action [Hide("wells_custom_load")]
            text _("Voltar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"
