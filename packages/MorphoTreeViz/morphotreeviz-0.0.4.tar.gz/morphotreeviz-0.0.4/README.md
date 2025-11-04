# MorphoTreeViz – Morphological Trees Visualization

Interactive visualization of morphological trees.


## Quick Start (import mtviz as viz)
```
import mtviz as viz

class Node:
    def __init__(self, id, level, area, children=None):
        self.id = id
        self.level = level
        self.area = area
        self.children = children or []

root = Node(1, 0, 10, [
    Node(2, 1, 5, [Node(4, 2, 3), Node(5, 2, 2)]),
    Node(3, 1, 5, [Node(6, 2, 1)])
])

pt = viz.PrintTree(lambda n: n.children, lambda n: f"{n.id}: {n.level}: {n.area}")
pt(root)
```

## Color (optional)
- Pass ANSI codes in `color` (e.g., `"\x1b[40m\x1b[37m"` for black background + white text).
- If you use `colorama` in your project, you can pass `Back.BLACK + Fore.WHITE`.

## Interactive Tree (viz.makePlotTree)
Use Bokeh to visualize and interact with the tree: hover tooltips, click actions, flood tools, and size/zoom controls.
```
import mtviz as viz
from bokeh.io import show, output_notebook

output_notebook()  # inline in Jupyter; use show(p) to open in browser

class Node:
    def __init__(self, id, level, area, children=None):
        self.id = id
        self.level = level
        self.area = area
        self.children = children or []

root = Node(1, 0, 10, [
    Node(2, 1, 5, [Node(4, 2, 3), Node(5, 2, 2)]),
    Node(3, 1, 5, [Node(6, 2, 1)])
])

p = viz.makePlotTree(
    root,
    lambda n: n.children,
    {
      "id:":      lambda n: n.id,
      "level:":   "level",
      "area:":    lambda n: n.area,
      "repCNPs":  lambda n: getattr(n, 'repCnps', []),
    },
    lambda n: n.id,
    node_size=18,
    flood_use=None,
)
show(p.panel)
```

## Image Overlay + Flood
You can compose a figure with a grayscale image and an RGBA overlay, then link DrawTree’s flood tools.
```
import mtviz as viz
from bokeh.layouts import row, column

img = ...  # 2D numpy array (grayscale)
bundle_img = viz.makePlotImage(img)
p_img = bundle_img.panel
img_source = bundle_img.source
alpha_slider = bundle_img.controls[0]

p_tree = viz.makePlotTree(
  root,
  lambda n: n.children,
  { "id:": lambda n: n.id, "repCNPs": lambda n: getattr(n, 'repCnps', []) },
  lambda n: n.id,
  image_source=img_source,
  alpha_slider=alpha_slider,
  flood_use='floodThreshold',
  flood_params={'polarity': 255},
)
show(row(p_tree, column(alpha_slider, p_img)))
```
