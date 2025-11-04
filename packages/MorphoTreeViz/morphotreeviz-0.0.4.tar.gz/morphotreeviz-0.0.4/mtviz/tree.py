"""Árvore interativa em Bokeh (makePlotTree).

Retorna um VizBundle com o painel (layout), a fonte principal dos nós e
os controles (rádio opcional, tamanho do nó, escala de visão).
"""

import os
import pkgutil
from bokeh.plotting import figure
from bokeh.models import (
    GraphRenderer, StaticLayoutProvider, ColumnDataSource, CustomJS,
    Circle, LabelSet, HoverTool, RadioButtonGroup, Slider, Div
)
from bokeh.layouts import column, row


def makePlotTree(
    root,
    get_children,
    get_val,
    get_id=None,
    *,
    node_size=18,
    color="#4682b4",
    selection_color="orange",
    label_text_color="#ffffff",
    image_source=None,
    alpha_slider=None,
    rep_label_name="repFZs",
    flood_use=None,
    flood_params=None,
    nbr=None,
    panel_width=None,
    panel_caption=None,
):
    # Coletar nós e arestas
    nodes = []
    index_of = {}
    edges = []
    children_map = {}

    def collect(node):
        idx = index_of.get(id(node))
        if idx is not None:
            return idx
        idx = len(nodes)
        index_of[id(node)] = idx
        nodes.append(node)
        ch = list(get_children(node) or [])
        children_map[idx] = []
        for c in ch:
            c_idx = collect(c)
            children_map[idx].append(c_idx)
            edges.append((idx, c_idx))
        return idx

    root_idx = collect(root)

    # Layout: arranjo simples e legível (folhas indexadas; pai no meio dos filhos)
    pos = {}
    counter = [0]

    def layout(idx, depth):
        kids = children_map.get(idx) or []
        if not kids:
            x = counter[0]
            counter[0] += 1
        else:
            xs = []
            for k in kids:
                layout(k, depth + 1)
                xs.append(pos[k][0])
            x = sum(xs) / len(xs)
        pos[idx] = (x, -depth)

    layout(root_idx, 0)

    node_indices = list(range(len(nodes)))
    ids = [str(get_id(n) if get_id else getattr(n, 'id', i)) for i, n in enumerate(nodes)]
    xs = [pos[i][0] for i in node_indices]
    ys = [pos[i][1] for i in node_indices]
    fills = [color for _ in node_indices]

    base_radius = max(1, (node_size/2))
    data = dict(index=node_indices, id=ids, x=xs, y=ys, fill=fills, r=[base_radius for _ in node_indices])
    tooltips = []

    if callable(get_val):
        values = [str(get_val(n)) for n in nodes]
        data["value"] = values
        tooltips.append(("value", "@value"))
    elif isinstance(get_val, dict):
        ordered_items = list(get_val.items())
        for key, getter in ordered_items:
            if callable(getter):
                raw_col = [getter(n) for n in nodes]
            elif isinstance(getter, str):
                raw_col = [getattr(n, getter, "") for n in nodes]
            else:
                raw_col = [getter for _ in nodes]

            if str(key) == rep_label_name:
                col = [list(map(int, v)) if isinstance(v, (list, tuple)) else ([] if v is None else [int(v)]) for v in raw_col]
                data[str(key)] = col
                tooltips.append((str(key).strip(), f"@{{{key}}}"))
                continue

            col = [str(v) for v in raw_col]
            data[str(key)] = col
            tooltips.append((str(key).strip(), f"@{{{key}}}"))
    else:
        values = [str(get_val) for _ in nodes]
        data["value"] = values
        tooltips.append(("value", "@value"))

    node_source = ColumnDataSource(data=data)

    starts = [u for (u, v) in edges]
    ends = [v for (u, v) in edges]

    gr = GraphRenderer()
    gr.node_renderer.data_source = node_source
    gr.node_renderer.glyph = Circle(radius='r', radius_units='screen', fill_color='fill')
    gr.node_renderer.selection_glyph = Circle(radius='r', radius_units='screen', fill_color=selection_color)
    gr.node_renderer.nonselection_glyph = Circle(radius='r', radius_units='screen', fill_color='fill')
    gr.node_renderer.hover_glyph = Circle(radius='r', radius_units='screen', fill_color='fill')
    gr.edge_renderer.data_source.data = dict(start=starts, end=ends)
    gr.layout_provider = StaticLayoutProvider(graph_layout={i: pos[i] for i in node_indices})

    xs_all = [x for x, _ in pos.values()]
    ys_all = [y for _, y in pos.values()]
    pad = 1
    xr = (min(xs_all) - pad, max(xs_all) + pad)
    yr = (min(ys_all) - pad, max(ys_all) + pad)

    _fig_kwargs = {}
    if panel_width is not None:
        try:
            _fig_kwargs['width'] = int(panel_width)
        except Exception:
            pass
    p = figure(x_range=xr, y_range=yr, tools="tap,pan,box_zoom,reset,save", toolbar_location="above", **_fig_kwargs)
    p.renderers.append(gr)

    # Tooltip no hover (suporta múltiplos rótulos)
    if tooltips:
        p.add_tools(HoverTool(tooltips=tooltips, renderers=[gr.node_renderer]))

    # Adicionar rótulos dentro dos nós (id do nó)
    p.add_layout(LabelSet(x='x', y='y', text='id', text_color=label_text_color, source=node_source,
                          text_align='center', text_baseline='middle'))

    # Slider de tamanho do nó
    size_slider = Slider(start=1, end=40, step=0.39, value=float(max(1, min(40, node_size))), title="Node size")
    size_slider.js_on_change('value', CustomJS(args=dict(nodes=node_source), code=(
        "const sz = this.value;\n"
        "const r = sz / 2;\n"
        "const rr = nodes.data['r'];\n"
        "for (let i=0;i<rr.length;i++){ rr[i] = r; }\n"
        "nodes.change.emit();\n"
    )))

    # Slider de escala da visão
    xmid = (xr[0] + xr[1]) / 2
    ymid = (yr[0] + yr[1]) / 2
    xspan = (xr[1] - xr[0])
    yspan = (yr[1] - yr[0])
    scale_slider = Slider(start=0.5, end=5, step=0.1, value=1, title="View scale")
    scale_slider.js_on_change('value', CustomJS(args=dict(plot=p, xmid=xmid, ymid=ymid, xspan=xspan, yspan=yspan), code=(
        "const s = this.value;\n"
        "plot.x_range.start = xmid - (xspan*s)/2;\n"
        "plot.x_range.end   = xmid + (xspan*s)/2;\n"
        "plot.y_range.start = ymid - (yspan*s)/2;\n"
        "plot.y_range.end   = ymid + (yspan*s)/2;\n"
    )))

    # Evento de clique: destacar nó e acionar flood opcional
    # Normaliza vizinhança (default: 8-vizinhos)
    def _norm_nbr(n):
        if n is None or n == 8 or n == '8':
            return [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        if n == 4 or n == '4':
            return [(-1,0),(1,0),(0,-1),(0,1)]
        # tenta converter iterável de pares
        try:
            pairs = []
            for a,b in n:
                pairs.append((int(a), int(b)))
            if pairs:
                return pairs
        except Exception:
            pass
        # fallback para 8
        return [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

    _nbr = _norm_nbr(nbr)

    node_source.selected.js_on_change(
        'indices',
        CustomJS(
            args=dict(
                source=node_source,
                selection_color=selection_color,
                base_color=color,
                img_source=image_source,
                alpha_ctrl=alpha_slider,
                rep_key=rep_label_name,
                flood_params=(flood_params or {}),
                flood_code=(pkgutil.get_data('mtviz', 'js/flood.js').decode('utf-8') if pkgutil.get_data('mtviz', 'js/flood.js') else open(os.path.join(os.path.dirname(__file__), 'js', 'flood.js'), 'r', encoding='utf-8').read()),
                nbr=_nbr,
                flood_initial=(flood_use if (flood_use in ('floodThreshold','floodExactMulti')) else None),
            ),
            code=(
                "const inds = cb_obj.indices;\n"
                "if (!inds.length) return;\n"
                "const i = inds[0];\n"
                "const fills = source.data['fill'];\n"
                "for (let k=0;k<fills.length;k++){ fills[k] = base_color; }\n"
                "fills[i] = selection_color;\n"
                "source.change.emit();\n"
                "if (img_source) {\n"
                "  const reps = source.data[rep_key] ? source.data[rep_key][i] : null;\n"
                "  if (reps && reps.length) {\n"
                "    if (!window.DrawTreeFlood) { try { eval(flood_code); } catch (e) { console.error('flood.js eval failed', e); } }\n"
                "    if (window.DrawTreeFlood) {\n"
                "      try { for (const k in flood_params) { if (Object.prototype.hasOwnProperty.call(flood_params,k)) window.DrawTreeFlood[k] = flood_params[k]; } } catch(e){}\n"
                "      try { if (!window.DrawTreeFlood.__init_set && flood_initial && window.DrawTreeFlood.use) { window.DrawTreeFlood.use(flood_initial); window.DrawTreeFlood.__init_set = true; } } catch(e){}\n"
                "    }\n"
                "    let fn = null;\n"
                "    if (window.DrawTreeFlood && typeof window.DrawTreeFlood.run === 'function') { fn = window.DrawTreeFlood.run; }\n"
                "    else if (typeof window.runFloodMulti === 'function') { fn = window.runFloodMulti; }\n"
                "    if (fn) { try { fn(img_source, alpha_ctrl, reps, nbr); return; } catch (e) { console.error(e); } }\n"
                "  }\n"
                "}\n"
            ),
        )
    )

    # Injetar flood.js (opcional)
    try:
        code_js = pkgutil.get_data('mtviz', 'js/flood.js')
        if not code_js:
            with open(os.path.join(os.path.dirname(__file__), 'js', 'flood.js'), 'r', encoding='utf-8') as f:
                code_js = f.read().encode('utf-8')
        # DocumentReady não disponível aqui sem bokeh.events; manter somente fallback no clique
        _ = code_js  # evita lint
    except Exception:
        pass

    controls = []
    if flood_use:
        active_idx = 1 if flood_use == 'floodThreshold' else 0
        radio = RadioButtonGroup(labels=["Proper part", "Connected component"], active=active_idx)
        radio.js_on_change('active', CustomJS(args=dict(
            source=node_source,
            img_source=image_source,
            alpha_ctrl=alpha_slider,
            rep_key=rep_label_name,
            flood_params=(flood_params or {}),
            flood_code=(pkgutil.get_data('mtviz', 'js/flood.js').decode('utf-8') if pkgutil.get_data('mtviz', 'js/flood.js') else open(os.path.join(os.path.dirname(__file__), 'js', 'flood.js'), 'r', encoding='utf-8').read()),
            selection_color=selection_color,
            base_color=color,
            nbr=_nbr,
        ), code=(
            # Preparar engine e trocar modo de uso
            "if (!window.DrawTreeFlood) { try { eval(flood_code); } catch (e) { console.error('flood.js eval failed', e); } }\n"
            "const name = (this.active === 1) ? 'floodThreshold' : 'floodExactMulti';\n"
            "if (window.DrawTreeFlood) {\n"
            "  try { for (const k in flood_params) { if (Object.prototype.hasOwnProperty.call(flood_params,k)) window.DrawTreeFlood[k] = flood_params[k]; } } catch(e){}\n"
            "  try { if (window.DrawTreeFlood.use) { window.DrawTreeFlood.use(name); window.DrawTreeFlood.__init_set = true; } } catch(e){}\n"
            "}\n"
            # Reaplicar efeito do clique no último nó selecionado
            "const inds = source.selected.indices || [];\n"
            "if (!inds.length) { return; }\n"
            "const i = inds[0];\n"
            # Reforçar destaque (opcional) para manter comportamento idêntico ao clique
            "try {\n"
            "  const fills = source.data['fill'];\n"
            "  for (let k = 0; k < fills.length; k++) fills[k] = base_color;\n"
            "  fills[i] = selection_color;\n"
            "  source.change.emit();\n"
            "} catch (e) { /* ignore */ }\n"
            # Reexecutar flood no mesmo nó, se houver imagem e representantes
            "if (img_source) {\n"
            "  const reps = source.data[rep_key] ? source.data[rep_key][i] : null;\n"
            "  if (reps && reps.length) {\n"
            "    if (!window.DrawTreeFlood) { try { eval(flood_code); } catch (e) { console.error('flood.js eval failed', e); } }\n"
            "    if (window.DrawTreeFlood) {\n"
            "      try { for (const k in flood_params) { if (Object.prototype.hasOwnProperty.call(flood_params,k)) window.DrawTreeFlood[k] = flood_params[k]; } } catch(e){}\n"
            "    }\n"
            "    let fn = null;\n"
            "    if (window.DrawTreeFlood && typeof window.DrawTreeFlood.run === 'function') { fn = window.DrawTreeFlood.run; }\n"
            "    else if (typeof window.runFloodMulti === 'function') { fn = window.runFloodMulti; }\n"
            "    if (fn) { try { fn(img_source, alpha_ctrl, reps, nbr); } catch (e) { console.error(e); } }\n"
            "  }\n"
            "}\n"
        )))
        controls.append(radio)

    caption_div = None
    if panel_caption:
        try:
            caption_div = Div(text=str(panel_caption), styles={'text-align': 'center', 'font-weight': 'bold', 'width': '100%'}, sizing_mode='stretch_width')
        except Exception:
            caption_div = Div(text=str(panel_caption), styles={'text-align': 'center', 'font-weight': 'bold', 'width': '100%'}, sizing_mode='stretch_width')

    _items = []
    if controls:
        _items.append(row(*controls))
    _items.append(row(size_slider, scale_slider))
    _items.append(p)
    if caption_div is not None:
        _items.append(caption_div)
    panel = column(*_items)
    from mtviz.bundle import VizBundle  # import tardio
    return VizBundle(panel=panel, source=node_source, controls=[*(controls or []), size_slider, scale_slider])


def makePlotTreeWithSelectedNodes(
    root,
    get_children,
    get_val,
    get_id=None,
    *,
    node_size=18,
    color="#4682b4",
    selection_color="orange",
    label_text_color="#ffffff",
    image_source=None,
    alpha_slider=None,
    rep_label_name="repFZs",
    flood_use=None,
    flood_params=None,
    nbr=None,
    panel_width=None,
    panel_caption=None,
    tauStar=None,
    F_lambda=None,
    F_lambda_b=None,
):
    # Coleta e estrutura básica (mesma base do makePlotTree)
    nodes = []
    index_of = {}
    edges = []
    children_map = {}

    def collect(node):
        idx = index_of.get(id(node))
        if idx is not None:
            return idx
        idx = len(nodes)
        index_of[id(node)] = idx
        nodes.append(node)
        ch = list(get_children(node) or [])
        children_map[idx] = []
        for c in ch:
            c_idx = collect(c)
            children_map[idx].append(c_idx)
            edges.append((idx, c_idx))
        return idx

    root_idx = collect(root)

    # Layout simples (mesma lógica)
    pos = {}
    counter = [0]

    def layout(idx, depth):
        kids = children_map.get(idx) or []
        if not kids:
            x = counter[0]
            counter[0] += 1
        else:
            xs = []
            for k in kids:
                layout(k, depth + 1)
                xs.append(pos[k][0])
            x = sum(xs) / len(xs)
        pos[idx] = (x, -depth)

    layout(root_idx, 0)

    node_indices = list(range(len(nodes)))
    ids = [str(get_id(n) if get_id else getattr(n, 'id', i)) for i, n in enumerate(nodes)]
    xs = [pos[i][0] for i in node_indices]
    ys = [pos[i][1] for i in node_indices]

    base_radius = max(1, (node_size/2))
    fills = [color for _ in node_indices]
    lines = [color for _ in node_indices]
    lws = [0 for _ in node_indices]

    # Normalizar listas de ids de seleção
    tauStar = set(map(str, (tauStar or [])))
    F_lam = set(map(str, (F_lambda or [])))
    F_lam_b = set(map(str, (F_lambda_b or [])))

    # Precedência: tauStar > F_lambda_b > F_lambda > default
    for i, sid in enumerate(ids):
        if sid in tauStar:
            fills[i] = "blue"
            lines[i] = "orange"
            lws[i] = 2
        elif sid in F_lam_b:
            fills[i] = "red"
        elif sid in F_lam:
            fills[i] = "blue"

    data = dict(index=node_indices, id=ids, x=xs, y=ys, fill=fills, line=lines, lw=lws, r=[base_radius for _ in node_indices])
    tooltips = []

    if callable(get_val):
        values = [str(get_val(n)) for n in nodes]
        data["value"] = values
        tooltips.append(("value", "@value"))
    elif isinstance(get_val, dict):
        ordered_items = list(get_val.items())
        for key, getter in ordered_items:
            if callable(getter):
                raw_col = [getter(n) for n in nodes]
            elif isinstance(getter, str):
                raw_col = [getattr(n, getter, "") for n in nodes]
            else:
                raw_col = [getter for _ in nodes]

            if str(key) == rep_label_name:
                col = [list(map(int, v)) if isinstance(v, (list, tuple)) else ([] if v is None else [int(v)]) for v in raw_col]
                data[str(key)] = col
                tooltips.append((str(key).strip(), f"@{{{key}}}"))
                continue

            col = [str(v) for v in raw_col]
            data[str(key)] = col
            tooltips.append((str(key).strip(), f"@{{{key}}}"))
    else:
        values = [str(get_val) for _ in nodes]
        data["value"] = values
        tooltips.append(("value", "@value"))

    node_source = ColumnDataSource(data=data)

    starts = [u for (u, v) in edges]
    ends = [v for (u, v) in edges]

    gr = GraphRenderer()
    gr.node_renderer.data_source = node_source
    gr.node_renderer.glyph = Circle(radius='r', radius_units='screen', fill_color='fill', line_color='line', line_width='lw')
    # Não alterar cores na seleção
    gr.node_renderer.selection_glyph = Circle(radius='r', radius_units='screen', fill_color='fill', line_color='line', line_width='lw')
    gr.node_renderer.nonselection_glyph = Circle(radius='r', radius_units='screen', fill_color='fill', line_color='line', line_width='lw')
    gr.node_renderer.hover_glyph = Circle(radius='r', radius_units='screen', fill_color='fill', line_color='line', line_width='lw')
    gr.edge_renderer.data_source.data = dict(start=starts, end=ends)
    gr.layout_provider = StaticLayoutProvider(graph_layout={i: pos[i] for i in node_indices})

    xs_all = [x for x, _ in pos.values()]
    ys_all = [y for _, y in pos.values()]
    pad = 1
    xr = (min(xs_all) - pad, max(xs_all) + pad)
    yr = (min(ys_all) - pad, max(ys_all) + pad)

    _fig_kwargs = {}
    if panel_width is not None:
        try:
            _fig_kwargs['width'] = int(panel_width)
        except Exception:
            pass
    p = figure(x_range=xr, y_range=yr, tools="tap,pan,box_zoom,reset,save", toolbar_location="above", **_fig_kwargs)
    p.renderers.append(gr)

    if tooltips:
        p.add_tools(HoverTool(tooltips=tooltips, renderers=[gr.node_renderer]))

    p.add_layout(LabelSet(x='x', y='y', text='id', text_color=label_text_color, source=node_source,
                          text_align='center', text_baseline='middle'))

    size_slider = Slider(start=1, end=40, step=0.39, value=float(max(1, min(40, node_size))), title="Node size")
    size_slider.js_on_change('value', CustomJS(args=dict(nodes=node_source), code=(
        "const sz = this.value;\n"
        "const r = sz / 2;\n"
        "const rr = nodes.data['r'];\n"
        "for (let i=0;i<rr.length;i++){ rr[i] = r; }\n"
        "nodes.change.emit();\n"
    )))

    xmid = (xr[0] + xr[1]) / 2
    ymid = (yr[0] + yr[1]) / 2
    xspan = (xr[1] - xr[0])
    yspan = (yr[1] - yr[0])
    scale_slider = Slider(start=0.5, end=5, step=0.1, value=1, title="View scale")
    scale_slider.js_on_change('value', CustomJS(args=dict(plot=p, xmid=xmid, ymid=ymid, xspan=xspan, yspan=yspan), code=(
        "const s = this.value;\n"
        "plot.x_range.start = xmid - (xspan*s)/2;\n"
        "plot.x_range.end   = xmid + (xspan*s)/2;\n"
        "plot.y_range.start = ymid - (yspan*s)/2;\n"
        "plot.y_range.end   = ymid + (yspan*s)/2;\n"
    )))

    # Normaliza vizinhança (default: 8-vizinhos)
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

    # Evento de clique + integração com flood (sem alterar cores)
    node_source.selected.js_on_change(
        'indices',
        CustomJS(
            args=dict(
                source=node_source,
                img_source=image_source,
                alpha_ctrl=alpha_slider,
                rep_key=rep_label_name,
                flood_params=(flood_params or {}),
                flood_code=(pkgutil.get_data('mtviz', 'js/flood.js').decode('utf-8') if pkgutil.get_data('mtviz', 'js/flood.js') else open(os.path.join(os.path.dirname(__file__), 'js', 'flood.js'), 'r', encoding='utf-8').read()),
                nbr=_nbr,
                flood_initial=(flood_use if (flood_use in ('floodThreshold','floodExactMulti')) else None),
            ),
            code=(
                "const inds = cb_obj.indices;\n"
                "if (!inds.length) return;\n"
                "const i = inds[0];\n"
                "if (img_source) {\n"
                "  const reps = source.data[rep_key] ? source.data[rep_key][i] : null;\n"
                "  if (reps && reps.length) {\n"
                "    if (!window.DrawTreeFlood) { try { eval(flood_code); } catch (e) { console.error('flood.js eval failed', e); } }\n"
                "    if (window.DrawTreeFlood) {\n"
                "      try { for (const k in flood_params) { if (Object.prototype.hasOwnProperty.call(flood_params,k)) window.DrawTreeFlood[k] = flood_params[k]; } } catch(e){}\n"
                "      try { if (!window.DrawTreeFlood.__init_set && flood_initial && window.DrawTreeFlood.use) { window.DrawTreeFlood.use(flood_initial); window.DrawTreeFlood.__init_set = true; } } catch(e){}\n"
                "    }\n"
                "    let fn = null;\n"
                "    if (window.DrawTreeFlood && typeof window.DrawTreeFlood.run === 'function') { fn = window.DrawTreeFlood.run; }\n"
                "    else if (typeof window.runFloodMulti === 'function') { fn = window.runFloodMulti; }\n"
                "    if (fn) { try { fn(img_source, alpha_ctrl, reps, nbr); return; } catch (e) { console.error(e); } }\n"
                "  }\n"
                "}\n"
            ),
        )
    )

    try:
        code_js = pkgutil.get_data('mtviz', 'js/flood.js')
        if not code_js:
            with open(os.path.join(os.path.dirname(__file__), 'js', 'flood.js'), 'r', encoding='utf-8') as f:
                code_js = f.read().encode('utf-8')
        _ = code_js
    except Exception:
        pass

    controls = []
    if flood_use:
        active_idx = 1 if flood_use == 'floodThreshold' else 0
        radio = RadioButtonGroup(labels=["Proper part", "Connected component"], active=active_idx)
        radio.js_on_change('active', CustomJS(args=dict(
            source=node_source,
            img_source=image_source,
            alpha_ctrl=alpha_slider,
            rep_key=rep_label_name,
            flood_params=(flood_params or {}),
            flood_code=(pkgutil.get_data('mtviz', 'js/flood.js').decode('utf-8') if pkgutil.get_data('mtviz', 'js/flood.js') else open(os.path.join(os.path.dirname(__file__), 'js', 'flood.js'), 'r', encoding='utf-8').read()),
            nbr=_nbr,
        ), code=(
            "if (!window.DrawTreeFlood) { try { eval(flood_code); } catch (e) { console.error('flood.js eval failed', e); } }\n"
            "const name = (this.active === 1) ? 'floodThreshold' : 'floodExactMulti';\n"
            "if (window.DrawTreeFlood) {\n"
            "  try { for (const k in flood_params) { if (Object.prototype.hasOwnProperty.call(flood_params,k)) window.DrawTreeFlood[k] = flood_params[k]; } } catch(e){}\n"
            "  try { if (window.DrawTreeFlood.use) { window.DrawTreeFlood.use(name); window.DrawTreeFlood.__init_set = true; } } catch(e){}\n"
            "}\n"
            "const inds = source.selected.indices || [];\n"
            "if (!inds.length) { return; }\n"
            "const i = inds[0];\n"
            "if (img_source) {\n"
            "  const reps = source.data[rep_key] ? source.data[rep_key][i] : null;\n"
            "  if (reps && reps.length) {\n"
            "    if (!window.DrawTreeFlood) { try { eval(flood_code); } catch (e) { console.error('flood.js eval failed', e); } }\n"
            "    if (window.DrawTreeFlood) {\n"
            "      try { for (const k in flood_params) { if (Object.prototype.hasOwnProperty.call(flood_params,k)) window.DrawTreeFlood[k] = flood_params[k]; } } catch(e){}\n"
            "    }\n"
            "    let fn = null;\n"
            "    if (window.DrawTreeFlood && typeof window.DrawTreeFlood.run === 'function') { fn = window.DrawTreeFlood.run; }\n"
            "    else if (typeof window.runFloodMulti === 'function') { fn = window.runFloodMulti; }\n"
            "    if (fn) { try { fn(img_source, alpha_ctrl, reps, nbr); } catch (e) { console.error(e); } }\n"
            "  }\n"
            "}\n"
        )))
        controls.append(radio)

    caption_div = None
    if panel_caption:
        try:
            caption_div = Div(text=str(panel_caption), styles={'text-align': 'center', 'font-weight': 'bold', 'width': '100%'}, sizing_mode='stretch_width')
        except Exception:
            caption_div = Div(text=str(panel_caption), styles={'text-align': 'center', 'font-weight': 'bold', 'width': '100%'}, sizing_mode='stretch_width')

    _items = []
    if controls:
        _items.append(row(*controls))
    _items.append(row(size_slider, scale_slider))
    _items.append(p)
    if caption_div is not None:
        _items.append(caption_div)
    panel = column(*_items)
    from mtviz.bundle import VizBundle
    return VizBundle(panel=panel, source=node_source, controls=[*(controls or []), size_slider, scale_slider])
