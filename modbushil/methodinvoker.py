import re
from typing import Any


class MethodInvoker:
    def __init__(self, method_config: dict[str, Any]):
        self.variable = method_config["set"]
        self.action = method_config["action"]
        if self.action == "eval":
            self.expression = method_config["expression"]
            # extract all $(variable) occurrences
            self.required_variables: list[str] = re.findall(
                r"\$\((.*?)\)", self.expression
            )
        elif self.action == "function":
            self.required_variables: list[str] = method_config["parameters"]
            self.function = method_config["function"]
        else:
            raise ValueError(f"Invalid method action: {self.action}")

    def invoke(self, variable_values: dict[str, Any]) -> float:
        if self.action == "eval":
            eval_expression = self.expression
            for var in self.required_variables:  # TODO: optimize
                if var not in variable_values:
                    raise ValueError(
                        f"Variable {var} not provided for method evaluation"
                    )
                eval_expression = eval_expression.replace(
                    f"$({var})", str(variable_values[var])
                )
            return eval(eval_expression)
        elif self.action == "function":
            params = [variable_values[var] for var in self.required_variables]
            return self.function(*params)
        else:
            raise ValueError(f"Invalid method action: {self.action}")
