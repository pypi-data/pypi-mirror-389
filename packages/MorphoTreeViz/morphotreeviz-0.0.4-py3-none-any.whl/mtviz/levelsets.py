"""Level sets visualization (makeLevelSets).

Gera duas imagens binárias com três níveis de cor a partir de um threshold t:
  - pixels ≥ t (preto se > t, cinza escuro se == t, branco se < t)
  - pixels ≤ t (preto se < t, cinza escuro se == t, branco se > t)

Retorna um VizBundle com:
  - panel: duas figuras lado a lado, com títulos "pixels ≥ t" e "pixels ≤ t"
  - controls: [slider_t]
"""

from typing import Optional

import numpy as np
from bokeh.plotting import figure
from bokeh.layouts import row
from bokeh.models import ColumnDataSource, Slider, CustomJS

from .bundle import VizBundle



def makeLevelSets(img, *, title_left: str = "pixels ≥", title_right: str = "pixels ≤",
                  width: int = 400, height: Optional[int] = None) -> VizBundle:
    """Cria duas imagens thresholded (≥t e ≤t) com 3 cores e um slider de threshold.

    Parâmetros
    - img: array 2D (grayscale)
    - title_left: título da imagem da esquerda (≥ t)
    - title_right: título da imagem da direita (≤ t)
    - width/height: dimensões das figuras individuais (height opcional; se None, preserva aspecto)
    """
    arr = np.asarray(img)
    if arr.ndim != 2:
        raise ValueError("img must be a 2D grayscale array")

    num_rows, num_cols = arr.shape

    # Cores RGBA para preenchimento (aqui, só o igual a t será visível)
    BLACK_0 = (255 << 24) | (0 << 16) | (0 << 8) | 0 
    WHITE_0 = (255 << 24) | (255 << 16) | (255 << 8) | 255 
    RED_50  = (255 << 24) | (0 << 16) | (0 << 8) | 139

    # Extrai níveis de cinza únicos (ignorando NaNs) e define slider discreto nesses níveis
    valid = arr[~np.isnan(arr)]
    if valid.size == 0:
        raise ValueError("img has no finite values")
    levels = np.unique(valid)
    # Índice inicial: nível do meio
    idx0 = 0
    t0 = int(levels[0])

    # Pré-computa as imagens RGBA iniciais
    def build_rgba_ge(a, t):
        ge_rgba = np.empty((num_rows, num_cols), dtype=np.uint32)
        gt = a > t
        eq = a == t
        lt = a < t
        ge_rgba[gt] = BLACK_0      # satisfaz (≥ t), invisível
        ge_rgba[eq] = RED_50       # igual a t, vermelho semi-transparente
        ge_rgba[lt] = WHITE_0      # não satisfaz, invisível
        return ge_rgba

    def build_rgba_le(a, t):
        le_rgba = np.empty((num_rows, num_cols), dtype=np.uint32)
        lt = a < t
        eq = a == t
        gt = a > t
        le_rgba[lt] = BLACK_0      # satisfaz (≤ t), invisível
        le_rgba[eq] = RED_50       # igual a t, vermelho semi-transparente
        le_rgba[gt] = WHITE_0      # não satisfaz, invisível
        return le_rgba

    ge0 = build_rgba_ge(arr, t0)
    le0 = build_rgba_le(arr, t0)

    source = ColumnDataSource(data=dict(
        imageOrig=[arr.copy()],
        numCols=[num_cols],
        numRows=[num_rows],
        ge=[ge0],
        le=[le0],
    ))

    # Fonte auxiliar para os níveis discretos do threshold
    levels_src = ColumnDataSource(data=dict(levels=levels.astype(float)))

    # Figuras
    if height is None:
        height = int(width * num_rows / max(1, num_cols))

    p_ge = figure(title=f"{title_left} {t0}", x_range=(0, num_cols), y_range=(num_rows, 0),
                  match_aspect=True, tools="reset,pan,wheel_zoom,save",
                  width=width, height=height)
    p_ge.image_rgba(image='ge', source=source, x=0, y=0, dw=num_cols, dh=num_rows)

    p_le = figure(title=f"{title_right} {t0}", x_range=(0, num_cols), y_range=(num_rows, 0),
                  match_aspect=True, tools="reset,pan,wheel_zoom,save",
                  width=width, height=height)
    p_le.image_rgba(image='le', source=source, x=0, y=0, dw=num_cols, dh=num_rows)

    # Slider do threshold
    slider = Slider(start=0, end=max(0, len(levels) - 1), value=idx0, step=1, title="threshold index", tooltips=False)
    slider.js_on_change('value', CustomJS(args=dict(src=source, levels_src=levels_src, p_left=p_ge, p_right=p_le), code=(
        "const idx = (this.value|0);\n"
        "const levels = levels_src.data.levels;\n"
        "const t = levels[Math.max(0, Math.min(idx, levels.length-1))];\n"
        "const num_cols = src.data.numCols[0]; const num_rows = src.data.numRows[0];\n"
        "const buf = src.data.imageOrig[0];\n"
        "const ge = src.data.ge[0]; const le = src.data.le[0];\n"
        "const N = num_cols * num_rows;\n"
        "const BLACK_0 = (255 << 24) | (0 << 16) | (0 << 8) | 0;\n"
        "const WHITE_0 = (255 << 24) | (255 << 16) | (255 << 8) | 255;\n"
        "const RED_50  = (255 << 24) | (0 << 16) | (0 << 8) | 139;\n"
        "for (let k = 0; k < N; k++) {\n"
        "  const v = buf[k];\n"
        "  if (!(Number.isFinite(v))) { ge[k] = WHITE_0; le[k] = WHITE_0; continue; }\n"
        "  ge[k] = (v === t) ? RED_50 : ((v > t) ? BLACK_0 : WHITE_0);\n"
        "  le[k] = (v === t) ? RED_50 : ((v < t) ? BLACK_0 : WHITE_0);\n"
        "}\n"
        "src.change.emit();\n"
        "const tStr = Number.isInteger(t) ? (t.toString()) : (t.toFixed(6));\n"
        "try { p_left.title.text = `pixels ≥ ${tStr}`; } catch(e) {}\n"
        "try { p_right.title.text = `pixels ≤ ${tStr}`; } catch(e) {}\n"
    )))

    return VizBundle(panel=row(p_ge, p_le), source=source, controls=[slider])
