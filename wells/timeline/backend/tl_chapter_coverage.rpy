## =============================================================================
## WELLS TIMELINE — tl_coverage.rpy
## Índice de cobertura de conteúdo já visto.
## As seções consolidadas mantêm a ordem de carregamento anterior.
## =============================================================================

## -----------------------------------------------------------------------------
## Seção 1: backend/tl_coverage.rpy
## -----------------------------------------------------------------------------

## =============================================================================
## WELLS TIMELINE — tl_coverage.rpy
## Índice de cobertura: reúne descritores de conteúdo visto para todos os ramos If da AST.
## =============================================================================

init -2 python:

    def _tl_build_coverage_index(nodes):
        """
        Walk all Label blocks from game scripts and build:
            persistent._tl_all_branch_descs — picklable seen-descriptor tuple per
                if-branch block (all entries including else). Used at render time to
                count globally locked branches via _tl_eval_seen_fn.
        ("never",) descriptors are excluded — unresolvable branches would always
        count as locked and inflate the number permanently.
        """

        if_nodes = []

        def visitor(node, state, _label=None):
            if type(node).__name__ == "If":
                if_nodes.append(node)
            return state

        _tl_walk_ast_blocks(nodes, visitor)

        branch_descs = []
        for node in if_nodes:
            for cond_str, block in (getattr(node, "entries", None) or []):
                if not block:
                    continue
                desc = _tl_make_seen_fn(block)
                if desc[0] != "never":
                    branch_descs.append(desc)

        persistent._tl_all_branch_descs = branch_descs
        _tl_log("Timeline: índice de cobertura: {} descrições de ramificações".format(len(branch_descs)))

