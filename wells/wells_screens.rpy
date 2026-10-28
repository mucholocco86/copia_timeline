################################################################################
## WELLS FRAMEWORK — SAY / MULTIPLE SAY — BASE LIMPA
## Um único sistema universal de diálogo + Incubus para diálogo múltiplo.
################################################################################

init 1999 screen say(who, what, multiple=None):
    # Escala visual adaptativa do SAY.
    # 1920x1080 continua sendo a base exata do Wells. Em resoluções maiores,
    # nome, diálogo, textbox e sua geometria crescem juntos. O menor eixo
    # é usado para preservar o encaixe também em proporções diferentes de 16:9.
    $ wells_scale_w = float(config.screen_width) / 1920.0
    $ wells_scale_h = float(config.screen_height) / 1080.0
    if wells_scale_w < wells_scale_h:
        $ wells_scale = wells_scale_w
    else:
        $ wells_scale = wells_scale_h
    if wells_scale < 1.0:
        $ wells_scale = 1.0

    $ wells_box_width = int(persistent.wells_textbox_width * wells_scale)
    if wells_box_width > int(config.screen_width * 0.92):
        $ wells_box_width = int(config.screen_width * 0.92)
    if wells_box_width < 100:
        $ wells_box_width = 100

    $ wells_dialogue_size = int((persistent.pref_text_size_dialogue or 28) * wells_scale)
    if wells_dialogue_size < 12:
        $ wells_dialogue_size = 12

    $ wells_name_size = int((persistent.pref_text_size_label or 30) * wells_scale)
    if wells_name_size < 12:
        $ wells_name_size = 12

    $ wells_line = int((persistent.wells_line_spacing or 5) * wells_scale)
    $ wells_y = int(((persistent.wells_dialogue_y_offset or 0) * wells_scale) + ((persistent.wells_textbox_y - 1.0) * config.screen_height))

    $ wells_opacity = float(persistent.wells_textbox_opacity)
    if wells_opacity < 0.0:
        $ wells_opacity = 0.0
    elif wells_opacity > 1.0:
        $ wells_opacity = 1.0
    $ wells_bg_alpha = int(wells_opacity * 255.0)

    $ wells_pad_x = int(45 * wells_scale)
    $ wells_pad_top = int(22 * wells_scale)
    $ wells_pad_bottom = int(20 * wells_scale)
    $ wells_name_gap = int((persistent.wells_name_dialogue_spacing if persistent.wells_name_dialogue_spacing is not None else 0) * wells_scale)
    $ wells_content_width = wells_box_width - (wells_pad_x * 2)
    if wells_content_width < 100:
        $ wells_content_width = 100

    # Mede nome + diálogo como um único bloco.
    # A textbox recebe exatamente a altura necessária e, como continua
    # ancorada pela base, qualquer crescimento acontece para cima.
    $ wells_say_height = wells_measure_say_text_height(
        who,
        what,
        wells_content_width,
        wells_name_size,
        wells_dialogue_size,
        wells_line,
        wells_name_gap,
        wells_pad_top,
        wells_pad_bottom,
        persistent.wells_force_outline
    )

    window id "window":
        # Correção 8.5: Substituído xalign por xpos + xanchor para manter o comportamento original sem conflito
        xpos persistent.wells_textbox_x
        xanchor 0.5
        yalign 1.0
        yoffset wells_y
        xsize wells_box_width

        ymaximum None

        if wells_say_height is not None:
            yminimum wells_say_height

        background Solid("#000000%02x" % wells_bg_alpha)
        padding (wells_pad_x, wells_pad_top, wells_pad_x, wells_pad_bottom)

        vbox:
            xpos 0
            ypos int(-15 * wells_scale)
            xsize wells_content_width
            spacing wells_name_gap

            if who is not None:
                text who id "who":
                    style "default"
                    # Correção 8.5: Mantido apenas xalign 0.0 (que já posiciona e ancora no pixel 0)
                    xalign 0.0
                    xsize wells_content_width
                    text_align 0.0
                    size wells_name_size
                    color "#FFFFFF"
                    if persistent.wells_force_outline:
                        outlines [(absolute(2), "#000000", 0, 0)]

            text what id "what":
                style "default"
                # Correção 8.5: Mantido apenas xalign 0.0 (que já posiciona e ancora no pixel 0)
                ypos int(15 * wells_scale)
                xalign 0.0
                xsize wells_content_width
                text_align 0.0
                line_spacing wells_line
                size wells_dialogue_size
                color "#FFFFFF"
                if persistent.wells_force_outline:
                    outlines [(absolute(2), "#000000", 0, 0)]

    if not renpy.variant("small"):
        add SideImage() xalign 0.0 yalign 1.0
        use quick_menu()


#################################################################################
## MULTIPLE SAY — INCUBUS / ÚNICO LAYOUT
################################################################################

init 1999 screen multiple_say(who, what, multiple):

    # MULTIPLE SAY — espelho estrutural do SAY normal.
    # O SAY original permanece intocado. O Multiple usa os mesmos princípios
    # de escala, medição e crescimento natural, mas conserva seus próprios
    # controles de posição, largura, tipografia e empilhamento.
    $ wells_scale_w = float(config.screen_width) / 1920.0
    $ wells_scale_h = float(config.screen_height) / 1080.0
    if wells_scale_w < wells_scale_h:
        $ wells_scale = wells_scale_w
    else:
        $ wells_scale = wells_scale_h
    if wells_scale < 1.0:
        $ wells_scale = 1.0

    $ wells_block = multiple[0] if (isinstance(multiple, (tuple, list)) and len(multiple) > 0) else (int(multiple) if multiple is not None else 1)
    $ wells_total_blocks = multiple[1] if (isinstance(multiple, (tuple, list)) and len(multiple) > 1) else wells_block
    if wells_block < 1:
        $ wells_block = 1
    if wells_total_blocks < 1:
        $ wells_total_blocks = 1

    # Geometria/tipografia exclusivas do Multiple.
    $ wells_box_width = int(persistent.wells_multiple_width * wells_scale)
    if wells_box_width > int(config.screen_width * 0.92):
        $ wells_box_width = int(config.screen_width * 0.92)
    if wells_box_width < 300:
        $ wells_box_width = 300

    $ wells_dialogue_size = int((persistent.wells_multiple_text_size or 25) * wells_scale)
    if wells_dialogue_size < 12:
        $ wells_dialogue_size = 12

    $ wells_name_size = int((persistent.wells_multiple_name_size or 25) * wells_scale)
    if wells_name_size < 12:
        $ wells_name_size = 12

    $ wells_line = int((persistent.wells_line_spacing or 5) * wells_scale)
    $ wells_pad_x = int(45 * wells_scale)
    $ wells_pad_top = int(22 * wells_scale)
    $ wells_pad_bottom = int(20 * wells_scale)

    # Distância automática: o Multiple herda a composição-base do SAY normal.
    # O slider Multi Name ↕ Dialogue é SOMENTE um offset fino sobre essa base.
    $ wells_name_gap = int((persistent.wells_multiple_name_dialogue_spacing if persistent.wells_multiple_name_dialogue_spacing is not None else 0) * wells_scale)
    $ wells_content_width = wells_box_width - (wells_pad_x * 2)
    if wells_content_width < 100:
        $ wells_content_width = 100

    $ wells_multiple_height = wells_measure_say_text_height(
        who,
        what,
        wells_content_width,
        wells_name_size,
        wells_dialogue_size,
        wells_line,
        wells_name_gap,
        wells_pad_top,
        wells_pad_bottom,
        persistent.wells_force_outline
    )

    $ wells_opacity = float(persistent.wells_textbox_opacity)
    if wells_opacity < 0.0:
        $ wells_opacity = 0.0
    elif wells_opacity > 1.0:
        $ wells_opacity = 1.0
    $ wells_bg_alpha = int(wells_opacity * 255.0)

    # ---------------------------------------------------------------------
    # ÂNCORA ADAPTATIVA DO MULTIPLE
    # ---------------------------------------------------------------------
    # O SAY normal funciona somente como uma "placa de trânsito": sua região
    # inferior define onde o Multiple NÃO deve entrar. Não há herança de X/Y
    # nem vínculo funcional entre as duas screens.
    #
    # A referência vertical usa a mesma base adaptativa do SAY (textbox_y +
    # dialogue_y_offset) e reserva acima dela uma altura mínima proporcional
    # à composição normal do SAY. Assim o Multiple nasce acima do rodapé/SAY
    # em 1920x1080, 4K e demais resoluções sem exigir Multi Y = -300.
    $ wells_say_bottom = int(config.screen_height + (((persistent.wells_dialogue_y_offset or 0) * wells_scale) + ((persistent.wells_textbox_y - 1.0) * config.screen_height)))
    $ wells_say_name_size_ref = int((persistent.pref_text_size_label or 31) * wells_scale)
    $ wells_say_dialogue_size_ref = int((persistent.pref_text_size_dialogue or 31) * wells_scale)
    $ wells_say_reserved_height = int(max(180 * wells_scale, wells_say_name_size_ref + (wells_say_dialogue_size_ref * 3) + (70 * wells_scale)))
    $ wells_safe_margin = int(30 * wells_scale)
    $ wells_multiple_safe_bottom = int(wells_say_bottom - wells_say_reserved_height - wells_safe_margin)

    # Multi X / Multi Y são offsets puros sobre a posição automática.
    # Zero = layout adaptativo padrão. A posição-base horizontal preserva o
    # layout visual validado do Multiple Say (20% da largura da tela), enquanto
    # o slider Multi X continua livre para deslocar o conjunto para ambos os lados.
    # O SAY permanece somente como referência vertical de limite seguro.
    $ wells_multi_x_offset = int(float(persistent.wells_multiple_x or 0.0) * config.screen_width)
    $ wells_multi_x = int((config.screen_width * 0.20) + wells_multi_x_offset)
    $ wells_multi_y = int((persistent.wells_multiple_y or 0) * wells_scale)
    $ wells_multi_step = int(float(persistent.wells_multiple_stack_step) * wells_scale)

    # V Step continua ajustável, mas nunca fica menor que a altura estimada do
    # bloco. A altura VISUAL da textbox, porém, não é travada: como no SAY,
    # yminimum fornece apenas o mínimo e o Ren'Py pode expandi-la naturalmente.
    $ wells_required_step = int((wells_multiple_height or 1) + (30 * wells_scale))
    if wells_multi_step < wells_required_step:
        $ wells_multi_step = wells_required_step

    # O último bloco fica imediatamente acima do limite seguro do SAY; os
    # anteriores sobem pelo V Step. yoffset é relativo ao fundo da tela.
    $ wells_multi_bottom_abs = int(wells_multiple_safe_bottom - ((wells_total_blocks - wells_block) * wells_multi_step) + wells_multi_y)
    $ wells_multi_position_y = int(wells_multi_bottom_abs - config.screen_height)

    # Mesma construção do screen SAY: uma única window, sem frame/namebox
    # intermediários. Isso evita a caixa preta/default e deixa o conteúdo
    # determinar a altura real em qualquer resolução.
    window id "window":
        xpos wells_multi_x
        xanchor 0.5
        yalign 1.0
        yoffset wells_multi_position_y
        xsize wells_box_width

        ymaximum None
        if wells_multiple_height is not None:
            yminimum wells_multiple_height

        background Solid("#000000%02x" % wells_bg_alpha)
        padding (wells_pad_x, wells_pad_top, wells_pad_x, wells_pad_bottom)

        vbox:
            xpos 0
            ypos int(-15 * wells_scale)
            xsize wells_content_width
            spacing wells_name_gap

            if who is not None:
                text who id "who":
                    style "default"
                    xalign 0.0
                    xsize wells_content_width
                    text_align 0.0
                    size wells_name_size
                    color "#FFFFFF"
                    if persistent.wells_force_outline:
                        outlines [(absolute(2), "#000000", 0, 0)]

            text what id "what":
                style "default"
                ypos int(15 * wells_scale)
                xalign 0.0
                xsize wells_content_width
                text_align 0.0
                line_spacing wells_line
                size wells_dialogue_size
                color "#FFFFFF"
                if persistent.wells_force_outline:
                    outlines [(absolute(2), "#000000", 0, 0)]

    if not renpy.variant("small"):
        add SideImage() xalign 0.0 yalign 1.0
        use quick_menu()

