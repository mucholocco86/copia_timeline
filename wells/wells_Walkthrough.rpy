# ========================================================================
# WELLS FRAMEWORK — WALKTHROUGH CORE (WF) — V8 WF — projeção estrutural seletiva
#
# Base desta versão:
# - arquitetura confirmada do manifesto Wells/URM;
# - ChoicesClass / URMChoice do consolidado do URM;
# - CodeView.nodesToCode do consolidado;
# - PathDetectionClass / Path do consolidado;
# - o Ren'Py continua sendo o executor da Choice.
#
# O Wells apenas observa Menu.items, analisa o AST e fornece dados para
# a camada visual wells_wt_screen.rpy. Não cria rollback paralelo, não substitui
# a Action nativa e não desenha notificações por conta própria.
# ========================================================================

init -998 python:

    # --------------------------------------------------------------------
    # Infraestrutura mínima equivalente ao x52NonPicklable do URM.
    # Evita que os objetos auxiliares do Walkthrough entrem no estado
    # serializado/rollback do jogo.
    # --------------------------------------------------------------------
    class WFNonPicklable(python_object):
        def __setstate__(self, d):
            pass

        def __getstate__(self):
            return {}

        def __getnewargs__(self):
            return ()

        def __iter__(self):
            return None

        def itervalues(self):
            return None


    # --------------------------------------------------------------------
    # CODE VIEW
    # AST -> representação humana.
    # Não executa código e não altera o jogo.
    # --------------------------------------------------------------------
    class WFCodeViewClass(WFNonPicklable):

        def stripRenpyCode(self, code):
            """
            Remove chamadas Python de infraestrutura que normalmente não
            descrevem consequência de escolha. Mantém explicitamente
            renpy.jump e renpy.call.

            Esta etapa segue o princípio confirmado no CodeView do URM:
            primeiro projetar apenas nós estruturais; depois retirar ruído
            Ren'Py/UI ainda presente dentro de blocos Python.
            """
            if not code:
                return ''

            try:
                patterns = (
                    r'^.*\brenpy\.(?!jump|call).+\n?',
                    r'^.*\bui\..+\n?',
                )

                for pattern in patterns:
                    code = renpy.re.sub(pattern, '', code, flags=renpy.re.MULTILINE)
            except Exception as e:
                print('WF: CodeView: falha ao limpar código RenPy/UI: {}'.format(e))

            return code

        def _wf_user_statement_code(self, node):
            """
            UserStatement é uma categoria ampla no Ren'Py e pode conter voice,
            play, stop, pause e muitos outros comandos. O Walkthrough não deve
            transformar todos eles em consequência.

            Mantemos somente os statements estruturais que o CodeView do URM
            também trata de forma explícita: call screen, show screen e
            hide screen.
            """
            try:
                parsed = getattr(node, 'parsed', None)
                if parsed:
                    head = parsed[0]
                    if head in (('call', 'screen'), ('show', 'screen'), ('hide', 'screen')):
                        if hasattr(node, 'get_code') and callable(node.get_code):
                            return node.get_code()

                # Fallback para versões/jogos em que parsed não tenha o mesmo
                # formato, sem abrir a porta para qualquer UserStatement.
                if hasattr(node, 'get_code') and callable(node.get_code):
                    code = node.get_code()
                    if code:
                        normalized = ' '.join(str(code).strip().lower().split())
                        if normalized.startswith('call screen '):
                            return code
                        if normalized.startswith('show screen '):
                            return code
                        if normalized.startswith('hide screen '):
                            return code
            except Exception:
                pass

            return None

        def nodesToCode(self, nodes, indentCount=0):
            """
            Projeção seletiva AST -> texto de Walkthrough.

            O bloco AST completo continua sendo lido, mas somente tipos com
            valor estrutural/informativo são convertidos para apresentação.
            Isso evita que voice/play/pause e outros nós audiovisuais entrem
            no guia apenas por existirem dentro da Choice.
            """
            output = ''

            def createLine(line):
                return '{}{}\n'.format('    ' * indentCount, line)

            if not hasattr(nodes, '__iter__'):
                return output

            for node in nodes:
                try:
                    if isinstance(node, renpy.ast.Python) and hasattr(node, 'code') and hasattr(node.code, 'source'):
                        source = node.code.source
                        if source:
                            output += createLine(source)

                    elif isinstance(node, renpy.ast.If):
                        entries = getattr(node, 'entries', None) or []
                        for i, entry in enumerate(entries):
                            if not entry or len(entry) < 2:
                                continue

                            condition = entry[0]
                            conditionNodes = entry[1]

                            if i == 0:
                                output += createLine('if {}:'.format(condition))
                            elif condition == 'True':
                                output += createLine('else:')
                            else:
                                output += createLine('elif {}:'.format(condition))

                            nested = self.nodesToCode(conditionNodes, indentCount + 1)
                            if nested:
                                output += nested
                                if not nested.endswith('\n'):
                                    output += '\n'

                    elif isinstance(node, renpy.ast.Jump):
                        target = getattr(node, 'target', None)
                        if target:
                            output += createLine('jump {}'.format(target))
                        # Diferença deliberada do URM: Wells continua lendo o
                        # bloco inteiro para não perder informação estrutural
                        # posterior já validada nos nossos testes.

                    elif isinstance(node, renpy.ast.Call):
                        label = getattr(node, 'label', None)
                        if label:
                            arguments = getattr(node, 'arguments', None)
                            if arguments:
                                if hasattr(arguments, 'get_code'):
                                    try:
                                        output += createLine('call {} {}'.format(label, arguments.get_code()))
                                    except Exception:
                                        output += createLine('call {} # arguments unavailable'.format(label))
                                else:
                                    output += createLine('call {} # arguments unavailable'.format(label))
                            else:
                                output += createLine('call {}'.format(label))

                    elif isinstance(node, renpy.ast.UserStatement):
                        code = self._wf_user_statement_code(node)
                        if code:
                            output += createLine(code)

                    elif isinstance(node, renpy.ast.Translate):
                        # O CodeView do URM resume conteúdo narrativo em vez de
                        # despejar diálogo/voice dentro da consequência.
                        if not output.endswith('# Some dialogue\n'):
                            output += createLine('# Some dialogue')

                except Exception as e:
                    print('WF: CodeView: falha ao projetar no AST: {}'.format(e))

            # Segunda barreira: blocos Python ainda podem conter chamadas
            # renpy/ui que não interessam ao Walkthrough.
            output = self.stripRenpyCode(output)
            output = output.rstrip()

            # Diálogo sozinho não constitui consequência útil.
            if output == '# Some dialogue':
                return ''

            return output


    wf_code_view = WFCodeViewClass()


    # --------------------------------------------------------------------
    # FILTRO DE APRESENTAÇÃO WF
    #
    # O leitor continua enxergando o bloco AST inteiro. Este filtro atua
    # SOMENTE no texto que será mostrado ao jogador. A regra é conservadora:
    # remove apenas instruções audiovisuais/temporais conhecidas, preservando
    # estado, flags, condições, jump, call e qualquer coisa desconhecida.
    # --------------------------------------------------------------------
    class WFWalkthroughDisplayFilter(WFNonPicklable):

        _wf_ignored_exact = (
            'hide screen ',
            'show screen',
            'pause',
            '# some dialogue',
        )

        _wf_ignored_prefixes = (
            'hide screen ',
            'show screen',
            'renpy.show_screen(',
            '$ renpy.show_screen(',
            'renpy.hide_screen(',
            '$ renpy.hide_screen(',
            'pause ',
            'renpy.pause(',
            '$ renpy.pause(',
            'play music ',
            'stop music',
            'queue music ',
            'play sound ',
            'stop sound',
            'queue sound ',
            'play audio ',
            'stop audio',
            'queue audio ',
            'play voice ',
            'stop voice',
            'queue voice ',
            'renpy.music.play(',
            'renpy.music.queue(',
            'renpy.music.stop(',
            'renpy.sound.play(',
            'renpy.sound.queue(',
            'renpy.sound.stop(',
            '$ renpy.music.play(',
            '$ renpy.music.queue(',
            '$ renpy.music.stop(',
            '$ renpy.sound.play(',
            '$ renpy.sound.queue(',
            '$ renpy.sound.stop(',
        )

        def _wf_is_ignored_line(self, stripped_line):
            lowered = stripped_line.strip().lower()
            if not lowered:
                return False

            if lowered in self._wf_ignored_exact:
                return True

            for prefix in self._wf_ignored_prefixes:
                if lowered.startswith(prefix):
                    return True

            return False

        def filtrar(self, code):
            if not code:
                return ''

            kept = []
            for line in str(code).splitlines():
                if self._wf_is_ignored_line(line):
                    continue
                kept.append(line)

            # Remove apenas linhas vazias excedentes nas pontas.
            return '\n'.join(kept).strip()


    wf_walkthrough_display_filter = WFWalkthroughDisplayFilter()


    # --------------------------------------------------------------------
    # CHOICES
    # Adaptação praticamente direta de ChoicesClass / URMChoice.
    # --------------------------------------------------------------------
    class WFChoicesClass(WFNonPicklable):

        @property
        def isDisplayingChoice(self):
            try:
                current = renpy.game.context().current
                script = renpy.game.script.lookup(current)
                return isinstance(script, renpy.ast.Menu)
            except Exception:
                return False

        @property
        def currentChoices(self):
            try:
                current = renpy.game.context().current
                script = renpy.game.script.lookup(current)

                if isinstance(script, renpy.ast.Menu):
                    choices = []
                    for i, item in enumerate(script.items):
                        if len(item) >= 3 and item[2]:
                            choices.append(WFChoice(i, item))
                    return choices
            except Exception as e:
                print('WF: Choices: falha ao ler Menu.items: {}'.format(e))

            return []

        @property
        def hiddenCount(self):
            count = 0
            for choice in self.currentChoices or []:
                if not choice.isVisible:
                    count += 1
            return count


    class WFChoice(WFNonPicklable):
        """
        Menu.items:
            0 -> texto original
            1 -> condição
            2 -> bloco AST completo da Choice
        """

        def __init__(self, index, choiceTuple):
            self._wf_index = index
            self._wf_choice = choiceTuple
            self._wf_code = None
            self._wf_jumpTo = None

        @property
        def index(self):
            return self._wf_index

        @property
        def rawText(self):
            try:
                return self._wf_choice[0]
            except Exception:
                return ''

        @property
        def text(self):
            """Texto de apresentação, substituído como no URM."""
            try:
                return renpy.exports.substitute(self.rawText)
            except Exception:
                return self.rawText

        @property
        def condition(self):
            try:
                return self._wf_choice[1]
            except Exception:
                return 'True'

        @property
        def block(self):
            try:
                return self._wf_choice[2]
            except Exception:
                return []

        @property
        def isVisible(self):
            try:
                return bool(eval(self.condition, renpy.store.__dict__))
            except Exception:
                return False

        @property
        def code(self):
            if self._wf_code is None:
                try:
                    self._wf_code = wf_code_view.nodesToCode(self.block)
                except Exception as e:
                    print('WF: Choices: falha ao gerar código da Choice: {}'.format(e))
                    self._wf_code = ''
            return self._wf_code

        @property
        def jumpTo(self):
            # Mantém a semântica confirmada do URM: resumo auxiliar apenas.
            if self._wf_jumpTo is None:
                self._wf_jumpTo = ''
                try:
                    for content in self.block:
                        if isinstance(content, renpy.ast.Jump):
                            self._wf_jumpTo = content.target
                            break
                except Exception:
                    pass
            return self._wf_jumpTo

        @property
        def guide(self):
            """
            Texto entregue ao wells_choices.
            Prioridade: projeção integral do bloco AST; jumpTo é apenas fallback.
            """
            if self.code:
                wf_visible_code = wf_walkthrough_display_filter.filtrar(self.code)
                if wf_visible_code:
                    return wf_visible_code
            if self.jumpTo:
                return 'jump {}'.format(self.jumpTo)
            return 'No consequences'


    wf_choices_core = WFChoicesClass()


    # --------------------------------------------------------------------
    # PATH DETECTION
    # Adaptação do mecanismo do URM para observação de caminhos futuros.
    # Não força caminhos e não altera context.next_node.
    # --------------------------------------------------------------------
    class WFPathDetectionClass(WFNonPicklable):
        lookAheadLimit = 20

        def nodeIsBlocking(self, node):
            try:
                if hasattr(node, 'interact') and node.interact:
                    return True
                elif isinstance(node, renpy.ast.UserStatement) and hasattr(node, 'get_code') and callable(node.get_code):
                    return node.get_code() == 'pause'
            except Exception:
                pass
            return False

        def nextNode(self, node):
            try:
                if isinstance(node, renpy.ast.Call):
                    if hasattr(node, 'label') and node.label:
                        return renpy.game.script.lookup(node.label)

                elif isinstance(node, renpy.ast.Jump):
                    if hasattr(node, 'predict') and callable(node.predict):
                        predict = node.predict()
                        if predict and isinstance(predict[0], renpy.ast.Node):
                            return predict[0]

                elif hasattr(node, 'next'):
                    return node.next
            except Exception:
                pass
            return None

        @property
        def nextIfStatement(self):
            try:
                current = renpy.game.script.lookup(renpy.game.context().current)
                forceableNode = True

                if not self.nodeIsBlocking(current):
                    return None

                next_node = self.nextNode(current)
                for _ in range(self.lookAheadLimit):
                    if not next_node:
                        break

                    if isinstance(next_node, renpy.ast.If):
                        return (next_node, forceableNode)

                    elif self.nodeIsBlocking(next_node):
                        break

                    elif isinstance(next_node, renpy.ast.Jump) or isinstance(next_node, renpy.ast.Call):
                        forceableNode = False

                    next_node = self.nextNode(next_node)

            except Exception:
                pass

            return None

        @property
        def pathIsNext(self):
            return bool(self.nextIfStatement)

        @property
        def statements(self):
            try:
                ifStatement = self.nextIfStatement
                if ifStatement:
                    statements = []
                    for i, item in enumerate(ifStatement[0].entries):
                        if len(item) >= 2:
                            statements.append(WFPath(i, item, ifStatement[1]))
                    return statements
            except Exception:
                pass
            return []

        @property
        def selectedIndex(self):
            for i, statement in enumerate(self.statements or []):
                if statement.isSelected:
                    return i
            return None

        @property
        def statementsCount(self):
            try:
                return len(self.statements or [])
            except Exception:
                return 0

        @property
        def selectedCondition(self):
            """Condição estrutural da ramificação que o Ren'Py selecionaria agora."""
            try:
                for statement in self.statements or []:
                    if statement.isSelected:
                        condition = str(statement.condition).strip()
                        if condition:
                            return condition
            except Exception:
                pass
            return None




    class WFPath(WFNonPicklable):
        def __init__(self, index, data, forceable=False):
            self._wf_index = index
            self._wf_condition = data[0]
            self._wf_nodes = data[1]
            self._wf_forceable = forceable
            self._wf_code = None
            self._wf_jumpTo = None

        @property
        def forceable(self):
            return self._wf_forceable

        @property
        def isSelected(self):
            try:
                return bool(eval(self._wf_condition, renpy.store.__dict__))
            except Exception:
                return False

        @property
        def condition(self):
            return self._wf_condition

        @property
        def code(self):
            if self._wf_code is None:
                try:
                    self._wf_code = wf_code_view.nodesToCode(self._wf_nodes)
                except Exception as e:
                    print('WF: PathDetection: falha ao gerar código do path: {}'.format(e))
                    self._wf_code = ''
            return self._wf_code

        @property
        def jumpTo(self):
            if self._wf_jumpTo is None:
                self._wf_jumpTo = ''
                try:
                    for content in self._wf_nodes:
                        if isinstance(content, renpy.ast.Jump):
                            self._wf_jumpTo = content.target
                            break
                except Exception:
                    pass
            return self._wf_jumpTo


    wf_path_detection = WFPathDetectionClass()


    # --------------------------------------------------------------------
    # PREVIOUS CHOICE PATH TRACKER
    #
    # Mantém o Path Detection independente da UI de Choices. Enquanto o
    # Ren'Py está em um Menu, guarda apenas a estrutura daquele Menu. No
    # primeiro ponto interativo depois da escolha, compara o nó atual com
    # os blocos AST das opções e aceita o resultado SOMENTE quando um único
    # ramo puder ser relacionado ao fluxo realmente percorrido.
    #
    # Não intercepta Action, não altera Menu.items e não executa código.
    # --------------------------------------------------------------------
    class WFPreviousChoicePathTracker(WFNonPicklable):
        reachLimit = 80

        def __init__(self):
            self._wf_menu_token = None
            self._wf_pending_choices = []
            self._wf_result = None
            self._wf_result_token = None

        def _current(self):
            try:
                context = renpy.game.context()
                token = getattr(context, 'current', None)
                node = renpy.game.script.lookup(token)
                return token, node
            except Exception:
                return None, None

        def _snapshot_menu(self, token):
            token_text = str(token)
            if self._wf_menu_token == token_text and self._wf_pending_choices:
                return

            try:
                self._wf_pending_choices = list(wf_choices_core.currentChoices or [])
            except Exception:
                self._wf_pending_choices = []

            self._wf_menu_token = token_text
            self._wf_result = None
            self._wf_result_token = None

        def _children(self, node):
            result = []
            try:
                if isinstance(node, renpy.ast.If):
                    for entry in getattr(node, 'entries', None) or []:
                        if entry and len(entry) >= 2 and entry[1]:
                            result.append(entry[1][0])

                if isinstance(node, renpy.ast.Call):
                    label = getattr(node, 'label', None)
                    if label:
                        try:
                            result.append(renpy.game.script.lookup(label))
                        except Exception:
                            pass

                elif isinstance(node, renpy.ast.Jump):
                    try:
                        predict = node.predict() if hasattr(node, 'predict') else None
                        if predict:
                            result.append(predict[0])
                    except Exception:
                        pass

                nxt = getattr(node, 'next', None)
                if nxt is not None:
                    result.append(nxt)
            except Exception:
                pass
            return [item for item in result if item is not None]

        def _choice_reaches(self, choice, target):
            try:
                block = choice.block or []
                if not block or target is None:
                    return False

                queue = list(block[:1])
                seen = set()
                steps = 0

                while queue and steps < self.reachLimit:
                    node = queue.pop(0)
                    steps += 1
                    if node is target:
                        return True

                    marker = id(node)
                    if marker in seen:
                        continue
                    seen.add(marker)

                    for child in self._children(node):
                        if id(child) not in seen:
                            queue.append(child)
            except Exception:
                pass
            return False

        def _build_result(self, choice, token):
            guide = ''
            try:
                guide = wf_walkthrough_display_filter.filtrar(choice.code) or ''
            except Exception:
                guide = ''

            if not guide:
                try:
                    if choice.jumpTo:
                        guide = 'jump {}'.format(choice.jumpTo)
                except Exception:
                    pass

            # Path só existe quando há alguma consequência estrutural útil.
            if not guide:
                return None

            return {
                'choice_text': choice.text or choice.rawText or '',
                'guide': guide,
                'token': str(token),
            }

        def observe(self):
            token, node = self._current()
            if node is None:
                return

            # Enquanto a Choice existe, apenas guardamos a estrutura dela.
            if isinstance(node, renpy.ast.Menu):
                self._snapshot_menu(token)
                return

            token_text = str(token)

            # O resultado pertence exclusivamente ao ponto interativo em que
            # foi reconhecido. Mudou o nó atual -> informação expirada.
            if self._wf_result is not None:
                if token_text != self._wf_result_token:
                    self._wf_result = None
                    self._wf_result_token = None
                    self._wf_pending_choices = []
                    self._wf_menu_token = None
                return

            if not self._wf_pending_choices:
                return

            matches = []
            for choice in self._wf_pending_choices:
                if self._choice_reaches(choice, node):
                    matches.append(choice)

            # Causalidade conservadora: se mais de uma opção alcança o mesmo
            # nó (ramos já convergiram), o Wells não inventa qual foi escolhida.
            if len(matches) == 1:
                result = self._build_result(matches[0], token)
                if result:
                    self._wf_result = result
                    self._wf_result_token = token_text

            # Este snapshot vale somente para o primeiro ponto após a Choice.
            self._wf_pending_choices = []
            self._wf_menu_token = None

        @property
        def result(self):
            self.observe()
            return self._wf_result


    wf_previous_choice_path = WFPreviousChoicePathTracker()


    # --------------------------------------------------------------------
    # FACHADA WELLS — namespace WF
    # Faz somente a ponte Choices -> screen choice existente.
    # --------------------------------------------------------------------
    class WFWalkthrough(WFNonPicklable):

        @staticmethod
        def _screen_caption(item):
            try:
                if hasattr(item, 'caption'):
                    return item.caption
                return item[0]
            except Exception:
                return ''

        @staticmethod
        def _norm(value):
            try:
                return str(value).strip()
            except Exception:
                return ''

        @classmethod
        def processar_menu_atual(cls, items_da_screen=None):
            """
            Retorna um mapa índice-visual -> WFChoice.

            Menu.items preserva também Choices estruturalmente invisíveis,
            enquanto screen choice normalmente recebe as visíveis. Por isso a
            correspondência é feita pelo texto apresentado, e depois por ordem
            apenas como fallback.
            """
            choices = wf_choices_core.currentChoices or []
            if not choices:
                return None

            if items_da_screen is None:
                return dict((i, c) for i, c in enumerate(choices))

            mapa = {}
            usados = set()

            try:
                for visual_index, screen_item in enumerate(items_da_screen):
                    caption = cls._norm(cls._screen_caption(screen_item))
                    encontrada = None

                    # 1) Casamento mais seguro: texto de apresentação igual.
                    for pos, choice in enumerate(choices):
                        if pos in usados:
                            continue
                        if cls._norm(choice.text) == caption:
                            encontrada = choice
                            usados.add(pos)
                            break

                    # 2) Se a tela aplicou uma transformação que alterou texto,
                    # tentamos casar pelo texto original.
                    if encontrada is None:
                        for pos, choice in enumerate(choices):
                            if pos in usados:
                                continue
                        
                            if cls._norm(choice.rawText) == caption:
                                encontrada = choice
                                usados.add(pos)
                                break

                    # 3) Fallback somente entre Choices atualmente visíveis.
                    if encontrada is None:
                        for pos, choice in enumerate(choices):
                            if pos not in usados and choice.isVisible:
                                encontrada = choice
                                usados.add(pos)
                                break

                    if encontrada is not None:
                        mapa[visual_index] = encontrada

            except Exception as e:
                print('WF: falha ao relacionar screen choice com Menu.items: {}'.format(e))

            return mapa or None

        @staticmethod
        def escolhas_atuais():
            """Retorna todas as Choices estruturais do Menu atual."""
            try:
                return wf_choices_core.currentChoices or []
            except Exception as e:
                print('WF: falha ao obter Choices atuais: {}'.format(e))
                return []

        @staticmethod
        def escolhas_visiveis():
            """Retorna somente as Choices que o jogo permitiria exibir agora."""
            resultado = []
            try:
                for choice in wf_choices_core.currentChoices or []:
                    if choice.isVisible:
                        resultado.append(choice)
            except Exception as e:
                print('WF: falha ao obter Choices visíveis: {}'.format(e))
            return resultado

        @staticmethod
        def esta_em_choice():
            """Indica se o contexto atual do Ren'Py está em um Menu/Choice."""
            try:
                esta = bool(wf_choices_core.isDisplayingChoice)
                if esta:
                    wf_previous_choice_path.observe()
                return esta
            except Exception:
                return False

        @staticmethod
        def path_condition():
            """
            Path Detection no mesmo ponto estrutural usado pelo URM:
            a partir do nó interativo atual, procura o próximo renpy.ast.If
            dentro do limite de look-ahead e retorna a condição do ramo que
            o próprio estado atual do jogo seleciona.
            """
            try:
                return wf_path_detection.selectedCondition
            except Exception as e:
                print('WF: PathDetection: falha ao obter condição: {}'.format(e))
            return None

        @staticmethod
        def path_details():
            """Retorna os ramos do próximo If e sua projeção estrutural."""
            resultado = []
            try:
                for statement in wf_path_detection.statements or []:
                    guide = ''
                    try:
                        guide = wf_walkthrough_display_filter.filtrar(statement.code) or ''
                    except Exception:
                        guide = ''

                    if not guide:
                        try:
                            if statement.jumpTo:
                                guide = 'jump {}'.format(statement.jumpTo)
                        except Exception:
                            pass

                    resultado.append({
                        'condition': str(statement.condition).strip(),
                        'selected': bool(statement.isSelected),
                        'guide': guide,
                    })
            except Exception as e:
                print('WF: PathDetection: falha ao obter detalhes: {}'.format(e))
            return resultado

        @staticmethod
        def path_token():
            """
            Identifica o ponto atual do fluxo. A UI usa isto apenas para
            fechar o painel quando diálogo/cena/choice/rollback mudar.
            """
            try:
                wf_previous_choice_path.observe()
                context = renpy.game.context()
                current = getattr(context, 'current', None)
                return str(current)
            except Exception:
                return ''

