import sys
import os 
import subprocess
import WDL

from miniwdl_parser2 import MiniWDLParser2


class MermaidNode:
    def __init__(self, id, name):
        self.open, self.close = self.set_parens()
        self.id = self.clean_string(id)
        self.name = self.clean_string(name)

    def set_parens(self):
        return None, None

    def __str__(self):
        return f'{self.id}{self.open}"{self.name}"{self.close}'

    @staticmethod
    def clean_string(text):
        return text.replace('"', "'")


class MermaidInputNode(MermaidNode):
    def set_parens(self):
        return "((", "))"


class MermaidCallNode(MermaidNode):
    def set_parens(self):
        return "{{", "}}"


class MermaidDeclNode(MermaidNode):
    def set_parens(self):
        return ">", "]"


class MermaidSubgraphNode(MermaidNode):
    def set_parens(self):
        return "[", "]"


class MermaidWDL:
    def __init__(
        self,
        group_edges=True,
        hide_input_names=False,
        suppress_workflow_input=False,
        suppress_hardcoded_variables=True,
        flowchart_dir="TD",
        max_input_str_length=200,
        output_name="output.md"
    ):
        self.group_edges = group_edges
        self.hide_input_names = hide_input_names
        self.suppress_workflow_input = suppress_workflow_input
        self.suppress_hardcoded_variables = suppress_hardcoded_variables
        self.flowchart_dir = flowchart_dir
        self.max_input_str_length = max_input_str_length
        self.output_name = output_name

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
                    grouped[edge_id_tuple]["task_ref_name"] += f", {edge['task_ref_name']}"
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

    def create_mm_node(self, node):
        if node.get("type") == "input":
            return str(MermaidInputNode(node.get("id"), node.get("name")))
        elif node.get("type") == "decl":
            return str(MermaidDeclNode(node.get("id"), node.get("name")))
        elif node.get("type") == "call":
            return str(MermaidCallNode(node.get("id"), node.get("name")))
        elif node.get("type") == "workflow_section":
            return str(node.get("id"))

    def create_arrow(self):
        return "-->"

    def create_arrow_text(self, text):
        if self.hide_input_names:
            return ""
        if len(text) > self.max_input_str_length:
            text = text[: self.max_input_str_length] + "..."
        return f"|{text}|"

    def add_mermaid_edge(self, mermaid_list, nodes, edge):
        node_from = self.get_node(nodes, edge["node_from"])
        node_to = self.get_node(nodes, edge["node_to"])
        if not self.suppress_node(node_from):
            mermaid_list.append(
                f"{self.create_mm_node(node_from)} {self.create_arrow()} {self.create_arrow_text(edge['task_ref_name'])} {self.create_mm_node(node_to)}"
            )

    def create_subgraphs(self, mermaid_list, nodes):
        for node in nodes:
            if node["type"] == "workflow_section":
                nodes_in_subgraph = [
                    sg_node for sg_node in nodes if sg_node["section"] == node["id"]
                ]
                mermaid_list.append(
                    f"subgraph {str(MermaidSubgraphNode(node.get('id'), node.get('name')))}"
                )
                for subgraph_node in nodes_in_subgraph:
                    mermaid_list.append(f"{self.create_mm_node(subgraph_node)}")
                mermaid_list.append("end")

    def create_mermaid_flowchart(self, nodes, edges):
        if self.group_edges:
            edge_map = self.group_edge(edges)
        else:
            edge_map = edges

        mermaid_list = [f"flowchart {self.flowchart_dir}"]

        self.create_subgraphs(mermaid_list, nodes)

        for edge in edge_map:
            self.add_mermaid_edge(mermaid_list, nodes, edge)

        with open(self.output_name, "w") as output:
            for ind, row in enumerate(mermaid_list):
                if ind == 0:
                    output.write(f"{row}\n")
                else:
                    output.write(f"    {row}\n")
    
    def create_mermaid_diagram(self):
        output_image = self.output_name.rsplit(".", 1)[0] + ".svg"

        # Define the command you want to run
        command = f"mmdc -i {self.output_name} -o {output_image}"

        # Run the command and capture the output and error streams
        try:
            completed_process = subprocess.run(
                command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        except subprocess.CalledProcessError as e:
            print(f"Command execution failed with return code {e.returncode}")




def main(doc, output_file = "output.md"):
    output_file_md = output_file.lstrip("./").replace("/", "_").rsplit(".", 1)[0] + ".mmd"
    parser = MiniWDLParser2(doc)
    parser.parse()

    # Check if the only nodes remaining are WorkflowInput and HardcodedVariable
    remaining = set([edge["node_from"] for edge in parser.edges]) - {"WorkflowInput", "HardcodedVariable"}


    mw = MermaidWDL(
        flowchart_dir="LR",
        suppress_workflow_input=len(remaining)>0, 
        suppress_hardcoded_variables=True,
        max_input_str_length=50, 
        hide_input_names=True, 
        output_name=output_file_md
    )
    mw.create_mermaid_flowchart(parser.nodes, parser.edges)
    mw.create_mermaid_diagram()


if __name__ == "__main__":
    input_file = sys.argv[1]
    doc = WDL.load(uri=input_file)
    main(doc, input_file)
