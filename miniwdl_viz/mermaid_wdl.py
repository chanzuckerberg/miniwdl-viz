import argparse
import sys
import subprocess
import WDL
from miniwdl_viz.py_mermaid import PyMermaid
from miniwdl_viz.miniwdl_parser import MiniWDLParser
import requests
import io
import base64
from PIL import Image
import matplotlib.pyplot as plt


class ParsedWDLToMermaid:
    """Takes a parsed WDL and converts it to a mermaid diagram"""
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
            self.py_mermaid.add_mermaid_edge_id(
                edge["node_from"], edge["node_to"], edge
            )

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

    def show_mermaid_flowchart(self, mermaid_list, plot_time=2, file_output=False):
        mermaid_str = "\n".join(mermaid_list)
        base64_str = base64.b64encode(mermaid_str.encode("ascii")).decode("ascii")
        img = Image.open(
            io.BytesIO(requests.get("https://mermaid.ink/img/" + base64_str).content)
        )
        plt.figure(figsize=(15, 9), dpi=100)
        plt.axis("off")
        plt.imshow(img)
        if file_output:
            output_image = self.output_name.rsplit(".", 1)[0] + ".png"
            plt.savefig(output_image)
        else:
            plt.pause(plot_time)

    def output_mermaid(self, mermaid_list, file_output=False):
        if file_output:
            with open(self.output_name, "w") as output:
                for ind, row in enumerate(mermaid_list):
                    if ind == 0:
                        output.write(f"{row}\n")
                    else:
                        output.write(f"    {row}\n")
        else:
            for ind, row in enumerate(mermaid_list):
                if ind == 0:
                    print(f"{row}")
                else:
                    print(f"    {row}")


def parse_wdl(input_file):
    doc = WDL.load(uri=input_file)
    parser = MiniWDLParser(doc)
    parser.parse()
    return parser

def parsed_wdl_to_mermaid(miniwdl_parser, pwm):
    return pwm.create_mermaid_flowchart(
        miniwdl_parser.workflow_name, miniwdl_parser.nodes, miniwdl_parser.edges
    )

def main():
    arg_parser = argparse.ArgumentParser(
        prog="ParsedWDLToMermaid",
        description=ParsedWDLToMermaid.__doc__,
    )
    arg_parser.add_argument("input")
    arg_parser.add_argument("-o", "--output-file", default="output.mmd")
    arg_parser.add_argument("--show-input-names", action='store_true', default=False, help="hides the input name strings")
    arg_parser.add_argument("--show-workflow-input", action='store_true', default=False, help="suppresses the workflow input node")
    arg_parser.add_argument("--show-hardcoded-variables", action='store_true', default=False, help="suppresses hardcoded variable node")
    arg_parser.add_argument("--flowchart-dir", choices=["TD", "LR"], default="LR", help="direction of the flow chart, TD (top down) or LR (left right)")
    arg_parser.add_argument("--max_input_str_length", type=int, default=200, help="if input names aren't hidden sets a max length for them")

    arg_parser.add_argument("--plot-flowchart", action='store_true', default=False, help="plot flowchart with matplotlib")
    arg_parser.add_argument("--plot-flowchart-file-output", action='store_true', default=False, help="plot outputs flowchart as a png file")
    arg_parser.add_argument("--plot-time", type=int, default=10, help="time to plot flowchart flow default:10")

    arg_parser.add_argument("--print-flowchart", action='store_true', default=False, help="print flowchart to console")
    arg_parser.add_argument("--print-flowchart-file-output", action='store_true', default=False, help="print flowchart to file output_file")



    args = arg_parser.parse_args()

    if args.input.endswith(".wdl"):
        miniwdl_parser = parse_wdl(args.input)

    pwm = ParsedWDLToMermaid(
        flowchart_dir=args.flowchart_dir,
        suppress_workflow_input=(not args.show_workflow_input), 
        suppress_hardcoded_variables=(not args.show_hardcoded_variables),
        max_input_str_length=args.max_input_str_length,
        hide_input_names=(not args.show_input_names),
        output_name=args.output_file,
    )
    mermaid_list = parsed_wdl_to_mermaid(miniwdl_parser, pwm)

    if args.plot_flowchart:
        pwm.show_mermaid_flowchart(mermaid_list=mermaid_list, plot_time=args.plot_time, file_output=args.plot_flowchart_file_output)
    
    if args.print_flowchart:
        pwm.output_mermaid(mermaid_list=mermaid_list, file_output=args.print_flowchart_file_output)


if __name__ == "__main__":
    main()
