## =============================================================================
## WELLS TIMELINE — tl_menu_state.rpy
## Identidade de menus, leitura de opções e funções auxiliares de retorno de escolha.
## As seções consolidadas mantêm a ordem de carregamento anterior.
## =============================================================================

## -----------------------------------------------------------------------------
## Seção 1: backend/tl_menu_location.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_menu_location.rpy
## Resolução da localização do menu: chaves estáveis de identificação dos nós do histórico.
## =============================================================================

init -2 python:

    def _tl_normalize_script_path(path):
        """Normalize script paths so runtime and dumped AST paths can be joined."""
        if not isinstance(path, str):
            return path
        if not path.startswith("game/") and "/" in path:
            path = "game/" + path
        if path.endswith(".rpyc"):
            return path[:-1]
        return path

    def _tl_menu_site_key(file_path, line_no):
        """Build a normalized persistent menu-image key from file/line data."""
        if not file_path or not line_no:
            return None
        return (_tl_normalize_script_path(file_path), line_no)

    def _tl_location_menu_ast_key(location):
        """Resolve a runtime `_location` tuple to the real Menu `(file, line)` key when possible."""
        if not isinstance(location, tuple):
            return None
        try:
            node = renpy.game.script.namemap.get(location)
            if node is not None and type(node).__name__ == "Menu":
                return _tl_menu_site_key(getattr(node, "filename", None), getattr(node, "linenumber", None))
        except Exception as e:
            _tl_log("TL menu_ast_key lookup failed: {}".format(e))
        return None

    def _tl_location_menu_site_key(location):
        """Return the normalized menu-site key from a runtime `_location` tuple."""
        menu_key = _tl_location_menu_ast_key(location)
        if menu_key is not None:
            return menu_key
        if not isinstance(location, tuple) or len(location) < 3:
            return None
        return _tl_menu_site_key(location[0], location[2])

    def _tl_node_menu_site_key(node):
        """Best-effort stable menu-site identity for a history node."""
        if not isinstance(node, dict):
            return None
        ast_key = node.get("ast_key")
        if isinstance(ast_key, (list, tuple)) and len(ast_key) == 2:
            return _tl_menu_site_key(ast_key[0], ast_key[1])
        return _tl_location_menu_site_key(node.get("_location"))

    def _tl_live_menu_lookup():
        """Return a lazy `(file, line) -> live Menu node` map from Ren'Py namemap."""
        rt_cache = _tl_runtime_cache_store()
        if "live_menu_lookup" in rt_cache:
            return rt_cache["live_menu_lookup"]
        lookup = {}
        try:
            namemap = renpy.game.script.namemap
        except Exception as e:
            _tl_log("TL option peek: namemap not available: {}".format(e))
            rt_cache["live_menu_lookup"] = {}
            return rt_cache["live_menu_lookup"]

        for node in namemap.values():
            if type(node).__name__ != "Menu":
                continue
            key = _tl_stmt_ast_key(node)
            if key and key not in lookup:
                lookup[key] = node

        rt_cache["live_menu_lookup"] = lookup
        return rt_cache["live_menu_lookup"]

## -----------------------------------------------------------------------------
## Seção 2: backend/tl_menu_options.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_menu_options.rpy
## Funções auxiliares de itens de menu: leitura original, filtragem, indexação e preenchimento do retorno de escolha.
## =============================================================================

init -2 python:

    def _tl_parse_menu_items(items):
        """
        Parse raw Ren'Py menu items (label, condition, block) into (prompt, valid_labels).
        Caption entries (block=None) contribute to the prompt string; option entries
        with a falsy condition are excluded. String conditions are evaluated via py_eval;
        options are included on eval failure so a broken condition doesn't silently vanish.
        Returns (prompt_str, valid_label_list).
        """
        prompt       = ""
        valid_labels = []
        for entry in items:
            label = entry[0]
            cond  = entry[1] if len(entry) > 1 else None
            block = entry[2] if len(entry) > 2 else None
            if block is None:
                ## Sem bloco → entrada de legenda ou prompt
                if not prompt:
                    prompt = label
            elif cond in (None, True, "True"):
                valid_labels.append(label)
            elif cond is False or cond == "False":
                pass  ## bloqueado explicitamente
            else:
                try:
                    if renpy.python.py_eval(cond):
                        valid_labels.append(label)
                except Exception:
                    valid_labels.append(label)  ## inclui quando a avaliação falha
        return prompt, valid_labels

    def _tl_valid_choice_entries(items):
        out = []
        for entry in items:
            label = entry[0]
            value = entry[1] if len(entry) > 1 else None
            if value is None:
                continue
            out.append((label, value))
        return out

    def _tl_choice_entry_for_index(items, choice_index):
        if choice_index is None or choice_index < 0:
            return None
        valid_items = _tl_valid_choice_entries(items)
        if choice_index >= len(valid_items):
            return None
        return valid_items[choice_index]

    def _tl_choice_index_from_return_value(items, rv):
        _valid = list(_tl_valid_choice_entries(items))
        for i, (_label, value) in enumerate(_valid):
            if value is rv:
                return i
        for i, (_label, value) in enumerate(_valid):
            if value == rv:
                return i
            try:
                if value.value == rv:
                    return i
            except AttributeError:
                pass
        return None

    def _tl_populate_choice_returns(node, items):
        if node is None:
            return
        _crs = _tl_runtime_choice_returns(node, create=True)
        if _crs is None:
            return
        for i, (_label, value) in enumerate(_tl_valid_choice_entries(items)):
            if i >= len(_crs):
                break
            if value is not None and hasattr(value, "get_chosen"):
                _crs[i] = value

