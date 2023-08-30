class MermaidNode:
    def __init__(self, id, name):
        self.open, self.close = self.set_parens()
        self.id = self.clean_string(id)
        self.name = self.clean_string(name)

    def set_parens(self):
        return None, None

    def __str__(self):
        return f'{self.id}{self.open}"{self.name}"{self.close}'
    
    def __repr__(self):
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
