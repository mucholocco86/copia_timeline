################################################################################
## 5. SCREEN PERFORMANCE
################################################################################

screen menu_performance():
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

                label _("PERFORMANCE"):
                        text_size wells_ui(48) 
                        text_color "#ff4444"

            hbox:
                xalign 0.5 spacing wells_ui(60) 
                vbox:
                    spacing wells_ui(15) xfill True
                    hbox:
                        xpos wells_ui_signed(670)
                        ypos wells_ui_signed(25)
                        xanchor 0.5
                        spacing wells_ui(40)

                        # --- COLUNA: PERFORMANCE (configuração) ---
                        vbox:
                            xsize wells_ui(400) spacing wells_ui(12)

                            vbox:
                                spacing wells_ui(6) xfill True

                                # --- SUBTÍTULO VIDEO PERFORMANCE COM MOLDURA ---
                                frame:
                                    xalign 0.5
                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                    padding wells_ui_pad(15, 2)
                                    text "VIDEO PERFORMANCE" size wells_ui(24) color "#2cf1ff" xalign 0.5

                                $ current_fps = "30 FPS" if preferences.gl_framerate == 30 else "60 FPS"
                                textbutton "Limit FPS: [current_fps]":
                                    xalign 0.5
                                    action Function(toggle_power_save)
                                    text_hover_color "#2bff00"
                                    text_size wells_ui(28)
                                    text_color  "#cacaca"

                                $ gl_ps_status = "ON" if preferences.gl_powersave else "OFF"
                                textbutton "Economia de energia: [gl_ps_status]":
                                    xalign 0.5
                                    action Preference("gl powersave", "toggle")
                                    text_hover_color "#2bff00"
                                    text_size wells_ui(28)
                                    text_color  "#adabab"

                            vbox:
                                spacing wells_ui(6) xfill True

                                # --- SUBTÍTULO RENDERIZAÇÃO COM MOLDURA ---
                                frame:
                                    xalign 0.5
                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                    padding wells_ui_pad(15, 2)
                                    text "RENDERIZAÇÃO DE VÍDEO" size wells_ui(22) color "#2cf1ff" xalign 0.5

                                $ hw_label = "Hardware (GPU)" if persistent.use_hw_video else "Software (CPU)"
                                textbutton "Decoding: [hw_label]":
                                    xalign 0.5
                                    action [ToggleField(persistent, "use_hw_video"), Notify("Restart game to apply changes")]
                                    text_hover_color "#2bff00"
                                    text_size wells_ui(28)

                                text "Use se você vir uma tela preta." size wells_ui(24) color "#949494" xalign 0.5

        button:
            padding wells_ui_pad(0, 0, 0, 0)
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(670) ypos wells_ui_signed(675) xanchor 0.5
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action Show("wells_menu_language")
            text _("Voltar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

