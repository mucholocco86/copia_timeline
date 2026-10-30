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

    _TL_EMPTY_PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def _tl_save_no_screenshot(slot):
        """Call renpy.save(slot) without including a screenshot."""
        renpy_major = getattr(renpy, "version_tuple", (7,))[0]
        if renpy_major >= 8:
            renpy.save(slot, include_screenshot=False, mutate_flag=False)
        else:
            iface = renpy.game.interface
            try:
                iface.get_screenshot = lambda: _TL_EMPTY_PNG
                renpy.save(slot)
            finally:
                try:
                    del iface.get_screenshot
                except AttributeError:
                    pass

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
        renpy.save_persistent()

    ## ── Funções internas da versão 2 ──────────────────────────────────────────────────

    def _write_recovery():
        persistent._tl_recovery_slot = None
        _tl_save_no_screenshot("wf_recovery")
        persistent._tl_recovery_slot = "wf_recovery"

    def _replay_entries(hist):
        return [
            {
                "index"        : n["index"],
                "chosen_index" : n["chosen_index"],
                "ast_key"      : _tl_node_menu_site_key(n),
            }
            for n in hist if n.get("chosen_index") is not None
        ]

    def _stage_menu_replay(hist, node_index, option_index):
        prev_node = next((n for n in hist if n["index"] == node_index - 1), None)
        persistent._tl_replay_path   = _replay_entries(hist)
        persistent._tl_replay_target = {"node_index": node_index, "option_index": option_index}
        persistent._tl_prev_thumb    = prev_node["thumb_bytes"] if prev_node else None
        persistent._tl_replaying     = True

    def _dispatch_snap(snap):
        persistent._tl_synthetic_jump = True
        renpy.save_persistent()
        renpy.game._tl_pending_snap = snap

    def _valid_snap(snap):
        return bool(snap and snap.get("roots") and snap.get("context") is not None)

    def _find_slot(node_index, hist, context):
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
        """Return to a recorded menu choice using a snapshot or a save fallback."""
        hist    = list(getattr(store, "_tl_history", []))
        context = list(store._tl_context)
        try:
            _write_recovery()
            _stage_menu_replay(hist, node_index, option_index)
            renpy.save_persistent()

            snap = _tl_get_menu_snapshot(node_index)
            if _valid_snap(snap):
                _dispatch_snap(snap)
                return

            fallback_slot = _find_slot(node_index, hist, context)
            if fallback_slot:
                store._tl_load_slot = fallback_slot
                return

            _tl_clear_replay_state()
            renpy.notify("Nenhum salvamento encontrado para essa escolha.")

        except (renpy.game.RestartTopContext, renpy.game.RestartContext):
            raise
        except Exception as exc:
            _tl_log("TL jump ERROR {}: {}".format(node_index, exc))
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
                    while len(thumb_cache) > TL_THUMB_CACHE_MAX:
                        thumb_cache.pop(next(iter(thumb_cache)))
        except Exception as exc:
            _tl_log("TL cancel thumb cache error: {}".format(exc))
        
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
            _tl_log("TL find_scene_seen_name: translator unavailable: {}".format(e))
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
            _tl_log("TL say_seen_name: translator unavailable: {}".format(e))
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
            _tl_log("TL follow_jump_seen_name failed for '{}': {}".format(target, e))
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
            _tl_log("TL eval_seen_fn failed: desc={} err={}".format(seen_fn, e))
        return False

    def _tl_option_seen(node, option_index):
        ## Consulta da AST ativa: percorre o bloco do menu em execução até encontrar o primeiro
        ## alvo relevante já visto. É mais preciso que os descritores em cache — trata alterações no script
        ## e ignora corretamente as linhas de legenda usando o índice visível.
        try:
            peek = _tl_option_peek_seen_fn(node, option_index)
            if peek is not None:
                result = _tl_eval_seen_fn(peek)
                if TL_DEBUG_SEEN:
                    _tl_log("TL opt_seen: node={} opt={} src=peek desc={} result={}".format(
                        node.get("index"), option_index, peek, result))
                return result
        except Exception as e:
            _tl_log("TL opt_seen peek_err: node={} opt={} err={}".format(node.get("index"), option_index, e))

        ## Consulta direta a persistent._chosen — dicionário ativo e autoritativo.
        ## ChoiceReturn grava (localização, label) → True quando uma opção é escolhida.
        ## É confiável entre save/load; cr.chosen (abaixo) é um snapshot pickle desatualizado
        ## e diverge do dicionário ativo após qualquer ciclo de save/load.
        location = node.get("_location")
        if location is not None and option_index < len(node.get("options", [])):
            label = node["options"][option_index]
            if persistent._chosen and (location, label) in persistent._chosen:
                if TL_DEBUG_SEEN:
                    _tl_log("TL opt_seen: node={} opt={} src=chosen loc={} label={} result=True".format(
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
                    if result and TL_DEBUG_SEEN:
                        _tl_log("TL opt_seen: node={} opt={} src=cr result=True".format(
                            node.get("index"), option_index))
                    return result
                except Exception as e:
                    _tl_log("TL opt_seen cr.get_chosen failed: node={} opt={} err={}".format(
                        node.get("index"), option_index, e))

        if TL_DEBUG_SEEN:
            _tl_log("TL opt_seen: node={} opt={} src=none result=False".format(
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
            if TL_DEBUG_SEEN:
                _tl_log("TL peek_seen: node={} opt={} key={} menu_lookup=None".format(
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

    def _entry_key(entry):
        """Return normalized site key from a shadow path entry (tuple or None)."""
        key = entry.get("ast_key") or entry.get("menu_site_key")
        return tuple(key) if isinstance(key, list) else key

    def _tl_shadow_match(shadow_path, node):
        """Return chosen_index from the first entry matching the current node, or None."""
        site_key = _tl_node_menu_site_key(node) if isinstance(node, dict) else None
        for entry in (shadow_path or []):
            if site_key is not None and _entry_key(entry) == site_key:
                return entry.get("chosen_index")
        return None

    def _tl_consume_shadow_path(shadow_path, node, chosen_index):
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
            if site_key is not None and _entry_key(entry) == site_key:
                orig_chosen = entry.get("chosen_index")
                remaining   = shadow_path[i + 1:] or None
                diverged    = orig_chosen if orig_chosen != chosen_index else None
               
                _tl_log("TL shadow match: node={} via=ast_key site={} div={}".format(
                    node.get("index") if isinstance(node, dict) else "?",
                    site_key, diverged))
                return remaining, diverged, "ast_key"
        
        _tl_log("TL shadow no-match: node={} sp_first={}".format(
            node.get("index") if isinstance(node, dict) else "?",
            _entry_key(shadow_path[0]) if shadow_path else None))
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
## rollback e revertido durante o rollback. _TL_PLAIN_DICT evita essa conversão.
## =============================================================================

init -2 python:

    import builtins as _tl_builtins
    _TL_PLAIN_DICT = _tl_builtins.dict

    def _tl_make_cache():
        c = _TL_PLAIN_DICT()
        c["menu"] = _TL_PLAIN_DICT()
        return c

    def _tl_get_snapshot_cache():
        if not hasattr(renpy.game.log, "_tl_snapshot_cache"):
            renpy.game.log._tl_snapshot_cache = _tl_make_cache()
        return renpy.game.log._tl_snapshot_cache

    def _tl_init_snapshot_cache():
        """Ensure cache exists on the loaded log. Called by _tl_on_load."""
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
            _tl_log("TL snapshot: deepcopy info failed: {}".format(e))
        snap = _TL_PLAIN_DICT()
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
                    _tl_log("TL snapshot: patched current {} → {}".format(ctx_cur, best_label))
                else:
                    _tl_log("TL snapshot: WARNING no enclosing label for {}".format(ctx_cur))
        return snap

    def _tl_cache_menu_snapshot(node_index, snap):
        """Write snap to cache["menu"][node_index]. Called after history append."""
        cache = _tl_get_snapshot_cache()
        cache["menu"][node_index] = snap
        _tl_log("TL snapshot: cached idx={} cache_menu_total={}".format(
            node_index, len(cache["menu"])))

    def _tl_get_menu_snapshot(node_index):
        """Return cache["menu"].get(node_index) or None."""
        return _tl_get_snapshot_cache()["menu"].get(node_index)

    def _tl_transfer_snapshot_cache(new_log):
        """Copy cache from current renpy.game.log to new_log."""
        old_cache = getattr(renpy.game.log, "_tl_snapshot_cache", None)
        if old_cache is not None:
            new_log._tl_snapshot_cache = old_cache
            _tl_log("TL unfreeze: cache copiado; menus={}".format(
                len(old_cache.get("menu", {}))))
        else:
            _tl_log("TL unfreeze: no cache to copy (old_log had none)")

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
            _tl_log("TL unfreeze: ctx deepcopy failed: {}".format(e))
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
        new_log.rollback_limit = 1

        _tl_transfer_snapshot_cache(new_log)

        _tl_log("TL unfreeze: ctx={} roots_keys={}".format(
            getattr(ctx, "current", "?"), len(roots)))

        ## Nunca retorna — a execução é retomada pelo label _after_load..
        new_log.unfreeze(roots, label="_after_load")

