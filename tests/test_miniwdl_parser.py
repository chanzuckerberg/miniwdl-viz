from miniwdl_viz.miniwdl_parser2 import MiniWDLParser2
from os.path import dirname, realpath, join
import WDL
import pytest


@pytest.fixture
def simple_wdl():
    doc = WDL.load(join(dirname(realpath(__file__)), "test_wdls", "simple.wdl"))
    parser = MiniWDLParser2(doc)
    parser.parse()
    return parser


@pytest.fixture
def complex_wdl():
    doc = WDL.load(
        join(
            dirname(realpath(__file__)),
            "test_wdls",
            "joint-discovery-gatk4-version.wdl",
        )
    )
    parser = MiniWDLParser2(doc)
    parser.parse()
    return parser


class TestMiniWDLParser:
    def test_simple_wdl(self, simple_wdl):
        assert len(simple_wdl.nodes) == 3
        assert len(simple_wdl.edges) == 6

    def test_complex_wdl(self, complex_wdl):
        call_nodes = [node for node in complex_wdl.nodes if node["type"] == "call"]
        subsection_nodes = [
            node for node in complex_wdl.nodes if node["type"] == "workflow_section"
        ]
        decl_nodes = [node for node in complex_wdl.nodes if node["type"] == "decl"]

        assert len(call_nodes) == 15
        assert len(subsection_nodes) == 8
        assert len(decl_nodes) == 2
