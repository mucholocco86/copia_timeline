################################################################################
## 3. SCREEN IDIOMA SELETOR
################################################################################

screen idioma_seletor():
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

                label _("LANGUAGE SELECTOR"):
                        text_size wells_ui(48) 
                        text_color "#ff4444"

            vbox:
                xalign 0.5
                yalign 0.5
                spacing wells_ui(15)

                if renpy.variant("small"):
                    xsize wells_ui(400) 
                else:
                    xsize wells_ui(380)

                label _("TRANSLATION"):
                    xalign 0.5 
                    text_size wells_ui(26) 
                    text_color "#347bff"
                    padding wells_ui_pad(25, 6)
                    background Frame("wells/gui/label_frame.png", 10, 10)

                vbox:
                    xalign 0.5
                    spacing wells_ui(6)
                    style_prefix "radio"
                    
                    frame:
                        xsize wells_ui(380) ysize wells_ui(280) background Solid("#0000004f")
                        
                        side "c r":
                            spacing wells_ui(10) 
                            
                            viewport:
                                id "vp_tl" mousewheel True draggable True
                                vbox spacing wells_ui(8) xfill True:
                                    $ langs = get_all_languages()
                                    for lang in langs:
                                        textbutton "[lang]".capitalize():
                                            action Language(None if lang=="Default" else lang)
                                            text_idle_color "#ffffff"
                                            text_hover_color "#ff0000"
                                            text_selected_idle_color "#2bff00"
                                            text_selected_hover_color "#2bff00"
                                            text_size wells_ui(26)
                                            xalign 0.5

                            vbar:
                                value YScrollValue("vp_tl")
                                top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)   
                                bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0) 
                                thumb Frame("wells/gui/v_pino.png", 0, 0)             
                                xsize wells_ui(20)                                               

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(670) ypos wells_ui_signed(675) xanchor 0.5  
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action Show("wells_menu_language")
            text _("Voltar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"
