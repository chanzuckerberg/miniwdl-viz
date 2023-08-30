import sys

import WDL


class MiniWDLParser2:
    """ """

    def __init__(self, wdl_doc):
        self.wdl_doc = wdl_doc
        self.nodes = []
        self.edges = []

    def parse_inputs(self, inputs):
        # TODO
        pass

    def parse_outputs(self, outputs):
        # TODO
        pass

    def get_referee_name(self, referee):
        if isinstance(referee, WDL.Gather):
            return referee.final_referee.workflow_node_id
        else:
            return referee.workflow_node_id

    def parse_input_item(self, input_item, node_ids):
        if isinstance(input_item, WDL.Expr.Ident):
            if (ref_name := self.get_referee_name(input_item.referee)) in node_ids:
                # If referee is not a defined node_id, probably comes from workflow_input
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
        else:
            raise

    def add_node(self, nodes, parent, id, name, type):
        section = (
            parent.name if isinstance(parent, WDL.Workflow) else parent.workflow_node_id
        )
        nodes.append({"id": id, "name": name, "section": section, "type": type})

    def parse_workflow(self, wdl_doc, nodes, edges):
        if isinstance(wdl_doc, WDL.Workflow):
            self.parse_inputs(wdl_doc.inputs)
            for task in wdl_doc.body:
                self.parse_workflow(task, nodes, edges)
            self.parse_outputs(wdl_doc.outputs)

        elif isinstance(wdl_doc, WDL.Call):
            self.add_node(
                nodes=nodes,
                parent=wdl_doc.parent,
                id=wdl_doc.workflow_node_id,
                name=wdl_doc.name,
                type="call",
            )
            for task_name, workflow_input in wdl_doc.inputs.items():
                input_param_list = self.parse_input_item(
                    workflow_input, [node["id"] for node in nodes]
                )
                for input_param in input_param_list:
                    edges.append(
                        {
                            "node_from": input_param["ref"],
                            "node_to": wdl_doc.workflow_node_id,
                            "workflow_ref_name": input_param["name"],
                            "task_ref_name": task_name,
                            "edge_type": input_param["type"],
                        }
                    )
        elif isinstance(wdl_doc, WDL.WorkflowSection):
            self.add_node(
                nodes=nodes,
                parent=wdl_doc.parent,
                id=wdl_doc.workflow_node_id,
                name=str(str(wdl_doc.expr)),
                type="workflow_section",
            )
            for task in wdl_doc.body:
                self.parse_workflow(task, nodes, edges)

        elif isinstance(wdl_doc, WDL.Decl):
            if wdl_doc.expr:
                self.add_node(
                    nodes=nodes,
                    parent=wdl_doc.parent,
                    id=wdl_doc.workflow_node_id,
                    name=wdl_doc.name,
                    type="decl",
                )
                input_param_list = self.parse_input_item(
                    wdl_doc.expr, [node["id"] for node in nodes]
                )
                for input_param in input_param_list:
                    task_name = self.remove_prefix(
                        input_param["name"],
                        self.remove_prefix(input_param["ref"], "call-") + ".",
                    )
                    edges.append(
                        {
                            "node_from": input_param["ref"],
                            "node_to": wdl_doc.workflow_node_id,
                            "workflow_ref_name": input_param["name"],
                            "task_ref_name": task_name,
                            "edge_type": "decl_to",
                        }
                    )

    @staticmethod
    def remove_prefix(string, prefix):
        if string.startswith(prefix):
            return string[len(prefix) :]
        return string

    def parse(self):
        self.parse_workflow(self.wdl_doc.workflow, self.nodes, self.edges)

        for node in self.nodes:
            print(node)

        for edge in self.edges:
            print(edge)


def main():
    input_file = sys.argv[1]
    doc = WDL.load(uri=input_file)
    parser = MiniWDLParser2(doc)
    parser.parse()


if __name__ == "__main__":
    main()
