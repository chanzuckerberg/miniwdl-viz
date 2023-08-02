import sys
import WDL
from miniwdl_parser import MiniWDLParser


def make_id_mapping(edges):
    """Creates a mapping between the nodes and a generated id.
    Could probably move this into the parser script
    """
    id_mapping = {"WorkflowInput": "id0"}
    inputid = condid = declid = 1  # initialize counters
    for edge in edges:
        # if the edge is an input and node is not already in the mapping
        if edge["edge_type"] == "input" and (edge["node_to"] not in id_mapping.keys()):
            id_mapping[edge["node_to"]] = f"id{inputid}"
            inputid += 1
        # the next 2 should only be declared once so we only need to id them once
        elif edge["edge_type"] == "cond":
            id_mapping[edge["node_from"]] = f"if{condid}"
            condid += 1
        elif (edge["edge_type"] == "decl_from") or (edge["edge_type"] == "decl_to"):
            id_mapping[edge["node_from"]] = f"decl{declid}"
            declid += 1
    return id_mapping


def group_edges(edges, suppress_workflow_input=False):
    """Groups edges that start and end from the same nodes together. 
        Could probably replace with pandas or something cleaner
    """
    smol_graph = {}
    for edge in edges:
        if suppress_workflow_input and edge["node_from"] == "WorkflowInput":
            # Sometimes it's hard to see the graph with the WorkflowInput variables 
            # so suppress the outputs
            continue
        if smol_graph.get(
            (edge["node_from"], edge["node_to"], edge["edge_type"]), None
        ):
            # if there is already an edge with the same nodes, 
            # then just append the task name at the end
            smol_graph[
                (edge["node_from"], edge["node_to"], edge["edge_type"])
            ] = list(set(
                smol_graph[(edge["node_from"], edge["node_to"], edge["edge_type"])] + 
                [edge["task_name"]]
                ))
        else:
            smol_graph[(edge["node_from"], edge["node_to"], edge["edge_type"])] = [edge[
                "task_name"
            ]]
    return smol_graph

def create_mermaid_list(id_mapping, smol_graph):
    output = ["flowchart TD"]  # mermaid header and name
    for node, inputs_list in smol_graph.items():
        inputs = ",".join(inputs_list)
        inputs = inputs.replace('"', "")  # replace some string breaking stuff
        if node[2] == "input":
            output.append(
                f"{id_mapping[node[0]]}{{{node[0]}}} --> |{inputs}|{id_mapping[node[1]]}{{{node[1]}}}"
            )
        elif node[2] == "cond":
            output.append(
                f"{id_mapping[node[0]]}[{node[0]}] --> |{inputs}| {id_mapping[node[1]]}{{{node[1]}}}" 
            )
        elif node[2] == "decl_from":
            output.append(
                f"{id_mapping[node[0]]}(({node[0]})) --> |{inputs}| {id_mapping[node[1]]}{{{node[1]}}}"
            )
        elif node[2] == "decl_to":
            output.append(
                f"{id_mapping[node[0]]}{{{node[0]}}} --> |{inputs}| {id_mapping[node[1]]}(({node[1]}))"
            )
    return output
    
def print_mermaid_list(mermaid):
    for ind, row in enumerate(mermaid):
        if ind == 0:
            print(row)
        else:
            print(f"    {row}")
    print()


def main(doc):
    parser = MiniWDLParser(doc)
    parser.parse()
    id_mapping = make_id_mapping(parser.edges)
    smol_graph = group_edges(parser.edges, suppress_workflow_input=False)
    mermaid_list = create_mermaid_list(id_mapping, smol_graph)
    print_mermaid_list(mermaid_list)


if __name__ == "__main__":
    input_file = sys.argv[1]
    doc = WDL.load(uri=input_file)
    main(doc)
