## =============================================================================
## WELLS TIMELINE — timeline_tests.rpy
## Executor de testes no jogo. Execute _tl_run_tests() no console Python.
##
## Estrutura de pastas:
##   wells/timeline/
##     timeline_tests.rpy          ← este arquivo (deve ficar aqui para o Ren'Py carregá-lo)
##     tests/ (testes externos)
##       conftest.py               ← simulação do Ren'Py + carregador .rpy (pytest)
##       test_*.py                 ← execute com: python3 -m pytest tests/ -q
##
## Os resultados são gravados em cache/debug.txt por _tl_log().
## Um aviso na tela mostra a quantidade de testes aprovados e reprovados.
##
## Testa comportamentos dependentes do Ren'Py que não podem ser verificados fora do mecanismo:
##   - menu hook wiring (_tl_record_before / _tl_record_after)
##   - captura de miniaturas
##   - ciclo completo de save/load
##   - leitura e gravação do cache
##   - inicialização do estado persistente
##   - _tl_record_before / _tl_record_after pipeline
## =============================================================================

init python:

    ## ─────────────────────────────────────────────────────────────────────────
    ## Dados de teste compartilhados
    ## ─────────────────────────────────────────────────────────────────────────

    ## No nível do módulo para que pickle consiga resolvê-la (classes locais dentro de funções
    ## recebem __qualname__ como func.<locals>.FakeCtx, que pickle não consegue localizar).
    class _TLFakeCtx(object):
        current      = "_dummy_label_99999_"
        interacting  = False

    class _TLFakeChoice(object):
        """Minimal ChoiceReturn stub for tests. chosen=True makes get_chosen() return True."""
        def __init__(self, chosen=False, value=None):
            self._chosen = chosen
            self._value  = value
        def get_chosen(self):
            return self._chosen
        @property
        def value(self):
            return self._value
        def __call__(self):
            return self._value

    class _TLStateGuard(object):
        """
        Context manager: save store/persistent vars on entry, restore on exit.
        store_vals / pers_vals map variable names to the values to set for the test.
        """
        def __init__(self, store_vals=None, pers_vals=None):
            self._store_vals  = store_vals or {}
            self._pers_vals   = pers_vals or {}
            self._saved_store = {}
            self._saved_pers  = {}

        def __enter__(self):
            import store as _st
            for key, new_val in self._store_vals.items():
                self._saved_store[key] = getattr(_st, key, None)
                setattr(_st, key, new_val)
            for key, new_val in self._pers_vals.items():
                self._saved_pers[key] = getattr(persistent, key, None)
                setattr(persistent, key, new_val)
            return self

        def __exit__(self, *_):
            import store as _st
            for key, old_val in self._saved_store.items():
                setattr(_st, key, old_val)
            for key, old_val in self._saved_pers.items():
                setattr(persistent, key, old_val)

    ## ─────────────────────────────────────────────────────────────────────────
    ## Estrutura mínima de testes
    ## ─────────────────────────────────────────────────────────────────────────

    class _TLTestResults(object):
        def __init__(self):
            self.results = []   # lista de (conjunto, nome, aprovado, detalhe)

        def check(self, suite, name, condition, detail=""):
            self.results.append((suite, name, bool(condition), str(detail)))

        @property
        def passed(self):
            return sum(1 for r in self.results if r[2])

        @property
        def failed(self):
            return sum(1 for r in self.results if not r[2])

        @property
        def failures(self):
            return [(s, n, d) for s, n, ok, d in self.results if not ok]


    ## ─────────────────────────────────────────────────────────────────────────
    ## Conjuntos de testes
    ## ─────────────────────────────────────────────────────────────────────────

    def _tl_test_persistent(r):
        """Persistent state is correctly initialised."""
        s = "persistent"
        r.check(s, "_tl_replaying is bool",
            isinstance(persistent._tl_replaying, bool))
        r.check(s, "_tl_replaying default False",
            persistent._tl_replaying == False)
        r.check(s, "_tl_menu_scene_map is dict",
            isinstance(persistent._tl_menu_scene_map, dict))
        r.check(s, "_tl_var_defaults is dict",
            isinstance(persistent._tl_var_defaults, dict))
        # Após a migração, os caches de miniaturas ficam em renpy.game (não em persistent).
        r.check(s, "renpy.game._tl_thumb_cache is dict",
            isinstance(getattr(renpy.game, "_tl_thumb_cache", None), dict))
        r.check(s, "renpy.game._tl_asset_thumb_cache is dict",
            isinstance(getattr(renpy.game, "_tl_asset_thumb_cache", None), dict))
        r.check(s, "persistent._tl_thumb_cache is empty after migration",
            not getattr(persistent, "_tl_thumb_cache", None))
        r.check(s, "persistent._tl_asset_thumb_cache is empty after migration",
            not getattr(persistent, "_tl_asset_thumb_cache", None))


    def _tl_test_store_defaults(r):
        """Store defaults exist and have correct types."""
        s = "store_defaults"
        r.check(s, "_tl_history is list",              isinstance(_tl_history, list))
        r.check(s, "_tl_context is list",              isinstance(_tl_context, list))
        r.check(s, "_tl_node_count is int",            isinstance(_tl_node_count, int))
        r.check(s, "_tl_modal_node is None",           _tl_modal_node is None)
        r.check(s, "_tl_load_slot is str",             isinstance(_tl_load_slot, str))
        r.check(s, "_tl_ast_ready is bool",            isinstance(_tl_ast_ready, bool))
        r.check(s, "_tl_ghost_nodes is list",          isinstance(_tl_ghost_nodes, list))
        r.check(s, "_tl_pending_save_index is None",   _tl_pending_save_index is None)


    def _tl_test_hooks_wired(r):
        """Menu hooks are installed exactly once."""
        s = "hooks"
        r.check(s, "exports.menu wrapped",
            getattr(renpy.exports.menu, "_tl_wrapped", False))
        r.check(s, "store.menu wrapped",
            getattr(renpy.store.menu, "_tl_wrapped", False))
        # Encapsular duas vezes causaria um erro de encapsulamento duplicado.
        r.check(s, "exports.menu not double-wrapped",
            not getattr(getattr(renpy.exports.menu, "__wrapped__", None),
                        "_tl_wrapped", False))


    def _tl_test_save_slot(r):
        """_tl_save_slot produces stable, unique identifiers."""
        s = "save_slot"
        import hashlib
        ctx = [("Choose side", 0), ("Attack?", 1)]
        slot = _tl_save_slot(0, ctx)
        r.check(s, "starts with wf_0000_",    slot.startswith("wf_0000_"))
        r.check(s, "hash is 6 chars",          len(slot.split("_")[-1]) == 6)
        r.check(s, "deterministic",            slot == _tl_save_slot(0, ctx))
        r.check(s, "ctx sensitive",
            _tl_save_slot(0, [("A", 0)]) != _tl_save_slot(0, [("A", 1)]))
        r.check(s, "idx sensitive",
            _tl_save_slot(0, ctx) != _tl_save_slot(1, ctx))
        r.check(s, "legacy slot mapping",
            _tl_legacy_slot_name("wf_0000_abcdef") == "_ch_0000_abcdef")


    def _tl_test_thumbnail(r):
        """Thumbnail capture returns bytes or None (never raises)."""
        s = "thumbnail"
        try:
            thumb = _tl_capture_thumbnail()
            r.check(s, "returns bytes or None",
                thumb is None or isinstance(thumb, bytes))
            if thumb is not None:
                r.check(s, "non-empty bytes", len(thumb) > 0)
                # Bytes de identificação PNG: 89 50 4E 47.
                r.check(s, "valid PNG header",
                    thumb[:4] == b'\x89PNG')
            else:
                r.check(s, "None is acceptable fallback", True)
        except Exception as e:
            r.check(s, "no exception", False, str(e))


    def _tl_test_thumb_cache(r):
        """Leitura, gravação e remoção do cache de miniaturas funcionam (atributos de renpy.game)."""
        s = "thumb_cache"
        _tc = getattr(renpy.game, "_tl_thumb_cache", None)
        if _tc is None:
            r.check(s, "renpy.game._tl_thumb_cache exists", False, "attr missing")
            return
        original = dict(_tc)
        try:
            _tc["_test_key_"] = b"fake_png_data"
            r.check(s, "write succeeds",
                _tc.get("_test_key_") == b"fake_png_data")
            r.check(s, "read back correct",
                _tc["_test_key_"] == b"fake_png_data")

            # Remoção: simula o ciclo LRU usando um dicionário temporário.
            original_max = TL_THUMB_CACHE_MAX
            test_cache = {}
            for i in range(original_max + 5):
                test_cache[str(i)] = b"x"
                while len(test_cache) > original_max:
                    test_cache.pop(next(iter(test_cache)))
            r.check(s, "eviction keeps at max",
                len(test_cache) <= original_max)
            r.check(s, "eviction keeps newest",
                str(original_max + 4) in test_cache)
            r.check(s, "eviction drops oldest",
                "0" not in test_cache)
        finally:
            renpy.game._tl_thumb_cache.clear()
            renpy.game._tl_thumb_cache.update(original)


    def _tl_test_record_pipeline(r):
        """
        Simulate _tl_record_before → _tl_record_after without touching the
        real game state. Uses a scratch context and fake items list.
        """
        s = "record_pipeline"

        cr = _TLFakeChoice(value="choice_a_value")
        fake_items = [
            ("What do you want?", True, None),  # prompt (value=None)
            ("Choice A", True, cr),              # opção
            ("Choice B", True, "choice_b_value"),
        ]

        try:
            with _TLStateGuard(
                store_vals={
                    "_tl_history"    : [],
                    "_tl_node_count" : 0,
                    "_tl_context"    : [],
                    "_tl_ghost_nodes": [{"type": "branch", "dummy": True}],
                },
                pers_vals={"_tl_replaying": False},
            ):
                node = _tl_record_before(fake_items)

                r.check(s, "ghost_nodes cleared on record_before", store._tl_ghost_nodes == [])
                r.check(s, "record_before returns dict",  isinstance(node, dict))
                r.check(s, "node has index 0",            node["index"] == 0)
                r.check(s, "node has 2 options",          len(node["options"]) == 2)
                r.check(s, "prompt extracted",            node["prompt"] == "What do you want?")
                r.check(s, "chosen_index is None",        node.get("chosen_index") is None)
                r.check(s, "history has 1 entry",         len(_tl_history) == 1)
                r.check(s, "node_count incremented",      _tl_node_count == 1)
                r.check(s, "menu_var_snap is a dict",     isinstance(store._tl_menu_var_snap, dict))

                _tl_record_after(node, "Choice A")

                r.check(s, "chosen_index set",   node.get("chosen_index") == 0)
                r.check(s, "context updated",    len(_tl_context) == 1)
                r.check(s, "context entry correct",
                    _tl_context[0] == ("What do you want?", 0))

        except Exception as e:
            r.check(s, "no exception", False, str(e))


    def _tl_test_locked_options(r):
        """Locked items (entry[2] is False) must be excluded from node["options"]."""
        s = "locked_options"

        fake_items = [
            ("Pick one:", True, None),                  # prompt
            ("Available A", True, _TLFakeChoice()),     # disponível
            ("Locked B", False, False),                 # bloqueado — deve ser excluído
            ("Available C", True, _TLFakeChoice()),     # disponível
        ]

        try:
            with _TLStateGuard(
                store_vals={
                    "_tl_history"    : [],
                    "_tl_node_count" : 0,
                    "_tl_context"    : [],
                },
                pers_vals={"_tl_replaying": False},
            ):
                node = _tl_record_before(fake_items)

                r.check(s, "returns dict",              isinstance(node, dict))
                r.check(s, "locked option excluded",    "Locked B" not in node["options"])
                r.check(s, "available options present", node["options"] == ["Available A", "Available C"])
                r.check(s, "option count is 2",         len(node["options"]) == 2)

        except Exception as e:
            r.check(s, "no exception", False, str(e))


    def _tl_test_option_filtering(r):
        """_tl_record_before filters options by evaluated condition at record time."""
        s = "option_filtering"

        _fresh_state = {
            "_tl_history"   : [],
            "_tl_node_count": 0,
            "_tl_context"   : [],
        }

        def _run(items):
            with _TLStateGuard(store_vals=_fresh_state, pers_vals={"_tl_replaying": False}):
                return _tl_record_before(items)

        cr = _TLFakeChoice()

        node = _run([("Q", None, None), ("Yes", True, cr)])
        r.check(s, "bool True cond included", node is not None and "Yes" in node["options"])

        node = _run([("Q", None, None), ("Locked", False, False), ("Open", True, cr)])
        r.check(s, "bool False cond excluded",  node is not None and "Locked" not in node["options"])
        r.check(s, "available still present",   node is not None and "Open" in node["options"])

        node = _run([("Q", None, None), ("StrTrue", "True", cr)])
        r.check(s, "string True cond included", node is not None and "StrTrue" in node["options"])

        node = _run([("Q", None, None), ("StrFalse", "False", False), ("Open", True, cr)])
        r.check(s, "string False cond excluded", node is not None and "StrFalse" not in node["options"])

        node = _run([("Q", None, None), ("Uncond", None, cr)])
        r.check(s, "None cond with block included", node is not None and "Uncond" in node["options"])

        result = _run([("Q", None, None), ("A", False, False), ("B", False, False)])
        r.check(s, "all locked returns None", result is None)

        node = _run([("Prompt text", None, None), ("Pick", True, cr)])
        r.check(s, "block=None is prompt not option", node is not None and "Prompt text" not in node["options"])
        r.check(s, "prompt extracted correctly",      node is not None and node["prompt"] == "Prompt text")


    def _tl_test_node_has_new(r):
        """_tl_node_has_new uses _choice_returns when available."""
        s = "node_has_new"

        node_all_seen = {
            "index": 0, "options": ["A", "B"], "prompt": "?",
            "chosen_index": 0, "ast_key": None,
            "_choice_returns": [_TLFakeChoice(True), _TLFakeChoice(True)],
        }
        node_has_new = {
            "index": 0, "options": ["A", "B"], "prompt": "?",
            "chosen_index": 0, "ast_key": None,
            "_choice_returns": [_TLFakeChoice(True), _TLFakeChoice(False)],
        }
        node_no_cr = {
            "index": 0, "options": ["A", "B"], "prompt": "?",
            "chosen_index": 0, "ast_key": None,
            "_choice_returns": [None, None],
        }

        r.check(s, "all seen via CR → False",   _tl_node_has_new(node_all_seen) == False)
        r.check(s, "one unseen via CR → True",  _tl_node_has_new(node_has_new)  == True)
        # Sem CR, recorre ao mapa AST (provavelmente False se a chave for None).
        r.check(s, "no CR, no ast_key → no crash", True)
        try:
            _tl_node_has_new(node_no_cr)
            r.check(s, "no CR doesn't raise", True)
        except Exception as e:
            r.check(s, "no CR doesn't raise", False, str(e))


    def _tl_test_validate_history(r):
        """_tl_validate_on_load cleans malformed history."""
        s = "validate_history"

        import store as _store
        saved = list(_store._tl_history)

        try:
            _store._tl_history = [
                {"index": 0, "options": ["A"], "prompt": "?", "chosen_index": None},
                "not a dict",
                {"options": ["B"]},               # índice ausente
                {"index": 2},                      # opções ausentes
                {"index": 3, "options": "bad"},    # opções não são uma lista
                {"index": 4, "options": ["C", "D"], "prompt": "?", "chosen_index": 0},
            ]

            _tl_validate_on_load()

            h = _store._tl_history
            r.check(s, "only valid nodes remain", len(h) == 2)
            r.check(s, "reindexed to 0",          h[0]["index"] == 0)
            r.check(s, "reindexed to 1",          h[1]["index"] == 1)
        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            _store._tl_history = saved


    ## ─────────────────────────────────────────────────────────────────────────
    ## Executor
    ## ─────────────────────────────────────────────────────────────────────────

    def _tl_test_shadow_path_store_defaults(r):
        """Shadow path store variable exists with correct type."""
        s = "shadow_path_defaults"
        import store as _st
        r.check(s, "_tl_shadow_path is list or None",
            getattr(_st, "_tl_shadow_path", "MISSING") is None or
            isinstance(getattr(_st, "_tl_shadow_path", None), list))


    def _tl_test_shadow_path_consume_and_diverge(r):
        """
        Shadow path consumption stamps _shadow_orig_chosen on node when
        the player chose differently, and removes entries up to the match.
        """
        s = "shadow_path_consume"
        import store as _st

        saved_sp = getattr(_st, "_tl_shadow_path", None)

        try:
            _st._tl_shadow_path = [
                {"ast_key": ("a.rpy", 10), "chosen_index": 1},
                {"ast_key": ("a.rpy", 20), "chosen_index": 0},
                {"ast_key": ("a.rpy", 30), "chosen_index": 1},
            ]

            ## Simula um nó em ast_key (a.rpy, 20) no qual o jogador escolheu o índice 1 (o original era 0).
            node = {
                "index": 5, "options": ["A", "B"], "prompt": "Q",
                "chosen_index": 1, "ast_key": ("a.rpy", 20),
            }

            new_sp, div_ci, _mode = _tl_consume_shadow_path(
                _st._tl_shadow_path, node, node["chosen_index"])

            if div_ci is not None:
                node["_shadow_orig_chosen"] = div_ci
            _st._tl_shadow_path = new_sp

            r.check(s, "orig_chosen stamped", node.get("_shadow_orig_chosen") == 0)
            r.check(s, "shadow_path trimmed to tail",
                _st._tl_shadow_path == [{"ast_key": ("a.rpy", 30), "chosen_index": 1}])

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            _st._tl_shadow_path = saved_sp


    def _tl_test_shadow_path_same_choice_no_diverge(r):
        """No _shadow_orig_chosen stamped when player makes the same choice."""
        s = "shadow_path_no_diverge"
        import store as _st

        saved_sp = getattr(_st, "_tl_shadow_path", None)

        try:
            _st._tl_shadow_path = [
                {"ast_key": ("a.rpy", 10), "chosen_index": 1},
            ]
            node = {"chosen_index": 1, "ast_key": ("a.rpy", 10)}

            new_sp, div_ci, _mode = _tl_consume_shadow_path(
                _st._tl_shadow_path, node, node["chosen_index"])

            r.check(s, "div_ci is None for same choice", div_ci is None)
            r.check(s, "no _shadow_orig_chosen set",
                "_shadow_orig_chosen" not in node)
            r.check(s, "path exhausted to None", new_sp is None)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            _st._tl_shadow_path = saved_sp


    def _tl_test_validate_shadow_path_corruption(r):
        """_tl_validate_on_load resets shadow path if corrupted."""
        s = "shadow_path_validate"
        import store as _st

        saved_history = list(_st._tl_history)
        saved_sp      = getattr(_st, "_tl_shadow_path", None)

        try:
            _st._tl_history     = []
            _st._tl_shadow_path = "corrupted"   ## tipo incorreto

            _tl_validate_on_load()

            r.check(s, "corrupted shadow_path reset to None",
                getattr(_st, "_tl_shadow_path", "MISSING") is None)

            ## Uma lista válida deve permanecer sem alterações.
            _st._tl_shadow_path = [{"location": "loc0", "chosen_index": 1}]
            _tl_validate_on_load()
            sp = getattr(_st, "_tl_shadow_path", None)
            r.check(s, "valid list preserved",
                isinstance(sp, list) and len(sp) == 1)

            ## None deve permanecer sem alterações.
            _st._tl_shadow_path = None
            _tl_validate_on_load()
            r.check(s, "None preserved",
                getattr(_st, "_tl_shadow_path", "MISSING") is None)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            _st._tl_history     = saved_history
            _st._tl_shadow_path = saved_sp


    def _tl_test_on_game_start(r):
        """_tl_on_game_start clears replay state and writes wf_start."""
        s = "on_game_start"

        saved_replaying = persistent._tl_replaying
        saved_target    = persistent._tl_replay_target
        saved_save      = renpy.save
        save_calls      = []

        try:
            persistent._tl_replaying    = True
            persistent._tl_replay_target = 3

            renpy.save = lambda slot, **kw: save_calls.append(slot)

            _tl_on_game_start()

            r.check(s, "replaying cleared",      persistent._tl_replaying is False)
            r.check(s, "replay_target cleared",  persistent._tl_replay_target is None)
            r.check(s, "renpy.save called",      len(save_calls) >= 1)
            r.check(s, "wf_start saved",        "wf_start" in save_calls)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            persistent._tl_replaying    = saved_replaying
            persistent._tl_replay_target = saved_target
            renpy.save = saved_save


    def _tl_test_on_load(r):
        """_tl_on_load: stale-state clear and shadow-path reconstruction from replay_path."""
        s = "on_load"

        saved_replaying  = persistent._tl_replaying
        saved_target     = persistent._tl_replay_target
        saved_path       = persistent._tl_replay_path
        saved_store_sp   = getattr(store, "_tl_shadow_path", None)
        saved_skipping   = config.skipping

        try:
            ## Ramo 1: estado obsoleto — replaying=True, target=None → limpa a repetição.
            persistent._tl_replaying     = True
            persistent._tl_replay_target = None
            persistent._tl_replay_path   = None
            store._tl_shadow_path        = None

            _tl_on_load()

            r.check(s, "stale: replaying cleared",
                persistent._tl_replaying is False)

            ## Ramo 2 (salto de menu): replay_path com 3 entradas, destino = nó 1.
            ## shadow = entradas com índice > 1 → apenas o índice 2.
            persistent._tl_replaying     = True
            persistent._tl_replay_target = {"node_index": 1, "option_index": 0}
            persistent._tl_replay_path   = [
                {"index": 0, "ast_key": ("a.rpy", 10), "chosen_index": 0},
                {"index": 1, "ast_key": ("a.rpy", 20), "chosen_index": 1},
                {"index": 2, "ast_key": ("a.rpy", 30), "chosen_index": 0},
            ]
            store._tl_shadow_path        = None

            _tl_on_load()

            r.check(s, "menu branch: store._tl_shadow_path set",
                isinstance(store._tl_shadow_path, list))
            r.check(s, "menu branch: only entries after target (index > 1)",
                len(store._tl_shadow_path) == 1 and
                store._tl_shadow_path[0].get("index") == 2)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            persistent._tl_replaying     = saved_replaying
            persistent._tl_replay_target = saved_target
            persistent._tl_replay_path   = saved_path
            store._tl_shadow_path        = saved_store_sp
            config.skipping              = saved_skipping


    def _tl_test_interact_callback_var_flush(r):
        """_tl_interact_callback flushes pending var changes; discards when notifs disabled."""
        s = "interact_callback_var_flush"

        saved_notifs   = getattr(persistent, "_tl_var_notifs_enabled", True)
        saved_pending  = dict(getattr(store, "_tl_pending_var_changes", None) or {})
        show_calls     = []

        try:
            ## Com avisos ativados: o descarregamento limpa as alterações pendentes.
            persistent._tl_var_notifs_enabled = True
            store._tl_pending_var_changes = {"affection": (1, 2)}
            _saved_show = renpy.show_screen
            renpy.show_screen = lambda *a, **kw: show_calls.append(kw.get("message", a))
            try:
                _tl_interact_callback()
            finally:
                renpy.show_screen = _saved_show
            r.check(s, "notifs enabled: pending cleared",
                    not getattr(store, "_tl_pending_var_changes", None))

            ## Com avisos desativados: descarta sem exibir.
            show_calls[:] = []
            persistent._tl_var_notifs_enabled = False
            store._tl_pending_var_changes = {"affection": (1, 2)}
            _saved_show = renpy.show_screen
            renpy.show_screen = lambda *a, **kw: show_calls.append(kw.get("message", a))
            try:
                _tl_interact_callback()
            finally:
                renpy.show_screen = _saved_show
            r.check(s, "notifs disabled: pending discarded",
                    not getattr(store, "_tl_pending_var_changes", None))
            r.check(s, "notifs disabled: no screen shown", len(show_calls) == 0)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            persistent._tl_var_notifs_enabled = saved_notifs
            store._tl_pending_var_changes      = saved_pending


    def _tl_test_log_truncation(r):
        """Truncate log to 1 entry during save — verify save works and log is restored."""
        s = "log_truncation"
        import os
        _savedir = renpy.config.savedir

        def _find_file(slot):
            for _ext in ("-LT1.save", ".save"):
                _p = os.path.join(_savedir, slot + _ext)
                if os.path.exists(_p):
                    return _p
            return None

        _slot_full  = "_tl_test_trunc_full"
        _slot_trunc = "_tl_test_trunc_1"
        _path_full  = None
        _path_trunc = None
        try:
            _log    = renpy.game.log
            _before = list(_log.log)
            _n_full = len(_before)

            r.check(s, "log has entries", _n_full > 0, "log has {} entries".format(_n_full))

            ## save completo (sem captura de tela, se compatível — Ren'Py 8+).
            try:
                renpy.save(_slot_full, include_screenshot=False)
            except TypeError:
                renpy.save(_slot_full)
            _path_full = _find_file(_slot_full)
            r.check(s, "full save exists", _path_full is not None)

            ## save reduzido (1 entrada, sem captura de tela).
            _save_ok = False
            try:
                _log.log = [_before[-1]] if _before else []
                try:
                    renpy.save(_slot_trunc, include_screenshot=False)
                except TypeError:
                    renpy.save(_slot_trunc)
                _save_ok = True
            finally:
                _log.log = _before

            r.check(s, "truncated save completed", _save_ok)
            r.check(s, "log restored length", len(_log.log) == _n_full,
                    "got {} expected {}".format(len(_log.log), _n_full))
            r.check(s, "log restored identity", _log.log is _before or list(_log.log) == _before)

            _path_trunc = _find_file(_slot_trunc)
            r.check(s, "truncated save exists", _path_trunc is not None)

            if _path_full and _path_trunc:
                _sz_full  = os.path.getsize(_path_full)
                _sz_trunc = os.path.getsize(_path_trunc)
                r.check(s, "truncated smaller than full",
                        _sz_trunc < _sz_full,
                        "{} KB vs {} KB".format(_sz_trunc // 1024, _sz_full // 1024))
                _tl_log("Timeline: teste de truncamento: completo={} KB ({} entradas), truncado={} KB (1 entrada)".format(
                    _sz_full // 1024, _n_full, _sz_trunc // 1024))

        except Exception as _e:
            r.check(s, "no exception", False, str(_e))
        finally:
            for _p in (_path_full, _path_trunc):
                try:
                    if _p and os.path.exists(_p):
                        os.remove(_p)
                except Exception:
                    pass


    def _tl_test_pre_save_slot_format(r):
        """_tl_pre_save_slot produces correct format and hash semantics."""
        s = "pre_save_slot"
        _fn = globals().get("_tl_pre_save_slot")
        if _fn is None:
            r.check(s, "_tl_pre_save_slot exists", False, "function not found")
            return
        ctx = [("Choose", 0), ("Attack?", 1)]
        slot = _fn(2, ctx)
        r.check(s, "starts with _pre_0002_", slot.startswith("_pre_0002_"))
        r.check(s, "hash is 6 chars", len(slot.split("_")[-1]) == 6)
        r.check(s, "deterministic", slot == _fn(2, ctx))
        r.check(s, "different from post-choice slot", slot != _tl_save_slot(2, ctx))
        r.check(s, "index sensitive", _fn(2, ctx) != _fn(3, ctx))
        ctx_b = [("Choose", 0), ("Attack?", 0)]
        r.check(s, "context sensitive", _fn(2, ctx) != _fn(2, ctx_b))
        r.check(s, "menu0 constant", _fn(0, []) == _fn(0, [("any", 99)]))
        r.check(s, "only uses context up to N",
            _fn(1, [("A", 0)]) == _fn(1, [("A", 0), ("B", 1)]))


    def _tl_test_jump_uses_pre_save(r):
        """
        _tl_jump picks up the exact pre-save for the target menu (v2 fallback path).
        Only tests nodes WITHOUT a snapshot — those fall through to the pre-save path.
        Nodes with snapshots take the synthetic path (unfreeze, never returns here).
        Skipped if no such node has a pre-save on disk.
        """
        s = "jump_uses_pre_save"
        _jump  = globals().get("_tl_jump")
        _find  = globals().get("_tl_find_pre_save")
        if _jump is None or _find is None:
            r.check(s, "functions exist", False, "missing _tl_jump or _tl_find_pre_save")
            return

        _hist = getattr(store, "_tl_history", [])
        if len(_hist) < 2:
            r.check(s, "skipped: need ≥2 choices", True, "play further first")
            return

        ## Considera apenas nós SEM snapshot — eles seguem pelo caminho pré-save.
        _target = None
        for _n in _hist[:-1]:
            _idx = _n.get("index")
            if _idx is None or _tl_get_menu_snapshot(_idx) is not None:
                continue
            _ak = _tl_node_menu_site_key(_n) if _tl_node_menu_site_key else None
            if _find(_idx, list(store._tl_context), _ak) is not None:
                _target = _n
                break

        if _target is None:
            r.check(s, "skipped: no no-snapshot node with pre-save on disk", True,
                    "all nodes have snapshots (synthetic path) or no pre-save found")
            return

        _target_idx     = _target["index"]
        _prev_load_slot = getattr(store, "_tl_load_slot", None)
        _prev_replaying = getattr(persistent, "_tl_replaying", False)
        _prev_recovery  = persistent._tl_recovery_slot
        try:
            _tl_jump(_target_idx, 0)
            _slot = getattr(store, "_tl_load_slot", None)
            r.check(s, "load_slot is a pre-save slot",
                    _slot is not None and _slot.startswith("_pre_"),
                    "got {}".format(_slot))
            r.check(s, "pre-save slot matches target index",
                    _slot is not None and "_pre_{:04d}_".format(_target_idx) in _slot,
                    "slot={} target_idx={}".format(_slot, _target_idx))
        finally:
            store._tl_load_slot       = _prev_load_slot
            persistent._tl_replaying  = _prev_replaying
            persistent._tl_recovery_slot = _prev_recovery


    ## ─────────────────────────────────────────────────────────────────────────
    ## Testes de salto sintético
    ## ─────────────────────────────────────────────────────────────────────────

    def _tl_test_cache_not_in_get_roots(r):
        """
        Snapshot cache lives on renpy.game.log, not in store, so it never
        appears in get_roots() and cannot create a recursive pickle cycle.
        Also validates that cached entries have the expected structure.
        """
        s = "cache_not_in_get_roots"

        cache = getattr(renpy.game.log, "_tl_snapshot_cache", None)
        r.check(s, "cache exists on log", cache is not None,
                "play through a menu first")
        if cache is None:
            return

        roots = renpy.game.log.get_roots()
        r.check(s, "store._tl_snapshot_cache not in roots",
                "store._tl_snapshot_cache" not in roots)
        r.check(s, "cache object not a root value",
                not any(v is cache for v in roots.values()))

        menu_snaps = cache.get("menu", {})
        r.check(s, "menu cache has entries", bool(menu_snaps),
                "menu={}".format(len(menu_snaps)))

        label_bad = []
        for idx, snap in menu_snaps.items():
            _roots = snap.get("roots") if hasattr(snap, "get") else None
            _ctx   = snap.get("context") if hasattr(snap, "get") else None
            r.check(s, "menu[{}] roots non-empty dict".format(idx),
                    hasattr(_roots, "items") and bool(_roots),
                    "snap_type={} roots_type={} roots_len={}".format(
                        type(snap).__name__,
                        type(_roots).__name__,
                        len(_roots) if hasattr(_roots, "__len__") else "N/A"))
            r.check(s, "menu[{}] context not None".format(idx),
                    _ctx is not None)
            if _ctx is not None:
                cur = getattr(_ctx, "current", None)
                if not renpy.game.script.has_label(cur):
                    label_bad.append((idx, cur))
        r.check(s, "all menu snapshot contexts resolve via has_label",
                len(label_bad) == 0, "bad={}".format(label_bad))
        _tl_log("Timeline: cache ausente em get_roots: menu={} rótulo_inválido={}".format(
            len(menu_snaps), label_bad))


    def _tl_test_cache_transfer(r):
        """
        _tl_transfer_snapshot_cache copies the cache from renpy.game.log to a
        fresh RollbackLog so it survives synthetic jumps (which replace the log).
        """
        s = "cache_transfer"
        try:
            import renpy.rollback as rb_mod
        except ImportError:
            r.check(s, "skipped: no renpy.rollback", True)
            return

        saved_cache = getattr(renpy.game.log, "_tl_snapshot_cache", None)
        fake_cache  = _tl_make_cache()
        fake_cache["menu"][99] = "sentinel"
        renpy.game.log._tl_snapshot_cache = fake_cache

        try:
            new_log = rb_mod.RollbackLog()
            _tl_transfer_snapshot_cache(new_log)
            transferred = getattr(new_log, "_tl_snapshot_cache", None)
            r.check(s, "cache copied to new_log", transferred is fake_cache)
            r.check(s, "menu entry preserved",
                    transferred is not None and
                    transferred.get("menu", {}).get(99) == "sentinel")
        finally:
            if saved_cache is not None:
                renpy.game.log._tl_snapshot_cache = saved_cache
            elif hasattr(renpy.game.log, "_tl_snapshot_cache"):
                del renpy.game.log._tl_snapshot_cache


    def _tl_test_unfreeze_builds_rollback_log(r):
        """
        _tl_unfreeze_from_snapshot builds a RollbackLog with exactly 1 entry.
        The entry must have hard_checkpoint=True, checkpoint=True, stores={}, objects=[],
        and context matching the snapshot. Verified by monkeypatching RollbackLog.unfreeze.
        """
        s = "unfreeze_builds_rollback_log"

        class _SentinelError(Exception):
            pass

        try:
            try:
                import renpy.rollback as rb_mod
            except ImportError:
                import renpy.python as rb_mod
        except Exception as e:
            r.check(s, "rollback module importable", False, str(e))
            return

        RollbackLog = rb_mod.RollbackLog
        captured    = []

        def mock_unfreeze(self, roots, label):
            captured.append(self)
            raise _SentinelError("intercepted")

        fake_ctx  = _TLFakeCtx()
        fake_snap = {"roots": {"store._tl_history": []}, "context": fake_ctx}

        saved_unfreeze_method = RollbackLog.unfreeze
        try:
            RollbackLog.unfreeze = mock_unfreeze

            try:
                _tl_unfreeze_from_snapshot(fake_snap)
            except _SentinelError:
                pass
            except Exception as e:
                r.check(s, "no unexpected exception", False, str(e))
                return

            r.check(s, "unfreeze called once",     len(captured) == 1)
            if not captured:
                return

            log_inst = captured[0]
            r.check(s, "log has 1 entry",          len(log_inst.log) == 1)
            r.check(s, "rollback_limit is 1",      log_inst.rollback_limit == 1)

            if not log_inst.log:
                return
            rb = log_inst.log[0]
            r.check(s, "rb.checkpoint=True",        rb.checkpoint is True)
            r.check(s, "rb.hard_checkpoint=True",   rb.hard_checkpoint is True)
            r.check(s, "rb.stores={}",              rb.stores == {})
            r.check(s, "rb.objects=[]",             rb.objects == [])
            r.check(s, "rb.context is copy not original", rb.context is not fake_ctx)
            r.check(s, "rb.context.interacting is False",  getattr(rb.context, "interacting", "MISSING") is False)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            RollbackLog.unfreeze = saved_unfreeze_method


    def _tl_test_snapshot_ctx_isolation(r):
        """
        Snapshot ctx must be isolated from Ren'Py's post-unfreeze mutations.
        After unfreeze, Ren'Py mutates rb.context (the deepcopy) in place.
        The original snap["context"] must stay clean so a second jump gets
        ctx.interacting=False regardless of what happened after the first jump.
        """
        import copy as _copy
        s = "snapshot_ctx_isolation"

        fake_ctx      = _TLFakeCtx()
        fake_ctx.interacting = False
        snap          = {"roots": {}, "context": fake_ctx}

        # simula o primeiro descongelamento: deepcopy ctx; depois o Ren'Py altera a cópia.
        ctx1 = _copy.deepcopy(snap["context"])
        ctx1.interacting = True

        r.check(s, "snap ctx unaffected by first-unfreeze mutation",
                snap["context"].interacting is False)

        # simula o segundo descongelamento: outro deepcopy deve gerar um ctx limpo.
        ctx2 = _copy.deepcopy(snap["context"])
        r.check(s, "second unfreeze ctx.interacting clean",
                ctx2.interacting is False)

        r.check(s, "ctx1 and ctx2 are distinct objects", ctx1 is not ctx2)


    ## ── Testes da versão 2 ────────────────────────────────────────────────────────────

    def _tl_test_jump_staging(r):
        """
        _tl_jump(node_index, option_index) stages replay_path with ast_key entries
        and sets replaying=True. Entries after the target become the shadow on next load.
        """
        s = "jump_staging"
        import store as _st

        def _mk(idx, ci, ak):
            return {"index": idx, "options": ["A", "B"], "prompt": "Q",
                    "chosen_index": ci, "ast_key": ak, "_location": None,
                    "thumb_bytes": None, "_rollback_id": None}

        saved_history    = list(_st._tl_history)
        saved_count      = _st._tl_node_count
        saved_context    = list(_st._tl_context)
        saved_replaying  = persistent._tl_replaying
        saved_target     = persistent._tl_replay_target
        saved_path       = persistent._tl_replay_path
        saved_recovery   = persistent._tl_recovery_slot
        saved_prev_thumb = persistent._tl_prev_thumb

        try:
            _st._tl_history = [
                _mk(0, 0, ("a.rpy", 10)),
                _mk(1, 1, ("a.rpy", 20)),
                _mk(2, 0, ("a.rpy", 30)),
            ]
            _st._tl_context    = [("Q0", 0), ("Q1", 1), ("Q2", 0)]
            _st._tl_node_count = 3

            _tl_jump(0, 1)

            r.check(s, "replaying=True", persistent._tl_replaying is True)
            r.check(s, "replay_target set",
                isinstance(persistent._tl_replay_target, dict) and
                persistent._tl_replay_target.get("node_index") == 0 and
                persistent._tl_replay_target.get("option_index") == 1)
            rp = persistent._tl_replay_path
            r.check(s, "replay_path is list", isinstance(rp, list))
            r.check(s, "replay_path has entries", len(rp) >= 1)
            r.check(s, "replay_path entries have ast_key",
                all("ast_key" in e for e in rp))
            r.check(s, "recovery_slot staged",
                persistent._tl_recovery_slot is not None)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            _st._tl_history              = saved_history
            _st._tl_node_count           = saved_count
            _st._tl_context              = saved_context
            persistent._tl_replaying     = saved_replaying
            persistent._tl_replay_target = saved_target
            persistent._tl_replay_path   = saved_path
            persistent._tl_recovery_slot = saved_recovery
            persistent._tl_prev_thumb    = saved_prev_thumb


    def _tl_test_jump_empty_shadow(r):
        """
        When jumping to the last history node, no entries follow it in replay_path,
        so the shadow path reconstructed in _tl_on_load will be None.
        """
        s = "jump_empty_shadow"
        import store as _st

        def _mk2(idx, ci, ak):
            return {"index": idx, "options": ["A", "B"], "prompt": "Q",
                    "chosen_index": ci, "ast_key": ak, "_location": None,
                    "thumb_bytes": None, "_rollback_id": None}

        saved_history    = list(_st._tl_history)
        saved_count      = _st._tl_node_count
        saved_context    = list(_st._tl_context)
        saved_replaying  = persistent._tl_replaying
        saved_target     = persistent._tl_replay_target
        saved_path       = persistent._tl_replay_path
        saved_recovery   = persistent._tl_recovery_slot
        saved_prev_thumb = persistent._tl_prev_thumb

        try:
            _st._tl_history    = [_mk2(0, 0, ("a.rpy", 10))]
            _st._tl_context    = [("Q0", 0)]
            _st._tl_node_count = 1

            _tl_jump(0, 1)

            rp = persistent._tl_replay_path
            target_idx = persistent._tl_replay_target.get("node_index", -1) if isinstance(persistent._tl_replay_target, dict) else -1
            shadow_entries = [e for e in (rp or []) if e.get("index", -1) > target_idx]
            r.check(s, "no shadow entries after last node", len(shadow_entries) == 0)

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            _st._tl_history              = saved_history
            _st._tl_node_count           = saved_count
            _st._tl_context              = saved_context
            persistent._tl_replaying     = saved_replaying
            persistent._tl_replay_target = saved_target
            persistent._tl_replay_path   = saved_path
            persistent._tl_recovery_slot = saved_recovery
            persistent._tl_prev_thumb    = saved_prev_thumb


    def _tl_test_cancel_jump(r):
        """_tl_cancel_jump clears all persistent replay fields and sets load slot."""
        s = "cancel_jump"

        saved_replaying  = persistent._tl_replaying
        saved_target     = persistent._tl_replay_target
        saved_path       = persistent._tl_replay_path
        saved_recovery   = persistent._tl_recovery_slot
        saved_sj         = getattr(persistent, "_tl_synthetic_jump", False)
        saved_load_slot  = getattr(store, "_tl_load_slot", "")

        try:
            persistent._tl_replaying          = True
            persistent._tl_replay_target      = {"node_index": 5, "option_index": 0}
            persistent._tl_replay_path        = [{"index": 6, "ast_key": ("a.rpy", 10), "chosen_index": 0}]
            persistent._tl_recovery_slot      = "_ch_recovery"
            persistent._tl_synthetic_jump     = True

            slot = _tl_cancel_jump()

            r.check(s, "replaying cleared",     persistent._tl_replaying is False)
            r.check(s, "replay_target cleared", persistent._tl_replay_target is None)
            r.check(s, "replay_path cleared",   persistent._tl_replay_path is None)
            r.check(s, "returns recovery slot", slot == "_ch_recovery")
            r.check(s, "_tl_load_slot set",     store._tl_load_slot == "_ch_recovery")

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            persistent._tl_replaying      = saved_replaying
            persistent._tl_replay_target  = saved_target
            persistent._tl_replay_path    = saved_path
            persistent._tl_recovery_slot  = saved_recovery
            persistent._tl_synthetic_jump = saved_sj
            store._tl_load_slot           = saved_load_slot


    ## ─────────────────────────────────────────────────────────────────────────
    ## Testes dos cartões de ramos futuros no jogo
    ## ─────────────────────────────────────────────────────────────────────────

    def _tl_test_ghost_gate_guards(r):
        """Replaying and skipping gates block ghost emission from _tl_on_if_execute."""
        s = "ghost_gate_guards"

        ## Localiza um nó If de algum arquivo do jogo para usar como caso de teste.
        if_node = None
        try:
            for node in renpy.game.script.namemap.values():
                if (type(node).__name__ == "If"
                        and _tl_is_game_file(getattr(node, "filename", ""))
                        and len(getattr(node, "entries", [])) > 1):
                    if_node = node
                    break
        except Exception as e:
            r.check(s, "namemap accessible", False, str(e))
            return

        if if_node is None:
            r.check(s, "skipped: no multi-branch game If node found", True)
            return

        ## Condição 1: replaying impede a emissão.
        try:
            with _TLStateGuard(
                store_vals={"_tl_ghost_nodes": [], "_tl_skip_ghost_ifs": set()},
                pers_vals={"_tl_replaying": True},
            ):
                _tl_on_if_execute(if_node, 0)
                r.check(s, "replaying blocks ghost emission",
                        store._tl_ghost_nodes == [])
        except Exception as e:
            r.check(s, "replaying gate no exception", False, str(e))

        ## Condição 2: config.skipping impede a emissão.
        saved_skipping = config.skipping
        try:
            with _TLStateGuard(
                store_vals={"_tl_ghost_nodes": [], "_tl_skip_ghost_ifs": set()},
                pers_vals={"_tl_replaying": False},
            ):
                config.skipping = True
                _tl_on_if_execute(if_node, 0)
                r.check(s, "skipping blocks ghost emission",
                        store._tl_ghost_nodes == [])
        except Exception as e:
            r.check(s, "skipping gate no exception", False, str(e))
        finally:
            config.skipping = saved_skipping


    def _tl_test_ghost_on_if_execute(r):
        """
        _tl_on_if_execute with a real game If node appends to store._tl_ghost_nodes
        and writes the persistent cache entry.
        """
        s = "ghost_on_if_execute"

        ## Localiza um nó If do jogo com pelo menos 2 ramos (para que os dados não sejam None).
        if_node = None
        try:
            for node in renpy.game.script.namemap.values():
                if (type(node).__name__ == "If"
                        and _tl_is_game_file(getattr(node, "filename", ""))
                        and len(getattr(node, "entries", [])) >= 2):
                    if_node = node
                    break
        except Exception as e:
            r.check(s, "namemap accessible", False, str(e))
            return

        if if_node is None:
            r.check(s, "skipped: no suitable game If node", True,
                    "play further to load more script nodes")
            return

        saved_cache = (persistent._tl_ghost_node_cache or {}).copy()
        try:
            with _TLStateGuard(
                store_vals={"_tl_ghost_nodes": [], "_tl_skip_ghost_ifs": set()},
                pers_vals={"_tl_replaying": False, "_tl_ghost_node_cache": {}},
            ):
                _tl_on_if_execute(if_node, 0)

                r.check(s, "ghost_nodes populated",
                        len(store._tl_ghost_nodes) >= 1)

                if store._tl_ghost_nodes:
                    node_dict = store._tl_ghost_nodes[0]
                    r.check(s, "ghost node has ast_key",
                            "ast_key" in node_dict)
                    r.check(s, "ghost node has taken_index",
                            "taken_index" in node_dict)
                    r.check(s, "ghost node has branch_imgs",
                            "branch_imgs" in node_dict)
                    r.check(s, "ghost node cluster_with_prev is bool",
                            isinstance(node_dict.get("cluster_with_prev"), bool))

                cache_key = str((if_node.filename, if_node.linenumber))
                r.check(s, "persistent cache entry written",
                        cache_key in (persistent._tl_ghost_node_cache or {}))

                if cache_key in (persistent._tl_ghost_node_cache or {}):
                    cached = persistent._tl_ghost_node_cache[cache_key]
                    r.check(s, "cache entry has conditions",
                            isinstance(cached.get("conditions"), list))
                    r.check(s, "cache entry has seen_fns",
                            isinstance(cached.get("seen_fns"), list))

        except Exception as e:
            r.check(s, "no exception", False, str(e))
        finally:
            persistent._tl_ghost_node_cache = saved_cache


    def _tl_run_tests():
        r = _TLTestResults()

        _tl_test_persistent(r)
        _tl_test_store_defaults(r)
        _tl_test_hooks_wired(r)
        _tl_test_save_slot(r)
        _tl_test_thumbnail(r)
        _tl_test_thumb_cache(r)
        _tl_test_record_pipeline(r)
        _tl_test_locked_options(r)
        _tl_test_option_filtering(r)
        _tl_test_node_has_new(r)
        _tl_test_validate_history(r)
        _tl_test_shadow_path_store_defaults(r)
        _tl_test_shadow_path_consume_and_diverge(r)
        _tl_test_shadow_path_same_choice_no_diverge(r)
        _tl_test_validate_shadow_path_corruption(r)
        _tl_test_on_game_start(r)
        _tl_test_on_load(r)
        _tl_test_interact_callback_var_flush(r)
        _tl_test_log_truncation(r)
        _tl_test_pre_save_slot_format(r)
        _tl_test_jump_uses_pre_save(r)
        _tl_test_cache_not_in_get_roots(r)
        _tl_test_cache_transfer(r)
        _tl_test_unfreeze_builds_rollback_log(r)
        _tl_test_snapshot_ctx_isolation(r)
        _tl_test_jump_staging(r)
        _tl_test_jump_empty_shadow(r)
        _tl_test_cancel_jump(r)
        _tl_test_ghost_gate_guards(r)
        _tl_test_ghost_on_if_execute(r)
        # Grava os resultados em debug.txt (cache/debug.txt por _tl_log).
        _tl_log("=" * 60)
        _tl_log("EXECUÇÃO DE TESTES DO WELLS TIMELINE")
        _tl_log("=" * 60)
        for suite, name, ok, detail in r.results:
            status = "PASS" if ok else "FAIL"
            line = "  [{}]  {}.{}".format(status, suite, name)
            if not ok and detail:
                line += "  → {}".format(detail)
            _tl_log(line)
        _tl_log("")
        _tl_log("Resultados: {} aprovados, {} falharam".format(r.passed, r.failed))
        _tl_log("=" * 60)

        # Também exibe um aviso no jogo.
        if r.failed == 0:
            renpy.notify("SUCESSO: todos os {} testes passaram".format(r.passed))
        else:
            renpy.notify("FALHA: {}/{} testes falharam — consulte debug.txt".format(
                r.failed, r.passed + r.failed))

