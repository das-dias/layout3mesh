from pathlib import Path
from typing import Optional
from collections import OrderedDict

import yaml
import gdstk

import numpy as np
from trimesh import Scene, creation, transformations, exchange
from shapely import Polygon

from .data import *

_LAYOUT_FILE_EXTENSIONS = [".oas", ".oasis", ".gds", ".gdsii"]

_LAYERSTACK_FILE_EXTENSIONS = [".yaml", ".yml", ".ymls"]

_OUT_FILE_EXTENSIONS = [".gltf", ".glb", ".obj", ".stl", ".ply"]

def load_layout(fp: str) -> Optional[gdstk.Library]:
    """Load a layout from a GDSII file.
    Args:
        fp: Path to the GDSII file.
    Returns:
        The top cell of the layout.
    """
    # check if file extension is .oas, .oasis, .gds, or .gdsii
    fp = str(Path(fp).resolve())
    ext = Path(fp).suffix

    assert Path(fp).exists(), f"File {fp} does not exist."

    lib = None
    if ext in _LAYOUT_FILE_EXTENSIONS[:2]:
        # load OASIS file
        lib = gdstk.read_oas(fp)

    elif ext in _LAYOUT_FILE_EXTENSIONS[2:]:
        # load GDSII file
        lib = gdstk.read_gds(fp)
    else:
        raise ValueError(
            f"Unsupported file extension: {ext}, Supported extensions: {_LAYOUT_FILE_EXTENSIONS}"
        )
    return lib


def load_layerstack(fp: str) -> LayerStack:
    """Load a layerstack from a YAML file
        and return a LayerStack Object
        mapping {(ly,dt) : LayerNode}
    Args:
        fp: Path to the YAML file.
    Returns:
        The layerstack.
    """
    fp = str(Path(fp).resolve())

    assert Path(fp).exists(), f"File {fp} does not exist."

    ext = Path(fp).suffix
    if ext not in _LAYERSTACK_FILE_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension: {ext}, Supported extensions: {_LAYERSTACK_FILE_EXTENSIONS}"
        )

    layerstack = {}
    layerstack_yaml = None
    try:
        with open(fp, "r") as f:
            layerstack_yaml = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Could not load layerstack from {fp}.") from e

    # convert layerstack to LayerStack object
    if not layerstack_yaml.get("layers"):
        raise ValueError("Layerstack is missing layers.")

    for layerkey, layer in layerstack_yaml["layers"].items():
        material = None
        properties = None
        metadata = None
        assert layer.get("metadata"), ValueError(f"Layer {layerkey} is missing metadata.")
        if layer.get("metadata"):
            material = Material(
                rgba=layer["metadata"].get("rgba"), text=layer["metadata"].get("text")
            )
            assert layer["metadata"].get("type"), ValueError(f"Layer {layerkey} is missing metadata type.")
            metadata = LayerMetadata(
                type=layer["metadata"].get("type"),
                keys=layer["metadata"].get("keys"),
                material=material,
            )
        
        assert layer.get("properties"), ValueError(f"Layer {layerkey} is missing properties.")
        # check if layer has all required properties
        obligatory_pars = ["ly", "dt"]
        fields = list(map(lambda x: layer["properties"].get(x), obligatory_pars))
        if None in fields:
            raise ValueError(
                f"Layer {layerkey} is missing properties: {[field for field in fields if field is None]}"
            )
        properties = LayerProperties(
            ly=layer["properties"].get("ly"),
            dt=layer["properties"].get("dt"),
            zh=layer["properties"].get("zh"), # z height base required for 3D extrude
            th=layer["properties"].get("th"), # thickness required for 3D extrude
            top=layer["properties"].get("top"), # top layer required for 3D extrude of Vias
            bot=layer["properties"].get("bot"), # bottom layer required for 3D extrude of Vias
        )
        
        lydt = (properties.ly, properties.dt)
        layerstack[lydt] = Layer(
            name=layerkey, lydt=lydt, metadata=metadata, properties=properties
        )
    
    # derive the zh and th properties for Vias, easing the 3D extruding process
    # get all cut type layers
    via_layers = [layer for layer in layerstack.values() if layer.metadata.type == "cut"]
    for via_layer in via_layers:
        top = via_layer.properties.top
        bot = via_layer.properties.bot
        assert top, ValueError(f"Layer {layerkey} is missing top property.")
        assert bot, ValueError(f"Layer {layerkey} is missing bot property.")
        # get the top and bottom layers by name
        top_layer = [layer for layer in layerstack.values() if layer.name == top][0]
        bot_layer = [layer for layer in layerstack.values() if layer.name == bot][0]
        # get the top and bottom layers thicknesses
        bot_th = bot_layer.properties.th
        # get the top and bottom layers heights
        top_zh = top_layer.properties.zh
        bot_zh = bot_layer.properties.zh
        # derive the zh and th properties for Vias
        via_layer.properties.zh = bot_zh + bot_th
        via_layer.properties.th = top_zh - via_layer.properties.zh
            

    return LayerStack(layerstack)


def _is_counter_clockwise(e1: np.ndarray, e2: np.ndarray):
    """routine to determine if
    two consecutive edges are
    clockwise or counter-clockwise
    Args:
        e1 ((x1,y1),(x2,y2)): edge 1
        e2 ((x2,y2),(x3,y3)): edge 2
    Returns:
        bool: True if counter-clockwise, False if clockwise
    """
    vec1 = e1[1] - e1[0]
    vec2 = e2[1] - e2[0]
    return np.cross(vec1, vec2) <= 0


def render_to_mesh(
    layout: gdstk.Library,
    layerstack: LayerStack,
    topcell: Optional[str] = None,
    out: Optional[str] = None,
    cmap: Optional[Dict[Tuple[int, int], Dict[int, Tuple[str, float]]]] = None,
) -> Scene:
    """Render a layout to a 3D file.

    Args:
        layout (gdstk.Library): IC Layout.
        layerstack (LayerStack): Layerstack.
        topcell (Optional[str]): Name of the layout's top cell to render.
        out (Optional[str]): Path to the output SVG file.
        cmap (Optional[Dict[Tuple[int, int], Dict[int, Tuple[str,float]]]]): Color map for each polygon of each layer.
        render_labels (bool): Render labels to SVG surface.
    Returns:
        trimesh.Scene: 3D trimesh Scene rendered from the layout.
    """
    out_ext = None
    if out:
        out_ext = Path(out).suffix
        assert (
            out_ext in _OUT_FILE_EXTENSIONS
        ), f"Unsupported output file format: {out_ext}; Try: {_OUT_FILE_EXTENSIONS}"

    # check if topcell exists
    tcell = max(layout.cells, key=lambda cell: cell.area())
    if topcell not in [cell.name for cell in layout.cells]:
        Warning(f"Topcell {topcell} not found in layout. Rendering largest cell.")
    else:
        tcell = layout[topcell]

    # create 3D scene
    canvas = Scene( base_frame=f"{tcell.name}" ,metadata={"id":f"{tcell.name}"})

    # setup colour mappings for each poly of each layer
    if cmap is None:
        cmap = {}
        for layer, datatype in layerstack.layers.keys():
            layer_cmap = {}
            layer_polys = tcell.get_polygons(layer=layer, datatype=datatype)
            for id, poly in enumerate(layer_polys):
                # must be in 6 digit hexadecimal format + opacity as alpha channel
                mat = layerstack[(layer, datatype)].metadata.material
                layer_cmap[id] = mat.rgba
            cmap[(layer, datatype)] = layer_cmap
    # render polygons to 3D Scene surface
    for layer, datatype in layerstack.layers.keys():
        layer_polys = tcell.get_polygons(layer=layer, datatype=datatype)
        # set the layer, datatype attributes of the polygon
        layer_name = layerstack[(layer, datatype)].name
        layer_canvas = Scene(base_frame=f"{tcell.name}", metadata={"id":f"{layer},{datatype},{layer_name}"})

        assert (
            layerstack[(layer, datatype)].properties.zh is not None
        ), f"Layer {layer},{datatype} is missing property zh."
        assert (
            layerstack[(layer, datatype)].properties.th is not None
        ), f"Layer {layer},{datatype} is missing property th."

        zbot = layerstack[(layer, datatype)].properties.zh
        height = layerstack[(layer, datatype)].properties.th

        for id, poly in enumerate(layer_polys):
            vertices = poly.points
            # create shapely polygon
            edges = list(zip(vertices[:-1], vertices[1:]))
            edge_pairs = list(zip(edges[:-1], edges[1:]))
            # get the counter clockwise edges
            shell_edges = []
            [shell_edges.extend(list(ep)) for ep in edge_pairs if _is_counter_clockwise(*ep)]
            shell_edges = [tuple(map(tuple, e)) for e in shell_edges]
            shell_edges = list(OrderedDict.fromkeys(shell_edges))
            shell = []
            [shell.append(tuple(v)) for e in shell_edges for v in e]
            shell = list(OrderedDict.fromkeys(shell))
            
            # get the clockwise edges
            holes_edges = []
            [holes_edges.extend(list(ep)) for ep in edge_pairs if not _is_counter_clockwise(*ep)]
            holes_edges = [tuple(map(tuple, e)) for e in holes_edges]
            holes_edges = list(OrderedDict.fromkeys(holes_edges))
            # reverse the order of the holes edges
            holes_edges = holes_edges[::-1]
            holes = []
            [holes.append(tuple(v)) for e in holes_edges for v in e]
            holes = list(OrderedDict.fromkeys(holes))
            
            spPoly = Polygon(shell=shell, holes=holes)
            # create 3D polygon from extrusion
            poly3D = creation.extrude_polygon(
                spPoly,
                height,
                transform=transformations.translation_matrix([0, 0, zbot]),
            )
            poly3D.visual.face_colors = cmap[(layer, datatype)][id]
            layer_canvas.add_geometry(
                poly3D,
                node_name=f"{layer},{datatype},{id}",
                metadata={"id":f"{layer},{datatype},{id}"},
                # TODO: explore possibility to add metadata for resistance, equivalent schematic net, etc...
            )
        canvas.add_geometry(layer_canvas, node_name=f"{layer},{datatype}", metadata={"id":f"{layer},{datatype}"})
        
    if out:
        canvas.export(out)

    return canvas
