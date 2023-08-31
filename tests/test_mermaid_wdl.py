from tests.test_miniwdl_parser import simple_wdl, complex_wdl
from miniwdl_viz.mermaid_wdl import ParsedWDLToMermaid
from os.path import join, dirname, realpath
import hashlib
import os


class TestMermaidWDL:
    def test_simple_mermaid_wdl(self, simple_wdl):
        output_filename = join(dirname(realpath(__file__)), "simple.mmd")
        mw = ParsedWDLToMermaid(
            flowchart_dir="LR",
            suppress_workflow_input=False,
            suppress_hardcoded_variables=True,
            output_name=output_filename,
        )
        mermaid_list = mw.create_mermaid_flowchart(simple_wdl.workflow_name, simple_wdl.nodes, simple_wdl.edges)
        assert (
            mermaid_list[1]
            == 'WorkflowInput(("WorkflowInput")) --> |input_file, docker_image_id| call-add_world{{"add_world"}}'
        )
        assert (
            mermaid_list[2]
            == 'call-add_world{{"add_world"}} --> |input_file| call-add_goodbye{{"add_goodbye"}}'
        )

        mw.output_mermaid(mermaid_list)
        with open(output_filename, "r") as f:
            file = f.read()
        hash = hashlib.md5(file.encode())
        assert hash.hexdigest() == "5447602150e9b75914b5fad0da96bf09"
        os.remove(output_filename)

    def test_complex_mermaid_wdl(self, complex_wdl):
        output_filename = join(dirname(realpath(__file__)), "complex.mmd")
        mw = ParsedWDLToMermaid(
            flowchart_dir="LR",
            suppress_workflow_input=False,
            suppress_hardcoded_variables=True,
            output_name=output_filename,
        )
        mermaid_list = mw.create_mermaid_flowchart(complex_wdl.workflow_name, complex_wdl.nodes, complex_wdl.edges)
        assert (
            mermaid_list[1]
            == 'subgraph scatter-L120C3-idx["range(length(unpadded_intervals))"]'
        )
        assert (
            mermaid_list[-1]
            == 'WorkflowInput(("WorkflowInput")) --> |output_prefix, disk_size, docker, gatk_path| call-GatherMetrics{{"GatherMetrics"}}'
        )

        mw.output_mermaid(mermaid_list)
        with open(output_filename, "r") as f:
            file = f.read()
        hash = hashlib.md5(file.encode())
        assert hash.hexdigest() == "70d17c20397b15e1ddc0b360ec98fa5c"
        os.remove(output_filename)
