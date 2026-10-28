# 01 — Loader x52MF2: carregamento, dependências e atualização

**Status:** 🟢 comportamento diretamente confirmado no material URM convertido/original disponível no laboratório; 🔵 interfaces Ren'Py relacionadas devem ser lidas no SDK 7.4.11.  
**Fonte primária:** `URM_REVERSO/01_MATERIAL_URM/1_URM_ORIGINAL/framework/bootstrap.rpy`.  
**Conferência:** a cópia em `2_URM_X52_CONVERTIDO/framework/bootstrap.rpy` tem o mesmo SHA GitHub (`9d72267c2d86c68aa9dac1fee94652c891a611fe`) e o mesmo conteúdo analisado.

## 1. Visão geral

O loader do URM não é apenas um leitor de arquivos. O bootstrap contém quatro responsabilidades conectadas:

1. definir o catálogo de módulos e suas dependências;
2. resolver a ordem e eliminar arquivos repetidos;
3. carregar fontes com sufixos próprios (`.x52rpy`, `.x52` e a variante terminada em `t`) e inseri-las no script Ren'Py;
4. localizar o archive do mod e preparar/aplicar atualizações.

Fluxo geral:

```text
x52MF2.load(modules, modName, mfPath)
        |
        +--> validar versão mínima
        +--> garantir módulo "main"
        +--> localizar archivePath
        +--> expandir aliases/dependências
        +--> deduplicar arquivos
        +--> loadFile(fullFn, modName, mfPath)
                    |
                    +--> escolher .x52t ou fonte base
                    +--> read() + decode()
                    +--> substituir placeholders quando aplicável
                    +--> renpy.load_string()
```

## 2. Catálogo de módulos e expansão de dependências

O bootstrap declara um `OrderedDict` chamado `availableModules`. Ele contém aliases de módulos e listas de arquivos/dependências. Exemplos confirmados no material:

- `main` inclui `bootstrap.rpy` e `modules/01utils.x52rpy`;
- `theming` depende de `fonts` e inclui `modules/10theme.x52rpy`, `theme.rpy.x52`, `screens/buttons.rpy.x52` e `screens/messagebars.rpy.x52`;
- `dialogs` depende de `theming`;
- `api`, `inputs`, `screeninjector`, `screenreader` e `tooltips` têm suas próprias entradas.

O método `load()` garante que `main` esteja na lista recebida, adicionando-o se necessário. Em seguida, `addFilesToLoad(files)`:

1. verifica se cada entrada é uma chave de `availableModules`;
2. se for, expande recursivamente essa lista;
3. se for um arquivo concreto, acrescenta-o apenas se ainda não estiver em `filesToLoad`.

Há um detalhe importante de ordem: depois, o código percorre as chaves de `availableModules` na ordem declarada e expande as que aparecem na lista de módulos solicitados. Portanto, não se deve presumir que a ordem literal da lista passada pelo chamador será reproduzida diretamente. A ordem de declaração do catálogo participa da ordem final de carregamento.

## 3. Regra de seleção de `.x52rpy`, `.x52` e da variante `t`

A função usa:

```python
ext = renpy.os.path.splitext(fullFn)[1].lower()
```

Se `ext` for `.x52rpy` ou `.x52`, verifica:

```python
loadableSource = renpy.loadable(fullFn)
loadableTransformed = renpy.loadable(fullFn + 't')
```

O sufixo `t` é anexado ao nome inteiro:

| Fonte base | Candidato transformado |
|---|---|
| `theme.rpy.x52` | `theme.rpy.x52t` |
| `modules/01utils.x52rpy` | `modules/01utils.x52rpyt` |

Se os dois forem carregáveis, o loader dá prioridade ao transformado:

```python
modFile = (
    renpy.loader.load(fullFn + 't')
    if loadableTransformed
    else renpy.loader.load(fullFn)
)
```

Depois lê e decodifica o conteúdo:

```python
modFileContents = modFile.read().decode()
```

**Limite da evidência:** o bootstrap prova que o URM consome a variante `t` quando ela existe. Ele não prova, por si só, quem gera essa variante nem quais transformações foram aplicadas a ela. Isso precisa ser pesquisado separadamente no restante do material.

## 4. Substituição de placeholders

O código só entra no bloco de substituição quando `loadableSource` é verdadeiro. Nesse caso:

- se `modName` não for `None`, substitui `_x52ModName_` por `modName`;
- se `mfPath` for verdadeiro, substitui `_x52MFPath_` por `mfPath`.

Isso ocorre mesmo quando a fonte efetivamente escolhida para leitura foi a variante terminada em `t`, desde que a fonte base também seja carregável.

Consequência: **não** é correto simplificar a regra para “o loader sempre substitui placeholders no arquivo transformado”. Se apenas a variante `t` estiver carregável e a fonte base não estiver, esse bloco de substituição não é executado.

## 5. Inserção no script Ren'Py

Após a leitura e as substituições, o URM faz:

```python
modFileLoaded = (renpy.load_string(modFileContents, fullFn) != None)
if not modFileLoaded:
    raise Exception(renpy.get_parse_errors())
```

O mecanismo observado é, portanto:

```text
renpy.loader.load(path)
  → file.read()
  → decode()
  → substituições de texto condicionais
  → renpy.load_string(texto, fullFn)
  → verificação de erros de parsing
```

O loader não chama `exec()` para executar arbitrariamente o texto Python. Ele entrega texto-fonte à API de carregamento de script do Ren'Py.

## 6. Fallback: diferença entre `.x52` e `.x52rpy`

A condição de fallback é específica:

```python
elif ext == '.x52rpy':
    fullFn = fullFn[:-6] + 'rpyc'
    if not renpy.loadable(fullFn):
        raise Exception(...)
```

O código transforma, por exemplo:

```text
modules/01utils.x52rpy
        ↓
modules/01utils.rpyc
```

O corte remove os seis caracteres finais `x52rpy`, mantendo o ponto anterior; por isso a concatenação produz `.rpyc`.

Esse fallback **não** se aplica a `.rpy.x52`, porque nesse caso `ext == '.x52'`. Se não houver nem fonte base nem variante `t`, a ramificação final levanta erro de arquivo não encontrado.

Outro detalhe: na ramificação de fallback `.rpyc`, o código mostrado apenas verifica `renpy.loadable(rpycFn)` e retorna da função; não chama `renpy.load_string()` para esse arquivo. A execução normal do `.rpyc` fica a cargo do mecanismo de script do Ren'Py.

## 7. Resolução de `archivePath`

`findArchivePath(fullFn)` percorre `renpy.loader.archives`. Quando encontra o arquivo solicitado dentro de um archive:

1. combina `renpy.config.basedir`, `game` e o nome do archive;
2. converte o caminho para absoluto;
3. se o arquivo sem extensão não existir, mas existir o mesmo caminho acrescido de `.rpa`, usa o caminho `.rpa`;
4. retorna o caminho resolvido.

A chamada inicial procura `{mfPath}/bootstrap.rpyc`. Quando encontra um archive e o objeto de módulo correspondente já existe no store e é um `renpy.python.StoreModule`, grava `archivePath` nesse módulo.

Se o archive não for encontrado, o loader altera `renpy.game.script.digest` para um MD5 com conteúdo aleatório. Esse comportamento está no código, mas seu propósito operacional exato deve permanecer marcado como questão de investigação até ser correlacionado com outros pontos do runtime.

## 8. Ciclo de atualização

No caminho de atualização do módulo API, o URM:

1. baixa um ZIP para `archivePath + '.tmp'`;
2. percorre os membros do ZIP até encontrar o primeiro arquivo com nome terminado em `.rpa`;
3. grava esse membro como `archivePath + '.update'`;
4. tenta remover o arquivo `.tmp`;
5. limpa o estado de atualizações e chama o callback de sucesso.

No bootstrap, se o arquivo `archivePath + '.update'` existir quando o módulo é carregado, o URM registra uma função `pendingUpdate` no objeto de módulo. Quando `applyUpdate(archivePath)` é chamada, tenta mover `.update` para `archivePath`. Se a movimentação falhar, registra o erro e tenta remover o arquivo de atualização; se tiver sucesso, chama `renpy.reload_script()`.

O código confirma a cadeia técnica, mas não prova sozinho todos os gatilhos de UI/estado seguro que levam à chamada de `pendingUpdate`. Isso continua como questão aberta.

## 9. O que isso significa para um loader próprio com sufixo `.wf`

O padrão reutilizável em alto nível é:

```text
launcher.rpy
  → manifesto explícito de módulos
  → renpy.loadable()
  → renpy.loader.load()
  → read().decode()
  → renpy.load_string()
```

Mas um loader WF não deve copiar indiscriminadamente todo o bootstrap:

- a extensão final precisa ser tratada explicitamente; para `wells_screen.rpy.wf`, `splitext(...)[1]` retorna `.wf`;
- a lista de módulos e a ordem de dependências precisam ser declaradas e testadas;
- o fallback para `.rpyc` só deve existir se houver requisito e regra próprios;
- placeholders como `_x52ModName_` e `_x52MFPath_` são convenções do URM, não recursos automáticos do Ren'Py;
- `.x52t` é uma convenção do URM, não um sufixo reconhecido automaticamente pelo motor;
- o carregamento dinâmico via `renpy.load_string()` precisa ser validado no SDK e no projeto-alvo, inclusive em relação à fase `init`, ordem de parsing, reload e rollback.

A implementação WF deve ser criada e testada no laboratório do projeto separado; este documento apenas registra a engenharia do URM e não altera o SDK nem os projetos protegidos.

## 10. Questões de continuação

- Encontrar se há produtor explícito de `.x52t` / `.x52rpyt` no material disponível.
- Correlacionar `availableModules` e as listas reais de arquivos com a árvore completa do URM.
- Determinar os pontos que acionam `pendingUpdate` e em que momento do ciclo do jogo isso acontece.
- Investigar o significado do ajuste aleatório de `renpy.game.script.digest` quando `findArchivePath()` não encontra archive.
- Só depois, definir uma especificação de loader WF sem copiar convenções não necessárias do URM.
