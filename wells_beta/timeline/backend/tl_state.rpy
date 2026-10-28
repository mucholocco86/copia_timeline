## =============================================================================
## WELLS TIMELINE — tl_state.rpy
## Save e recuperação, estado de conteúdo visto, dicas de repetição e caches de snapshots.
## As seções consolidadas mantêm a ordem de carregamento anterior.
## =============================================================================

## -----------------------------------------------------------------------------
## Seção 1: backend/tl_saveload.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_saveload.rpy
## Controle de salto: prioriza snapshots e usa saves em disco como alternativa de compatibilidade.
## =============================================================================

init -2 python:

    import renpy.execution as _tl_execution
    _WELLS_TL_RESTART_EXCEPTIONS = tuple(
        exc_type for exc_type in (
            getattr(renpy.game, "RestartTopContext", None),
            getattr(renpy.game, "RestartContext", None),
            getattr(_tl_execution, "RestartTopContext", None),
            getattr(_tl_execution, "RestartContext", None),
        ) if exc_type is not None
    )

    _WELLS_TL_EMPTY_PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def _tl_save_no_screenshot(slot):
        """Call renpy.save(slot) without including a screenshot."""
        renpy_major = getattr(renpy, "version_tuple", (7,))[0]
        if renpy_major >= 8:
            try:
                renpy.save(slot, include_screenshot=False, mutate_flag=False)
                return
            except TypeError as exc:
                ## Ren'Py 8.1.x does not accept include_screenshot. Fall back to
                ## the interface hook used by Ren'Py 6/7 instead of failing the
                ## recovery save before a Timeline jump can dispatch its snapshot.
                error_text = str(exc)
                if ("unexpected keyword argument" not in error_text
                        and "unexpected keyword" not in error_text):
                    raise
                _tl_log("Timeline save: API sem include_screenshot; usando captura vazia")

        iface = renpy.game.interface
        try:
            previous_screenshot = iface.get_screenshot
        except Exception:
            previous_screenshot = None
        try:
            iface.get_screenshot = lambda: _WELLS_TL_EMPTY_PNG
            renpy.save(slot)
        finally:
            if previous_screenshot is None:
                try:
                    del iface.get_screenshot
                except AttributeError:
                    pass
            else:
                iface.get_screenshot = previous_screenshot

    def _tl_save_slot(node_index, context):
        raw = repr(tuple(context))
        slot_hash  = _tl_hashlib.md5(raw.encode("utf-8")).hexdigest()[:6]
        return "wf_{:04d}_{}".format(node_index, slot_hash)

    def _tl_pre_save_slot(node_index, context, ast_key=None):
        raw = repr((tuple(context[:node_index]), ast_key))
        slot_hash  = _tl_hashlib.md5(raw.encode("utf-8")).hexdigest()[:6]
        return "_pre_{:04d}_{}".format(node_index, slot_hash)

    def _tl_find_pre_save(node_index, context, ast_key=None, save_dir=None):
        """Return pre-menu save slot for node_index if it exists on disk, else None."""
        import os
        slot = _tl_pre_save_slot(node_index, context, ast_key)
        root = save_dir if save_dir is not None else renpy.config.savedir
        for ext in ("-LT1.save", ".save"):
            if os.path.exists(os.path.join(root, slot + ext)):
                return slot
        return None

    def _tl_legacy_slot_name(slot_name):
        """Map a Wells slot name to its previous Chronology name."""
        if slot_name.startswith("wf_"):
            return "_ch_" + slot_name[3:]
        return None

    def _tl_slot_exists(slot_name, save_dir=None, extensions=("-LT1.save", ".save")):
        """Return the first matching slot, preferring Wells names over legacy names."""
        import os
        root = save_dir if save_dir is not None else renpy.config.savedir
        candidates = [slot_name]
        legacy = _tl_legacy_slot_name(slot_name)
        if legacy:
            candidates.append(legacy)
        for candidate in candidates:
            for ext in extensions:
                if os.path.exists(os.path.join(root, candidate + ext)):
                    return True, candidate
        return False, None

    def _tl_clear_replay_state():
        persistent._tl_replaying      = False
        persistent._tl_recovery_slot  = None
        persistent._tl_replay_path    = None
        persistent._tl_replay_target  = None
        persistent._tl_prev_thumb     = None
        persistent._tl_synthetic_jump = False
        persistent._tl_choice_return_pending = False
        store._tl_native_rollback_checkpoints = None
        store._tl_native_rollback_force = True
        try:
            renpy.game._tl_choice_return_ast_key = None
        except Exception:
            pass
        renpy.save_persistent()

    ## ── Funções internas da versão 2 ──────────────────────────────────────────────────

    def _wf_tl_write_recovery():
        persistent._tl_recovery_slot = None
        _tl_save_no_screenshot("wf_recovery")
        persistent._tl_recovery_slot = "wf_recovery"

    def _wf_tl_replay_entries(hist):
        entries = []
        for node in hist:
            if node.get("chosen_index") is None:
                continue
            entries.append({
                "index": node["index"],
                "chosen_index": node["chosen_index"],
                "option_ast_index": node.get("chosen_ast_index"),
                "ast_key": _tl_node_menu_site_key(node),
            })
        return entries

    def _wf_tl_stage_menu_replay(hist, node_index, option_index):
        prev_node = next((n for n in hist if n["index"] == node_index - 1), None)
        target_node = next((n for n in hist if n["index"] == node_index), None)
        option_ast_index = _tl_node_option_ast_index(target_node, option_index)
        persistent._tl_replay_path = _wf_tl_replay_entries(hist)
        persistent._tl_replay_target = {
            "node_index": node_index,
            "option_index": option_index,
            "option_ast_index": option_ast_index,
        }
        persistent._tl_prev_thumb = prev_node["thumb_bytes"] if prev_node else None
        persistent._tl_replaying = True

    def _wf_tl_dispatch_snap(snap):
        persistent._tl_synthetic_jump = True
        renpy.save_persistent()
        renpy.game._tl_pending_snap = snap

    def _wf_tl_valid_snap(snap):
        return bool(snap and snap.get("roots") and snap.get("context") is not None)

    def _tl_legacy_rollback_checkpoint_count(log, anchor):
        """Mirror Ren'Py's identifier distance for a live SDK 6.99 log entry."""
        if anchor is None:
            return None
        try:
            ## Ren'Py's identifier cache starts at one and counts hard
            ## checkpoints. SDK 6.99 predates that field, where checkpoint is
            ## the equivalent boundary. Match the engine's 1-based distance.
            checkpoints = 1
            for entry in reversed(getattr(log, "log", ())):
                if id(entry) == anchor:
                    return checkpoints
                if hasattr(entry, "hard_checkpoint"):
                    is_boundary = bool(entry.hard_checkpoint)
                else:
                    is_boundary = bool(getattr(entry, "checkpoint", False))
                if is_boundary:
                    checkpoints += 1
        except Exception:
            pass
        return None

    def _tl_native_rollback_checkpoints(node):
        """Return the native rollback distance to a recorded menu, when available.

        Modern Ren'Py SDKs provide the same checkpoint lookup used by their
        RollbackToIdentifier action. Ren'Py 6.99 has no identifier API, so its
        in-memory log entry can be used only while that entry remains present.
        """
        if not isinstance(node, dict):
            return None

        identifier = node.get("_rollback_id")
        get_checkpoints = getattr(renpy, "get_identifier_checkpoints", None)
        if callable(get_checkpoints) and identifier is not None:
            try:
                checkpoints = get_checkpoints(identifier)
                if checkpoints is not None and checkpoints > 0:
                    return checkpoints, "menu"
            except Exception as exc:
                _tl_log("Timeline native rollback lookup failed: {}".format(exc))
            ## With identifier lookup available, a missing identifier is not a
            ## safe reason to guess from compiled-script line locations.
            return None

        anchor = node.get("_rollback_anchor")
        if anchor is None:
            return None

        try:
            checkpoints = _tl_legacy_rollback_checkpoint_count(
                renpy.game.log, anchor)
            if checkpoints is not None:
                return checkpoints, True
        except Exception as exc:
            _tl_log("Timeline legacy rollback lookup failed: {}".format(exc))
        return None

    def _tl_arm_choice_return(node):
        """Remember the AST menu whose native options must remain reselectable."""
        key = node.get("ast_key") if isinstance(node, dict) else None
        if isinstance(key, (list, tuple)) and len(key) == 2:
            renpy.game._tl_choice_return_ast_key = tuple(key)
            return True
        renpy.game._tl_choice_return_ast_key = None
        return False

    def _tl_unlock_returned_choice(ast_key):
        """Clear fixed rollback only when the recorded target menu is reached."""
        pending = getattr(renpy.game, "_tl_choice_return_ast_key", None)
        if not isinstance(pending, (list, tuple)) or not isinstance(ast_key, (list, tuple)):
            return False
        if tuple(pending) != tuple(ast_key):
            return False

        ## URMChoice.Action clears this flag before returning ChoiceReturn. The
        ## Timeline restores the original menu first, so do it just before the
        ## native menu interaction is built, and only for that AST menu.
        try:
            renpy.game.log.rollback_is_fixed = False
        except Exception as exc:
            _tl_log("Timeline choice unlock failed: {}".format(exc))
        renpy.game._tl_choice_return_ast_key = None
        _tl_log("Timeline choice unlocked for reselection: ast_key={}".format(tuple(ast_key)))
        return True

    def _wf_tl_find_slot(node_index, hist, context):
        """
        Tier 1: exact pre-save at target index.
        Tier 2: walk history downward from node_index-1; first hit wins (closest save).
        """
        import os
        save_dir = renpy.config.savedir

        target_node = next((node for node in hist if node["index"] == node_index), None)
        ast_key     = _tl_node_menu_site_key(target_node) if target_node else None
        pre_slot    = _tl_find_pre_save(node_index, context, ast_key)
        if pre_slot:
            return pre_slot

        hist_by_idx = {node["index"]: node for node in hist}

        for idx in range(node_index - 1, -1, -1):
            hist_node = hist_by_idx.get(idx)
            if hist_node:
                pre = _tl_find_pre_save(idx, context, _tl_node_menu_site_key(hist_node), save_dir)
                if pre:
                    return pre
                chk_slot = _tl_save_slot(idx, context)
                exists, actual_slot = _tl_slot_exists(chk_slot, save_dir, ("-LT1.save",))
                if exists:
                    return actual_slot

        exists, start_slot = _tl_slot_exists("wf_start", save_dir, ("-LT1.save",))
        if exists:
            return start_slot
        return None

    ## ── API pública ───────────────────────────────────────────────────────────

    def _tl_jump(node_index=None, option_index=None):
        """Return to a recorded menu so the game's own choice screen is shown again."""
        hist    = list(getattr(store, "_tl_history", []))
        context = list(store._tl_context)
        try:
            ## Não reutiliza uma distância nativa antiga se o novo destino cair
            ## no caminho de compatibilidade por snapshot/pré-save.
            store._tl_native_rollback_checkpoints = None
            store._tl_native_rollback_force = True
            target_node = next((n for n in hist if n.get("index") == node_index), None)
            _tl_arm_choice_return(target_node)
            _wf_tl_write_recovery()
            native_target = _tl_native_rollback_checkpoints(target_node)
            if native_target is not None:
                checkpoints, force = native_target
                persistent._tl_replaying = False
                persistent._tl_replay_path = None
                persistent._tl_replay_target = None
                persistent._tl_prev_thumb = None
                persistent._tl_choice_return_pending = True
                persistent._tl_synthetic_jump = False
                store._tl_native_rollback_checkpoints = checkpoints
                store._tl_native_rollback_force = force
                renpy.save_persistent()
                _tl_log("Timeline native rollback: menu={} checkpoints={}".format(
                    node_index, checkpoints))
                return

            snap = _tl_get_menu_snapshot(node_index)
            if _wf_tl_valid_snap(snap):
                ## The snapshot is taken immediately before the target menu. Restore it
                ## directly instead of replaying old choices and auto-selecting this one.
                persistent._tl_replaying = False
                persistent._tl_replay_path = None
                persistent._tl_replay_target = None
                persistent._tl_prev_thumb = None
                persistent._tl_choice_return_pending = True
                renpy.save_persistent()
                _wf_tl_dispatch_snap(snap)
                return

            ## Older SDK/game combinations may lack a usable in-memory snapshot.
            ## Keep the compatibility replay only to reach the menu; the target choice
            ## itself is left to the game's normal choice screen.
            _wf_tl_stage_menu_replay(hist, node_index, option_index)
            persistent._tl_choice_return_pending = True
            renpy.save_persistent()
            fallback_slot = _wf_tl_find_slot(node_index, hist, context)
            if fallback_slot:
                store._tl_load_slot = fallback_slot
                return

            _tl_clear_replay_state()
            renpy.notify("Nenhum salvamento encontrado para essa escolha.")

        except _WELLS_TL_RESTART_EXCEPTIONS:
            raise
        except Exception as exc:
            _tl_log("Timeline jump ERROR {}: {}".format(node_index, exc))
            _tl_clear_replay_state()

    def _tl_cancel_jump():
        """
        Cancel an in-progress jump and restore from recovery save.
        Caches thumbnails from history nodes into renpy.game._tl_thumb_cache
        to avoid re-loading them after the recovery load.
        """
        slot = persistent._tl_recovery_slot

        try:
            thumb_cache = getattr(renpy.game, "_tl_thumb_cache", {})
            for node in store._tl_history:
                cache_key = str(node.get("ast_key")) if node.get("ast_key") else None
                if cache_key and node.get("thumb_bytes") and cache_key not in thumb_cache:
                    thumb_cache[cache_key] = node["thumb_bytes"]
                    node["thumb_bytes"] = None
                    while len(thumb_cache) > WELLS_TL_THUMB_CACHE_MAX:
                        thumb_cache.pop(next(iter(thumb_cache)))
        except Exception as exc:
            _tl_log("Timeline cancel thumb cache error: {}".format(exc))
        
        _tl_clear_replay_state()
        if slot:
            store._tl_load_slot = slot
            return slot
        return None

## -----------------------------------------------------------------------------
## Seção 2: backend/tl_seen_check.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_seen_check.rpy
## Rastreamento de conteúdo visto: descritores, avaliação e verificação por opção.
## =============================================================================

init -2 python:

    def _tl_find_scene_seen_name(start_node, max_hops=80):
        """Find the first translated say-name reachable after a scene node."""
        try:
            translator = renpy.game.script.translator
        except Exception as e:
            _tl_log("Timeline find_scene_seen_name: translator unavailable: {}".format(e))
            translator = None
        node = start_node
        hops = 0
        while node is not None and hops < max_hops:
            stype = type(node).__name__
            if stype in ("Say", "TranslateSay"):
                return _tl_say_seen_name(node)
            if stype in ("Jump", "Call", "Return", "Menu"):
                return None
            node = getattr(node, "next", None)
            hops += 1
        return None

    def _tl_say_seen_name(node):
        """Resolve the correct seen key for a Say or TranslateSay node.

        RenPy 8.5.2+: return identifier string; eval uses renpy.seen_translation().
        Older RenPy: return node.name tuple; eval checks _seen_ever directly.
        Translated games: resolve to TranslateSay node for old RenPy fallback.
        """
        ident = getattr(node, "identifier", None)
        if ident and getattr(renpy, "seen_translation", None):
            return ident
        ## Ren'Py antigo: resolve o nó de tradução em jogos traduzidos; se falhar, usa o próprio nó.
        try:
            translator = renpy.game.script.translator
        except Exception as e:
            _tl_log("Timeline say_seen_name: translator unavailable: {}".format(e))
            translator = None
        translated_node = translator.lookup_translate(ident) if (translator and ident) else None
        seen_node = translated_node if (translated_node is not None and not isinstance(translated_node, tuple)) else node
        return getattr(seen_node, "name", None) or getattr(node, "name", None)

    def _tl_follow_jump_seen_name(target, max_hops=30):
        """Follow a Jump/Call target label one hop and return the first Say's
        translator-resolved name, or None if no Say is found.

        Used so that option blocks that are purely Python + Jump can use a
        language-specific _seen_ever check instead of renpy.seen_label, which
        is language-agnostic and causes false positives when the player visited
        the target label in a different locale.
        """
        try:
            namemap = renpy.game.script.namemap
            label_node = namemap.get(target)
            if label_node is None:
                return None
            node = getattr(label_node, "next", None)
            hops = 0
            while node is not None and hops < max_hops:
                node_type = type(node).__name__
                if node_type in ("Say", "TranslateSay"):
                    return _tl_say_seen_name(node)
                if node_type in ("Jump", "Call", "Return", "Menu", "Label"):
                    return None
                node = getattr(node, "next", None)
                hops += 1
        except Exception as e:
            _tl_log("Timeline follow_jump_seen_name failed for '{}': {}".format(target, e))
        return None

    def _tl_first_scene_seen_name(block):
        """Return the first scene-backed seen identity for a branch block."""
        if not block:
            return None
        for node in block:
            if type(node).__name__ == "Scene":
                return _tl_find_scene_seen_name(getattr(node, "next", None))
            if type(node).__name__ in ("Jump", "Call", "Return", "Menu"):
                return None
        return None

    def _tl_scene_ast_id(stmt):
        """Stable structural id for a Scene AST node."""
        if stmt is None:
            return None
        try:
            return (stmt.filename, stmt.linenumber)
        except Exception:
            return None

    def _tl_make_seen_fn(block):
        ## Retorna uma tupla de descritor serializável com pickle, não uma lambda.
        ## Percorre o bloco diretamente — nunca segue .next até o código compartilhado após o menu.
        ##
        ## Prioridade: intervalo Say/TranslateSay > primeiro Scene > primeiro Show com expressão > label de salto > ("never",)
        ## Show simples (sobreposição de personagem, sem argumentos de expressão) é ignorado — é compartilhado entre os ramos.
        ## Show com argumentos de expressão (ParameterizedText) É específico do ramo: _seen_images armazena
        ## as partes originais de imspec, para que a tupla seja passada diretamente a renpy.seen_image.
        ##
        ## ("never",) — sempre não visto (recorre a persistent._chosen)
        ## ("say", name) — nome único resolvido pelo tradutor em _seen_ever
        ## ("say_range", first, last) — nomes Say inicial e final; o primeiro faz a verificação rápida,
        ##                               o último confirma após percorrer tudo
        ## ("image", name_tuple) — fundo Scene ou Show com expressão; renpy.seen_image usa as partes originais
        ## ("label", target) — renpy.seen_label (sem Say/Scene antes de Jump/Call)
        if not block:
            return ("never",)

        say_first  = None   ## primeiro nome resolvido por Say/TranslateSay
        say_last   = None   ## último nome resolvido por Say/TranslateSay (sobrescrito a cada ocorrência)
        scene_best = None   ## primeiro fundo Scene — alternativa de imagem
        show_best  = None   ## primeiro Show com expressão — alternativa ParameterizedText

        def _make_say_result():
            if say_first is None:
                return None
            if say_last != say_first:
                return ("say_range", say_first, say_last)
            return ("say", say_first)

        for node in block:
            node_type = type(node).__name__
            if node_type in ("Say", "TranslateSay"):
                seen_key = _tl_say_seen_name(node)
                if seen_key is not None:
                    if say_first is None:
                        say_first = seen_key
                    say_last = seen_key
            elif node_type == "Scene" and scene_best is None:
                img = _tl_scene_stmt_img_name(node)
                if img:
                    scene_best = ("image", tuple(img.split()))
            elif node_type == "Show" and show_best is None:
                imspec = getattr(node, "imspec", None)
                if imspec and imspec[0]:
                    parts = tuple(str(p) for p in imspec[0])
                    ## Usa somente em shows cujo nome contém argumentos de expressão (tem '(').
                    ## Shows simples como `show eileen happy` são sobreposições de personagem compartilhadas
                    ## por vários ramos — não é possível associá-los a um único ramo, então são ignorados.
                    ## _seen_images guarda as partes originais de imspec, então não é preciso usar eval.
                    if any("(" in p for p in parts):
                        show_best = ("image", parts)
            elif node_type == "Jump":
                target = getattr(node, "target", None)
                followed = _tl_follow_jump_seen_name(target) if target else None
                result_lbl = ("say", followed) if followed else (("label", target) if target else ("never",))
                return _make_say_result() or scene_best or show_best or result_lbl
            elif node_type == "Call":
                target = getattr(node, "label", None) if isinstance(getattr(node, "label", None), str) else None
                followed = _tl_follow_jump_seen_name(target) if target else None
                result_lbl = ("say", followed) if followed else (("label", target) if target else ("never",))
                return _make_say_result() or scene_best or show_best or result_lbl
            elif node_type in ("Return", "Menu"):
                return _make_say_result() or scene_best or show_best or ("never",)
            ## Python, If, With, Show simples etc. — ignorar
        return _make_say_result() or scene_best or show_best or ("never",)

    def _tl_make_scene_seen_fn(block):
        """Build a scene-based seen descriptor for branch/ghost checks."""
        seen_name = _tl_first_scene_seen_name(block)
        if seen_name:
            return ("say", seen_name)
        return ("never",)

    def _tl_eval_seen_fn(seen_fn):
        """Evaluate a seen_fn descriptor tuple against live RenPy state."""
        try:
            if seen_fn[0] == "say":
                seen_key = seen_fn[1]
                if isinstance(seen_key, str):
                    return renpy.seen_translation(seen_key)
                return bool(seen_key in (persistent._seen_ever or {}))
            elif seen_fn[0] == "say_range":
                first_key, last_key = seen_fn[1], seen_fn[2]
                if isinstance(first_key, str):
                    ## Caminho rápido: primeiro nó não visto → certamente não visto.
                    if not renpy.seen_translation(first_key):
                        return False
                    ## Primeiro nó visto → confirma percorrendo tudo até o último nó.
                    return renpy.seen_translation(last_key)
                seen_ever = persistent._seen_ever or {}
                if first_key not in seen_ever:
                    return False
                return bool(last_key in seen_ever)
            elif seen_fn[0] == "image":
                return renpy.seen_image(seen_fn[1])
            elif seen_fn[0] == "label":
                return renpy.seen_label(seen_fn[1])
        except Exception as e:
            _tl_log("Timeline eval_seen_fn failed: desc={} err={}".format(seen_fn, e))
        return False

    def _tl_option_seen(node, option_index):
        ## Consulta da AST ativa: percorre o bloco do menu em execução até encontrar o primeiro
        ## alvo relevante já visto. É mais preciso que os descritores em cache — trata alterações no script
        ## e ignora corretamente as linhas de legenda usando o índice visível.
        try:
            peek = _tl_option_peek_seen_fn(node, option_index)
            if peek is not None:
                result = _tl_eval_seen_fn(peek)
                if WELLS_TL_DEBUG_SEEN:
                    _tl_log("Timeline opt_seen: node={} opt={} src=peek desc={} result={}".format(
                        node.get("index"), option_index, peek, result))
                return result
        except Exception as e:
            _tl_log("Timeline opt_seen peek_err: node={} opt={} err={}".format(node.get("index"), option_index, e))

        ## Consulta direta a persistent._chosen — dicionário ativo e autoritativo.
        ## ChoiceReturn grava (localização, label) → True quando uma opção é escolhida.
        ## É confiável entre save/load; cr.chosen (abaixo) é um snapshot pickle desatualizado
        ## e diverge do dicionário ativo após qualquer ciclo de save/load.
        location = node.get("_location")
        if location is not None and option_index < len(node.get("options", [])):
            label = node["options"][option_index]
            if persistent._chosen and (location, label) in persistent._chosen:
                if WELLS_TL_DEBUG_SEEN:
                    _tl_log("Timeline opt_seen: node={} opt={} src=chosen loc={} label={} result=True".format(
                        node.get("index"), option_index, location, repr(label)))
                return True

        ## Alternativa legada: ChoiceReturn.get_chosen() — confiável apenas dentro da
        ## mesma sessão; mantida para nós sem _location (saves anteriores ao mod).
        crs = _tl_runtime_choice_returns(node) or []
        if option_index < len(crs):
            cr = crs[option_index]
            if cr is not None:
                try:
                    result = bool(cr.get_chosen())
                    if result and WELLS_TL_DEBUG_SEEN:
                        _tl_log("Timeline opt_seen: node={} opt={} src=cr result=True".format(
                            node.get("index"), option_index))
                    return result
                except Exception as e:
                    _tl_log("Timeline opt_seen cr.get_chosen failed: node={} opt={} err={}".format(
                        node.get("index"), option_index, e))

        if WELLS_TL_DEBUG_SEEN:
            _tl_log("Timeline opt_seen: node={} opt={} src=none result=False".format(
                node.get("index"), option_index))
        return False

    def _tl_option_peek_seen_fn(node, option_index):
        """
        Return a live AST seen descriptor for the option's first meaningful content.

        Uses the runtime Ren'Py Menu node so we can inspect the option block directly
        without storing extra metadata on timeline nodes. Caption-only menu rows are
        skipped because they have no block.
        """
        ast_key = node.get("ast_key")
        if not isinstance(ast_key, (list, tuple)) or len(ast_key) != 2:
            return None

        menu = (_tl_live_menu_lookup() or {}).get(tuple(ast_key))
        if menu is None:
            if WELLS_TL_DEBUG_SEEN:
                _tl_log("Timeline peek_seen: node={} opt={} key={} menu_lookup=None".format(
                    node.get("index"), option_index, ast_key))
            return None

        visible_index = 0
        for item in (getattr(menu, "items", None) or []):
            block = item[2] if len(item) > 2 else None
            if not block:
                continue
            if visible_index == option_index:
                desc = _tl_make_seen_fn(block)
                if desc and desc[0] != "never":
                    return desc
                return None
            visible_index += 1
        return None

    def _tl_node_has_new(node):
        ## Ignora a opção escolhida — ela já foi explorada (o jogador seguiu esse caminho).
        ## Isso corresponde à lógica da janela modal (os indicadores da opção escolhida também ficam ocultos).
        chosen_idx = node.get("chosen_index")
        for i in range(len(node.get("options", []))):
            if i == chosen_idx:
                continue
            if not _tl_option_seen(node, i):
                return True
        return False

## -----------------------------------------------------------------------------
## Seção 3: backend/tl_shadow_path.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_shadow_path.rpy
## Caminho auxiliar: sequência de dicas para repetição e detecção de divergência após um salto.
## As entradas são montadas a partir de persistent._tl_replay_path em _tl_on_load.
## Formato de entrada: {"index": N, "chosen_index": CI, "ast_key": (file, line)}
## Compatibilidade anterior: entradas antigas com "menu_site_key" (lista ou tupla) continuam sendo reconhecidas.
## =============================================================================

init -2 python:

    def _wf_tl_entry_key(entry):
        """Return normalized site key from a shadow path entry (tuple or None)."""
        key = entry.get("ast_key") or entry.get("menu_site_key")
        return tuple(key) if isinstance(key, list) else key

    def _tl_shadow_match(shadow_path, node):
        """Return chosen_index from the first entry matching the current node, or None."""
        site_key = _tl_node_menu_site_key(node) if isinstance(node, dict) else None
        for entry in (shadow_path or []):
            if site_key is not None and _wf_tl_entry_key(entry) == site_key:
                return entry.get("chosen_index")
        return None

    def _tl_consume_shadow_path(shadow_path, node, chosen_index, chosen_ast_index=None):
        """
        Consume shadow path entries up to and including the first entry matching node.
        Returns (new_path_or_none, diverged_orig_ci_or_none, match_mode_or_none).

        On match: discards all entries before and including the match; returns the
        tail as the new path (None when exhausted). If the player chose differently
        from the shadow, returns the original chosen_index as diverged_orig_ci.
        Backward compat: old entries with "menu_site_key" (list or tuple) match via ast_key.
        """
        if not shadow_path:
            return shadow_path, None, None
        site_key = _tl_node_menu_site_key(node) if isinstance(node, dict) else None
        for i, entry in enumerate(shadow_path):
            if site_key is not None and _wf_tl_entry_key(entry) == site_key:
                orig_chosen = entry.get("chosen_index")
                orig_ast_index = entry.get("option_ast_index")
                remaining = shadow_path[i + 1:] or None
                if orig_ast_index is not None and chosen_ast_index is not None:
                    diverged = orig_chosen if orig_ast_index != chosen_ast_index else None
                else:
                    diverged = orig_chosen if orig_chosen != chosen_index else None
               
                _tl_log("Timeline shadow match: node={} via=ast_key site={} div={}".format(
                    node.get("index") if isinstance(node, dict) else "?",
                    site_key, diverged))
                return remaining, diverged, "ast_key"
        
        _tl_log("Timeline shadow no-match: node={} sp_first={}".format(
            node.get("index") if isinstance(node, dict) else "?",
            _wf_tl_entry_key(shadow_path[0]) if shadow_path else None))
        return shadow_path, None, None

## -----------------------------------------------------------------------------
## Seção 4: backend/tl_snapshot_cache.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_snapshot_cache.rpy
## Cache de snapshots: captura, armazenamento, recuperação e transferência de snapshots do estado do jogo.
## Os snapshots ficam em renpy.game.log._tl_snapshot_cache — fora do store —
## para serem serializados automaticamente na entrada de log do save e nunca aparecerem
## em get_roots(), eliminando o ciclo recursivo da abordagem antiga por nó.
##
## IMPORTANTE: todos os dicionários de cache e snapshot devem ser dicts nativos do Python, NÃO
## RevertableDict. Nos blocos init python do Ren'Py, literais {} são convertidos
## em __renpy__dict__(), que cria RevertableDict — rastreado pelo sistema de
## rollback e revertido durante o rollback. _WELLS_TL_PLAIN_DICT evita essa conversão.
## =============================================================================

init -2 python:

    try:
        import __builtin__ as _tl_builtins
    except ImportError:
        import builtins as _tl_builtins
    _WELLS_TL_PLAIN_DICT = _tl_builtins.dict

    def _tl_make_cache():
        c = _WELLS_TL_PLAIN_DICT()
        c["menu"] = _WELLS_TL_PLAIN_DICT()
        return c

    def _tl_drop_saved_snapshot_cache():
        """Remove the legacy cache from RollbackLog before a save can pickle it."""
        try:
            if hasattr(renpy.game.log, "_tl_snapshot_cache"):
                delattr(renpy.game.log, "_tl_snapshot_cache")
        except Exception:
            pass

    def _tl_get_snapshot_cache():
        ## RollbackLog is serialized with every Ren'Py save. Keep full snapshots on the
        ## runtime game module instead, so the save does not recursively pickle them.
        _tl_drop_saved_snapshot_cache()
        if not hasattr(renpy.game, "_tl_snapshot_cache"):
            renpy.game._tl_snapshot_cache = _tl_make_cache()
        return renpy.game._tl_snapshot_cache

    def _tl_reset_snapshot_cache():
        """Discard snapshots from a different loaded game state."""
        _tl_drop_saved_snapshot_cache()
        renpy.game._tl_snapshot_cache = _tl_make_cache()
        return renpy.game._tl_snapshot_cache

    def _tl_init_snapshot_cache():
        """Ensure the runtime-only snapshot cache exists after loading."""
        _tl_get_snapshot_cache()

    def _tl_capture_snapshot():
        """
        Capture full game state as a snapshot dict {"roots": ..., "context": ctx}.

        ctx.info (scene list, music) is deep-copied at capture time because rollback_copy()
        is shallow — ctx.info is a live reference that mutates as the game continues.
        All other ctx fields are isolated at unfreeze time via deepcopy in _tl_unfreeze_from_snapshot.

        In compiled .rpyc files ctx.current is a (filename, serial, linenumber) tuple that
        has_label() cannot resolve. Patched to the enclosing label so RollbackLog.rollback()
        stops correctly at our synthetic entry.
        """
        import copy as _copy
        renpy.game.log.complete(False)  # descarrega no log as alterações pendentes do store
        ctx = renpy.game.context().rollback_copy()
        try:
            ctx.info = _copy.deepcopy(ctx.info)
        except Exception as e:
            _tl_log("Timeline snapshot: deepcopy info failed: {}".format(e))
        snap = _WELLS_TL_PLAIN_DICT()
        snap["roots"]   = renpy.game.log.get_roots()
        snap["context"] = ctx
        # Ajusta ctx.current em arquivos .rpyc compilados nos quais o label é uma tupla.
        ctx_cur = getattr(ctx, "current", None)
        if ctx_cur is not None and not renpy.game.script.has_label(ctx_cur):
            if isinstance(ctx_cur, tuple) and len(ctx_cur) >= 3:
                target_file, target_line = ctx_cur[0], ctx_cur[2]
                best_label, best_line = None, -1
                for lname, lnode in renpy.game.script.namemap.items():
                    if (isinstance(lname, str)
                            and type(lnode).__name__ == "Label"
                            and getattr(lnode, "filename", None) == target_file
                            and getattr(lnode, "linenumber", -1) <= target_line
                            and lnode.linenumber > best_line):
                        best_line = lnode.linenumber
                        best_label = lname
                if best_label:
                    ctx.current = best_label
                    _tl_log("Timeline snapshot: patched current {} → {}".format(ctx_cur, best_label))
                else:
                    _tl_log("Timeline snapshot: WARNING no enclosing label for {}".format(ctx_cur))
        return snap

    def _tl_cache_menu_snapshot(node_index, snap):
        """Write snap to cache["menu"][node_index]. Called after history append."""
        cache = _tl_get_snapshot_cache()
        cache["menu"][node_index] = snap
        _tl_log("Timeline snapshot: cached idx={} cache_menu_total={}".format(
            node_index, len(cache["menu"])))

    def _tl_get_menu_snapshot(node_index):
        """Return cache["menu"].get(node_index) or None."""
        return _tl_get_snapshot_cache()["menu"].get(node_index)

    def _tl_transfer_snapshot_cache(new_log):
        """Keep menu snapshots in runtime memory, outside the serialized RollbackLog."""
        cache = _tl_get_snapshot_cache()
        _tl_log("Timeline unfreeze: cache runtime preservado; menus={}".format(
            len(cache.get("menu", {}))))

    def _tl_unfreeze_from_snapshot(snap):
        """
        Build a single-entry RollbackLog from snap and call unfreeze(). Never returns.
        Caller is responsible for writing the recovery save and staging persistent vars
        before calling this. snap must have 'roots' and 'context' keys.
        """
        try:
            import renpy.rollback as rb_mod
        except ImportError:
            import renpy.python as rb_mod

        roots = snap["roots"]
        # Copia ctx em profundidade para que as alterações do Ren'Py após descongelar não corrompam o snapshot armazenado.
        # Também reinicia interacting para corrigir saves criados antes desta alteração.
        try:
            import copy as _copy
            ctx = _copy.deepcopy(snap["context"])
        except Exception as e:
            _tl_log("Timeline unfreeze: ctx deepcopy failed: {}".format(e))
            ctx = snap["context"]
        ctx.interacting = False

        # Monta um RollbackLog sintético com uma entrada no contexto de destino.
        # Rollback() __init__ lê renpy.game.log — constrói antes que o descongelamento o substitua.
        # stores={} e objects=[] indicam que o rollback não altera o estado; roots cuida disso.
        # not_greedy=True encerra imediatamente a passagem greedy nesta entrada.
        new_log             = rb_mod.RollbackLog()
        rb                  = rb_mod.Rollback()
        rb.context          = ctx
        rb.stores           = {}
        rb.objects          = []
        rb.checkpoint       = True
        rb.hard_checkpoint  = True
        rb.purged           = False
        rb.retain_after_load = False
        rb.random           = []
        rb.forward          = None
        if hasattr(rb, "not_greedy"):
            rb.not_greedy = True
        new_log.log            = [rb]
        ## RollbackLog.current must reference the active final entry. Ren'Py 8.1
        ## uses it in unfreeze() -> rollback() -> suspend_checkpointing().
        ## Assigning only .log leaves current=None and crashes on not_greedy.
        new_log.current         = rb
        new_log.rollback_limit = 1

        _tl_transfer_snapshot_cache(new_log)

        _tl_log("Timeline unfreeze: ctx={} roots_keys={}".format(
            getattr(ctx, "current", "?"), len(roots)))

        ## Nunca retorna — a execução é retomada pelo label _after_load..
        new_log.unfreeze(roots, label="_after_load")


