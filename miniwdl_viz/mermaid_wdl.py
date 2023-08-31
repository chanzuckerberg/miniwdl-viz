import sys
import os
import subprocess
import WDL
from miniwdl_viz.py_mermaid import PyMermaid
from miniwdl_viz.miniwdl_parser2 import MiniWDLParser2


class ParsedWDLToMermaid:
    def __init__(
        self,
        group_edges=True,
        hide_input_names=False,
        suppress_workflow_input=False,
        suppress_hardcoded_variables=True,
        flowchart_dir="TD",
        max_input_str_length=200,
        output_name="output.mmd",
    ):
        self.group_edges = group_edges
        self.suppress_workflow_input = suppress_workflow_input
        self.suppress_hardcoded_variables = suppress_hardcoded_variables
        self.output_name = output_name

        self.py_mermaid = PyMermaid(
            hide_input_names=hide_input_names,
            max_length_input_names=max_input_str_length,
            flowchart_dir=flowchart_dir,
        )

    def suppress_node(self, node):
        if self.suppress_workflow_input and node["name"] == "WorkflowInput":
            return True
        elif self.suppress_hardcoded_variables and node["name"] == "HardcodedVariable":
            return True
        return False

    def group_edge(self, edges):
        grouped = {}
        seen = set()

        for edge in edges:
            edge_id_tuple = (edge["node_from"], edge["node_to"])
            seen_tuple = (*edge_id_tuple, edge["task_ref_name"])

            if edge_id_tuple in grouped:
                if seen_tuple not in seen:
                    grouped[edge_id_tuple][
                        "task_ref_name"
                    ] += f", {edge['task_ref_name']}"
            else:
                grouped[edge_id_tuple] = edge
            seen.add(seen_tuple)

        return list(grouped.values())

    def get_node(self, nodes, node_name):
        if node_name in ["WorkflowInput", "HardcodedVariable"]:
            return {"id": node_name, "name": node_name, "type": "input"}
        else:
            nodes_matching = [node for node in nodes if node["id"] == node_name]
            assert len(nodes_matching) == 1
            return nodes_matching[0]

    def add_mermaid_edge(self, nodes, edge):
        node_from = self.get_node(nodes, edge["node_from"])
        if not self.suppress_node(node_from):
            self.py_mermaid.add_mermaid_edge_id(edge["node_from"], edge["node_to"], edge)

    def create_subgraphs(self, workflow_name, nodes):
        for node in nodes:
            if node["type"] == "workflow_section":
                nodes_in_subgraph = [
                    sg_node for sg_node in nodes if sg_node["section"] == node["id"]
                ]
                self.py_mermaid.add_subgraph(
                    node.get("id"), node.get("name"), nodes_in_subgraph
                )
            elif node["section"] == workflow_name:
                self.py_mermaid.add_node(node)

    def create_mermaid_flowchart(self, workflow_name, nodes, edges):
        if self.group_edges:
            edge_map = self.group_edge(edges)
        else:
            edge_map = edges

        self.create_subgraphs(workflow_name, nodes)

        for edge in edge_map:
            self.add_mermaid_edge(nodes, edge)

        return self.py_mermaid.mermaid_list

    def output_mermaid(self, mermaid_list):
        with open(self.output_name, "w") as output:
            for ind, row in enumerate(mermaid_list):
                if ind == 0:
                    output.write(f"{row}\n")
                else:
                    output.write(f"    {row}\n")

    def create_mermaid_diagram(self):
        output_image = self.output_name.rsplit(".", 1)[0] + ".svg"

        # mermaid command. depends on downloading the mermaid-cli
        command = f"mmdc -i {self.output_name} -o {output_image}"

        try:
            completed_process = subprocess.run(
                command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        except subprocess.CalledProcessError as e:
            print(f"Command execution failed with return code {e.returncode}")


def main(doc, output_file="output.md"):
    output_file_md = (
        output_file.lstrip("./").replace("/", "_").rsplit(".", 1)[0] + ".mmd"
    )
    parser = MiniWDLParser2(doc)
    parser.parse()

    # Check if the only nodes remaining are WorkflowInput and HardcodedVariable
    remaining = set([edge["node_from"] for edge in parser.edges]) - {
        "WorkflowInput",
        "HardcodedVariable",
    }

    mw = ParsedWDLToMermaid(
        flowchart_dir="LR",
        suppress_workflow_input=True, #len(remaining) > 0,
        suppress_hardcoded_variables=True,
        max_input_str_length=50,
        hide_input_names=True,
        output_name=output_file_md,
    )
    mermaid_list = mw.create_mermaid_flowchart(parser.workflow_name, parser.nodes, parser.edges)
    mw.output_mermaid(mermaid_list)
    mw.create_mermaid_diagram()


if __name__ == "__main__":
    input_file = sys.argv[1]
    doc = WDL.load(uri=input_file)
    main(doc, input_file)
