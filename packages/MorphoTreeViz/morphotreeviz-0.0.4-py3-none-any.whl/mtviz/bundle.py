"""Pacote de utilidades do mtviz

Define o contêiner VizBundle para padronizar retornos de funções
de visualização (painel do Bokeh + fontes + controles).
"""

from typing import Any, Iterable, List, Optional


class VizBundle:
    """Contêiner de visualização.

    Atributos:
    - panel: layout/figura do Bokeh a ser exibido (bokeh.io.show(panel))
    - source: ColumnDataSource principal associado à visualização
    - controls: lista de widgets de controle (sliders/botões/etc.)

    Compatibilidade: permite desempacotar como (panel, source, primeiro_controle).
    """

    def __init__(self, panel: Any, *, source: Optional[Any] = None, controls: Optional[Iterable[Any]] = None) -> None:
        self.panel = panel
        self.source = source
        self.controls: List[Any] = list(controls or [])

    def __iter__(self):
        # Permite: panel, source, ctrl = VizBundle(...)
        first = self.controls[0] if self.controls else None
        yield self.panel
        yield self.source
        yield first

    def __getattr__(self, name: str):
        """Delegar atributos desconhecidos para o painel.

        Útil para chamadas que esperam um objeto do Bokeh (ex.: métodos/props),
        embora não substitua verificações de tipo (isinstance) feitas pelo Bokeh.
        """
        return getattr(self.panel, name)
