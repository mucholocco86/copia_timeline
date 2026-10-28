################################################################################
## 2. SCREEN MENU PRINCIPAL (CENTRALIZADO)
################################################################################

screen wells_menu_language():
    modal True
    zorder 200
    tag menu
    add Solid("#00000080") 

    frame:
        xalign 0.5 yalign 0.4
        background Frame("wells/gui/frame_menu.png", 10, 10)

        # --- LÓGICA DE RESOLUÇÃO E MOBILE ---
        if renpy.variant("small"):
            xsize wells_ui(1600) ysize wells_ui(950) padding wells_ui_pad(60, 50)
        else:
            xsize wells_ui(1450) ysize wells_ui(820) padding wells_ui_pad(50, 40)

        vbox:
            xfill True
            spacing wells_ui(25)

            frame:
                xpos wells_ui_signed(670)
                xanchor 0.5
                ypos wells_ui_signed(15)
                background Frame("wells/gui/label_frame.png", 0, 0)
                padding wells_ui_pad(10, 10)

                label _("Wells Framework"):
                        text_size wells_ui(48) 
                        text_color "#ff4444"

            hbox:
                xalign 0.5 spacing wells_ui(60) 

# --- COLUNA 1: SISTEMA (FONTES) ---
                vbox:
                    xsize wells_ui(420) spacing wells_ui(15) 
                    ypos wells_ui_signed(20)
                    xanchor 0.5
                    xpos wells_ui_signed(160)

                    label _("FONTS"):
                        xalign 0.3
                        text_size wells_ui(26) 
                        text_color "#347bff"
                        padding wells_ui_pad(25, 6)
                        background Frame("wells/gui/label_frame.png", 10, 10)

                    frame:
                        xsize wells_ui(380) ysize wells_ui(220) background Solid("#00000066")
                        
                        side "c r":
                            spacing wells_ui(10) 
                            
                            viewport:
                                id "vp_fonts" mousewheel True draggable True
                                vbox spacing wells_ui(8) xfill True:
                                    for fonte in listar_fontes():
                                        # Monta o caminho virtual limpo relativo aceito nativamente pela engine
                                        textbutton "[fonte]":
                                            action [SetField(persistent, "font_escolhida", "wells/fonts/" + fonte), Preference("font transform", "wells_custom")]
                                            text_font ("wells/fonts/" + fonte) text_size wells_ui(24)
                                            text_selected_color "#2bff00"
                                            text_hover_color "#ff0000"
                                            selected (persistent.font_escolhida == ("wells/fonts/" + fonte))

                            vbar:
                                value YScrollValue("vp_fonts")
                                top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)   
                                bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0) 
                                thumb Frame("wells/gui/v_pino.png", 10, 10)             
                                xsize wells_ui(20)                                               

                    # --- BOTÃO REINICIAR UNIVERSAL DE FONTES ---
                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(45))
                        xpos wells_ui_signed(150) ypos wells_ui_signed(6) xanchor 0.5
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        # [CORREÇÃO] Define a escolha como None e desliga o transformador para restaurar a fonte original do jogo
                        action [SetField(persistent, "font_escolhida", None), Preference("font transform", None)] 
                        text _("Reiniciar Font") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

                # --- COLUNA 2: TODOS OS SLIDERS (CONTROLES) ---
                vbox:
                    xsize wells_ui(420) spacing wells_ui(10) 
                    ypos wells_ui_signed(20)
                    xanchor 0.5
                    xpos wells_ui_signed(290)

                    label _("SOUNDS"):
                        xalign 0.5 
                        text_size wells_ui(26) 
                        text_color "#347bff"
                        padding wells_ui_pad(25, 6)
                        background Frame("wells/gui/label_frame.png", 10, 10)

                    vbox spacing wells_ui(4):

                        label _("Music"):
                            xalign 0.5 
                            text_size wells_ui(24) 
                            text_color "#2cf1ff"
                            padding wells_ui_pad(15, 4)
                            background Frame("wells/gui/label_frame.png", 10, 10)

                        bar:
                            value Preference("music volume") 
                            xsize wells_ui(400) ysize wells_ui(25)
                            idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                            hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                            idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                            hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                            thumb "wells/gui/pino.png"
                            thumb_shadow None
                            thumb_offset 1

                        label _("SFX"):
                            xalign 0.5 
                            text_size wells_ui(24) 
                            text_color "#2cf1ff"
                            padding wells_ui_pad(15, 4)
                            background Frame("wells/gui/label_frame.png", 10, 10)

                        bar:
                            value Preference("sound volume") 
                            xsize wells_ui(400) ysize wells_ui(25)
                            idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                            hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                            idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                            hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                            thumb "wells/gui/pino.png"
                            thumb_shadow None
                            thumb_offset 1

                        label _("Voice"):
                            xalign 0.5 
                            text_size wells_ui(24) 
                            text_color "#2cf1ff"
                            padding wells_ui_pad(15, 4)
                            background Frame("wells/gui/label_frame.png", 10, 10)

                        bar:
                            value Preference("voice volume") 
                            xsize wells_ui(400) ysize wells_ui(25)
                            idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                            hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                            idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                            hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                            thumb "wells/gui/pino.png"
                            thumb_shadow None
                            thumb_offset 1

                    vbox spacing wells_ui(10):

                        button:
                            padding wells_ui_pad(0, 0, 0, 0)
                            xysize (wells_ui(180), wells_ui(45))
                            xpos wells_ui_signed(200) ypos wells_ui_signed(25) xanchor 0.5
                            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                            action Preference("all mute", "toggle")
                            text _("MUTE") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(290) ypos wells_ui_signed(675) xanchor 0.5
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action [Show("idioma_seletor"), Hide("wells_menu_language")]
            text _("Idiomas") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(480) ypos wells_ui_signed(675) xanchor 0.5
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action [Show("menu_performance"), Hide("wells_menu_language")]
            text _("Performance") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(670) ypos wells_ui_signed(675) xanchor 0.5  # Este é o centro real exato do painel (1450 / 2)
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action [Show("dialogue_adjusts"), Hide("wells_menu_language")]
            text _("Diálogo") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(860) ypos wells_ui_signed(675) xanchor 0.5
            idle_background Frame("wells/gui/Restore-idle.png", 5, 5)
            hover_background Frame("wells/gui/Restore-hover.png", 5, 5)
            action Function(restore_wells_defaults)
            text _("Restore") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(1050) ypos wells_ui_signed(675) xanchor 0.5
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action [Hide("wells_menu_language")]
            text _("Fechar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"