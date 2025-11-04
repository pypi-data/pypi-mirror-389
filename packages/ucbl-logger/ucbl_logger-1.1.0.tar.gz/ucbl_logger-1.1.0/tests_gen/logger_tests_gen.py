import ast
import os

# Path to the logger.py file
logger_path = "../ucbl_logger/logger.py"


# Parse the logger.py file and extract function definitions
class LoggerASTParser(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}

    def visit_FunctionDef(self, node):
        # Collect function names and their arguments
        if not node.name.startswith('_'):  # Skip private/magic methods
            arg_names = [arg.arg for arg in node.args.args]
            docstring = ast.get_docstring(node)

            # Handle default values for arguments
            num_defaults = len(node.args.defaults)
            num_args = len(arg_names)
            defaults = [None] * (num_args - num_defaults) + node.args.defaults
            default_values = [d.s if isinstance(d, ast.Constant) else None for d in defaults]

            # Identify mandatory arguments (those without default values)
            mandatory_args = [arg for arg, default in zip(arg_names, default_values) if default is None]

            # Add function info
            self.functions[node.name] = {
                'args': arg_names,
                'mandatory_args': mandatory_args,
                'docstring': docstring,
                'body': node.body
            }
        self.generic_visit(node)


def generate_test_file(functions, output_file="generated_tests/test_logger.py"):
    # Organize the generated test file content
    with open(output_file, 'w') as f:
        f.write("import unittest\n")
        f.write("import logging\n")
        f.write("from io import StringIO\n")
        f.write("from ucbl_logger.logger import UCBLLogger\n\n")
        f.write("class GeneratedTestLogger(unittest.TestCase):\n")
        f.write("    def setUp(self):\n")
        f.write("        self.log_stream = StringIO()\n")
        f.write("        self.logger = UCBLLogger(log_level=logging.INFO)\n")
        f.write("        self.stream_handler = logging.StreamHandler(self.log_stream)\n")
        f.write("        self.logger.logger.addHandler(self.stream_handler)\n")
        f.write("        self.logger.task_type = 'User'\n")
        f.write("        self.logger.stack_level = 2\n\n")
        f.write("    def tearDown(self):\n")
        f.write("        self.logger.logger.handlers = []\n\n")

        # Generate test cases based on the function analysis
        for func, info in functions.items():
            # Test for critical=True if present in args
            if 'critical' in info['args']:
                f.write(f"    def test_{func}_critical(self):\n")
                f.write(f"        # Test {func} with critical=True\n")
                f.write(f"        self.logger.{func}('Critical test', critical=True)\n")
                f.write(f"        log_output = self.log_stream.getvalue()\n")
                f.write(f"        self.assertIn('~CRITICAL RISK~', log_output)\n\n")

            # Test for minor=True if present in args
            if 'minor' in info['args']:
                f.write(f"    def test_{func}_minor(self):\n")
                f.write(f"        # Test {func} with minor=True\n")
                f.write(f"        self.logger.{func}('Minor test', minor=True)\n")
                f.write(f"        log_output = self.log_stream.getvalue()\n")
                f.write(f"        self.assertIn('~MINOR RISK~', log_output)\n\n")

            # Default test for the function with regular log level
            f.write(f"    def test_{func}_default(self):\n")
            f.write(f"        # Test {func} with default parameters\n")
            f.write(f"        self.logger.{func}('Default test')\n")
            f.write(f"        log_output = self.log_stream.getvalue()\n")
            f.write(f"        self.assertIn('Default test', log_output)\n")
            f.write(f"        self.assertIn('[USER_TASK]', log_output)\n\n")

            # Test cases for mandatory arguments
            if info['mandatory_args']:
                args_str = ', '.join([f"'{arg}_value'" for arg in info['mandatory_args']])
                f.write(f"    def test_{func}_mandatory_args(self):\n")
                f.write(f"        # Test {func} with mandatory arguments\n")
                f.write(f"        self.logger.{func}({args_str})\n")
                f.write(f"        log_output = self.log_stream.getvalue()\n")
                f.write(f"        self.assertIn({args_str.split(', ')[0]}, log_output)\n\n")


def main():
    # Read the logger.py file
    with open(logger_path, "r") as f:
        tree = ast.parse(f.read())

    # Parse the AST to extract function names and logic
    parser = LoggerASTParser()
    parser.visit(tree)

    # Generate test cases based on the parsed functions and their parameters
    if not os.path.exists("generated_tests"):
        os.makedirs("generated_tests")
    generate_test_file(parser.functions)


if __name__ == "__main__":
    main()
