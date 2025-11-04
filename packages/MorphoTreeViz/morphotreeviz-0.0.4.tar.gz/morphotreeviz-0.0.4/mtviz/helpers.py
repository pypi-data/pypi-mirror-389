import mtviz as viz
from bokeh.io import output_notebook, show
from bokeh.layouts import column, row
from bokeh.resources import INLINE

def getPlotTree(root, title):
    return viz.makePlotTree(
        root,
        lambda n: n.children,
        {
            "id:": lambda n: n.id,
            "level:": lambda n: n.level,
            "area:": lambda n: n.area,
        },
        lambda n: n.id,
        panel_caption = title
    ).panel

def printTree(root, attrs=['id']):
    _printTree = viz.PrintTree(
        lambda n: n.children,
        lambda n: ": ".join(str(getattr(n, a)) for a in attrs),
        color='\x1b[40m\x1b[37m'
    )
    return _printTree(root)

def showComponentTree(root, image=None, panel_caption=None, panel_width=500, width=900, nbr=None):
    p_img = img_source = alpha_slider = None
    if(image is not None):
        p_img, img_source, alpha_slider = viz.makePlotImage(image, width=width, nbr=nbr)

    p_tree = viz.makePlotTree(
        root,
        lambda n: n.children,
        {
            "id:": lambda n: n.id,
            "repNode": lambda n: n.repNode,
            "level:": lambda n: n.level,
            #"NumFZs:": lambda n: n.numFlatzones,
            "repFZs": lambda n: n.repCNPs, # lista de índices flat
            "area:": lambda n: n.area,
        },
        lambda n: n.id,
        image_source=img_source,
        alpha_slider=alpha_slider,
        flood_use= None if image is None else 'floodExactMulti', 
        rep_label_name='repFZs',
        flood_params={'polarity': 255 if root.level < root.children[0].level else 0},
        nbr=nbr,
        panel_caption = panel_caption if panel_caption is not None else "max-tree" if root.level < root.children[0].level else "min-tree",
        panel_width=panel_width
    )
    if(image is not None):
        show(row(p_tree.panel, column(alpha_slider, p_img)))
    else:
        show(p_tree.panel)


def showComponentTrees(rootL, rootR, image=None, panel_width=600, width=500, nbr=None):
    p_img = img_source = alpha_slider = None
    if(image is not None):
        p_img, img_source, alpha_slider = viz.makePlotImage(image, title="Image", alpha=150, width=width, nbr=nbr)

    p_treeL = viz.makePlotTree(
        rootL,
        lambda n: n.children,
        {
            "id:": lambda n: n.id,
            "repNode": lambda n: n.repNode,
            "level:": lambda n: n.level,
            #"NumFZs:": lambda n: n.numFlatzones,
            "repFZs": lambda n: n.repCNPs, # lista de índices flat
            "area:": lambda n: n.area,
        },
        lambda n: n.id,
        image_source=img_source,
        alpha_slider=alpha_slider,
        flood_use= None if image is None else 'floodThreshold', 
        rep_label_name='repFZs',
        flood_params={'polarity': 255 if rootL.level < rootL.children[0].level else 0},
        nbr=nbr,
        panel_caption = "max-tree" if rootL.level < rootL.children[0].level else "min-tree",
        panel_width=panel_width
    )
    
    p_treeR = viz.makePlotTree(
        rootR,
        lambda n: n.children,
        {
            "id:": lambda n: n.id,
            "repNode": lambda n: n.repNode,
            "level:": lambda n: n.level,
            #"NumFZs:": lambda n: n.numFlatzones,
            "repFZs": lambda n: n.repCNPs, # lista de índices flat
            "area:": lambda n: n.area,
        },
        lambda n: n.id,
        image_source=img_source,
        alpha_slider=alpha_slider,
        flood_use= None if image is None else 'floodThreshold', 
        rep_label_name='repFZs',
        flood_params={'polarity': 255 if rootR.level < rootR.children[0].level else 0},
        nbr=nbr,
        panel_caption = "max-tree" if rootR.level < rootR.children[0].level else "min-tree",
        panel_width=panel_width
    )


    if(image is not None):
        show(row(p_treeL.panel, column(alpha_slider, p_img), p_treeR.panel) )
    else:
        show( row(p_treeL.panel, p_treeR.panel) )

def showNode(image, N, title="The connected component associated with the node is in red", alpha=255, width=450, nbr=None):
    p = viz.makePlotImagePixels(image, N.pixelsOfCC, title=title, width=width, alpha=alpha, nbr=nbr)
    show(p.panel)

def showImage(image, width=900, nbr=None):
    p = viz.makePlotImage(image, width=width, nbr=nbr)
    show(p.panel)


def showLevelSets(image, width=450):
    bundle = viz.makeLevelSets(image, width=width)
    show( column(bundle.controls[0], bundle.panel) ) # slider em bundle.controls[0]    




def showComponentTreesWithSelectedNodes(rootL, rootR, image, L, tauL, F_λ, F_λb,  panel_width=600, width=500, nbr=None):
    p_img = img_source = alpha_slider = None
    if(image is not None):
        p_img, img_source, alpha_slider = viz.makePlotImage(image, title="Image", width=width, alpha=200, nbr=nbr)

    F_lambda = [n.id for nodes in F_λ.values() for n in nodes]
    F_lambda_b = [n.id for n in F_λb]
    p_treeL = viz.makePlotTreeWithSelectedNodes(
        rootL,
        lambda n: n.children,
        {
            "id:": lambda n: n.id,
            "repNode": lambda n: n.repNode,
            "level:": lambda n: n.level,
            #"NumFZs:": lambda n: n.numFlatzones,
            "repFZs": lambda n: n.repCNPs, # lista de índices flat
            "area:": lambda n: n.area,
        },
        lambda n: n.id,
        image_source=img_source,
        alpha_slider=alpha_slider,
        flood_use= None if image is None else 'floodThreshold', 
        rep_label_name='repFZs',
        flood_params={'polarity': 255 if rootL.level < rootL.children[0].level else 0},
        nbr=nbr,
        tauStar=tauL,
        F_lambda=F_lambda,
        F_lambda_b=F_lambda_b,
        panel_caption = "max-tree" if rootL.level < rootL.children[0].level else "min-tree",
        panel_width=panel_width
    )
    p_treeR = viz.makePlotTreeWithSelectedNodes(
        rootR,
        lambda n: n.children,
        {
            "id:": lambda n: n.id,
            "repNode": lambda n: n.repNode,
            "level:": lambda n: n.level,
            #"NumFZs:": lambda n: n.numFlatzones,
            "repFZs": lambda n: n.repCNPs, # lista de índices flat
            "area:": lambda n: n.area,
        },
        lambda n: n.id,
        image_source=img_source,
        alpha_slider=alpha_slider,
        flood_use= None if image is None else 'floodThreshold', 
        rep_label_name='repFZs',
        flood_params={'polarity': 255 if rootR.level < rootR.children[0].level else 0},
        nbr=nbr,
        tauStar=[L.id],
        panel_caption = "max-tree" if rootR.level < rootR.children[0].level else "min-tree",
        panel_width=panel_width
    )
    if(image is not None):
        show(row(p_treeL.panel, column(alpha_slider, p_img), p_treeR.panel) )
    else:
        show( row(p_treeL.panel, p_treeR.panel) )

