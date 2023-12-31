from miniwdl_viz.mermaid_node import (
    MermaidCallNode,
    MermaidDeclNode,
    MermaidInputNode,
    MermaidSubgraphNode,
)


class PyMermaid:
    def __init__(
        self,
        hide_input_names=False,
        max_length_input_names=200,
        flowchart_dir="TD",
        style_classes="classDef done fill:#f96",
    ):
        self.hide_input_names = hide_input_names
        self.max_length_input_names = max_length_input_names
        self.flowchart_dir = flowchart_dir
        self.node_tracking = {}
        self.mermaid_list = [f"flowchart {self.flowchart_dir}"]
        self.mermaid_list.append(style_classes)

    def create_arrow(self):
        return "-->"

    def create_arrow_text(self, text):
        if self.hide_input_names:
            return ""
        if len(text) > self.max_length_input_names:
            text = text[: self.max_length_input_names] + "..."
        return f"|{text}|"

    def create_mm_node(self, node):
        if node.get("type") == "input":
            return MermaidInputNode(node.get("id"), node.get("name"))
        elif node.get("type") == "decl":
            return MermaidDeclNode(node.get("id"), node.get("name"))
        elif node.get("type") == "call":
            return MermaidCallNode(node.get("id"), node.get("name"))
        elif node.get("type") == "workflow_section":
            return str(node.get("id"))

    def add_mermaid_edge(self, node_from, node_to, edge):
        self.mermaid_list.append(
            f"{self.create_mm_node(node_from)} {self.create_arrow()} {self.create_arrow_text(edge['task_ref_name'])} {self.create_mm_node(node_to)}"
        )

    def add_mermaid_edge_id(self, id_from, id_to, edge):
        self.mermaid_list.append(
            f"{id_from} {self.create_arrow()} {self.create_arrow_text(edge['task_ref_name'])} {id_to}"
        )

    def add_subgraph(self, id, name, subgraph_nodes):
        self.mermaid_list.append(f"subgraph {MermaidSubgraphNode(id, name)}")
        for subgraph_node in subgraph_nodes:
            self.add_node(subgraph_node)
        self.mermaid_list.append("end")

    def set_node_class(self, node_id, node_class="done"):
        node_ind = self.node_tracking.get(node_id)
        if not node_ind:
            return

        self.mermaid_list[node_ind] = f"{self.mermaid_list[node_ind]}:::{node_class}"

    def add_node(self, node):
        self.node_tracking[node["id"]] = len(self.mermaid_list)
        self.mermaid_list.append(f"{self.create_mm_node(node)}")
