from unittest import TestCase

import modbushil.methodinvoker as mi


class TestMethodInvoker(TestCase):
    def test_simple_eval(self):
        config = {"set": "var1", "action": "eval", "expression": "5 + 3"}
        invoker = mi.MethodInvoker(config)
        variable_buffer = {}
        result = invoker.invoke(variable_buffer)
        self.assertEqual(result, 8)
    
    def test_simple_function(self):
        def add():
            return 10 + 15

        config = {
            "set": "sum",
            "action": "function",
            "function": add,
            "parameters": [],
        }
        invoker = mi.MethodInvoker(config)
        variable_buffer = {}
        result = invoker.invoke(variable_buffer)
        self.assertEqual(result, 25)

    def test_eval_with_variables(self):
        config = {
            "set": "result",
            "action": "eval",
            "expression": "$(a) * $(b) + $(c)",
        }
        invoker = mi.MethodInvoker(config)
        variable_buffer = {"a": 2, "b": 3, "c": 4}
        result = invoker.invoke(variable_buffer)
        self.assertEqual(result, 10)

    def test_function_with_parameters(self):
        def multiply(x, y):
            return x * y

        config = {
            "set": "product",
            "action": "function",
            "function": multiply,
            "parameters": ["x", "y"],
        }
        invoker = mi.MethodInvoker(config)
        variable_buffer = {"x": 4, "y": 5}
        result = invoker.invoke(variable_buffer)
        self.assertEqual(result, 20)
    
    def test_lambda_function(self):
        config = {
            "set": "difference",
            "action": "function",
            "function": lambda x, y: x - y,
            "parameters": ["x", "y"],
        }
        invoker = mi.MethodInvoker(config)
        variable_buffer = {"x": 10, "y": 3}
        result = invoker.invoke(variable_buffer)
        self.assertEqual(result, 7)

