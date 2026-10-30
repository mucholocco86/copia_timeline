## =============================================================================
## WELLS TIMELINE — timeline_runtime.rpy
## Estado do store e hooks de execução e de salvamento.
## As seções consolidadas mantêm a ordem de carregamento anterior.
## =============================================================================

## -----------------------------------------------------------------------------
## Seção 1: timeline_hooks.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — timeline_hooks.rpy
## =============================================================================

init -1 python:

    def _tl_resolve_node_location():
        """
        Return (ast_key, location, node_type) for the current execution context.
        ast_key is (filename, linenumber) when the current node is a named AST node,
        else None. location is the raw context.current label string.
        """
        location  = None
        ast_key   = None
        node_type = None
        try:
            current = renpy.game.context().current
            if current is not None:
                location = current
                node_obj = renpy.game.script.namemap.get(current)
                if node_obj is not None:
                    node_type = type(node_obj).__name__
                    ast_key   = (node_obj.filename, node_obj.linenumber)
        except Exception as e:
            _tl_log("TL location lookup failed: {}".format(e))
        return ast_key, location, node_type

    def _tl_resolve_img_name(ast_key, location):
        """
        Return img_name for the current menu.
        Live scene resolution is authoritative and updates the persistent map;
        persistent map by ast_key or location key is the fallback.
        """
        ast_site_key = (_tl_menu_site_key(ast_key[0], ast_key[1])
                        if isinstance(ast_key, tuple) and len(ast_key) == 2 else None)
        img_name = None
        if not persistent._tl_replaying and not config.skipping:
            img_name = _tl_resolve_live_menu_img_name()
            if img_name and ast_site_key:
                persistent._tl_menu_scene_map[ast_site_key] = img_name
        if not img_name:
            img_cache = persistent._tl_menu_scene_map or {}
            loc_key   = _tl_location_menu_site_key(location)
            if ast_site_key and ast_site_key in img_cache:
                img_name = img_cache[ast_site_key]
            elif loc_key and loc_key in img_cache:
                img_name = img_cache[loc_key]
        if TL_DEBUG_MENU:
            _tl_log("TL img_name: ast_key={} img_name={}".format(ast_key, img_name))
        return img_name

    def _tl_capture_thumb(node, ast_key):
        """
        Capture or restore a screenshot thumbnail for the given menu node.
        Uses the runtime thumb cache; only captures when not replaying and not skipping.
        Sets node["thumb_bytes"] directly when the cache is unavailable.
        """
        need_frozen_thumb = bool(node["img_name"] and _tl_img_name_is_movie(node["img_name"]))
        if node["img_name"] and not need_frozen_thumb:
            return
        cache_key    = str(ast_key) if ast_key else None
        thumb_cache  = getattr(renpy.game, "_tl_thumb_cache", {})
        cached_thumb = thumb_cache.get(cache_key) if cache_key else None
        if not persistent._tl_replaying and not cached_thumb and not config.skipping:
            thumb = _tl_capture_thumbnail()
            if thumb:
                if cache_key:
                    try:
                        thumb_cache[cache_key] = thumb
                        while len(thumb_cache) > TL_THUMB_CACHE_MAX:
                            thumb_cache.pop(next(iter(thumb_cache)))
                    except Exception as e:
                        _tl_log("TL thumb cache write failed: {}".format(e))
                        node["thumb_bytes"] = thumb
                else:
                    node["thumb_bytes"] = thumb
        if need_frozen_thumb and TL_DEBUG_MENU:
            _tl_log("TL movie thumb fallback: ast_key={} img_name={}".format(ast_key, node["img_name"]))

    def _tl_record_before(items):
        if not hasattr(store, "_tl_history"):
            return None  ## os valores padrão do store ainda não foram aplicados (menu anterior ao início do jogo)
        global _tl_node_count, _tl_history, _tl_context

        ## Descarrega alterações imediatas de variáveis (fora de init) e alterações init-in-arm (capturadas no menu).
        ## Com avisos desativados: descarta as alterações pendentes para que a ativação durante a sessão comece limpa.
        try:
            if getattr(persistent, "_tl_var_notifs_enabled", True):
                _tl_flush_var_changes()
                _tl_flush_menu_snap()
            else:
                store._tl_pending_var_changes = {}
                store._tl_menu_var_snap = None
        except Exception as e:
            _tl_log("TL var flush error: {}".format(e))

        ## Os nós de ramos futuros acumulados desde o último menu foram resolvidos — limpa-os.
        store._tl_ghost_nodes          = []
        store._tl_skip_ghost_ifs       = set()
        store._tl_recently_changed_vars = set()

        ast_key, location, node_type = _tl_resolve_node_location()

        ## Snapshot para salto sintético — capturado antes da execução do menu para que get_roots()
        ## ainda não inclua este nó. Armazenado em renpy.game.log._tl_snapshot_cache
        ## (fora do store), para acompanhar cada save sem aparecer em roots.
        snap = None
        if not persistent._tl_replaying:
            try:
                snap = _tl_capture_snapshot()
                _tl_log("TL snapshot: idx={} ctx={} roots_keys={}".format(
                    _tl_node_count,
                    getattr(snap["context"], "current", "?"),
                    len(snap["roots"])
                ))
            except Exception as e:
                _tl_log("TL snapshot ERROR idx={}: {}".format(_tl_node_count, e))

        prompt, valid_items = _tl_parse_menu_items(items)
        if not valid_items:
            return None

        ## Durante a repetição, reutiliza o nó já existente no histórico em vez de
        ## criar um novo. Isso preserva a miniatura original e
        ## choice_returns para manter corretas a lógica e a exibição dos indicadores.
        if persistent._tl_replaying:
            target = persistent._tl_replay_target
            for existing in _tl_history:
                if existing["index"] == _tl_node_count:
                    ## Restaura a miniatura N-1 do snapshot, se houver.
                    if (target and existing["index"] == target["node_index"] - 1
                            and persistent._tl_prev_thumb):
                        existing["thumb_bytes"]   = persistent._tl_prev_thumb
                        persistent._tl_prev_thumb = None
                        renpy.save_persistent()
                    _tl_node_count += 1
                    return existing

        rollback_id = None
        ## Obtém o identificador de rollback — permite voltar usando RollbackToIdentifier
        ## se este nó ainda estiver no log de rollback.
        try:
            if renpy.game.log and renpy.game.log.current:
                rollback_id = renpy.game.log.current.identifier
        except Exception as e:
            _tl_log("TL rollback_id failed: {}".format(e))

        node = {
            "index"             : _tl_node_count,
            "prompt"            : prompt,
            "options"           : valid_items,
            "chosen_index"      : None,
            "thumb_bytes"       : None,
            "ast_key"           : ast_key,
            "_location"         : location,
            "_rollback_id"      : rollback_id,
        }
        menu_site = _tl_node_menu_site_key(node)
        _tl_log("TL menu enter: node={} ast={} site={} opts={} current_type={}".format(
            node["index"], node["ast_key"], menu_site,
            len(node["options"]), node_type))
        if node_type != "Menu":
            _tl_log("TL menu current-node mismatch: node={} ast={} current_type={} loc={}".format(
                node["index"], node["ast_key"], node_type, node.get("_location")))
        if (node["ast_key"] is not None and menu_site is not None
                and tuple(node["ast_key"]) != tuple(menu_site)):
            _tl_log("TL menu ast/site mismatch: node={} ast={} site={} loc={}".format(
                node["index"], node["ast_key"], menu_site, node.get("_location")))

        node["img_name"] = _tl_resolve_img_name(ast_key, location)
        _tl_capture_thumb(node, ast_key)

        _tl_history = _tl_history + [node]
        if snap is not None:
            _tl_cache_menu_snapshot(node["index"], snap)
        _tl_node_count += 1

        ## Captura todas as variáveis de rota (inclusive None) para detectar alterações no próximo menu.
        try:
            store._tl_menu_var_snap = _tl_snapshot_route_vars()
        except Exception as e:
            _tl_log("TL menu var snap error: {}".format(e))

        return node


    def _tl_record_after(node, chosen_label=None, chosen_index=None):
        global _tl_context

        if node is None:
            return

        choice_source = "index"
        if chosen_index is None and chosen_label is not None:
            choice_source = "label_fallback"
            for i, label in enumerate(node["options"]):
                if label == chosen_label:
                    chosen_index = i
                    break

        if chosen_index is None or chosen_index < 0 or chosen_index >= len(node["options"]):
            _tl_log("TL NO MATCH: chosen_index={} chosen_label={}".format(
                repr(chosen_index), repr(chosen_label)))
            return

        node["chosen_index"] = chosen_index
        _tl_context = _tl_context + [(node["prompt"], chosen_index)]
        _tl_log("TL choice: node={} idx={} label={} source={}".format(
            node.get("index"), chosen_index,
            repr(node["options"][chosen_index]) if chosen_index < len(node["options"]) else None,
            choice_source))

        pass  ## saves de checkpoint removidos; os pré-saves cobrem todos os menus


    _tl_pending = [None]

    if not getattr(renpy.exports.menu, "_tl_wrapped", False):
        _tl_original_exports_menu = renpy.exports.menu

        def _tl_exports_wrapper(items, set=None, args=None, kwargs=None, item_arguments=None):
            _tl_pending[0] = _tl_record_before(items)
            return _tl_original_exports_menu(items, set, args, kwargs, item_arguments)

        _tl_exports_wrapper._tl_wrapped = True
        renpy.exports.menu = _tl_exports_wrapper

    def _tl_replay_pick(n_index, items, path, target):
        """
        During replay, return (chosen_index, choice_value) for the current node, or None
        if this node is not on the replay path. Does not modify persistent state.
        """
        if target and n_index == target["node_index"]:
            opt_index    = target["option_index"]
            choice_entry = _tl_choice_entry_for_index(items, opt_index)
            return (opt_index, choice_entry[1]) if choice_entry else None
        for path_entry in (path or []):
            if path_entry["index"] == n_index:
                chosen_index = path_entry["chosen_index"]
                choice_entry = (_tl_choice_entry_for_index(items, chosen_index)
                                if chosen_index is not None else None)
                return (chosen_index, choice_entry[1]) if choice_entry else None
        return None

    if not getattr(renpy.store.menu, "_tl_wrapped", False):
        _tl_original_store_menu = renpy.store.menu

        def _tl_store_wrapper(items):
            ## ── Interceptação da repetição ───────────────────────────────────────────
            if persistent._tl_replaying:
                node = _tl_pending[0]
                if node is not None:
                    target  = persistent._tl_replay_target
                    path    = persistent._tl_replay_path or []
                    n_index = node["index"]

                    if target and n_index == target["node_index"]:
                        _tl_log("TL replay: arrived at node={} option={}".format(
                            n_index, target["option_index"]))
                        persistent._tl_replaying     = False
                        persistent._tl_replay_path   = None
                        persistent._tl_replay_target = None
                        ## Sempre desativa o skip ao terminar a repetição — shadow_path permanece definido
                        ## para o botão "Reproduzir automaticamente daqui?", mas o jogador precisa
                        ## ativá-lo manualmente. A repetição auxiliar não é ativada automaticamente.
                        config.skipping = None
                        renpy.save_persistent()

                        _tl_populate_choice_returns(node, items)
                        pick = _tl_replay_pick(n_index, items, path, target)
                        if pick is not None:
                            opt_index, value = pick
                            _tl_pending[0] = None
                            ## Marca a divergência se o salto escolher uma opção diferente.
                            ## node["chosen_index"] pode ser None se o save carregado for de
                            ## antes da criação deste nó; por isso, lê a escolha original de
                            ## persistent._tl_replay_path, capturado antes do carregamento.
                            orig_chosen = next(
                                (e["chosen_index"] for e in path if e["index"] == n_index), None)
                            _tl_record_after(node, chosen_index=opt_index)
                            if orig_chosen is not None and opt_index != orig_chosen:
                                node["_shadow_orig_chosen"] = orig_chosen
                            ## Chama value() em vez de ler .value diretamente para que
                            ## ChoiceReturn.__call__ registre esta escolha em
                            ## persistent._chosen — necessário para que get_chosen()
                            ## retorne True e os indicadores desapareçam após a repetição.
                            return value() if hasattr(value, "value") else value

                    else:
                        pick = _tl_replay_pick(n_index, items, path, target)
                        if pick is not None:
                            chosen_index, value = pick
                            _tl_populate_choice_returns(node, items)
                            _tl_pending[0] = None
                            _tl_record_after(node, chosen_index=chosen_index)
                            return value() if hasattr(value, "value") else value

            ## ── Fluxo normal ───────────────────────────────────────────────────
            node = _tl_pending[0]
            if node is not None:
                _tl_populate_choice_returns(node, items)

            rv = _tl_original_store_menu(items)

            node = _tl_pending[0]
            if node is not None and rv is not None:
                chosen_index = _tl_choice_index_from_return_value(items, rv)

                if chosen_index is not None:
                    _tl_record_after(node, chosen_index=chosen_index)
                else:
                    _tl_log("TL choice resolve failed: node={} valid_opts={} rv_type={}".format(
                        node.get("index"), len(_tl_valid_choice_entries(items)), type(rv).__name__))

                ## Auxílio à repetição: consome entradas do caminho auxiliar ao alcançar um menu correspondente.
                ## Descarta todas as entradas anteriores à correspondência e também a própria correspondência.
                ## Se o jogador escolheu outra opção, marca _shadow_orig_chosen no nó
                ## para que o indicador de divergência continue visível depois que a entrada for removida.
                if store._tl_shadow_path and node is not None:
                    try:
                        remaining, diverged_ci, _ = _tl_consume_shadow_path(
                            store._tl_shadow_path, node, node.get("chosen_index"))
                        if remaining != store._tl_shadow_path:  ## correspondência encontrada — atualiza o caminho
                            if diverged_ci is not None:
                                node["_shadow_orig_chosen"] = diverged_ci
                            store._tl_shadow_path = remaining
                    except Exception as e:
                        _tl_log("TL shadow ERROR: node={} err={}".format(node.get("index"), e))

                _tl_pending[0] = None

            return rv

        _tl_store_wrapper._tl_wrapped = True
        renpy.store.menu = _tl_store_wrapper


init 0 python:
    try:
        _tl_build_ast_map()
    except Exception as e:
        _tl_log("TL AST error: {}".format(e))
        store._tl_ast_ready = True


init python:
    def _tl_on_game_start():
        try:
            _tl_clear_replay_state()
            _tl_save_no_screenshot("wf_start")
        except Exception as e:
            _tl_log("TL ERROR initial save failed: {}".format(e))

    def _tl_on_load():
        _tl_init_snapshot_cache()

        ## Limpa somente quando replaying é True e target é None — estado obsoleto
        ## de uma sessão encerrada inesperadamente. Se ambos estiverem definidos, o carregamento da repetição é válido
        ## e não devemos limpar os dados; caso contrário, os menus serão executados com replaying=False e
        ## farão novas capturas de tela.
        is_synthetic = getattr(persistent, "_tl_synthetic_jump", False)
        if is_synthetic:
            persistent._tl_synthetic_jump = False
            try:
                for scr in renpy.config.overlay_screens:
                    if renpy.display.screen.get_screen(scr) is not None:
                        renpy.display.screen.hide_screen(scr)
                _tl_log("TL on_load: overlay screens hidden after snapshot jump")
            except Exception as e:
                _tl_log("TL on_load: overlay hide failed: {}".format(e))

        if persistent._tl_replaying and persistent._tl_replay_target is None:
            _tl_log("TL stale replay state cleared on load")
            _tl_clear_replay_state()
        elif not persistent._tl_replaying and persistent._tl_replay_path:
            ## Descarta caminhos auxiliares de capítulo gravados por versões antigas.
            _tl_log("TL legacy chapter replay state cleared on load")
            _tl_clear_replay_state()
        elif persistent._tl_replaying:
            _tl_log("TL on_load: path={} target={} replay_path_len={}".format(
                "synthetic" if is_synthetic else "pre-save",
                persistent._tl_replay_target,
                len(persistent._tl_replay_path or [])
            ))
            if not is_synthetic:
                ## Caminho pré-save: reativa o skip para avançar rapidamente até o destino.
                ## O caminho sintético chega diretamente ao destino — não precisa de skip.
                config.skipping = "fast"
        elif persistent._tl_recovery_slot and not persistent._tl_replay_path:
            ## Salto concluído (destino alcançado), mas o jogador salvou e carregou antes
            ## de cancelar — o slot de recuperação ficou obsoleto. Limpa-o para que o Timeline
            ## não exiba um botão de cancelamento para um salto já concluído.
            _tl_log("TL on_load: stale recovery slot cleared (completed jump)")
            _tl_clear_replay_state()
        
        ## Reconstrói o caminho auxiliar após um salto para uma escolha.
        if (persistent._tl_replay_path
                and persistent._tl_replaying
                and persistent._tl_replay_target):
            target_idx = persistent._tl_replay_target["node_index"]
            shadow = [e for e in persistent._tl_replay_path if e.get("index", -1) > target_idx]
            store._tl_shadow_path = shadow or None
            _tl_log("TL on_load: shadow_path set count={}".format(
                len(store._tl_shadow_path) if isinstance(store._tl_shadow_path, list) else store._tl_shadow_path))
        
        ## Cria wf_start se não existir um save inicial atual nem legado.
        if not _tl_slot_exists("wf_start", extensions=("-LT1.save",))[0]:
            try:
                _tl_save_no_screenshot("wf_start")
            except Exception as e:
                _tl_log("TL ERROR start save failed on load: {}".format(e))
        ## Os nós de ramos futuros são temporários — sempre os reinicia ao carregar para limpar qualquer
        ## estado obsoleto (inclusive saves _TlNoRollbackList antigos de sessões anteriores).
        store._tl_ghost_nodes    = []
        store._tl_skip_ghost_ifs = set()
        ## Preenche img_name nos nós do histórico usando o mapa persistente de cenas.
        ## Ignora em carregamentos de repetição — o pré-save foi criado nesta sessão, então todos
        ## os nós já têm img_name preenchido.
        if not persistent._tl_replaying:
            _tl_migrate_img_names()

    def _tl_interact_callback():
        if not hasattr(store, "_tl_history"):
            return  ## os valores padrão do store ainda não foram aplicados (interação anterior ao início do jogo)

        ## Descarrega todas as alterações de variáveis acumuladas desde a última interação como um único
        ## aviso. Se os avisos estiverem desativados, descarta as alterações para começar limpo ao ativá-los durante a sessão.
        if getattr(persistent, "_tl_var_notifs_enabled", True):
            _tl_flush_var_changes()
        else:
            store._tl_pending_var_changes = {}

    config.start_callbacks.append(_tl_on_game_start)
    config.after_load_callbacks.append(_tl_on_load)
    config.interact_callbacks.append(_tl_interact_callback)

## -----------------------------------------------------------------------------
## Seção 2: timeline_init.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — timeline_init.rpy
## Variáveis de store, dados persistentes, constantes e funções auxiliares.
## =============================================================================

init -2 python:

    import os, uuid, time as _tl_time, json as _tl_json
    import hashlib as _tl_hashlib
    try:
        import __builtin__ as _tl_builtins
    except ImportError:
        import builtins as _tl_builtins

    _tl_builtin_id = _tl_builtins.id

    ## Armazena as funções nativas antes que personagens do jogo possam sobrescrevê-las.
    _TL_MIN = min
    _TL_MAX = max

    def _tl_log(msg):
        try:
            debug_dir = os.path.join(renpy.config.gamedir, "cache")
            if not os.path.isdir(debug_dir):
                os.makedirs(debug_dir)
            debug_path = os.path.join(debug_dir, "debug.txt")
            with open(debug_path, "a") as f:
                f.write(msg + "\n")
        except Exception:
            pass

    ## Dimensões das miniaturas
    TL_THUMB_WIDTH  = 320
    TL_THUMB_HEIGHT = 180

    TL_THUMB_CACHE_MAX  = 500  ## limite de miniaturas (~25 MB com cerca de 50 KB por miniatura)
    TL_DEBUG_GHOST      = False   ## detalhes da síntese de ramos futuros (execução If, agrupamento, imagens dos ramos, resolução de imagens)
    TL_DEBUG_SEEN       = False   ## detalhes da resolução do estado visto (opt_seen, peek_seen)
    TL_DEBUG_ROUTE      = False   ## detalhes do rastreador de rotas (diferenças de variáveis por bloco Python e busca por valores padrão)
    TL_DEBUG_MENU       = False   ## detalhes do fluxo por menu (entrada no menu, img_name, consumo do caminho auxiliar)
    TL_DEBUG_ASSET      = False   ## detalhes do cache de miniaturas (cache encontrado/gerado e atualizações do mapa de cenas)

    def _tl_runtime_cache_store():
        """
        Return a transient runtime cache dict hung off `renpy.game.script`.

        This keeps live AST objects and other heavyweight helpers out of the
        save payload while preserving simple in-session memoization.
        """
        try:
            script = renpy.game.script
        except Exception:
            return {}
        cache = getattr(script, "_tl_runtime_cache_store", None)
        if not isinstance(cache, dict):
            cache = {}
            try:
                setattr(script, "_tl_runtime_cache_store", cache)
            except Exception:
                return {}
        return cache

    def _tl_runtime_choice_returns(node, create=False):
        """Return transient choice-return slots for one history node."""
        if not isinstance(node, dict):
            return None
        rt    = _tl_runtime_cache_store()
        cache = rt.setdefault("choice_returns", {})
        key   = _tl_builtin_id(node)
        if create and key not in cache:
            cache[key] = [None] * len(node.get("options", []))
        return cache.get(key) or node.get("_choice_returns")

    ## -------------------------------------------------------------------------
    ## Constantes de tamanho de fonte
    ## -------------------------------------------------------------------------
    TL_SIZE_BODY     = 21   ## todo o texto comum — opções, labels e botões
    TL_SIZE_TITLE    = 38   ## cabeçalho "TIMELINE"
    TL_SIZE_DOT      = 14   ## ● pontos indicadores
    TL_SIZE_BADGE    = 12   ## rótulos pequenos
    TL_SIZE_HEADER   = 28   ## cabeçalho da janela modal
    TL_SIZE_SUBTITLE = 17   ## linhas de informações secundárias (alterações de variáveis e condições)

    def _tl_load_thumb_dict(path):
        """
        Load the thumbnail pickle from path. Tries gzip first, falls back to raw.
        Returns {} on any failure so callers always get a valid dict.
        """
        import gzip
        from renpy.compat.pickle import loads
        try:
            with gzip.open(path, "rb") as f:
                thumb_data = loads(f.read())
            _tl_log("Timeline: miniaturas carregadas (gzip): miniaturas={} recursos={}".format(
                len(thumb_data.get("thumb", {})), len(thumb_data.get("asset_thumb", {}))))
            return thumb_data
        except Exception as err:
            _tl_log("TL thumbs gzip load error: {} — trying raw".format(err))
        try:
            with open(path, "rb") as f:
                thumb_data = loads(f.read())
            _tl_log("TL thumbs loaded (raw): thumb={} asset={}".format(
                len(thumb_data.get("thumb", {})), len(thumb_data.get("asset_thumb", {}))))
            return thumb_data
        except Exception as err:
            _tl_log("TL thumbs raw load error: {}".format(err))
            return {}

## Variáveis por save — podem ser carregadas com segurança em saves anteriores ao mod.
default _tl_history    = []   ## lista de dicionários de nós
default _tl_context    = []   ## [(prompt, chosen_index), ...]
default _tl_node_count = 0

## Estado da interface — não é salvo.
default _tl_modal_node  = None  ## nó cuja janela modal está aberta
default _tl_load_slot   = ""    ## slot a carregar pelo label _tl_do_load
default _tl_pending_save_index    = None  ## legado — gravação de checkpoints removida; mantido para saves e testes antigos
default _tl_early_save_idx        = None  ## legado — gravação de checkpoints removida; mantido para saves e testes antigos
default _tl_ast_ready  = False  ## True quando o mapa AST estiver pronto
default _tl_shadow_path = None  ## [{location, chosen_index}] dicas de repetição, ou None
default _tl_ghost_nodes      = []   ## dicionários de ramos futuros If no trecho atual da cena
default _tl_skip_ghost_ifs   = set()   ## chaves AST cujas linhas irmãs já foram emitidas
default _tl_pending_var_changes = {} ## {var_name: (old_val, new_val)} — enviados ao aviso e depois limpos
default _tl_menu_var_snap = None    ## snapshot das variáveis de rota anterior ao menu para identificar mudanças no próximo menu
default _tl_recently_changed_vars = set()  ## variáveis alteradas desde o último menu; limpas em _tl_record_before
default _tl_var_if_seen_keys = {}   ## {var_name: set(ast_keys)} — nós If executados nesta sessão

## Estado da repetição — armazenado em persistent para sobreviver a um ciclo de save/load.
init python:
    if persistent._tl_replaying is None:
        persistent._tl_replaying = False
    if not hasattr(persistent, "_tl_img_movie_cache") or persistent._tl_img_movie_cache is None:
        persistent._tl_img_movie_cache = {}
    if not hasattr(persistent, "_tl_var_notifs_enabled") or persistent._tl_var_notifs_enabled is None:
        persistent._tl_var_notifs_enabled = False

    if not hasattr(persistent, "_tl_asset_thumb_dirty"):
        persistent._tl_asset_thumb_dirty = False

    if not hasattr(persistent, "_tl_ghost_node_cache") or persistent._tl_ghost_node_cache is None:
        persistent._tl_ghost_node_cache = {}

    if persistent._tl_scene_map_version is None or persistent._tl_scene_map_version < 3:
        persistent._tl_menu_scene_map = {}
        persistent._tl_scene_map_version = 3
    elif persistent._tl_menu_scene_map is None:
        persistent._tl_menu_scene_map = {}

    ## ── Cache de miniaturas — mantido nos atributos de renpy.game (não em persistent) ──────────
    ## renpy.game é um objeto de módulo Python cujos atributos sobrevivem a renpy.load(), mas
    ## não são serializados por save_persistent(). Isso mantém persistent pequeno para
    ## que save_persistent() seja rápido durante os saltos.
    ## O cache é carregado de um arquivo pickle na inicialização e gravado ao sair.
    _tl_thumbs_path = os.path.join(renpy.config.savedir, "_tl_thumbs.pkl")
    try:
        if os.path.exists(_tl_thumbs_path):
            thumb_data = _tl_load_thumb_dict(_tl_thumbs_path)
            renpy.game._tl_thumb_cache       = thumb_data.get("thumb", {})
            renpy.game._tl_asset_thumb_cache = thumb_data.get("asset_thumb", {})
        else:
            _tl_log("TL thumbs init: no pkl file — starting empty")
            renpy.game._tl_thumb_cache      = {}
            renpy.game._tl_asset_thumb_cache = {}
    except Exception as e:
        _tl_log("TL thumbs load error: {}".format(e))
        renpy.game._tl_thumb_cache      = {}
        renpy.game._tl_asset_thumb_cache = {}

    ## Migração única: transfere os caches persistentes existentes para renpy.game.
    ## Depois disso, persistent._tl_thumb_cache / _tl_asset_thumb_cache permanecem vazios.
    mig_thumb  = len(getattr(persistent, "_tl_thumb_cache", None) or {})
    mig_asset  = len(getattr(persistent, "_tl_asset_thumb_cache", None) or {})
    if mig_thumb:
        renpy.game._tl_thumb_cache.update(persistent._tl_thumb_cache)
        persistent._tl_thumb_cache = {}
    if mig_asset:
        renpy.game._tl_asset_thumb_cache.update(persistent._tl_asset_thumb_cache)
        persistent._tl_asset_thumb_cache = {}
    if mig_thumb or mig_asset:
        _tl_log("TL thumbs migration: moved thumb={} asset={} from persistent".format(
            mig_thumb, mig_asset))
        if mig_asset:
            persistent._tl_asset_thumb_dirty = True

    def _tl_save_thumbs():
        import gzip
        thumb_cache       = getattr(renpy.game, "_tl_thumb_cache", None)
        asset_thumb_cache = getattr(renpy.game, "_tl_asset_thumb_cache", None)
        dirty             = getattr(persistent, "_tl_asset_thumb_dirty", False)
        path              = os.path.join(renpy.config.savedir, "_tl_thumbs.pkl")
        has_replay_thumbs = bool(thumb_cache)
        no_file           = not os.path.exists(path)
        has_asset_thumbs  = bool(asset_thumb_cache)
        if not dirty and not has_replay_thumbs and not (no_file and has_asset_thumbs):
            _tl_log("Timeline: gravação das miniaturas ignorada: cache sem alterações")
            return
        try:
            from renpy.compat.pickle import dumps
            thumb_data = {
                "thumb":       thumb_cache or {},
                "asset_thumb": asset_thumb_cache or {},
            }
            with gzip.open(path, "wb", compresslevel=1) as f:
                f.write(dumps(thumb_data))
            _tl_log("TL thumbs saved: thumb={} asset={}".format(
                len(thumb_data["thumb"]), len(thumb_data["asset_thumb"])))
            persistent._tl_asset_thumb_dirty = False
            renpy.save_persistent()
        except Exception as e:
            _tl_log("TL thumbs save error: {}".format(e))

    config.quit_callbacks.append(_tl_save_thumbs)


init -2 python:

    def _tl_count_locked_branches():
        descs = getattr(persistent, "_tl_all_branch_descs", None) or []
        return sum(1 for desc in descs if not _tl_eval_seen_fn(desc))


    def _tl_build_ast_map():
        try:
            namemap = renpy.game.script.namemap
        except Exception as e:
            _tl_log("TL AST: namemap not available: {}".format(e))
            store._tl_ast_ready = True
            return

        nodes = list(namemap.values())
        if not nodes:
            store._tl_ast_ready = True
            return

        _tl_log("Timeline: analisando {} nós identificados no AST".format(len(nodes)))
        store._tl_ast_ready = True

        _tl_build_route_index(nodes)
        _tl_build_coverage_index(nodes)
        _tl_build_menu_scene_index(nodes)


    def _tl_salvage_history_ast_keys(line_slop=100):
        """
        Re-match stale history ast_keys to current AST menus after a game script update.

        A node is stale when its ast_key is not present in the live menu lookup.
        Matching uses content (history options ⊆ live menu labels) as the primary
        signal and line proximity (within line_slop) as secondary. A used-key set
        prevents two history nodes from claiming the same live menu.

        On match: re-stamps ast_key and clears img_name so _tl_migrate_img_names()
        can refill it from the current scene map.

        Returns {skipped, matched, unmatched, total}.
        User-triggered only — not called automatically on load.
        """
        _live    = _tl_live_menu_lookup()
        _history = getattr(store, "_tl_history", [])
        if not _history:
            _msg = "Salvage: nothing to do (empty history)"
            _tl_log("TL salvage: " + _msg)
            renpy.notify(_msg)
            return {"skipped": 0, "matched": 0, "unmatched": 0, "total": 0}

        ## Monta o mapa de candidatos: arquivo -> [(linha, nó de menu)] ordenados.
        _by_file = {}
        for (_cfile, _cline), _cmenu in _live.items():
            _by_file.setdefault(_cfile, []).append((_cline, _cmenu))
        for _lst in _by_file.values():
            _lst.sort()

        _skipped       = 0
        _matched       = 0
        _unmatched     = 0
        _any_matched   = False
        _used_keys     = set()   ## chaves ativas (arquivo, linha) associadas a uma chave obsoleta resolvida
        _stale_to_live = {}      ## chave obsoleta (arquivo, linha) -> chave ativa (arquivo, linha) ou None

        for _n in _history:
            _ak = _n.get("ast_key")
            if not isinstance(_ak, (list, tuple)) or len(_ak) != 2:
                _unmatched += 1
                continue
            _ak = tuple(_ak)
            _stored_file, _stored_line = _ak

            ## Já é válido — há um menu ativo nesta chave exata.
            if _ak in _live:
                _skipped += 1
                continue

            ## A mesma chave obsoleta já apareceu (por exemplo, em um menu repetido) — reutiliza o resultado em cache.
            if _ak in _stale_to_live:
                _cached = _stale_to_live[_ak]
                if _cached is None:
                    _unmatched += 1
                else:
                    _live_menu = _live[_cached]
                    _n["ast_key"]  = (_live_menu.filename, _live_menu.linenumber)
                    _n["img_name"] = None
                    _matched    += 1
                    _any_matched = True
                continue

            ## Obsoleto e ainda não visto — procura candidatos no mesmo arquivo.
            _candidates   = _by_file.get(_stored_file, [])
            _history_opts = frozenset(_n.get("options") or [])

            _best      = None
            _best_dist = line_slop + 1
            for (_cline, _cmenu) in _candidates:
                _ckey = (_stored_file, _cline)
                if _ckey in _used_keys:
                    continue                   ## já associada a outra chave obsoleta
                _live_labels = frozenset(
                    _item[0] for _item in (_cmenu.items or []) if _item[2] is not None
                )
                if not (_history_opts <= _live_labels):
                    continue                   ## conteúdo diferente
                _dist = abs(_stored_line - _cline)
                if _dist <= line_slop and _dist < _best_dist:
                    _best      = (_cline, _cmenu)
                    _best_dist = _dist

            if _best is None:
                _stale_to_live[_ak] = None
                _unmatched += 1
                _tl_log("TL salvage: node={} {}:{} -> unmatched (opts={})".format(
                    _n.get("index"), _stored_file, _stored_line, len(_history_opts)))
                continue

            _new_line, _new_menu = _best
            _new_key              = (_stored_file, _new_line)
            _stale_to_live[_ak]  = _new_key
            _used_keys.add(_new_key)
            _n["ast_key"]  = (_new_menu.filename, _new_menu.linenumber)
            _n["img_name"] = None
            _matched    += 1
            _any_matched = True
            _tl_log("TL salvage: node={} {} {}->{}".format(
                _n.get("index"), _stored_file, _stored_line, _new_line))

        if _any_matched:
            _tl_migrate_img_names()
            renpy.save_persistent()

        _msg = "Salvage: {} matched / {} missed / {} ok".format(_matched, _unmatched, _skipped)
        _tl_log("TL salvage: total={} matched={} unmatched={} skipped={}".format(
            len(_history), _matched, _unmatched, _skipped))
        renpy.notify(_msg)
        return {"skipped": _skipped, "matched": _matched, "unmatched": _unmatched, "total": len(_history)}


    def _tl_migrate_img_names():
        """
        Stamp img_name on history nodes that are missing it, using the persistent
        menu image map. Runs once per load (store flag guards re-entry from timeline screen).
        """
        _scene_map = persistent._tl_menu_scene_map or {}
        if not _scene_map:
            return
        _history  = getattr(store, "_tl_history", [])
        _changed  = 0
        _misses   = 0
        for _n in _history:
            if _n.get("img_name") is not None:
                continue
            _k = _n.get("ast_key")
            _ast_key = _tl_menu_site_key(_k[0], _k[1]) if isinstance(_k, tuple) and len(_k) == 2 else None
            _loc_key = _tl_location_menu_site_key(_n.get("_location"))
            if _ast_key and _ast_key in _scene_map:
                _n["img_name"] = _scene_map[_ast_key]
                _changed += 1
            elif _loc_key and _loc_key in _scene_map:
                _n["img_name"] = _scene_map[_loc_key]
                _changed += 1
            else:
                _misses += 1
        _tl_log("Timeline: migração de imagens: total={} alteradas={} não encontradas={}".format(
            len(_history), _changed, _misses))

## -----------------------------------------------------------------------------
## Seção 3: timeline_save_hooks.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## MOD TIMELINE — timeline_save_hooks.rpy
## Tratamento controlado de falhas para compatibilidade de saves.
## =============================================================================
##
## Dois casos de falha tratados aqui:
##
## Caso 1 — Mod instalado, save sem dados do Timeline (save antigo carregado):
##   As instruções `default` em timeline_init.rpy já tratam este caso.
##   _tl_history assume [] como padrão e exibe "Nenhuma escolha registrada ainda"
##   A tela fica vazia, e o mod começa a registrar a partir da sessão atual.
##   Não é necessário código especial — o Ren'Py aplica os valores padrão às variáveis ausentes.
##
## Caso 2 — Mod REMOVIDO, save COM dados do Timeline:
##   Por projeto, o sistema de save do Ren'Py ignora variáveis desconhecidas nos pickles —
##   o jogo carrega normalmente e as chaves _tl_* são ignoradas. Sem erro.
##
## O que adicionamos: um hook pós-carregamento que valida _tl_history,
## para que saves corrompidos ou incompletos sejam tratados sem encerrar o jogo.

init python:
    def _tl_validate_on_load():
        """
        Called after every save load. Resets timeline state if loaded
        data is corrupt or an unexpected type.
        """
        import store as _store
        _tl_runtime_cache_store().pop("choice_returns", None)

        ## Se _tl_history estiver ausente ou tiver tipo inválido, reinicia como lista vazia.
        history = getattr(_store, "_tl_history", None)
        if not isinstance(history, list):
            _tl_log("TL: _tl_history invalid on load ({}), resetting".format(type(history)))
            _store._tl_history = []

        ## Valida cada nó e descarta silenciosamente as entradas malformadas.
        clean = []
        for node in getattr(_store, "_tl_history", []):
            if (isinstance(node, dict)
                    and "index" in node
                    and "options" in node
                    and isinstance(node["options"], list)):
                ## Saves antigos podem conter dados temporários usados apenas durante a execução.
                node.pop("_state_snapshot", None)
                node.pop("_choice_returns", None)
                node.pop("chapter_start", None)
                node.pop("chapter_end", None)
                clean.append(node)
            else:
                _tl_log("TL: dropping malformed node: {}".format(repr(node)[:80]))
        _store._tl_history = clean

        ## Reindexa os nós caso os índices estejam obsoletos.
        for i, node in enumerate(_store._tl_history):
            node["index"] = i

        ## Valida o caminho auxiliar — deve ser uma lista ou None.
        if not isinstance(getattr(_store, "_tl_shadow_path", None), (list, type(None))):
            _store._tl_shadow_path = None

        ## Reinicia o estado temporário da interface — não é seguro restaurá-lo entre sessões.
        _store._tl_modal_node       = None
        _store._tl_ghost_nodes      = []

        ## Remove o resultado do executor de testes, se existir — _TLTestResults é uma instância de classe
        ## e não pode ser desserializado sem o mod. Limpá-lo aqui corrige saves
        ## que tenham sido contaminados antes desta correção.
        if hasattr(_store, "_tl_test_results"):
            del _store._tl_test_results
        ## NOTA: _tl_ast_ready e _tl_ast_map são derivados do
        ## script estático do jogo (não muda entre carregamentos) — não os reinicie aqui.
        _tl_log("Timeline: validação após o carregamento concluída ({} nós)".format(
            len(_store._tl_history)))

    ## Registra o validador como callback after_load.
    config.after_load_callbacks.append(_tl_validate_on_load)

