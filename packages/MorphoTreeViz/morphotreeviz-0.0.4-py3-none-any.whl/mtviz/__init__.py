"""mtviz: API pública do MorphoTreeViz

Uso:
    import mtviz as viz
    pt = viz.PrintTree(...)
    b  = viz.makePlotTree(...)
"""

# Console (pretty-print no terminal)
from .console import PrintTree  # classe (chamável)

# Árvore interativa em Bokeh
from .tree import makePlotTree, makePlotTreeWithSelectedNodes               # função que retorna um VizBundle com o painel
from .image import makePlotImage, makePlotImagePixels
from .levelsets import makeLevelSets
from .bundle import VizBundle                 # contêiner de retorno padronizado
from .helpers import (
    printTree,
    showComponentTree,
    showComponentTrees,
    showNode,
    showImage,
    showLevelSets,
    showComponentTreesWithSelectedNodes,
    getPlotTree
)


__all__ = [
    "PrintTree",
    "VizBundle",
    "makePlotTree",
    "makePlotTreeWithSelectedNodes",
    "makePlotImage",
    "makePlotImagePixels",
    "makeLevelSets",
    # Helpers (alto nível)
    "printTree",
    "showComponentTree",
    "showComponentTrees",
    "showNode",
    "showImage",
    "showLevelSets",
    "showComponentTreesWithSelectedNodes",
]


def show(obj, *args, **kwargs):
    """Atalho para exibir vizualizações do mtviz.

    Aceita tanto um VizBundle quanto um objeto Bokeh nativo. Para VizBundle,
    repassa o atributo ``panel`` ao ``bokeh.io.show``.
    """
    from bokeh.io import show as _bokeh_show
    if isinstance(obj, VizBundle):
        return _bokeh_show(obj.panel, *args, **kwargs)
    return _bokeh_show(obj, *args, **kwargs)
