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
            _tl_log("Timeline location lookup failed: {}".format(e))
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
        if WELLS_TL_DEBUG_MENU:
            _tl_log("Timeline img_name: ast_key={} img_name={}".format(ast_key, img_name))
        return img_name

    def _tl_capture_thumb(node, ast_key, force=False):
        """
        Capture or restore a screenshot thumbnail for the given menu node.
        Defers capture while a nested menu context is active, so a save/load
        screen cannot be cached as the scene thumbnail.
        """
        need_frozen_thumb = bool(node["img_name"] and _tl_img_name_is_movie(node["img_name"]))
        ## Captura forçada ocorre com a choice visível e inclui a composição de tela atual.
        need_runtime_thumb = bool(force) or (not node["img_name"] or need_frozen_thumb)
        if not force and node["img_name"] and not need_frozen_thumb:
            ## Sem captura ativa de choice, dispensa a captura quando há um arquivo direto.
            ## Com force=True, preserva a composição completa mostrada durante a escolha.
            need_runtime_thumb = not bool(_tl_resolve_asset_file(node["img_name"]))
        if not need_runtime_thumb:
            return False
        contexts = getattr(renpy.game, "contexts", None)
        if not force and contexts is not None and len(contexts) > 1:
            node["_tl_thumb_capture_pending"] = True
            _tl_log("Timeline thumb: captura adiada em contexto de menu aninhado; node={} ast={}".format(
                node.get("index"), ast_key))
            return False
        cache_key    = str(ast_key) if ast_key else None
        thumb_cache  = getattr(renpy.game, "_tl_thumb_cache", {})
        cached_thumb = thumb_cache.get(cache_key) if cache_key else None
        captured = False
        if not persistent._tl_replaying and (force or not cached_thumb) and not config.skipping:
            thumb = _tl_capture_thumbnail()
            if thumb:
                if cache_key:
                    try:
                        thumb_cache[cache_key] = thumb
                        while len(thumb_cache) > WELLS_TL_THUMB_CACHE_MAX:
                            thumb_cache.pop(next(iter(thumb_cache)))
                    except Exception as e:
                        _tl_log("Timeline thumb cache write failed: {}".format(e))
                        node["thumb_bytes"] = thumb
                else:
                    node["thumb_bytes"] = thumb
                captured = True
        if need_frozen_thumb and WELLS_TL_DEBUG_MENU:
            _tl_log("Timeline movie thumb fallback: ast_key={} img_name={}".format(ast_key, node["img_name"]))
        return captured

    def _tl_begin_choice_thumb_capture(node):
        """Schedule a thumbnail capture while Ren'Py is displaying this choice."""
        try:
            renpy.game._tl_pending_choice_thumb = {
                "node": node,
                "ticks": 0,
            }
        except Exception as e:
            _tl_log("Timeline thumb: não foi possível agendar captura da choice: {}".format(e))

    def _tl_end_choice_thumb_capture(node):
        """Discard a pending capture after its menu interaction ends."""
        try:
            pending = getattr(renpy.game, "_tl_pending_choice_thumb", None)
            if pending and (node is None or pending.get("node") is node):
                renpy.game._tl_pending_choice_thumb = None
        except Exception:
            pass

    def _tl_capture_visible_choice_thumb():
        """Capture only after the game choice screen is active and rendered."""
        try:
            pending = getattr(renpy.game, "_tl_pending_choice_thumb", None)
            if not pending:
                return

            ## Não capture menus auxiliares abertos em contexto aninhado, como save/load.
            contexts = getattr(renpy.game, "contexts", None)
            if contexts is not None and len(contexts) > 1:
                return

            try:
                choice_screen = renpy.display.screen.get_screen("choice")
            except Exception:
                choice_screen = None
            if choice_screen is None:
                return

            ## Aguarda mais um ciclo periódico para a choice já ter sido desenhada.
            pending["ticks"] += 1
            if pending["ticks"] < 2:
                return

            node = pending.get("node")
            if node is not None:
                captured = _tl_capture_thumb(node, node.get("ast_key"), force=True)
                node["_tl_thumb_capture_pending"] = False
                if captured:
                    _tl_log("Timeline thumb: captura feita com a choice visível; node={} ast={}".format(
                        node.get("index"), node.get("ast_key")))
                else:
                    ## Remove uma captura anterior possivelmente incorreta; não a reaproveita.
                    key = str(node["ast_key"]) if node.get("ast_key") else None
                    cache = getattr(renpy.game, "_tl_thumb_cache", {})
                    if key:
                        cache.pop(key, None)
                    _tl_log("Timeline thumb: captura da choice indisponível; node={} ast={}".format(
                        node.get("index"), node.get("ast_key")))
            renpy.game._tl_pending_choice_thumb = None
        except Exception as e:
            _tl_log("Timeline thumb: falha ao capturar choice visível: {}".format(e))
            try:
                renpy.game._tl_pending_choice_thumb = None
            except Exception:
                pass

    def _tl_register_choice_thumb_callback():
        """Register without replacing callbacks already installed by the game."""
        try:
            renpy.game._tl_pending_choice_thumb = None
        except Exception:
            pass

        _tl_capture_visible_choice_thumb._wells_tl_choice_thumb_callback = True
        callbacks = getattr(config, "periodic_callbacks", None)
        if isinstance(callbacks, list):
            ## Shift+R redefines the function object. Remove its old registration first.
            callbacks[:] = [
                callback for callback in callbacks
                if not getattr(callback, "_wells_tl_choice_thumb_callback", False)
            ]
            callbacks.append(_tl_capture_visible_choice_thumb)
            return

        previous = getattr(config, "periodic_callback", None)
        if getattr(previous, "_wells_tl_choice_thumb_wrapper", False):
            previous = getattr(previous, "_wells_tl_previous_callback", None)

        def _tl_legacy_periodic_callback():
            if previous:
                previous()
            _tl_capture_visible_choice_thumb()

        _tl_legacy_periodic_callback._wells_tl_choice_thumb_wrapper = True
        _tl_legacy_periodic_callback._wells_tl_previous_callback = previous
        config.periodic_callback = _tl_legacy_periodic_callback

    _tl_register_choice_thumb_callback()


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
            _tl_log("Timeline var flush error: {}".format(e))

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
                _tl_log("Timeline snapshot: idx={} ctx={} roots_keys={}".format(
                    _tl_node_count,
                    getattr(snap["context"], "current", "?"),
                    len(snap["roots"])
                ))
            except Exception as e:
                _tl_log("Timeline snapshot ERROR idx={}: {}".format(_tl_node_count, e))

        prompt, valid_items, option_ast_indices = _tl_parse_menu_items(items)
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
            _tl_log("Timeline rollback_id failed: {}".format(e))

        node = {
            "index"             : _tl_node_count,
            "prompt"            : prompt,
            "options"           : valid_items,
            "option_ast_indices": option_ast_indices,
            "chosen_index"      : None,
            "chosen_ast_index"  : None,
            "_tl_options_pending_sync": True,
            "thumb_bytes"       : None,
            "ast_key"           : ast_key,
            "_location"         : location,
            "_rollback_id"      : rollback_id,
        }
        menu_site = _tl_node_menu_site_key(node)
        _tl_log("Timeline menu enter: node={} ast={} site={} opts={} current_type={}".format(
            node["index"], node["ast_key"], menu_site,
            len(node["options"]), node_type))
        if node_type != "Menu":
            _tl_log("Timeline menu current-node mismatch: node={} ast={} current_type={} loc={}".format(
                node["index"], node["ast_key"], node_type, node.get("_location")))
        if (node["ast_key"] is not None and menu_site is not None
                and tuple(node["ast_key"]) != tuple(menu_site)):
            _tl_log("Timeline menu ast/site mismatch: node={} ast={} site={} loc={}".format(
                node["index"], node["ast_key"], menu_site, node.get("_location")))

        node["img_name"] = _tl_resolve_img_name(ast_key, location)
        ## A captura é solicitada agora, mas só será feita quando a tela da choice
        ## estiver ativa e já tiver sido desenhada pelo Ren'Py.
        node["_tl_thumb_capture_pending"] = True

        _tl_history = _tl_history + [node]
        if snap is not None:
            _tl_cache_menu_snapshot(node["index"], snap)
        _tl_node_count += 1

        ## Captura todas as variáveis de rota (inclusive None) para detectar alterações no próximo menu.
        try:
            store._tl_menu_var_snap = _tl_snapshot_route_vars()
        except Exception as e:
            _tl_log("Timeline menu var snap error: {}".format(e))

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
            _tl_log("Timeline NO MATCH: chosen_index={} chosen_label={}".format(
                repr(chosen_index), repr(chosen_label)))
            return

        node["chosen_index"] = chosen_index
        node["chosen_ast_index"] = _tl_node_option_ast_index(node, chosen_index)
        _tl_context = _tl_context + [(node["prompt"], chosen_index)]
        _tl_log("Timeline choice: node={} idx={} label={} source={}".format(
            node.get("index"), chosen_index,
            repr(node["options"][chosen_index]) if chosen_index < len(node["options"]) else None,
            choice_source))

        ## Mantém um registro leve das escolhas fora dos saves do Ren'Py.
        ## O JSON guarda somente o mapa de caminhos, sem snapshots ou miniaturas.
        _tl_route_map_record_current_history()

        pass  ## saves de checkpoint removidos; os pré-saves cobrem todos os menus


    _tl_pending = [None]

    if not getattr(renpy.exports.menu, "_tl_wrapped", False):
        _tl_original_exports_menu = renpy.exports.menu

        def _tl_make_exports_wrapper(original_menu):
            ## A closure retains the original through Shift+R even if the store is reinitialized.
            def _tl_exports_wrapper(items, *args, **kwargs):
                _tl_pending[0] = _tl_record_before(items)
                return original_menu(items, *args, **kwargs)

            _tl_exports_wrapper._tl_wrapped = True
            _tl_exports_wrapper._tl_original = original_menu
            _tl_exports_wrapper.__wrapped__ = original_menu
            return _tl_exports_wrapper

        renpy.exports.menu = _tl_make_exports_wrapper(_tl_original_exports_menu)

    def _tl_abort_replay(reason):
        """Stop automatic replay if the recorded structural choice is no longer available."""
        persistent._tl_replaying = False
        persistent._tl_replay_path = None
        persistent._tl_replay_target = None
        store._tl_shadow_path = None
        config.skipping = None
        renpy.save_persistent()
        _tl_log("Timeline replay canceled safely: {}".format(reason))

    def _tl_replay_pick(n_index, items, path, target, node=None):
        """
        Resolve recorded choices by their original Menu.items index.
        Older saved history without that index falls back to the stored visible position.
        """
        if target and n_index == target["node_index"]:
            opt_index = target["option_index"]
            ast_index = target.get("option_ast_index")
            if ast_index is None:
                ast_index = _tl_node_option_ast_index(node, opt_index)
            if ast_index is not None:
                choice_entry = _tl_choice_entry_for_ast_index(items, ast_index)
                if choice_entry is None:
                    _tl_abort_replay("opção estrutural {} ausente no menu {}".format(ast_index, n_index))
                    return None
                history_index = _tl_node_option_index_for_ast(node, ast_index, opt_index)
                return history_index, choice_entry[1]
            choice_entry = _tl_choice_entry_for_index(items, opt_index)
            return (opt_index, choice_entry[1]) if choice_entry else None

        for path_entry in (path or []):
            if path_entry["index"] == n_index:
                chosen_index = path_entry["chosen_index"]
                ast_index = path_entry.get("option_ast_index")
                if ast_index is None:
                    ast_index = _tl_node_option_ast_index(node, chosen_index)
                if ast_index is not None:
                    choice_entry = _tl_choice_entry_for_ast_index(items, ast_index)
                    if choice_entry is None:
                        _tl_abort_replay("opção estrutural {} ausente no menu {}".format(ast_index, n_index))
                        return None
                    history_index = _tl_node_option_index_for_ast(node, ast_index, chosen_index)
                    return history_index, choice_entry[1]
                choice_entry = (_tl_choice_entry_for_index(items, chosen_index)
                                if chosen_index is not None else None)
                return (chosen_index, choice_entry[1]) if choice_entry else None
        return None

    if not getattr(renpy.store.menu, "_tl_wrapped", False):
        _tl_original_store_menu = renpy.store.menu

    def _tl_make_store_wrapper(original_store_menu):
        def _tl_store_wrapper(items, *args, **kwargs):
            node = _tl_pending[0]
            if node is not None and node.pop("_tl_options_pending_sync", False):
                _tl_sync_node_options(node, items)

            ## Intercepta a retomada automática de escolhas.
            if persistent._tl_replaying:
                node = _tl_pending[0]
                if node is not None:
                    target = persistent._tl_replay_target
                    path = persistent._tl_replay_path or []
                    n_index = node["index"]

                    if target and n_index == target["node_index"]:
                        _tl_log("Timeline replay: choice screen restored at node={}".format(n_index))
                        persistent._tl_replaying = False
                        persistent._tl_replay_path = None
                        persistent._tl_replay_target = None
                        config.skipping = None
                        renpy.save_persistent()
                        ## Fall through to original_store_menu below. This presents the
                        ## game's actual choice screen instead of selecting from a card.

                    else:
                        pick = _tl_replay_pick(n_index, items, path, target, node)
                        if pick is not None:
                            chosen_index, value = pick
                            _tl_populate_choice_returns(node, items)
                            _tl_pending[0] = None
                            _tl_record_after(node, chosen_index=chosen_index)
                            return value() if hasattr(value, "value") else value

            ## Fluxo normal.
            node = _tl_pending[0]
            if node is not None:
                _tl_populate_choice_returns(node, items)

            ## O callback periódico captura a imagem durante a tela real da choice.
            ## O pedido fica fora do store do jogo, para não entrar nos save games.
            node = _tl_pending[0]
            if node is not None and node.get("_tl_thumb_capture_pending"):
                _tl_begin_choice_thumb_capture(node)

            rv = original_store_menu(items, *args, **kwargs)

            ## Se a escolha terminou antes da captura, descarta o pedido. O cache da cena
            ## continua disponível como alternativa, sem reaproveitar uma tela antiga.
            node = _tl_pending[0]
            _tl_end_choice_thumb_capture(node)
            if node is not None and rv is not None:
                chosen_index = _tl_choice_index_from_return_value(items, rv, node)
                if chosen_index is not None:
                    _tl_record_after(node, chosen_index=chosen_index)
                else:
                    _tl_log("Timeline escolha não resolvida: nó={} opções={} tipo={}".format(
                        node.get("index"), len(_tl_valid_choice_entries(items)), type(rv).__name__))

                if store._tl_shadow_path and node is not None:
                    try:
                        remaining, diverged_ci, _ = _tl_consume_shadow_path(
                            store._tl_shadow_path, node, node.get("chosen_index"),
                            node.get("chosen_ast_index"))
                        if remaining != store._tl_shadow_path:
                            if diverged_ci is not None:
                                node["_shadow_orig_chosen"] = diverged_ci
                            store._tl_shadow_path = remaining
                    except Exception as e:
                        _tl_log("Timeline shadow ERRO: nó={} erro={}".format(node.get("index"), e))

                _tl_pending[0] = None
            return rv

        _tl_store_wrapper._tl_wrapped = True
        _tl_store_wrapper._tl_original = original_store_menu
        _tl_store_wrapper.__wrapped__ = original_store_menu
        return _tl_store_wrapper


    if not getattr(renpy.store.menu, "_tl_wrapped", False):
        renpy.store.menu = _tl_make_store_wrapper(renpy.store.menu)


init 0 python:
    try:
        _tl_build_ast_map()
    except Exception as e:
        _tl_log("Timeline AST error: {}".format(e))
        store._tl_ast_ready = True


init python:
    def _tl_on_game_start():
        try:
            _tl_clear_replay_state()
            _tl_save_no_screenshot("wf_start")
        except Exception as e:
            _tl_log("Timeline ERROR initial save failed: {}".format(e))

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
                _tl_log("Timeline on_load: overlay screens hidden after snapshot jump")
            except Exception as e:
                _tl_log("Timeline on_load: overlay hide failed: {}".format(e))

        if persistent._tl_replaying and persistent._tl_replay_target is None:
            _tl_log("Timeline stale replay state cleared on load")
            _tl_clear_replay_state()
        elif not persistent._tl_replaying and persistent._tl_replay_path:
            ## Descarta caminhos auxiliares de capítulo gravados por versões antigas.
            _tl_log("Timeline legacy chapter replay state cleared on load")
            _tl_clear_replay_state()
        elif persistent._tl_replaying:
            _tl_log("Timeline on_load: path={} target={} replay_path_len={}".format(
                "synthetic" if is_synthetic else "pre-save",
                persistent._tl_replay_target,
                len(persistent._tl_replay_path or [])
            ))
            if not is_synthetic:
                ## Caminho pré-save: reativa o skip para avançar rapidamente até o destino.
                ## O caminho sintético chega diretamente ao destino — não precisa de skip.
                config.skipping = "fast"
        elif (persistent._tl_recovery_slot and not persistent._tl_replay_path
                and not getattr(persistent, "_tl_choice_return_pending", False)):
            ## Salto concluído (destino alcançado), mas o jogador salvou e carregou antes
            ## de cancelar — o slot de recuperação ficou obsoleto. Limpa-o para que o Timeline
            ## não exiba um botão de cancelamento para um salto já concluído.
            _tl_log("Timeline on_load: stale recovery slot cleared (completed jump)")
            _tl_clear_replay_state()
        
        ## Reconstrói o caminho auxiliar após um salto para uma escolha.
        if (persistent._tl_replay_path
                and persistent._tl_replaying
                and persistent._tl_replay_target):
            target_idx = persistent._tl_replay_target["node_index"]
            shadow = [e for e in persistent._tl_replay_path if e.get("index", -1) > target_idx]
            store._tl_shadow_path = shadow or None
            _tl_log("Timeline on_load: shadow_path set count={}".format(
                len(store._tl_shadow_path) if isinstance(store._tl_shadow_path, list) else store._tl_shadow_path))
        
        ## Cria wf_start se não existir um save inicial atual nem legado.
        if not _tl_slot_exists("wf_start", extensions=("-LT1.save",))[0]:
            try:
                _tl_save_no_screenshot("wf_start")
            except Exception as e:
                _tl_log("Timeline ERROR start save failed on load: {}".format(e))
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
    try:
        config.after_load_callbacks.append(_tl_on_load)
    except Exception:
        ## Ren'Py 6.99 não fornece after_load_callbacks. O label_callback é a
        ## alternativa disponível; _after_load é executado após restaurar um save.
        ## O marcador impede empilhar wrappers em recargas Shift+R.
        if not getattr(config.label_callback, "_wells_tl_after_load_hook", False):
            _tl_previous_label_callback = config.label_callback

            def _tl_compat_label_callback(label, abnormal):
                if _tl_previous_label_callback is not None:
                    _tl_previous_label_callback(label, abnormal)
                if label == "_after_load":
                    _tl_on_load()
                    validator = getattr(renpy.store, "_tl_validate_on_load", None)
                    if validator is not None:
                        validator()

            _tl_compat_label_callback._wells_tl_after_load_hook = True
            config.label_callback = _tl_compat_label_callback
    config.interact_callbacks.append(_tl_interact_callback)

## -----------------------------------------------------------------------------
## Seção 2: timeline_init.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — timeline_init.rpy
## Variáveis de store, dados persistentes, constantes e funções auxiliares.
## =============================================================================

init -2 python:

    import os, time as _tl_time, json as _tl_json
    import hashlib as _tl_hashlib
    try:
        import __builtin__ as _tl_builtins
    except ImportError:
        import builtins as _tl_builtins

    _tl_builtin_id = _tl_builtins.id

    ## Armazena as funções nativas antes que personagens do jogo possam sobrescrevê-las.
    _WELLS_TL_MIN = min
    _WELLS_TL_MAX = max

    def _tl_log(msg):
        try:
            debug_dir = _tl_wells_cache_dir()
            if debug_dir is None:
                return
            debug_path = os.path.join(debug_dir, "debug.txt")
            with open(debug_path, "a") as f:
                f.write(msg + "\n")
        except Exception:
            pass

    WELLS_TL_ROUTE_MAP_VERSION = 1
    WELLS_TL_ROUTE_MAP_NAME = "timeline_routes.json"

    def _tl_route_map_empty():
        return {
            "format_version": WELLS_TL_ROUTE_MAP_VERSION,
            "game": {
                "name": getattr(renpy.config, "name", "") or "",
                "folder": os.path.basename(os.path.normpath(renpy.config.gamedir)),
            },
            "active_route_id": None,
            "next_route_number": 1,
            "routes": [],
        }

    def _tl_route_map_path():
        cache_dir = _tl_wells_cache_dir()
        if cache_dir is None:
            return None
        return os.path.join(cache_dir, WELLS_TL_ROUTE_MAP_NAME)

    def _tl_route_map_load():
        path = _tl_route_map_path()
        if path is None:
            return _tl_route_map_empty()
        for candidate in (path, path + ".tmp"):
            try:
                with open(candidate, "rb") as route_file:
                    data = _tl_json.loads(route_file.read())
                expected_game = _tl_route_map_empty()["game"]
                if (not isinstance(data, dict)
                        or data.get("format_version") != WELLS_TL_ROUTE_MAP_VERSION
                        or data.get("game") != expected_game
                        or not isinstance(data.get("routes"), list)):
                    raise ValueError("formato ou jogo diferente")
                if not isinstance(data.get("next_route_number"), int):
                    data["next_route_number"] = len(data["routes"]) + 1
                data["routes"] = [route for route in data["routes"]
                                  if isinstance(route, dict)
                                  and route.get("id")
                                  and isinstance(route.get("choices"), list)]
                return data
            except IOError:
                continue
            except Exception as e:
                _tl_log("Timeline: mapa de rotas inválido em {}: {}".format(candidate, e))
        return _tl_route_map_empty()

    def _tl_route_map_save(data):
        path = _tl_route_map_path()
        if path is None:
            _tl_log("Timeline: pasta wells_cache indisponível; mapa de rotas não gravado.")
            return False
        temp_path = path + ".tmp"
        try:
            encoded = _tl_json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True)
            with open(temp_path, "wb") as route_file:
                route_file.write(encoded.encode("utf-8"))
            if hasattr(os, "replace"):
                os.replace(temp_path, path)
            else:
                if os.path.exists(path):
                    os.remove(path)
                os.rename(temp_path, path)
            return True
        except Exception as e:
            _tl_log("Timeline: falha ao gravar mapa de rotas: {}".format(e))
            return False

    def _tl_route_common_prefix(left, right):
        count = 0
        limit = min(len(left), len(right))
        while count < limit:
            a = left[count]
            b = right[count]
            if not isinstance(a, dict) or not isinstance(b, dict):
                break
            if (a.get("menu_key") != b.get("menu_key")
                    or a.get("selected_index") != b.get("selected_index")
                    or a.get("selected_label") != b.get("selected_label")):
                break
            count += 1
        return count

    def _tl_route_map_upsert(data, choices):
        """Add a played choice path or extend its matching route in the sidecar map."""
        if not choices:
            return data, None, False

        routes = data.get("routes", [])
        active_id = data.get("active_route_id")
        ranked = []
        for route in routes:
            existing = route.get("choices", [])
            common = _tl_route_common_prefix(existing, choices)
            ranked.append((common, route.get("id") == active_id, route))

        exact = [item for item in ranked
                 if len(item[2].get("choices", [])) == len(choices)
                 and item[0] == len(choices)]
        if exact:
            selected_route = next((item[2] for item in exact if item[1]), exact[0][2])
            changed = data.get("active_route_id") != selected_route.get("id")
            data["active_route_id"] = selected_route.get("id")
            return data, selected_route.get("id"), changed

        extensions = [item for item in ranked
                      if len(item[2].get("choices", [])) < len(choices)
                      and item[0] == len(item[2].get("choices", []))]
        if extensions:
            selected_route = next((item[2] for item in extensions if item[1]),
                                  max(extensions, key=lambda item: item[0])[2])
            selected_route["choices"] = list(choices)
            data["active_route_id"] = selected_route.get("id")
            return data, selected_route.get("id"), True

        matching_prefixes = [item for item in ranked
                             if len(choices) < len(item[2].get("choices", []))
                             and item[0] == len(choices)]
        if matching_prefixes:
            selected_route = next((item[2] for item in matching_prefixes if item[1]),
                                  max(matching_prefixes, key=lambda item: len(item[2].get("choices", [])))[2])
            changed = data.get("active_route_id") != selected_route.get("id")
            data["active_route_id"] = selected_route.get("id")
            return data, selected_route.get("id"), changed

        parent = max(ranked, key=lambda item: item[0]) if ranked else None
        if parent and parent[0] == 0:
            parent = None
        branch_at = parent[0] if parent else 0
        route_number = data.get("next_route_number", len(routes) + 1)
        route_id = "r{}".format(route_number)
        data["next_route_number"] = route_number + 1
        data["routes"].append({
            "id": route_id,
            "parent_route_id": parent[2].get("id") if parent else None,
            "branch_at": branch_at,
            "choices": list(choices),
        })
        data["active_route_id"] = route_id
        return data, route_id, True

    def _tl_route_map_record_current_history():
        """Store the current selected choices as a small, JSON-safe route trace."""
        try:
            history = getattr(store, "_tl_history", [])
            trace = []
            occurrences = {}
            for node in history:
                if not isinstance(node, dict) or node.get("chosen_index") is None:
                    continue
                source = node.get("ast_key")
                if isinstance(source, (tuple, list)) and len(source) == 2:
                    source = [str(source[0]), int(source[1])]
                else:
                    source = [str(node.get("_location") or ""), 0]
                prompt = node.get("prompt", "")
                options = node.get("options", [])
                base_key = _tl_json.dumps(
                    [source, prompt, options], ensure_ascii=True, sort_keys=True)
                occurrence = occurrences.get(base_key, 0)
                occurrences[base_key] = occurrence + 1
                menu_key = "{}#{}".format(base_key, occurrence)
                chosen = node.get("chosen_index")
                try:
                    chosen = int(chosen)
                except Exception:
                    continue
                label = options[chosen] if chosen < len(options) else ""
                trace.append({
                    "menu_key": menu_key,
                    "source": source,
                    "prompt": prompt,
                    "options": options,
                    "selected_index": chosen,
                    "selected_label": label,
                })

            if not trace:
                return
            ledger = getattr(renpy.game, "_wells_tl_route_map", None)
            if not isinstance(ledger, dict):
                ledger = _tl_route_map_load()
            ledger, route_id, changed = _tl_route_map_upsert(ledger, trace)
            renpy.game._wells_tl_route_map = ledger
            if changed:
                if _tl_route_map_save(ledger):
                    _tl_log("Timeline: mapa de rotas atualizado; rota={} escolhas={}".format(
                        route_id, len(trace)))
        except Exception as e:
            _tl_log("Timeline: não foi possível atualizar o mapa de rotas: {}".format(e))

    def _tl_route_map_history_indexes():
        """Map JSON menu keys to the matching choice nodes in the active save history."""
        indexes = {}
        occurrences = {}
        for node in getattr(store, "_tl_history", []) or []:
            if not isinstance(node, dict):
                continue
            source = node.get("ast_key")
            if isinstance(source, (tuple, list)) and len(source) == 2:
                source = [str(source[0]), int(source[1])]
            else:
                source = [str(node.get("_location") or ""), 0]
            prompt = node.get("prompt", "")
            options = node.get("options", [])
            base_key = _tl_json.dumps(
                [source, prompt, options], ensure_ascii=True, sort_keys=True)
            occurrence = occurrences.get(base_key, 0)
            occurrences[base_key] = occurrence + 1
            menu_key = "{}#{}".format(base_key, occurrence)
            indexes[menu_key] = node.get("index")
        return indexes

    def _tl_build_choice_graph():
        """Return a compact prefix-sharing graph built only from the JSON route ledger."""
        ledger = getattr(renpy.game, "_wells_tl_route_map", None) or {}
        routes = [route for route in ledger.get("routes", [])
                  if isinstance(route, dict) and isinstance(route.get("choices"), list)]
        def _route_number(route):
            route_id = str(route.get("id", ""))
            try:
                return int(route_id[1:]) if route_id.startswith("r") else 0
            except Exception:
                return 0
        routes.sort(key=_route_number)

        nodes = {}
        edges = {}
        active_id = ledger.get("active_route_id")
        for lane, route in enumerate(routes):
            prefix = []
            parent_id = None
            route_id = route.get("id")
            for column, choice in enumerate(route.get("choices", [])):
                if not isinstance(choice, dict):
                    continue
                prefix.append((choice.get("menu_key"), choice.get("selected_index")))
                node_id = _tl_json.dumps(prefix, ensure_ascii=True, sort_keys=True)
                node = nodes.get(node_id)
                if node is None:
                    node = {
                        "id": node_id,
                        "choice": choice,
                        "column": column,
                        "lane": lane,
                        "route_ids": [],
                        "active": False,
                    }
                    nodes[node_id] = node
                if route_id not in node["route_ids"]:
                    node["route_ids"].append(route_id)
                if route_id == active_id:
                    node["active"] = True
                if parent_id is not None:
                    edge_id = (parent_id, node_id)
                    edge = edges.get(edge_id)
                    if edge is None:
                        edge = {"from": parent_id, "to": node_id, "active": False}
                        edges[edge_id] = edge
                    if route_id == active_id:
                        edge["active"] = True
                parent_id = node_id

        history_indexes = _tl_route_map_history_indexes()
        result_nodes = list(nodes.values())
        for node in result_nodes:
            node["history_index"] = history_indexes.get(
                node["choice"].get("menu_key"))
        return {
            "nodes": result_nodes,
            "edges": list(edges.values()),
            "active_route_id": active_id,
            "route_count": len(routes),
        }

    ## Carrega o mapa externo uma vez ao iniciar. Ele fica em renpy.game, fora dos saves.
    renpy.game._wells_tl_route_map = _tl_route_map_load()
    if not os.path.exists(_tl_route_map_path() or ""):
        _tl_route_map_save(renpy.game._wells_tl_route_map)

    ## Dimensões das miniaturas
    WELLS_TL_THUMB_WIDTH  = 320
    WELLS_TL_THUMB_HEIGHT = 180

    WELLS_TL_THUMB_CACHE_MAX  = 500  ## limite de miniaturas (~25 MB com cerca de 50 KB por miniatura)
    WELLS_TL_DEBUG_GHOST      = False   ## detalhes da síntese de ramos futuros (execução If, agrupamento, imagens dos ramos, resolução de imagens)
    WELLS_TL_DEBUG_SEEN       = False   ## detalhes da resolução do estado visto (opt_seen, peek_seen)
    WELLS_TL_DEBUG_ROUTE      = False   ## detalhes do rastreador de rotas (diferenças de variáveis por bloco Python e busca por valores padrão)
    WELLS_TL_DEBUG_MENU       = False   ## detalhes do fluxo por menu (entrada no menu, img_name, consumo do caminho auxiliar)
    WELLS_TL_DEBUG_ASSET      = False   ## detalhes do cache de miniaturas (cache encontrado/gerado e atualizações do mapa de cenas)

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

    def _tl_load_thumb_dict(path):
        """
        Load the thumbnail pickle from path. Tries gzip first, falls back to raw.
        Returns {} on any failure so callers always get a valid dict.
        """
        import gzip
        from renpy.compat.pickle import loads
        try:
            with gzip.open(path, "rb") as f:
                _wells_tl_thumb_data = loads(f.read())
            _tl_log("Timeline: miniaturas carregadas (gzip): miniaturas={} recursos={}".format(
                len(_wells_tl_thumb_data.get("thumb", {})), len(_wells_tl_thumb_data.get("asset_thumb", {}))))
            return _wells_tl_thumb_data
        except Exception as err:
            _tl_log("Timeline thumbs gzip load error: {} — trying raw".format(err))
        try:
            with open(path, "rb") as f:
                _wells_tl_thumb_data = loads(f.read())
            _tl_log("Timeline thumbs loaded (raw): thumb={} asset={}".format(
                len(_wells_tl_thumb_data.get("thumb", {})), len(_wells_tl_thumb_data.get("asset_thumb", {}))))
            return _wells_tl_thumb_data
        except Exception as err:
            _tl_log("Timeline thumbs raw load error: {}".format(err))
            return {}

## Variáveis por save — podem ser carregadas com segurança em saves anteriores ao mod.
default _tl_history    = []   ## lista de dicionários de nós
default _tl_context    = []   ## [(prompt, chosen_index), ...]
default _tl_node_count = 0

## Estado da interface — não é salvo.
default _tl_modal_node  = None  ## nó cuja janela modal está aberta
default _tl_load_slot   = ""    ## slot a carregar pelo label wells_tl_do_load
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
    if not hasattr(persistent, "_tl_choice_return_pending") or persistent._tl_choice_return_pending is None:
        persistent._tl_choice_return_pending = False


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
    ## Um cache pickle antigo pode ser lido na inicialização. O Timeline não grava
    ## miniaturas ao encerrar o jogo.
    _tl_thumbs_path = os.path.join(renpy.config.savedir, "_tl_thumbs.pkl")
    try:
        if os.path.exists(_tl_thumbs_path):
            _wells_tl_thumb_data = _tl_load_thumb_dict(_tl_thumbs_path)
            renpy.game._tl_thumb_cache       = _wells_tl_thumb_data.get("thumb", {})
            renpy.game._tl_asset_thumb_cache = _wells_tl_thumb_data.get("asset_thumb", {})
        else:
            _tl_log("Timeline thumbs init: no pkl file — starting empty")
            renpy.game._tl_thumb_cache      = {}
            renpy.game._tl_asset_thumb_cache = {}
    except Exception as e:
        _tl_log("Timeline thumbs load error: {}".format(e))
        renpy.game._tl_thumb_cache      = {}
        renpy.game._tl_asset_thumb_cache = {}

    ## Migração única: transfere os caches persistentes existentes para renpy.game.
    ## Depois disso, persistent._tl_thumb_cache / _tl_asset_thumb_cache permanecem vazios.
    _wells_tl_mig_thumb  = len(getattr(persistent, "_tl_thumb_cache", None) or {})
    _wells_tl_mig_asset  = len(getattr(persistent, "_tl_asset_thumb_cache", None) or {})
    if _wells_tl_mig_thumb:
        renpy.game._tl_thumb_cache.update(persistent._tl_thumb_cache)
        persistent._tl_thumb_cache = {}
    if _wells_tl_mig_asset:
        renpy.game._tl_asset_thumb_cache.update(persistent._tl_asset_thumb_cache)
        persistent._tl_asset_thumb_cache = {}
    if _wells_tl_mig_thumb or _wells_tl_mig_asset:
        _tl_log("Timeline thumbs migration: moved thumb={} asset={} from persistent".format(
            _wells_tl_mig_thumb, _wells_tl_mig_asset))
init -2 python:

    def _tl_count_locked_branches():
        descs = getattr(persistent, "_tl_all_branch_descs", None) or []
        return sum(1 for desc in descs if not _tl_eval_seen_fn(desc))


    def _tl_build_ast_map():
        try:
            namemap = renpy.game.script.namemap
        except Exception as e:
            _tl_log("Timeline AST: namemap not available: {}".format(e))
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
            _tl_log("Timeline salvage: " + _msg)
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
                _tl_log("Timeline salvage: node={} {}:{} -> unmatched (opts={})".format(
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
            _tl_log("Timeline salvage: node={} {} {}->{}".format(
                _n.get("index"), _stored_file, _stored_line, _new_line))

        if _any_matched:
            _tl_migrate_img_names()
            renpy.save_persistent()

        _msg = "Salvage: {} matched / {} missed / {} ok".format(_matched, _unmatched, _skipped)
        _tl_log("Timeline salvage: total={} matched={} unmatched={} skipped={}".format(
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
            _tl_log("WELLS_TIMELINE: _tl_history invalid on load ({}), resetting".format(type(history)))
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
                _tl_log("WELLS_TIMELINE: dropping malformed node: {}".format(repr(node)[:80]))
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
    try:
        config.after_load_callbacks.append(_tl_validate_on_load)
    except Exception:
        ## O fallback instalado acima também chama este validador no SDK 6.99.
        pass


