# ========================================================================
# WELLS FRAMEWORK — WALKTHROUGH UI
# Arquivo: wells_wt_screen.rpy
#
# Responsabilidade exclusiva deste módulo:
# - notificação clicável "Walkthrough" quando existir uma Choice ativa;
# - notificação informativa "Path condition: ...";
# - painel próprio do Walkthrough com viewport vertical;
# - nenhuma execução de Choice e nenhuma alteração de variável do jogo.
#
# Backend utilizado: wells_Walkthrough.rpy
# ========================================================================

screen wf_walkthrough_notification():
    zorder 999

    $ wf_tem_choice = WFWalkthrough.esta_em_choice()
    $ wf_path_condition = WFWalkthrough.path_condition() if not wf_tem_choice else None

    if wf_tem_choice:
        button:
            xpos wells_ui_signed(0)
            ypos wells_ui_signed(130)
            xanchor 0.0
            yanchor 0.0
            padding wells_ui_pad(14, 7, 14, 7)
            background Solid("#0c0c0c80")
            hover_background Solid("#0c0c0cb8")
            action Show("wf_walkthrough_panel")

            text "Walkthrough 🔎":
                size wells_ui(25)
                color "#00ff00"
                hover_color "#7dff7d"
                xalign 0.5
                text_align 0.5
                if persistent.wells_force_outline:
                    outlines [(absolute(2), "#000000", 0, 0)]

    elif wf_path_condition:
        button:
            xpos wells_ui_signed(0)
            ypos wells_ui_signed(130)
            xanchor 0.0
            yanchor 0.0
            padding wells_ui_pad(14, 7, 14, 7)
            background Solid("#0c0c0c80")
            hover_background Solid("#0c0c0cb8")
            action Show("wf_path_panel", wf_path_token=WFWalkthrough.path_token())

            text "Path 🔀":
                size wells_ui(25)
                color "#00ff00"
                hover_color "#7dff7d"
                xalign 0.5
                text_align 0.5
                substitute False
                if persistent.wells_force_outline:
                    outlines [(absolute(2), "#000000", 0, 0)]


screen wf_path_panel(wf_path_token=None):
    modal False
    zorder 1002

    $ wf_path_now = WFWalkthrough.path_condition()
    $ wf_path_details = WFWalkthrough.path_details()
    $ wf_path_current_token = WFWalkthrough.path_token()

    # O painel pertence somente ao instante em que o Path foi aberto.
    # Qualquer avanço, rollback, mudança de cena/choice ou desaparecimento
    # da notificação muda o token/estado e fecha o painel na interação seguinte.
    if (not wf_path_now) or WFWalkthrough.esta_em_choice() or (wf_path_token != wf_path_current_token):
        timer 0.01 action Hide("wf_path_panel")

    # Clique em qualquer área fora do conteúdo fecha imediatamente.
    button:
        xfill True
        yfill True
        background Solid("#00000001")
        hover_background Solid("#00000001")
        action Hide("wf_path_panel")

    frame:
        xalign 0.5
        yalign 0.5
        xsize wells_ui(840)
        ymaximum wells_ui(520)
        padding wells_ui_pad(24, 20, 24, 22)
        background Solid("#0c0c0cee")

        vbox:
            xfill True
            spacing wells_ui(12)

            fixed:
                xfill True
                ysize wells_ui(44)

                text "Path Detection 🔀":
                    xalign 0.0
                    yalign 0.5
                    size wells_ui(30)
                    color "#00ff00"
                    if persistent.wells_force_outline:
                        outlines [(absolute(2), "#000000", 0, 0)]

                button:
                    padding wells_ui_pad(0, 0, 0, 0)
                    xysize (wells_ui(180), wells_ui(45))
                    xalign 1.0
                    yalign 0.5
                    idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                    hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                    action Hide("wf_path_panel")

                    text _("Fechar"):
                        xalign 0.5
                        yalign 0.5
                        size wells_ui(22)
                        hover_color "#2bff00"

            frame:
                xfill True
                background Solid("#00000038")
                padding wells_ui_pad(14, 10, 14, 10)
                side "c r":
                    viewport:
                        id "vp_path_details"
                        xfill True
                        ymaximum wells_ui(400)
                        mousewheel True
                        draggable True
                        arrowkeys True

                        vbox:
                            xfill True
                            spacing wells_ui(10)

                            if wf_path_details:
                                for wf_path_item in wf_path_details:
                                    frame:
                                        xfill True
                                        background Solid("#141414c8")
                                        padding wells_ui_pad(14, 10, 14, 12)

                                        vbox:
                                            xfill True
                                            spacing wells_ui(6)

                                            text ("✓ " if wf_path_item['selected'] else "• ") + wf_path_item['condition']:
                                                size wells_ui(25)
                                                color ("#ffffff" if wf_path_item['selected'] else "#bdbdbd")
                                                substitute False
                                                if persistent.wells_force_outline:
                                                    outlines [(absolute(2), "#000000", 0, 0)]

                                            if wf_path_item['guide']:
                                                text wf_path_item['guide']:
                                                    size wells_ui(22)
                                                    color "#ffffff"
                                                    substitute False
                                                    if persistent.wells_force_outline:
                                                        outlines [(absolute(2), "#000000", 0, 0)]
                            else:
                                text "No additional path details":
                                    xalign 0.5
                                    size wells_ui(24)
                                    color "#aaaaaa"


                    vbar:
                        value YScrollValue("vp_path_details")
                        top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)
                        bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0)
                        thumb Frame("wells/gui/v_pino.png", 10, 10)
                        xsize wells_ui(20)

screen wf_walkthrough_panel():
    modal True
    zorder 1001

    $ wf_choices_panel = WFWalkthrough.escolhas_visiveis()

    frame:
        xfill True
        yfill True
        background Solid("#00000066")

    frame:
        xalign 0.5
        yalign 0.5
        xsize wells_ui(1280)
        ysize wells_ui(820)
        padding wells_ui_pad(22, 18, 22, 20)
        background Solid("#0c0c0ce8")

        vbox:
            spacing wells_ui(12)

            fixed:
                xfill True
                ysize wells_ui(48)

                text "Walkthrough 🔎":
                    xalign 0.5
                    yalign 0.5
                    size wells_ui(30)
                    color "#00ff00"
                    if persistent.wells_force_outline:
                        outlines [(absolute(2), "#000000", 0, 0)]

                button:
                    padding wells_ui_pad(0, 0, 0, 0)
                    xysize (wells_ui(180), wells_ui(45))
                    xalign 1.0
                    yalign 0.5
                    idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                    hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                    action Hide("wf_walkthrough_panel")

                    text _("Fechar"):
                        xalign 0.5
                        yalign 0.5
                        size wells_ui(22)
                        hover_color "#2bff00"

            frame:
                xfill True
                yfill True
                background Solid("#00000038")
                padding wells_ui_pad(12, 12, 8, 12)

                side "c r":
                    viewport:
                        id "vp_wt"
                        xfill True
                        yfill True
                        mousewheel True
                        draggable True
                        arrowkeys True

                        vbox:
                            xfill True
                            spacing wells_ui(14)

                            if wf_choices_panel:
                                for wf_numero, wf_choice in enumerate(wf_choices_panel):
                                    frame:
                                        xfill True
                                        background Solid("#141414b8")
                                        padding wells_ui_pad(16, 12, 16, 14)

                                        vbox:
                                            xfill True
                                            spacing wells_ui(7)

                                            text "{}. {}".format(wf_numero + 1, wf_choice.text):
                                                size wells_ui(28)
                                                color "#00ff00"
                                                xalign 0.0
                                                text_align 0.0
                                                substitute False
                                                if persistent.wells_force_outline:
                                                    outlines [(absolute(2), "#000000", 0, 0)]

                                            frame:
                                                xfill True
                                                background Solid("#0c0c0c70")
                                                padding wells_ui_pad(12, 8, 12, 8)

                                                text wf_choice.guide:
                                                    size wells_ui(28)
                                                    color "#ffffff"
                                                    xalign 0.0
                                                    text_align 0.0
                                                    substitute False
                                                    if persistent.wells_force_outline:
                                                        outlines [(absolute(2), "#000000", 0, 0)]

                            else:
                                text "No active choices":
                                    xalign 0.5
                                    size wells_ui(26)
                                    color "#aaaaaa"

                    vbar:
                        value YScrollValue("vp_wt")
                        top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)
                        bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0)
                        thumb Frame("wells/gui/v_pino.png", 10, 10)
                        xsize wells_ui(20)


init 998 python:
    try:
        if 'wf_walkthrough_notification' not in config.overlay_screens:
            config.overlay_screens.append('wf_walkthrough_notification')
    except Exception as e:
        print('WF: UI Walkthrough: não foi possível registrar overlay: {}'.format(e))
