import WDL
import re

SELECT_ALL = "select_all"
SELECT_FIRST = "select_first"
DEFINED = "defined"
FLATTEN = "flatten"
LENGTH = "length"
FLOOR = "floor"
DIV = "_div"
AT = "_at"
READ_LINES = "read_lines"
GLOB = "glob"

function_map = {"_eqeq": " == ", "_neq": " != ", "_land": " && ", "_lte": " <= "}


class MiniWDLParser:
    """

    TODO: Support function declarations (eg. select_first)
    TODO: add edges in the items
    """

    def __init__(self, wdl_doc):
        self.wdl_doc = wdl_doc
        self.edges = []
        self.declarations = {}

    def parse_workflow_task(self, task):
        """parses a task in a workflow
        a task can be one of either:
        Call,
        Conditional,
        Declaration
        returns a list of parsed tasks
        """
        if isinstance(task, WDL.Tree.Call):
            return self.read_call_task(task)
        elif isinstance(task, WDL.Tree.Conditional) or isinstance(
            task, WDL.Tree.Scatter
        ):
            return self.read_conditional_task(task)
        elif isinstance(task, WDL.Tree.Decl):
            return self.read_declaration_task(task)
        else:
            breakpoint()
            raise Exception(f"Unsupported workflow task type")

    ###################
    ### Read Tasks ####
    ###################

    def read_conditional_task(self, conditional):
        """parses a conditional task
        a conditional task is an "if" condition that contains
        tasks to run
        """
        tasks = []
        cond_string = self.parse_conditional_item(conditional.expr)
        for item in conditional.body:
            ## TODO: fix issue of nested if statements
            parsed_items = self.parse_workflow_task(item)
            for item in parsed_items:
                self.edges.append(
                    {
                        "node_from": cond_string,
                        "node_to": item["name"],
                        "workflow_name": "true",
                        "task_name": "true",
                        "edge_type": "cond",
                    }
                )
            tasks.extend(parsed_items)

        return tasks

    def read_declaration_task(self, declaration):
        decl = {"name": declaration.name, "inputs": [], "type": type(declaration)}

        expression = declaration.expr
        parsed_expression = []
        if expression is None:
            """If input declaration is outside of the input section
            (not recommended)
            """
            return [decl]
        elif type(expression) == WDL.Expr.IfThenElse:
            parsed_expression.extend(self.parse_input_item(expression.consequent))
            parsed_expression.extend(self.parse_input_item(expression.alternative))
            # declaration name is the name of the variable being declared
            self.declarations[declaration.name] = "if_then_else"
            decl["inputs"] = parsed_expression
        else:
            if hasattr(expression, "function_name"):
                parsed_expression = self.parse_input_item(expression)
                operator = function_map.get(expression.function_name, "")
                expression_name = operator.join(
                    [
                        re.sub('\(|\)|"', "_", str(argument))
                        for argument in expression.arguments
                    ]
                )
                self.declarations[declaration.name] = str(expression_name)

        for reference_string in parsed_expression:
            output_from, output_var, intype = self.create_node_variables(
                reference_string=reference_string, intype="decl_to"
            )

            self.edges.append(
                {
                    "node_from": output_from,
                    "node_to": self.declarations[declaration.name],
                    "workflow_name": output_var,
                    "task_name": output_var,
                    "edge_type": intype,
                }
            )
        return [decl]

    def read_call_task(self, call):
        task = {"name": call.name, "inputs": [], "type": type(call)}
        # For each input to the call
        for short_name, reference in call.inputs.items():
            # eg. short_name = reads1_fastq
            # eg. reference = fastp_qc.fastp1_fastq

            reference_strings = self.parse_input_item(reference)
            for reference_string in reference_strings:
                output_from, output_var, intype = self.create_node_variables(
                    reference_string=reference_string, intype="input"
                )
                self.edges.append(
                    {
                        "node_from": output_from,
                        "node_to": call.name,
                        "workflow_name": output_var,
                        "task_name": short_name,
                        "edge_type": intype,
                    }
                )
                # add to files list
                key = ".".join([output_from, output_var])
                task["inputs"].append(key)
        return [task]

    ###################
    ### Parse Items ###
    ###################

    def parse_input_item(self, reference):
        if isinstance(reference, WDL.Expr.Get):
            return self.parse_get_expression(reference)
        elif isinstance(reference, WDL.Expr.Apply):
            return self.parse_apply_expression(reference)
        elif isinstance(reference, WDL.Expr.Array):
            return self.parse_array_expression(reference)
        elif isinstance(reference, WDL.Expr.IfThenElse):
            return self.parse_if_then_else_expression(reference)
        elif isinstance(
            reference,
            (
                WDL.Expr.Ident,
                WDL.Expr.String,
                WDL.Expr.Int,
                WDL.Expr.Float,
                WDL.Expr.Boolean,
                WDL.Expr.Null,
            ),
        ):
            # TODO: add hard-coded constants to edges
            return [str(reference)]  # ignore hard-coded constants
        breakpoint()

        raise Exception(f"Unsupported input item: {reference}")

    def parse_if_then_else_expression(self, if_else_expression):
        parsed_expression = []
        parsed_expression.extend(self.parse_input_item(if_else_expression.consequent))
        parsed_expression.extend(self.parse_input_item(if_else_expression.alternative))
        return parsed_expression

    def parse_get_expression(self, get_exp):
        expression = get_exp.expr
        if isinstance(expression, WDL.Expr.Ident):
            return [str(expression.name)]
        else:
            raise Exception(f"Unsupported get expression")

    def parse_apply_expression(self, apply_exp):
        function_name = str(apply_exp.function_name)
        if function_name == DEFINED:
            return []
        else:
            return self.parse_array_expression(apply_exp.arguments[0])

    def parse_array_expression(self, array_exp):
        items = []
        for item in array_exp.children:
            items.extend(self.parse_input_item(item))
        return items

    def parse_conditional_item(self, expr):
        # TODO: add function_names
        # Try to add function to `parse_input_item`
        if type(expr) == WDL.Expr.Get:
            return ",".join(self.parse_input_item(expr))

        operator = function_map.get(expr.function_name, "")

        return operator.join(
            [re.sub('\(|\)|"', "_", str(argument)) for argument in expr.arguments]
        )

    ######################
    ### Misc Functions ###
    ######################

    def create_node_variables(self, reference_string, intype="input"):
        if reference_string.startswith('"') and reference_string.endswith('"'):
            return "HardcodedInput", reference_string, intype

        expression_components = reference_string.split(".")

        if (
            len(expression_components) > 1
        ):  # The file comes from another task in this stage
            return expression_components[0], expression_components[1], intype
        elif self.declarations.get(
            reference_string, None
        ):  # If the variable is a declaration
            # breakpoint()
            return (
                self.declarations[reference_string],
                str(reference_string),
                "decl_from",
            )
        else:
            return "WorkflowInput", reference_string, intype

    def parse(self):
        for task in self.wdl_doc.workflow.body:
            self.parse_workflow_task(task)
