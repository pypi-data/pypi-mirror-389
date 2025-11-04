"""Composição de imagem + overlay RGBA e tooltip (makePlotImage)."""

import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, LinearColorMapper, ColorBar, BasicTicker, Slider, CustomJS, Label
)
from bokeh.palettes import Greys256


def makePlotImage(img, *, title="Image + overlay", width=900, alpha=100, nbr=None):
    # Garantir array 2D
    img = np.asarray(img)
    if img.ndim != 2:
        raise ValueError("img must be a 2D grayscale array")

    num_rows, num_cols = img.shape
    img_vis = img

    overlay_rgba = np.zeros((num_rows, num_cols), dtype=np.uint32)
    visited = np.zeros((num_rows * num_cols,), dtype=np.uint8)

    source = ColumnDataSource(data=dict(
        image=[img_vis.copy()],
        imageOrig=[img_vis.copy()],
        overlay=[overlay_rgba],
        visited=[visited],
        numCols=[num_cols],
        numRows=[num_rows],
    ))

    # Ponto e texto do tooltip
    tip_source = ColumnDataSource(data=dict(mx=[0], my=[0], tip_text=[""]))

    cmap = LinearColorMapper(palette=Greys256, low=float(img_vis.min()), high=float(img_vis.max()))
    height = int(width * num_rows / num_cols)
    p = figure(title=title, x_range=(0, num_cols), y_range=(num_rows, 0), match_aspect=True,
               tools="reset,pan,wheel_zoom,save", width=width, height=height)
    p.image(image='image', source=source, x=0, y=0, dw=num_cols, dh=num_rows, color_mapper=cmap)
    #p.add_layout(ColorBar(color_mapper=cmap, ticker=BasicTicker(desired_num_ticks=9)), 'right')
    p.image_rgba(image='overlay', source=source, x=0, y=0, dw=num_cols, dh=num_rows)

    # Marcador + label com borda laranja (fundo transparente)
    p.scatter(x='mx', y='my', size=4, marker='circle', source=tip_source, fill_color='magenta', line_color='magenta')
    lbl = Label(x=0, y=0, x_units='data', y_units='data', text='', text_align='left', text_baseline='bottom',
                text_color='magenta', background_fill_color=None, background_fill_alpha=0.0,
                border_line_color='magenta', border_line_alpha=1.0)
    p.add_layout(lbl)

    # Label de hover (índice do pixel e level) — transparente e texto verde
    lbl_hover = Label(
        x=0, y=0, x_units='data', y_units='data', text='',
        text_align='left', text_baseline='top', text_color='magenta',
        background_fill_color=None, background_fill_alpha=0.0,
        border_line_color=None, border_line_alpha=0.0,
        text_font_size='10pt', visible=False,
    )
    p.add_layout(lbl_hover)

    # Marcador pequeno para posição do mouse (hover)
    hover_source = ColumnDataSource(data=dict(hx=[0.0], hy=[0.0]))
    hover_marker = p.scatter(x='hx', y='hy', size=5, marker='circle', source=hover_source,
                             fill_color='magenta', line_color='magenta', alpha=1.0)
    hover_marker.visible = False

    alpha_slider = Slider(start=0, end=255, value=int(alpha), step=1, title="Alpha (overlay)")
    alpha_cb = CustomJS(args=dict(source=source, alpha_slider=alpha_slider), code="""
        const num_cols = source.data.numCols[0];
        const num_rows = source.data.numRows[0];
        const overBuf  = source.data.overlay[0];
        const visited  = source.data.visited[0];
        const a  = (alpha_slider.value|0);
        const rp = (255 * a / 255) | 0;
        const newVal = (rp<<24) | (0<<16) | (0<<8) | a;
        const N = num_cols * num_rows;
        for (let k = 0; k < N; k++) overBuf[k] = visited[k] ? newVal : 0;
        source.change.emit();
    """)
    alpha_slider.js_on_change('value', alpha_cb)

    # Callback de clique: flood + tooltip sempre dentro
    # Normaliza vizinhança (default 8-vizinhos)
    def _norm_nbr(n):
        if n is None or n == 8 or n == '8':
            return [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        if n == 4 or n == '4':
            return [(-1,0),(1,0),(0,-1),(0,1)]
        try:
            pairs = []
            for a,b in n:
                pairs.append((int(a), int(b)))
            if pairs:
                return pairs
        except Exception:
            pass
        return [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

    _nbr = _norm_nbr(nbr)

    tap_cb = CustomJS(args=dict(source=source, tip=tip_source, alpha_slider=alpha_slider, label=lbl, nbr=_nbr), code="""
        const ev = cb_obj; const x = ev.x, y = ev.y;
        const num_cols = source.data.numCols[0]; const num_rows = source.data.numRows[0];
        if (!(Number.isFinite(x) && Number.isFinite(y))) return;
        if (x < 0 || x >= num_cols || y < 0 || y >= num_rows) return;

        const col = Math.floor(x); const row = Math.floor(y);
        const seedIdx = row * num_cols + col;

        const bufOrig = source.data.imageOrig[0];
        const overBuf = source.data.overlay[0];
        const visited = source.data.visited[0];
        overBuf.fill(0); visited.fill(0);

        const a  = (alpha_slider.value|0);
        const rp = (255 * a / 255) | 0; const newVal = (rp<<24) | (0<<16) | (0<<8) | a;
        const target = bufOrig[seedIdx]; if (!Number.isFinite(target)) return;

        const stack = [seedIdx]; visited[seedIdx] = 1; overBuf[seedIdx] = newVal; let rep = seedIdx;
        while (stack.length) {
            const k0 = stack.pop(); const r0 = (k0 / num_cols) | 0; const c0 = k0 % num_cols; if (k0 < rep) rep = k0;
            for (let i = 0; i < nbr.length; i++) {
                const rr = r0 + nbr[i][0], cc = c0 + nbr[i][1];
                if (rr < 0 || rr >= num_rows || cc < 0 || cc >= num_cols) continue;
                const kk = rr * num_cols + cc; if (visited[kk]) continue;
                if (bufOrig[kk] === target) { visited[kk] = 1; overBuf[kk] = newVal; stack.push(kk); }
            }
        }

        // Marcar ponto central do clique
        tip.data.mx[0] = col + 0.5; tip.data.my[0] = row + 0.5;

        // Posicionar tooltip sempre dentro
        const margin = 0.35, offX = 0.35, offY = 0.45;
        let placeBelow = (row < 1.5), placeAbove = (row > num_rows - 1.5);
        let alignRight = (col > num_cols - 3), alignLeft  = (col < 3);
        let tx = col + offX; let ty = row - offY; label.text_baseline = 'bottom';
        if (placeBelow) { ty = row + offY; label.text_baseline = 'top'; }
        if (placeAbove) { ty = row - offY; label.text_baseline = 'bottom'; }
        label.text_align = 'left'; if (alignRight && !alignLeft) { label.text_align = 'right'; tx = col - offX; }
        if (alignLeft && !alignRight) { label.text_align = 'left'; tx = col + offX; }
        if (tx < margin) tx = margin; if (tx > num_cols - margin) tx = num_cols - margin;
        if (ty < margin) ty = margin; if (ty > num_rows - margin) ty = num_rows - margin;

        label.x = tx; label.y = ty; label.text = `repFZ: ${rep}\nlevel: ${target}`; label.change.emit();
        tip.change.emit(); source.change.emit();
    """)
    p.js_on_event('tap', tap_cb)

    # Evento adicional: hover para mostrar índice e level, sempre dentro da imagem
    hover_cb = CustomJS(args=dict(source=source, hover_label=lbl_hover, hover_source=hover_source, hover_marker=hover_marker), code="""
        const ev = cb_obj; const x = ev.x, y = ev.y;
        const num_cols = source.data.numCols[0]; const num_rows = source.data.numRows[0];
        if (!(Number.isFinite(x) && Number.isFinite(y)) || x < 0 || x >= num_cols || y < 0 || y >= num_rows) {
            hover_label.visible = false; hover_label.change.emit();
            hover_marker.visible = false; hover_marker.change.emit();
            return;
        }
        const col = Math.floor(x); const row = Math.floor(y);
        const idx = row * num_cols + col;
        const bufOrig = source.data.imageOrig[0];
        const level = bufOrig[idx];
        // Posiciona próximo ao pixel, ajustando alinhamento para manter dentro
        const margin = 0.35, offX = 0.35, offY = 0.45;
        let placeBelow = (row < 1.5), placeAbove = (row > num_rows - 1.5);
        let alignRight = (col > num_cols - 3), alignLeft  = (col < 3);
        let tx = col + offX; let ty = row - offY; hover_label.text_baseline = 'bottom';
        if (placeBelow) { ty = row + offY; hover_label.text_baseline = 'top'; }
        if (placeAbove) { ty = row - offY; hover_label.text_baseline = 'bottom'; }
        hover_label.text_align = 'left'; if (alignRight && !alignLeft) { hover_label.text_align = 'right'; tx = col - offX; }
        if (alignLeft && !alignRight) { hover_label.text_align = 'left'; tx = col + offX; }
        if (tx < margin) tx = margin; if (tx > num_cols - margin) tx = num_cols - margin;
        if (ty < margin) ty = margin; if (ty > num_rows - margin) ty = num_rows - margin;
        hover_label.x = tx; hover_label.y = ty;
        hover_label.text = `idx: ${idx}\nlevel: ${level}`;
        hover_label.visible = true;
        hover_label.change.emit();

        // Atualiza marcador de hover no centro do pixel
        hover_source.data.hx[0] = col + 0.5;
        hover_source.data.hy[0] = row + 0.5;
        hover_source.change.emit();
        hover_marker.visible = true;
        hover_marker.change.emit();
    """)
    p.js_on_event('mousemove', hover_cb)

    # Ao clicar em "reset" (ferramenta do Bokeh), limpar a sobreposição
    reset_cb = CustomJS(args=dict(source=source), code="""
        try {
            const overBuf  = source.data.overlay[0];
            const visited  = source.data.visited[0];
            if (overBuf && visited) { overBuf.fill(0); visited.fill(0); }
            source.change.emit();
        } catch (e) { /* ignore */ }
    """)
    p.js_on_event('reset', reset_cb)

    from mtviz.bundle import VizBundle
    return VizBundle(panel=p, source=source, controls=[alpha_slider])


def makePlotImagePixels(img, pixels, *, title="Image + pixels overlay", width=900, alpha=120, nbr=None):
    """Exibe uma imagem 2D com um overlay definido pelo usuário via lista de pixels.

    Parâmetros:
    - img: array 2D (grayscale)
    - pixels: pode ser
        * lista/iterável de pares (row, col)
        * máscara booleana 2D com mesma forma de ``img``
        * índices lineares (inteiros) no buffer achatado (row*num_cols + col)
    - title, width, alpha: mesmos sentidos do makePlotImage original

    Retorna VizBundle com:
    - panel: figura Bokeh
    - source: ColumnDataSource com campos: image, overlay, mask, numCols, numRows
    - controls: [alpha_slider]
    """
    import numpy as _np

    img = _np.asarray(img)
    if img.ndim != 2:
        raise ValueError("img must be a 2D grayscale array")

    num_rows, num_cols = img.shape

    # Normaliza pixels -> índices lineares
    def _to_indices(px):
        # máscara booleana 2D
        if isinstance(px, _np.ndarray) and px.dtype == bool:
            if px.shape != img.shape:
                raise ValueError("boolean mask must have same shape as img")
            return _np.flatnonzero(px)
        # array-like com pares (r,c)
        try:
            arr = _np.asarray(px, dtype=object)
            if arr.ndim == 2 and arr.shape[1] == 2:
                rr = arr[:, 0].astype(int)
                cc = arr[:, 1].astype(int)
                if ((rr < 0).any() or (rr >= num_rows).any() or
                        (cc < 0).any() or (cc >= num_cols).any()):
                    raise ValueError("(row,col) out of bounds")
                return rr * num_cols + cc
        except Exception:
            pass
        # índices lineares
        idx = _np.asarray(list(px), dtype=int)
        if ((idx < 0).any() or (idx >= num_rows * num_cols).any()):
            raise ValueError("linear indices out of bounds")
        return idx

    idx = _to_indices(pixels)

    # Buffers
    overlay_rgba = _np.zeros((num_rows, num_cols), dtype=_np.uint32)
    mask = _np.zeros((num_rows * num_cols,), dtype=_np.uint8)
    mask[idx] = 1

    # Preenche overlay conforme alpha (vermelho, consistente com versão original)
    a = int(alpha) & 0xFF
    rp = int((255 * a) / 255) & 0xFF
    newVal = (rp << 24) | (0 << 16) | (0 << 8) | a
    overlay_rgba.flat[idx] = newVal

    source = ColumnDataSource(data=dict(
        image=[img.copy()],
        overlay=[overlay_rgba],
        mask=[mask],
        numCols=[num_cols],
        numRows=[num_rows],
    ))

    cmap = LinearColorMapper(palette=Greys256, low=float(img.min()), high=float(img.max()))
    height = int(width * num_rows / num_cols)
    p = figure(title=title, x_range=(0, num_cols), y_range=(num_rows, 0), match_aspect=True,
               tools="reset,pan,wheel_zoom,save", width=width, height=height)
    p.image(image='image', source=source, x=0, y=0, dw=num_cols, dh=num_rows, color_mapper=cmap)
    #p.add_layout(ColorBar(color_mapper=cmap, ticker=BasicTicker(desired_num_ticks=9)), 'right')
    p.image_rgba(image='overlay', source=source, x=0, y=0, dw=num_cols, dh=num_rows)

    # Slider de alpha para o overlay de pixels
    alpha_slider = Slider(start=0, end=255, value=int(alpha), step=1, title="Alpha (overlay)")
    alpha_cb = CustomJS(args=dict(source=source, alpha_slider=alpha_slider), code="""
        const num_cols = source.data.numCols[0];
        const num_rows = source.data.numRows[0];
        const overBuf  = source.data.overlay[0];
        const mask     = source.data.mask[0];
        const a  = (alpha_slider.value|0);
        const rp = (255 * a / 255) | 0;
        const newVal = (rp<<24) | (0<<16) | (0<<8) | a;
        const N = num_cols * num_rows;
        for (let k = 0; k < N; k++) overBuf[k] = mask[k] ? newVal : 0;
        source.change.emit();
    """)
    alpha_slider.js_on_change('value', alpha_cb)

    # Tooltip de hover (índice do pixel e level) — transparente e verde
    lbl_hover_px = Label(
        x=0, y=0, x_units='data', y_units='data', text='',
        text_align='left', text_baseline='top', text_color='magenta',
        background_fill_color=None, background_fill_alpha=0.0,
        border_line_color=None, border_line_alpha=0.0,
        text_font_size='10pt', visible=False,
    )
    p.add_layout(lbl_hover_px)

    # Marcador de hover para pixels
    hover_source_px = ColumnDataSource(data=dict(hx=[0.0], hy=[0.0]))
    hover_marker_px = p.scatter(x='hx', y='hy', size=5, marker='circle', source=hover_source_px,
                                fill_color='magenta', line_color='magenta', alpha=1.0)
    hover_marker_px.visible = False

    hover_cb_px = CustomJS(args=dict(source=source, hover_label=lbl_hover_px, hover_source=hover_source_px, hover_marker=hover_marker_px), code="""
        const ev = cb_obj; const x = ev.x, y = ev.y;
        const num_cols = source.data.numCols[0]; const num_rows = source.data.numRows[0];
        if (!(Number.isFinite(x) && Number.isFinite(y)) || x < 0 || x >= num_cols || y < 0 || y >= num_rows) {
            hover_label.visible = false; hover_label.change.emit();
            hover_marker.visible = false; hover_marker.change.emit();
            return;
        }
        const col = Math.floor(x); const row = Math.floor(y);
        const idx = row * num_cols + col;
        const bufImg = source.data.image[0];
        const level = bufImg[idx];
        const margin = 0.35, offX = 0.35, offY = 0.45;
        let placeBelow = (row < 1.5), placeAbove = (row > num_rows - 1.5);
        let alignRight = (col > num_cols - 3), alignLeft  = (col < 3);
        let tx = col + offX; let ty = row - offY; hover_label.text_baseline = 'bottom';
        if (placeBelow) { ty = row + offY; hover_label.text_baseline = 'top'; }
        if (placeAbove) { ty = row - offY; hover_label.text_baseline = 'bottom'; }
        hover_label.text_align = 'left'; if (alignRight && !alignLeft) { hover_label.text_align = 'right'; tx = col - offX; }
        if (alignLeft && !alignRight) { hover_label.text_align = 'left'; tx = col + offX; }
        if (tx < margin) tx = margin; if (tx > num_cols - margin) tx = num_cols - margin;
        if (ty < margin) ty = margin; if (ty > num_rows - margin) ty = num_rows - margin;
        hover_label.x = tx; hover_label.y = ty;
        hover_label.text = `idx: ${idx}\nlevel: ${level}`;
        hover_label.visible = true;
        hover_label.change.emit();

        hover_source.data.hx[0] = col + 0.5;
        hover_source.data.hy[0] = row + 0.5;
        hover_source.change.emit();
        hover_marker.visible = true;
        hover_marker.change.emit();
    """)
    p.js_on_event('mousemove', hover_cb_px)

    from mtviz.bundle import VizBundle
    return VizBundle(panel=p, source=source, controls=[alpha_slider])
