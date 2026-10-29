# Damos um nome de arquivo neutro e de alta prioridade, ex: 01_well_age_check.rpy

init -999 python:
    _original_Start = Start

    # Modificamos a ação do botão Start para apontar para a label de maioridade do framework
    class WellsHookedAgeStart(_original_Start):
        def __call__(self):
            start_action = _original_Start("wells_framework_age_label")
            return start_action()

        def get_sensitive(self):
            return _original_Start.get_sensitive(self)

        def get_selected(self):
            return _original_Start.get_selected(self)

    Start = WellsHookedAgeStart

# Mantém os backgrounds da introdução no comportamento original.
# Somente os elementos funcionais criados para 1920x1080 (mensagens,
# selo 18+ e botões YES/NO) recebem a escala adaptativa.
transform wells_intro_adaptive_scale:
    zoom wells_ui_scale_value()

transform wells_intro_background_position:
    xalign 0.5
    yalign 0.5

transform wells_text_position:
    xalign 0.5
    yalign 0.5
    zoom wells_ui_scale_value()


# Label universal (Introdução Visual + Verificação de Idade)
label wells_framework_age_label:
    $ renpy.block_rollback()
    
    scene black with Dissolve (1.0)

    show expression Frame("wells/gui/introduction/intro_frame.png", 0, 0) as wells_bg_frame at wells_intro_background_position with dissolve
    $ renpy.pause(5, hard=True)
    scene black with Dissolve (1.0)

    show expression Frame("wells/gui/introduction/logotipo.png", 0, 0) as wells_bg_frame at wells_intro_background_position with dissolve

    show expression "wells/gui/introduction/introtext1.png" as wells_msg at wells_text_position with dissolve
    $ renpy.pause(5, hard=True)

    show expression "wells/gui/introduction/introtext2.png" as wells_msg at wells_text_position with dissolve
    $ renpy.pause(5, hard=True)
    hide wells_msg with dissolve

    show expression Frame("wells/gui/introduction/aviso.png", 0, 0) as wells_bg_frame at wells_intro_background_position with dissolve
    hide wells_msg with Dissolve (1.0)
    call screen wells_age_verification_buttons
    
    # Se o jogador clicou em SIM (Return), o script continua aqui, limpa tudo e inicia o jogo
    hide wells_bg_frame with dissolve
    scene black with Dissolve (1.0)
    jump start


    # SCREEN EXCLUSIVA: Mostra a pergunta final e os imagebuttons provisórios
screen wells_age_verification_buttons():
    modal True
    
    # 1. O Selo 18+ fica cravado no centro exato da tela (x=0.5, y=0.5)
    add "wells/gui/introduction/introtext3.png" at wells_intro_adaptive_scale:
        xalign 0.5
        yalign 0.5

    # 2. Botão "YES" posicionado acima do selo
    # O yanchor 1.0 faz a base do botão se alinhar com a posição vertical definida
    imagebutton at wells_intro_adaptive_scale:
        xalign 0.5
        ypos 0.34  # Quanto menor o número, mais para cima o botão sobe
        yanchor 1.0
        idle "wells/gui/introduction/18_yes-idle.png"
        hover "wells/gui/introduction/18_yes-hover.png" # Provisório: usa a mesma imagem enquanto não tiver a versão hover
        action Return()
        
    # 3. Botão "NO" posicionado abaixo do selo
    # O yanchor 0.0 faz o topo do botão se alinhar com a posição vertical definida
    imagebutton at wells_intro_adaptive_scale:
        xalign 0.5
        ypos 0.66  # Quanto maior o número, mais para baixo o botão desce
        yanchor 0.0
        idle "wells/gui/introduction/18_no-idle.png"
        hover "wells/gui/introduction/18_no-hover.png"  # Provisório: usa a mesma imagem enquanto não tiver a versão hover
        action Quit(confirm=False)