## =============================================================================
## WELLS TIMELINE — tl_theme.rpy
## Tokens de design, estilos e gradientes de foco.
## =============================================================================

## =============================================================================
## Tokens de design — todas as cores e dimensões em um só lugar
## =============================================================================

init python:
    # ── Funções auxiliares de contraste ───────────────────────────────────
    def hex_to_rgb(hex_color):
        """Convert #rrggbb to (r,g,b) 0–255."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def relative_luminance(rgb):
        """Return relative luminance for contrast calculation (0–1)."""
        def channel(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126*channel(r) + 0.7152*channel(g) + 0.0722*channel(b)

    def contrast_ratio(rgb1, rgb2):
        """Contrast ratio as per WCAG (1–21)."""
        l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
        if l1 < l2: l1, l2 = l2, l1
        return (l1 + 0.05) / (l2 + 0.05)

    def pick_accent_color(bg_colors, fallback="#e8c97e"):
        """Choose a readable accent color over given bg_colors."""
        candidates = [
            getattr(gui, "accent_color", None),
            getattr(gui, "choice_button_text_hover_color", None),
            getattr(gui, "hover_color", None),
            getattr(gui, "selected_color", None),
        ]

        for c in candidates:
            if not c:
                continue
            rgb = hex_to_rgb(c)
            if rgb == (255,255,255):  # ignora branco puro
                continue

            # verifica o contraste em todos os fundos
            ok = all(contrast_ratio(rgb, hex_to_rgb(bg)) >= 3.0 for bg in bg_colors)
            if ok:
                return c

        return fallback  # nenhuma cor adequada encontrada

    # ── Fundos usados no cálculo de contraste ──────────────────────────────────
    header_bg = "#000000bb"   # igual a TL["header_bg"]
    footer_bg = "#00000055"   # igual a TL["footer_bg"]
    accent_color = pick_accent_color([header_bg, footer_bg])

    # ── Cores do mod Timeline ──────────────────────────────────────────────
    TL = {
        ## Cor de destaque
        "accent": accent_color,

        ## Sobreposição
        "overlay_bg"    : "#00000099",   ## base preta com 60% de opacidade
        "noise_alpha"   : "#ffffff0c",   ## tom sutil para o ruído visual

        ## Cabeçalho
        "header_bg"     : header_bg,
        "header_text"   : "#f0ece4",
        "header_sub"    : "#9a9183",
        "new_dot"       : accent_color,     ## dourado quente para o indicador de conteúdo novo

        ## Cartão
        "card_bg"       : "#00000000",   ## transparente — sem fundo no cartão
        "thumb_bg"      : "#0a0a0a",
        "divider"       : accent_color + "55",  ## semitransparente

        ## Linhas de opções
        "opt_chosen_fg" : "#f0ece4",     ## escolhida nesta sessão — mantida para a cor da seta
        "opt_fg"        : "#f0ece4",     ## texto de todas as opções — uniforme, sem esmaecer
        "opt_new_dot"   : accent_color,     ## ponto dourado para opções ainda não vistas

        ## Linha de rodapé
        "footer_bg"     : footer_bg,
        "footer_text"   : "#9a9183",
        "btn_bg"        : "#ffffff14",
        "btn_hover_bg"  : "#ffffff28",
        "hover_bg"      : accent_color + "30",  ## fundo de foco compartilhado por todas as linhas e botões interativos
        "btn_text"      : "#c8c0b4",

        ## Janela modal
        "modal_bg"      : "#1a1814ee",
        "modal_header"  : "#f0ece4",
    }

    def _tl_make_hover_gradient(color_hex, center_w=100, edge_w=50, base_hex=None):
        ## Gradiente horizontal: esmaecimento de edge_w px, centro sólido de center_w px e esmaecimento final de edge_w px.
        ## Frame(..., edge_w, 0) mantém fixas as áreas de esmaecimento e estica o centro
        ## para acomodar qualquer largura de botão.
        ## base_hex: quando informado, as bordas são pré-mescladas (foco sobre fundo, Porter-Duff) para
        ## que correspondam exatamente ao fundo normal do botão, sem ficarem transparentes.
        import io as _io
        import pygame as _pg

        h      = color_hex.lstrip("#")
        hr, hg, hb = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        ha     = int(h[6:8], 16) if len(h) >= 8 else 255

        if base_hex is not None:
            bh = base_hex.lstrip("#")
            br, bg_, bb = int(bh[0:2], 16), int(bh[2:4], 16), int(bh[4:6], 16)
            ba = int(bh[6:8], 16) if len(bh) >= 8 else 255
        else:
            br = bg_ = bb = ba = 0

        def _pixel(t):
            if base_hex is None:
                return (hr, hg, hb, int(ha * t))
            ## Composição Porter-Duff "over": foco (com alfa efetivo ha*t) sobre o fundo.
            eff_h = (ha / 255.0) * t
            eff_b = ba / 255.0
            out_f = eff_h + eff_b * (1.0 - eff_h)
            if out_f > 0:
                pr = int((hr * eff_h + br * eff_b * (1.0 - eff_h)) / out_f)
                pg = int((hg * eff_h + bg_ * eff_b * (1.0 - eff_h)) / out_f)
                pb = int((hb * eff_h + bb * eff_b * (1.0 - eff_h)) / out_f)
            else:
                pr = pg = pb = 0
            return (pr, pg, pb, int(out_f * 255))

        total_w = edge_w + center_w + edge_w
        surf    = renpy.display.pgrender.surface((total_w, 1), True)

        for x in range(edge_w):
            t = x / float(edge_w)
            t = t * t * (3.0 - 2.0 * t)
            surf.set_at((x, 0), _pixel(t))
        for x in range(edge_w, edge_w + center_w):
            surf.set_at((x, 0), _pixel(1.0))
        for x in range(edge_w + center_w, total_w):
            t = (total_w - 1 - x) / float(edge_w)
            t = t * t * (3.0 - 2.0 * t)
            surf.set_at((x, 0), _pixel(t))

        import tempfile as _tf, os as _os
        tmp = _tf.mktemp(suffix=".png")
        try:
            _pg.image.save(surf, tmp)
            with open(tmp, "rb") as _f:
                png_bytes = _f.read()
        finally:
            try: _os.unlink(tmp)
            except: pass

        return Frame(_tl_im_Data(png_bytes, "tl_hg.png"), edge_w, 0)

    _tl_hover_gradient      = _tl_make_hover_gradient(TL["hover_bg"])
    _tl_hover_gradient_wide = _tl_make_hover_gradient(TL["hover_bg"], center_w=60, edge_w=22, base_hex=TL["footer_bg"])


## =============================================================================
## Estilos — definidos explicitamente, sem herdar estilos do jogo ou de outros mods.
## =============================================================================

init python:
    _tl_font_reg  = "wells/fonts/Roboto-Regular.ttf"
    _tl_font_bold = _tl_font_reg

    ## O Timeline usa Roboto-Regular em todos os textos para manter a mesma tipografia em qualquer jogo.
    _TL_GLYPH_RANGES = [
        (0x00B7, 0x00B7),   ## · ponto médio
        (0x2190, 0x21FF),   ## ↑ ↓ → ↺ setas
        (0x2387, 0x2387),   ## ⎇ ramo
        (0x2713, 0x2717),   ## ✓ marca, ✕ fechar, ✗ cruz
        (0x25BE, 0x25BE),   ## ▾ triângulo para baixo
        (0x25CF, 0x25CF),   ## ● círculo preenchido
    ]

    def _tl_make_fontgroup(base):
        # Retorna a fonte Roboto definida pelo Timeline, sem depender da fonte do jogo.
        return base

    _tl_fontgroup      = _tl_make_fontgroup(_tl_font_reg)
    _tl_bold_fontgroup = _tl_make_fontgroup(_tl_font_bold)



style tl_base is text:
    font _tl_fontgroup
    size TL_SIZE_BODY
    color "#f0ece4"
    italic False
    bold False
    underline False
    strikethrough False
    outlines []
    drop_shadow None
    kerning 0.0
    layout "tex"

style tl_base_bold is text:
    font _tl_bold_fontgroup
    size TL_SIZE_BODY
    color "#f0ece4"
    italic False
    bold True
    underline False
    strikethrough False
    outlines []
    drop_shadow None
    kerning 0.0

style tl_icon is text:
    font _tl_fontgroup
    size TL_SIZE_DOT
    color "#f0ece4"
    italic False
    bold False
    outlines []
    drop_shadow None

style tl_frame_base is _default:
    background None
    padding (0, 0, 0, 0)

init python:
    def _tl_noise_bg():
        return Solid(TL["noise_alpha"])