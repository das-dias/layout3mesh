import pytest
from pathlib import Path

from trimesh import Scene, Trimesh

from layout3mesh import __version__
from layout3mesh.layout3mesh import load_layout, load_layerstack, render_to_mesh
from layout3mesh.data import LayerStack

def test_version():
    assert __version__ == '0.1.0'


def test_load_layout():
    layout = load_layout("./tests/data/crossed_metal.gds")
    assert layout is not None
    assert len(layout.cells) > 0
    assert layout.top_level() is not None
    assert len(layout.top_level()) == 1
    assert layout.top_level()[0].name == "crossed_metal"
    # TODO: expand tests

def test_load_layerstack():
    layerstack = load_layerstack("./tests/data/mock_layers.ymls")
    assert layerstack is not None
    assert type(layerstack) == LayerStack
    assert len(layerstack.layers) > 0
    assert len(layerstack.layers) == 3
    assert layerstack[(2, 0)] is not None
    assert layerstack[(2, 0)].name == "met1"
    assert layerstack[(1, 0)] is None
    assert layerstack.layers[(2, 0)].metadata is not None
    assert layerstack.layers[(2, 0)].metadata.type == "routing"
    assert layerstack.layers[(2, 0)].metadata.keys == ["Metal1", "M1"]
    # TODO: expand tests
    
    
def test_render_to_mesh():
    layout = load_layout("./tests/data/crossed_metal.gds")
    layerstack = load_layerstack("./tests/data/mock_layers.ymls")
    
    mesh = render_to_mesh(layout, layerstack, topcell="crossed_metal", out="./tests/data/crossed_metal.glb")
    
    assert mesh is not None
    assert type(mesh) == Scene
    assert Path("./tests/data/crossed_metal.glb").exists()