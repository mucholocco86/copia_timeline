################################################################################
## WELLS FRAMEWORK — ESCALA VISUAL ADAPTATIVA DA INTERFACE
## Base lógica: 1920x1080. Usa o menor eixo para também preservar encaixe
## em proporções diferentes de 16:9. Não altera valores persistentes nem
## a geometria interna de say / multiple_say.
################################################################################

init -999 python:

    def wells_ui_scale_value():
        try:
            sx = float(config.screen_width) / 1920.0
            sy = float(config.screen_height) / 1080.0
            if sx < sy:
                scale = sx
            else:
                scale = sy
            if scale <= 0.0:
                return 1.0
            return scale
        except Exception:
            return 1.0

    def wells_ui(value):
        result = int(round(float(value) * wells_ui_scale_value()))
        if result < 1:
            return 1
        return result

    def wells_ui_signed(value):
        return int(round(float(value) * wells_ui_scale_value()))

    def wells_ui_pad(left, top, right=None, bottom=None):
        if right is None:
            right = left
        if bottom is None:
            bottom = top
        return (
            wells_ui_signed(left),
            wells_ui_signed(top),
            wells_ui_signed(right),
            wells_ui_signed(bottom)
        )


################################################################################
## WELLS FRAMEWORK — CÁLCULO DINÂMICO DA TEXTBOX / REN'PY 8.5
################################################################################

init 998 python:

    def wells_measure_say_text_height(
        who,
        what,
        content_width,
        name_size,
        dialogue_size,
        line_spacing,
        name_gap,
        pad_top,
        pad_bottom,
        force_outline=False
    ):
        """
        Mede nome + diálogo usando o próprio renderizador de texto do Ren'Py.
        Retorna a altura total necessária para a textbox.
        """

        try:
            content_width = max(100, int(content_width))
            available_height = max(config.screen_height * 4, 4096)

            common = {
                "style": "default",
                "xsize": content_width,
                "text_align": 0.0,
                "slow": False,
                "substitute": False,
            }

            if force_outline:
                common["outlines"] = [(absolute(2), "#000000", 0, 0)]

            total = int(pad_top) + int(pad_bottom)

            if who is not None:
                name_displayable = Text(
                    who,
                    size=int(name_size),
                    color="#FFFFFF",
                    **common
                )
                name_render = renpy.render(
                    name_displayable,
                    content_width,
                    available_height,
                    0.0,
                    0.0
                )
                total += int(name_render.get_size()[1])

                # O controle pode usar espaçamento negativo para aproximar
                # visualmente nome e diálogo. Esse valor NÃO deve diminuir a
                # altura estrutural da textbox, senão a caixa pode colapsar
                # até virar apenas uma linha.
                if int(name_gap) > 0:
                    total += int(name_gap)

            dialogue_displayable = Text(
                what,
                size=int(dialogue_size),
                color="#FFFFFF",
                line_spacing=int(line_spacing),
                **common
            )
            dialogue_render = renpy.render(
                dialogue_displayable,
                content_width,
                available_height,
                0.0,
                0.0
            )
            total += int(dialogue_render.get_size()[1])

            # Nunca devolve uma caixa menor que o conteúdo básico.
            return max(1, total)

        except Exception:
            # Segurança: se um jogo extremamente customizado impedir a medição,
            # não quebra a say screen; deixa o Ren'Py usar a altura natural.
            return None


################################################################################
## WELLS FRAMEWORK — DIALOGUE CONTROLS / BASE LIMPA
################################################################################

screen dialogue_adjusts():
    modal True
    zorder 200
    tag menu
    add Solid("#00000080")

    $ wells_name_pct = int(persistent.pref_text_size_label or 31)
    $ wells_dialogue_pct = int(persistent.pref_text_size_dialogue or 31)
    $ wells_x_pct = int((persistent.wells_textbox_x or 0.5) * 100)
    $ wells_y_pct = int((persistent.wells_textbox_y or 1.0) * 100)
    $ wells_width_value = int(persistent.wells_textbox_width or 960)
    $ wells_opacity_pct = int((persistent.wells_textbox_opacity if persistent.wells_textbox_opacity is not None else 0.35) * 100)
    $ wells_multiple_x_pct = int((persistent.wells_multiple_x or 0.0) * 100)
    $ wells_multiple_width_value = int(persistent.wells_multiple_width or 600)
    $ wells_step_value = int(persistent.wells_multiple_stack_step or 310)
    $ wells_name_adjust_value = int(persistent.wells_name_size_offset or 2)
    $ wells_gap_value = int(persistent.wells_name_dialogue_spacing if persistent.wells_name_dialogue_spacing is not None else 0)
    $ wells_multiple_y_value = int(persistent.wells_multiple_y or 0)
    $ wells_multiple_name_size = int(persistent.wells_multiple_name_size or 25)
    $ wells_multiple_dialogue_size = int(persistent.wells_multiple_text_size or 25)
    $ wells_multiple_gap_value = int(persistent.wells_multiple_name_dialogue_spacing if persistent.wells_multiple_name_dialogue_spacing is not None else 0)
    $ wells_choice_width_value = int(persistent.wells_choice_width or 920)
    $ wells_choice_x_pct = int((persistent.wells_choice_xpos or 0.5) * 100)
    $ wells_choice_y_pct = int((persistent.wells_choice_ypos or 0.5) * 100)

    frame:
        xalign 0.5
        yalign 0.4
        background Frame("wells/gui/frame_menu.png", 10, 10)
        xsize wells_ui(1450)
        ysize wells_ui(820)
        padding wells_ui_pad(50, 40)

        vbox:
            xfill True
            spacing wells_ui(15)

            frame:
                xpos wells_ui_signed(670)
                xanchor 0.5
                ypos wells_ui_signed(15)
                background Frame("wells/gui/label_frame.png", 0, 0)
                padding wells_ui_pad(10, 10)
                label _("DIALOGUE MENU"):
                    text_size wells_ui(42)
                    text_color "#ff4444"

            frame:
                xpos wells_ui_signed(120)
                ypos wells_ui_signed(60)
                xsize wells_ui(760)
                ysize wells_ui(400)
                background None
                padding wells_ui_pad(10, 10, 10, 10)

                side "c r":
                    xalign 0.5
                    ypos wells_ui_signed(0)
                    spacing wells_ui(15)

                    viewport:
                        id "wells_painel_controles_vp"
                        mousewheel True
                        draggable True
                        arrowkeys True
                        xsize wells_ui(720)
                        ysize wells_ui(380)

                        vbox:
                            spacing wells_ui(18)
                            xsize wells_ui(680)

                            frame:
                                xsize wells_ui(700)
                                background Frame("wells/gui/frame_control.png", 10, 10)
                                padding wells_ui_pad(12, 12)

                                vbox:
                                    spacing wells_ui(8)
                                    xfill True

                                    frame:
                                        xalign 0.5
                                        background Frame("wells/gui/label_frame.png", 10, 10)
                                        padding wells_ui_pad(12, 4)
                                        label _("DIALOGUE"):
                                            text_size wells_ui(26)
                                            text_color "#ff4444"

                                    hbox:
                                        spacing wells_ui(18)
                                        xfill True

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Name Size: [wells_name_pct]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "pref_text_size_label", range=48, offset=12, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "Textbox X: [wells_x_pct]%":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_textbox_x", range=1.0, step=0.01)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "Textbox Width: [wells_width_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_textbox_width", range=1560, offset=500, step=10)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "Line Spacing: [persistent.wells_line_spacing]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_line_spacing", range=50, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "DIalogue Adjust: [wells_name_adjust_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_name_size_offset", range=10, offset=-10, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            # CHOICE X

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Text Size: [wells_dialogue_pct]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "pref_text_size_dialogue", range=48, offset=12, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "Textbox Y: [wells_y_pct]%":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_textbox_y", range=1.0, step=0.01)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "Textbox Opacity: [wells_opacity_pct]%":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_textbox_opacity", range=1.0, step=0.01)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                            vbox spacing wells_ui(4):
                                                label "Name ↕ Dialogue: [wells_gap_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_name_dialogue_spacing", range=200, offset=-100, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                            frame:
                                xsize wells_ui(700)
                                background Frame("wells/gui/frame_control.png", 10, 10)
                                padding wells_ui_pad(12, 12)

                                vbox:
                                    spacing wells_ui(8)
                                    xfill True

                                    frame:
                                        xalign 0.5
                                        background Frame("wells/gui/label_frame.png", 10, 10)
                                        padding wells_ui_pad(12, 4)
                                        label _("MULTIPLE DIALOGUE"):
                                            text_size wells_ui(26)
                                            text_color "#ff4444"

                                    # Prioridade visual: tipografia primeiro.
                                    hbox:
                                        spacing wells_ui(18)
                                        xfill True

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Multi Name Size: [wells_multiple_name_size]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_name_size", range=21, offset=12, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Multi Dialogue Size: [wells_multiple_dialogue_size]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_text_size", range=21, offset=12, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                    # Ajuste fino exclusivo sobre a distância automática Nome ↕ Diálogo.
                                    # Em 0 o Multiple já usa a composição-base adaptativa do SAY.
                                    # Valores +/- apenas refinam a preferência visual do usuário.
                                    hbox:
                                        spacing wells_ui(18)
                                        xfill True

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Multi Name ↕ Dialogue: [wells_multiple_gap_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_name_dialogue_spacing", range=200, offset=-100, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                    # Posição vem depois da tipografia.
                                    hbox:
                                        spacing wells_ui(18)
                                        xfill True

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Multi X: [wells_multiple_x_pct]%":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)

                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_x", range=1.0, offset=-0.5, step=0.01)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                        vbox:
                                            spacing wells_ui(14)
                                            yalign 0.0
                                            xsize wells_ui(330)

                                            # CHOICE Y

                                            vbox spacing wells_ui(4):
                                                label "Multi Y: [wells_multiple_y_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_y", range=600, offset=-300, step=5)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                    hbox:
                                        spacing wells_ui(18)
                                        xfill True

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Multi Width: [wells_multiple_width_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_width", range=1400, offset=300, step=10)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1
                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Multi V Step: [wells_step_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_multiple_stack_step", range=600, offset=100, step=5)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                            frame:
                                xsize wells_ui(700)
                                background Frame("wells/gui/frame_control.png", 10, 10)
                                padding wells_ui_pad(12, 12)

                                vbox:
                                    spacing wells_ui(8)
                                    xfill True

                                    frame:
                                        xalign 0.5
                                        background Frame("wells/gui/label_frame.png", 10, 10)
                                        padding wells_ui_pad(12, 4)
                                        label _("CHOICES"):
                                            text_size wells_ui(26)
                                            text_color "#ff4444"

                                    hbox:
                                        spacing wells_ui(18)
                                        xfill True

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Choice X: [wells_choice_x_pct]%":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_choice_xpos", range=1.0, step=0.01)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1
                                            # CHOICE WIDTH

                                            vbox spacing wells_ui(4):
                                                label "Choice Width: [wells_choice_width_value]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_choice_width", range=1500, offset=300, step=10)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                                        vbox:
                                            spacing wells_ui(10)
                                            xsize wells_ui(315)

                                            vbox spacing wells_ui(4):
                                                label "Choice Y: [wells_choice_y_pct]%":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_choice_ypos", range=1.0, step=0.01)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1
                                            # CHOICE SPACING

                                            vbox spacing wells_ui(4):
                                                label "Choice Spacing: [persistent.wells_choice_spacing]":
                                                    text_size wells_ui(24)
                                                    text_color "#2cf1ff"
                                                    padding wells_ui_pad(15, 2)
                                                    background Frame("wells/gui/label_frame.png", 10, 10)
                                                bar:
                                                    value FieldValue(persistent, "wells_choice_spacing", range=100, step=1)
                                                    xsize wells_ui(320)
                                                    ysize wells_ui(25)
                                                    xalign 0.5
                                                    idle_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    hover_right_bar Frame("wells/gui/barra_vazia.png", 5, 5)
                                                    idle_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    hover_left_bar Frame("wells/gui/barra_cheia.png", 5, 5)
                                                    thumb "wells/gui/pino.png"
                                                    thumb_shadow None
                                                    thumb_offset 1

                    vbar:
                        value YScrollValue("wells_painel_controles_vp")
                        top_bar Frame("wells/gui/vertical_cheia.png", 0, 0)
                        bottom_bar Frame("wells/gui/vertical_vazia.png", 0, 0)
                        thumb Frame("wells/gui/v_pino_wsc.png", 10, 10)
                        xsize wells_ui(12)

            vbox:
                spacing wells_ui(8)
                xpos wells_ui_signed(920)
                ypos wells_ui_signed(-350)
                xsize wells_ui(186)

                vbox:
                    spacing wells_ui(8)

                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action Preference("skip", "toggle")
                        if preferences.skip_unseen:
                            text _("Pular Texto") xalign 0.5 yalign 0.5 size wells_ui(20) color "#39ff14" hover_color "#00f3ff"
                        else:
                            text _("Pular Texto") xalign 0.5 yalign 0.5 size wells_ui(20) color "#FFFFFF" hover_color "#2bff00"
                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action Preference("after choices", "toggle")
                        if preferences.skip_after_choices:
                            text _("Após Escolhas") xalign 0.5 yalign 0.5 size wells_ui(20) color "#39ff14" hover_color "#00f3ff"
                        else:
                            text _("Após Escolhas") xalign 0.5 yalign 0.5 size wells_ui(20) color "#FFFFFF" hover_color "#2bff00"

                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action Preference("transitions", "toggle")
                        if preferences.transitions == 2:
                            text _("Transições") xalign 0.5 yalign 0.5 size wells_ui(20) color "#FFFFFF" hover_color "#00f3ff"
                        else:
                            text _("Transições") xalign 0.5 yalign 0.5 size wells_ui(20) color "#39ff14" hover_color "#2bff00"

                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action ToggleField(persistent, "wells_force_outline")

                        if persistent.wells_force_outline:
                            text "CONTORNO" xalign 0.5 yalign 0.5 size wells_ui(18) color "#39ff14" hover_color "#00f3ff"
                        else:
                            text "CONTORNO" xalign 0.5 yalign 0.5 size wells_ui(18) color "#FFFFFF" hover_color "#2bff00"

                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action If(persistent.wells_choice_slot == 0, SetField(persistent, "wells_choice_slot", 1), SetField(persistent, "wells_choice_slot", 0))
                        if persistent.wells_choice_slot == 0:
                            text "Choice: Padrão" xalign 0.5 yalign 0.5 size wells_ui(18) color "#00f3ff" hover_color "#2bff00"
                        else:
                            text "Choice: Original" xalign 0.5 yalign 0.5 size wells_ui(18) color "#39ff14" hover_color "#00f3ff"

                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action Function(wells_click_speed_up)
                        text _("Speed +") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"

                    frame:
                        xalign 0.5
                        background Frame("wells/gui/label_frame.png", 10, 10)
                        padding wells_ui_pad(12, 4)
                        xminimum wells_ui(100)
                        text get_wells_click_time_text() align (0.5, 0.5) size wells_ui(26) text_align 0.5

                    button:
                        padding wells_ui_pad(0, 0, 0, 0)
                        xysize (wells_ui(180), wells_ui(42))
                        idle_background Frame("wells/gui/Button-idle.png", 5, 5)
                        hover_background Frame("wells/gui/Button-hover.png", 5, 5)
                        action Function(wells_click_speed_down)
                        text _("Speed -") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"


        button:
            xysize (wells_ui(180), wells_ui(45))
            xpos wells_ui_signed(670)
            ypos wells_ui_signed(675)
            xanchor 0.5
            idle_background Frame("wells/gui/Button-idle.png", 5, 5)
            hover_background Frame("wells/gui/Button-hover.png", 5, 5)
            action Show("wells_menu_language")
            text _("Voltar") xalign 0.5 yalign 0.5 size wells_ui(22) hover_color "#2bff00"
