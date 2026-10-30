## =============================================================================
## WELLS TIMELINE — tl_ast_tools.rpy
## Inspeção da AST e funções auxiliares compartilhadas para AST.
## As seções consolidadas mantêm a ordem de carregamento anterior.
## =============================================================================

## -----------------------------------------------------------------------------
## Seção 1: backend/tl_ast_dump.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — timeline_ast_dump.rpy
## Exportador de AST CFG — ferramenta de desenvolvimento acionada pelo botão de dev.
## Percorre renpy.game.script.namemap para os labels informados e grava um
## JSON estruturado, lido pela ferramenta externa gen_cfg.py para gerar
## o arquivo DOT. Não analisa texto .rpy — usa a AST ativa do Ren'Py.
## =============================================================================

init -2 python:

    def _tl_cfg_dump_ast(labels=None, outfile=None):
        """
        Dump AST for the given label names to a JSON file.
        If labels is None, dumps ALL labels in the namemap.
        outfile: absolute path; defaults to <moddir>/cfg/full_ast.json
        """
        import renpy.ast as _rast

        _moddir = os.path.join(renpy.config.gamedir, "wells/timeline")
        if not os.path.isdir(_moddir):
            os.makedirs(_moddir)
        if outfile is None:
            _cfgdir = os.path.join(_moddir, "cfg")
            if not os.path.isdir(_cfgdir):
                os.makedirs(_cfgdir)
            outfile = os.path.join(_cfgdir, "full_ast.json")

        _namemap = renpy.game.script.namemap

        if labels is None:
            labels = [
                k for k in _namemap.keys()
                if isinstance(k, str) and not k.startswith("_")
            ]

        def _img_str(stmt):
            imspec = getattr(stmt, "imspec", None)
            if imspec and imspec[0]:
                return " ".join(imspec[0])
            return None

        def _json_safe(val):
            """Recursively convert any Ren'Py AST value to a JSON-safe form."""
            if val is None or isinstance(val, (bool, int, float, str)):
                return val
            if isinstance(val, (list, tuple)):
                _items = list(val)
                ## Uma lista linear de nós AST é um bloco — serializa recursivamente.
                if _items and all(isinstance(_v, _rast.Node) for _v in _items):
                    return _serialize_block(_items)
                return [_json_safe(_v) for _v in _items]
            if isinstance(val, dict):
                return {str(_k): _json_safe(_v) for _k, _v in val.items()}
            if isinstance(val, _rast.Node):
                _n = getattr(val, "name", None)
                if _n is not None:
                    return {"__node__": list(_n)}
                return {"__type__": type(val).__name__}
            ## PyCode e objetos semelhantes com .source.
            if hasattr(val, "source"):
                return val.source
            try:
                return str(val)
            except Exception:
                return None

        def _serialize_block(stmts):
            """Serialize a list of AST statements generically using Ren'Py's own attributes."""
            out = []
            for s in (stmts or []):
                t = type(s).__name__
                _name = list(s.name) if getattr(s, "name", None) is not None else None
                _next_lbl = _stmt_next_boundary(s)
                ## Exporta de forma genérica todos os atributos da instância; as chaves universais prevalecem no final.
                d = {}
                for _a, _v in (vars(s) if hasattr(s, "__dict__") else {}).items():
                    if _a in ("name", "next", "linenumber"):
                        continue
                    try:
                        d[_a] = _json_safe(_v)
                    except Exception:
                        pass
                ## Campos específicos necessários para percorrer as fórmulas.
                if isinstance(s, _rast.Jump):
                    d["target"] = getattr(s, "target", None)
                elif isinstance(s, _rast.Call):
                    d["target"] = getattr(s, "label", None)
                elif isinstance(s, _rast.If):
                    d["entries"] = [
                        [str(cond), _serialize_block(block)]
                        for cond, block in (getattr(s, "entries", None) or [])
                    ]
                elif isinstance(s, _rast.Menu):
                    d["items"] = [
                        [text, str(cond) if cond else None, _serialize_block(block) if block else None]
                        for text, cond, block in (getattr(s, "items", None) or [])
                    ]
                elif t in ("Python", "EarlyPython"):
                    d["code"] = getattr(getattr(s, "code", None), "source", None)
                ## As chaves universais são definidas por último para que vars(s) não as sobrescreva.
                d["type"] = t
                d["name"] = _name
                d["linenumber"] = getattr(s, "linenumber", None)
                d["next"] = _next_lbl
                ## UserStatement: acrescenta screen_jumps calculados para a navegação.
                if t == "UserStatement":
                    _us_text = (getattr(s, "line", None) or "").strip()
                    _screen_jumps = []
                    import re as _re_us
                    _sm = _re_us.match(r'^call\s+screen\s+(\w+)', _us_text)
                    if _sm:
                        _sname = _sm.group(1)
                        try:
                            import renpy.display.screen as _rscr
                            _sobj = _rscr.screens.get((_sname, None)) or _rscr.screens.get((_sname,))
                            if _sobj and hasattr(_sobj, "ast"):
                                def _walk_sl_jumps(node):
                                    if node is None:
                                        return
                                    for _kv in (getattr(node, "keyword", None) or []):
                                        if len(_kv) >= 2 and "action" in str(_kv[0]).lower():
                                            _extract_sl_jump(_kv[1])
                                    for _v2 in (getattr(node, "positional", None) or []):
                                        _extract_sl_jump(_v2)
                                    for _an in ("children", "block", "body"):
                                        for _child in (getattr(node, _an, None) or []):
                                            _walk_sl_jumps(_child)
                                    for _entry in (getattr(node, "entries", None) or []):
                                        _eblock = _entry[1] if isinstance(_entry, (list, tuple)) and len(_entry) > 1 else getattr(_entry, "block", None)
                                        for _child in (_eblock or []):
                                            _walk_sl_jumps(_child)
                                def _extract_sl_jump(action):
                                    if hasattr(action, "target") and isinstance(getattr(action, "target", None), str):
                                        _screen_jumps.append(action.target)
                                        return
                                    if isinstance(action, (list, tuple)):
                                        for _a2 in action:
                                            _extract_sl_jump(_a2)
                                        return
                                    try:
                                        _s2 = str(action)
                                        for _m in _re_us.finditer(r'Jump\(["\'](\w+)["\']\)', _s2):
                                            _screen_jumps.append(_m.group(1))
                                    except Exception:
                                        pass
                                _walk_sl_jumps(_sobj.ast)
                        except Exception as _se:
                            _tl_log("TL cfg: screen jump extract failed for '{}': {}".format(_sname, _se))
                    d["screen_jumps"] = _screen_jumps if _screen_jumps else None
                out.append(d)
            return out

        def _find_next_label(node):
            cur = getattr(node, "next", None)
            while cur is not None:
                if isinstance(cur, _rast.Label):
                    return cur.name
                cur = getattr(cur, "next", None)
            return None

        def _stmt_next_boundary(s):
            nxt = getattr(s, "next", None)
            if nxt is None:
                return None
            if isinstance(nxt, _rast.Label):
                return nxt.name          # texto → ponto de entrada do label
            _nxt_name = getattr(nxt, "name", None)
            if _nxt_name is not None:
                return list(_nxt_name)   # lista → ID do nó de instrução [arquivo, serial, linha]
            return None                  # sem nome → trata como sequência dentro do bloco

        result = {}

        for lname in labels:
            lnode = _namemap.get(lname)
            if lnode is None:
                _tl_log("TL cfg dump: label '{}' not found in namemap".format(lname))
                continue
            if isinstance(lnode, _rast.Label):
                block = list(getattr(lnode, "block", None) or [])
                if not block:
                    nxt = getattr(lnode, "next", None)
                    if nxt is not None and not isinstance(nxt, _rast.Label):
                        block = [nxt]
            else:
                block = [lnode]
            result[lname] = {
                "file": getattr(lnode, "filename", None),
                "line": getattr(lnode, "linenumber", None),
                "next_label": _find_next_label(lnode),
                "block": _serialize_block(block),
            }
            _tl_log("TL cfg dump: '{}' -> {} stmts".format(lname, len(block)))

        try:
            _outdir = os.path.dirname(outfile)
            if not os.path.exists(_outdir):
                os.makedirs(_outdir)
            with open(outfile, "w") as _f:
                _tl_json.dump(result, _f, indent=2)
            _tl_log("TL cfg dump: written to {}".format(outfile))
        except Exception as _e:
            _tl_log("TL cfg dump error: {}".format(_e))
            renpy.notify("Falha ao exportar a CFG — consulte debug.txt")
            return

        _tl_log("TL cfg dump: {} labels written to {}".format(len(result), outfile))
        renpy.notify("CFG exportada: {} rótulos".format(len(result)))

## -----------------------------------------------------------------------------
## Seção 2: backend/tl_ast_utils.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_ast_utils.rpy
## Funções auxiliares de AST compartilhadas por vários arquivos do backend.
## Carregado antes dos demais arquivos tl_*.rpy do backend (ordenação alfabética em init -2).
## =============================================================================

init -2 python:

    import ast as _tl_pyast_util
    import re as _tl_re_util
    _tl_pyast_Constant_util = getattr(_tl_pyast_util, "Constant", None)

    def _tl_strip_renpy_tags(s):
        """Strip {tag} markup from s, leaving inner text."""
        return _tl_re_util.sub(r'\{[^}]*\}', '', s)

    def _tl_ast_literal_value(node):
        """
        Return the string value of an AST literal node (Python 2/3 compat).
        Handles Constant (Py 3.8+), Str, Num (Py 2/3), and True/False Names.
        Returns None if the node is not a recognized literal.
        """
        if _tl_pyast_Constant_util and isinstance(node, _tl_pyast_Constant_util):
            return str(node.value)
        if isinstance(node, _tl_pyast_util.Str):
            return str(node.s)
        if isinstance(node, _tl_pyast_util.Num):
            return str(node.n)
        if isinstance(node, _tl_pyast_util.Name) and node.id in ("True", "False"):
            return node.id
        return None

    def _tl_extract_compare_literals(cond_str):
        """
        Parse cond_str and return all comparator literal values (as strings)
        from Compare nodes. Works across all comparison operators (==, !=, >, <, etc.).
        Returns [] on parse error or if the string has no Compare nodes.
        """
        if not cond_str or cond_str in ("True", "False", "None", "else"):
            return []
        try:
            tree = _tl_pyast_util.parse(cond_str, mode="eval")
        except SyntaxError:
            return []
        results = []
        for compare_node in _tl_pyast_util.walk(tree):
            if not isinstance(compare_node, _tl_pyast_util.Compare):
                continue
            for comparator in compare_node.comparators:
                val = _tl_ast_literal_value(comparator)
                if val is not None:
                    results.append(val)
        return results

    def _tl_is_game_file(f):
        """
        True if f is a game script path — not a RenPy internal and not this mod.
        RenPy stores filenames relative to game/; internals start with 'renpy/'.
        All mod files live under wells/timeline/ (legacy renpy-chronology-mod/ is also excluded).
        so the mod-dir check covers them too.
        Single canonical check: update here when the mod directory name changes.
        """
        return (
            bool(f)
            and not f.startswith("renpy/")
            and "wells/timeline" not in f
            and "renpy-chronology-mod" not in f
        )

    def _tl_walk_ast_blocks(nodes, visitor_fn, initial_state=None):
        """
        Walk all Label node blocks from game scripts, visiting every nested node.
        Recurses into If entries and Menu item blocks.
        Already-seen nodes (by identity) are skipped to prevent cycles.

        visitor_fn(node, state, current_label) -> new_state is called once per unique
        visited node. current_label is the name of the Label node whose block contains
        this node (propagates unchanged into If/Menu sub-blocks).
        State is threaded sequentially through each block; child blocks inherit the
        state at the point the branch is reached.
        initial_state defaults to None for stateless visitors (return state unchanged).
        """
        visited = set()
        work = []

        for label_node in nodes:
            if type(label_node).__name__ != "Label":
                continue
            if not _tl_is_game_file(getattr(label_node, "filename", "")):
                continue
            label_block = getattr(label_node, "block", None)
            if label_block:
                work.append((list(label_block) if not isinstance(label_block, list) else label_block, initial_state, label_node.name))

        while work:
            block, state, cur_label = work.pop()
            for node in (block or []):
                node_id = _tl_builtin_id(node)
                if node_id in visited:
                    continue
                visited.add(node_id)
                state = visitor_fn(node, state, cur_label)

                node_type = type(node).__name__
                if node_type == "If":
                    for _, item_block in (getattr(node, "entries", None) or []):
                        if item_block:
                            work.append((item_block, state, cur_label))
                elif node_type == "Menu":
                    for item in (getattr(node, "items", None) or []):
                        item_block = item[2] if isinstance(item, (list, tuple)) and len(item) > 2 else None
                        if item_block:
                            work.append((item_block, state, cur_label))

    def _tl_prettify_var(name):
        """Convert a snake_case variable name to a readable label."""
        _STRIP_PREFIXES = ("mc_", "flag_", "is_", "has_", "wf_", "ch_")
        s = name
        for pfx in _STRIP_PREFIXES:
            if s.startswith(pfx):
                s = s[len(pfx):]
                break
        parts = s.split("_")
        return " ".join(p.capitalize() for p in parts if p)

