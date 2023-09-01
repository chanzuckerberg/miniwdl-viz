import argparse
import yaml
import json
from pathlib import Path

import WDL


class MiniWDLParser2:
    """Parses a miniwdl file into inputs, outputs, nodes, and edges"""

    def __init__(self, wdl_doc):
        self.wdl_doc = wdl_doc
        self.workflow_name = ""
        self.nodes = []
        self.edges = []
        self.inputs = {}
        self.outputs = {}

    def parse_inputs(self, inputs):
        if inputs is None: 
            return
        for input in inputs:
            self.inputs[input.name] = str(input.type)

    def parse_outputs(self, outputs):
        if outputs is None:
            return
        for output in outputs:
            self.outputs[output.name] = str(output.type)

    def get_referee_name(self, referee):
        if isinstance(referee, WDL.Gather):
            return referee.final_referee.workflow_node_id
        else:
            return referee.workflow_node_id

    def parse_input_item(self, input_item, node_ids):
        if isinstance(input_item, WDL.Expr.Ident):
            # If referee is not a defined node_id, probably comes from workflow_input
            if (ref_name := self.get_referee_name(input_item.referee)) in node_ids:
                ref = ref_name
            else:
                ref = "WorkflowInput"
            return [{"name": f"{input_item.name}", "ref": f"{ref}", "type": "input"}]
        elif isinstance(
            input_item,
            (
                WDL.Expr.String,
                WDL.Expr.Int,
                WDL.Expr.Float,
                WDL.Expr.Boolean,
                WDL.Expr.Null,
            ),
        ):
            return [
                {"name": f"{input_item}", "ref": "HardcodedVariable", "type": "input"}
            ]
        elif isinstance(input_item, WDL.Expr.Base):
            names = []
            for child_input_item in input_item.children:
                names.extend(self.parse_input_item(child_input_item, node_ids))
            return names

    def add_node(self, nodes, parent, id, name, type):
        section = (
            parent.name if isinstance(parent, WDL.Workflow) else parent.workflow_node_id
        )
        nodes.append({"id": id, "name": name, "section": section, "type": type})

    def add_edge(self, nodes, edges, input, node_id, task_name=None):
        input_param_list = self.parse_input_item(
            input, [node["id"] for node in nodes]
        )
        for input_param in input_param_list:
            if not task_name:
                task_name = self.remove_prefix(
                        input_param["name"],
                        self.remove_prefix(input_param["ref"], "call-") + ".",
                )

            edges.append(
                {
                    "node_from": input_param["ref"],
                    "node_to": node_id,
                    "workflow_ref_name": input_param["name"],
                    "task_ref_name": task_name,
                    "edge_type": input_param["type"],
                }
            )

    def parse_workflow(self, wdl_doc, nodes, edges):
        """Parse WDL workflow. Handles WDL Workflow, Call, Decl, and WorkflowSection (if/scatter) nodes"""
        if isinstance(wdl_doc, WDL.Workflow):
            """If workflow, parse the inputs, outputs and recursively parse each call"""
            if not self.workflow_name:
                self.workflow_name = wdl_doc.name
            self.parse_inputs(wdl_doc.inputs)
            for task in wdl_doc.body:
                self.parse_workflow(task, nodes, edges)
            self.parse_outputs(wdl_doc.outputs)

        elif isinstance(wdl_doc, WDL.Call):
            """If Call, add the node and parse each input item to determine the type and referee"""
            self.add_node(
                nodes=nodes,
                parent=wdl_doc.parent,
                id=wdl_doc.workflow_node_id,
                name=wdl_doc.name,
                type="call",
            )
            for task_name, workflow_input in wdl_doc.inputs.items():
                self.add_edge(nodes, edges, workflow_input, wdl_doc.workflow_node_id, task_name)

        elif isinstance(wdl_doc, WDL.WorkflowSection):
            """If WorkflowSection (if/scatter), add node and recurse on each call in the section"""
            self.add_node(
                nodes=nodes,
                parent=wdl_doc.parent,
                id=wdl_doc.workflow_node_id,
                name=str(str(wdl_doc.expr)),
                type="workflow_section",
            )
            self.add_edge(nodes, edges, wdl_doc.expr, wdl_doc.workflow_node_id)
            for task in wdl_doc.body:
                self.parse_workflow(task, nodes, edges)

        elif isinstance(wdl_doc, WDL.Decl):
            """If Decl, add node, then parse edges to add the type and refree"""
            if wdl_doc.expr:
                self.add_node(
                    nodes=nodes,
                    parent=wdl_doc.parent,
                    id=wdl_doc.workflow_node_id,
                    name=wdl_doc.name,
                    type="decl",
                )
                self.add_edge(nodes, edges, wdl_doc.expr, wdl_doc.workflow_node_id)

    @staticmethod
    def remove_prefix(string, prefix):
        if string.startswith(prefix):
            return string[len(prefix) :]
        return string

    def parse(self):
        self.parse_workflow(self.wdl_doc.workflow, self.nodes, self.edges)

    def to_dict(self):
        return {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "nodes": self.nodes,
            "edges": self.edges
        }

def write_output(filename, out_type, dict):
    with open(f"{filename}.{out_type}", "w") as f:
        if out_type == "yaml":
            yaml.dump(
                dict, 
                f,
                sort_keys=False
            )
        elif out_type == "json":
            json.dump(
                dict,
                f,
                indent=4
            )

def main():
    arg_parser = argparse.ArgumentParser(
        prog="MiniWDLParser",
        description="Parses a miniwdl file into inputs, outputs, nodes, and edges",
    )
    arg_parser.add_argument("input_wdl")
    arg_parser.add_argument("-d", "--output-dir")
    arg_parser.add_argument("-o", "--output-file")
    arg_parser.add_argument("-j", "--json-output", action='store_true', default=False)

    args = arg_parser.parse_args()

    doc = WDL.load(uri=args.input_wdl)
    parser = MiniWDLParser2(doc)
    parser.parse()

    out_type = "json" if args.json_output else "yaml"
    filename = args.output_file if args.output_file else Path(args.input_wdl).stem 
    write_output(filename, out_type, parser.to_dict())
    

if __name__ == "__main__":
    main()
