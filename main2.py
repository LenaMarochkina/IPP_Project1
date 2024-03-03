import sys
import re
from enum import Enum
import getopt
import xml.dom.minidom

class OperandTypes(Enum):
    VAR = "var"
    SYMB = "symb"
    TYPE = "type"
    LABEL = "label"

class ErrorCodes(Enum):
    ERR_PARAMETER = 10
    ERR_INPUT = 11
    ERR_OUTPUT = 12
    ERR_HEADER = 21
    ERR_SRC_CODE = 22
    ERR_SYNTAX = 23
    ERR_INTERNAL = 99
    EXIT_SUCCESS = 0

class ErrorHandler:
    @staticmethod
    def exit_with_error(err_code, message):
        sys.stderr.write(f"\033[31m[{err_code.name}]\033[0m {message}({err_code.value}) \n")
        sys.exit(err_code.value)

class Validators:
    @staticmethod
    def is_header(line):
        return line is not None and line.lower() == ".ippcode23"

    @staticmethod
    def is_var(var):
        if "@" not in var:
            return False
        frame, name = var.split("@")
        if frame not in ["GF", "TF", "LF"]:
            return False
        return Validators.is_label(name)

    @staticmethod
    def is_symb(symb):
        if "@" not in symb:
            return False
        type, literal = symb.split("@")
        if not Validators.is_type(type):
            return Validators.is_var(symb)
        if type == "int":
            return bool(re.match(r"^(([-+]?\d+)|(0[oO]?[0-7]+)|(0[xX][0-9a-fA-F]+))$", literal))
        elif type == "bool":
            return bool(re.match(r"^(true|false)$", literal))
        elif type == "nil":
            return bool(re.match(r"^nil$", literal))
        elif type == "string":
            return not bool(re.match(r"^.*(\\\\(?!\d\d\d)).*$/u", literal))
        return True

    @staticmethod
    def is_type(type):
        return bool(re.match(r"^(int|bool|string|nil)$", type))

    @staticmethod
    def is_label(label):
        return bool(re.match(r"^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", label))

class InstructionRule:
    def __init__(self, *operand_types):
        self.operands = list(operand_types)

    def get_operands(self):
        return self.operands

    def has_no_operands(self):
        return not bool(self.operands)

INSTRUCTION_RULES = {
    "move": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB),
    "createframe": InstructionRule(),
    "pushframe": InstructionRule(),
    "popframe": InstructionRule(),
    "defvar": InstructionRule(OperandTypes.VAR),
    "call": InstructionRule(OperandTypes.LABEL),
    "return": InstructionRule(),

    "pushs": InstructionRule(OperandTypes.SYMB),
    "pops": InstructionRule(OperandTypes.VAR),
    "add": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "sub": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "mul": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "idiv": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "lt": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "gt": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "eq": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "and": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "or": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "not": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB),
    "int2char": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB),
    "stri2int": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),

    "read": InstructionRule(OperandTypes.VAR, OperandTypes.TYPE),
    "write": InstructionRule(OperandTypes.SYMB),

    "concat": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "strlen": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB),
    "getchar": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),
    "setchar": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB, OperandTypes.SYMB),

    "type": InstructionRule(OperandTypes.VAR, OperandTypes.SYMB),

    "label": InstructionRule(OperandTypes.LABEL),
    "jump": InstructionRule(OperandTypes.LABEL),
    "jumpifeq": InstructionRule(OperandTypes.LABEL, OperandTypes.SYMB, OperandTypes.SYMB),
    "jumpifneq": InstructionRule(OperandTypes.LABEL, OperandTypes.SYMB, OperandTypes.SYMB),
    "exit": InstructionRule(OperandTypes.SYMB),

    "dprint": InstructionRule(OperandTypes.SYMB),
    "break": InstructionRule(),
}

class Formatter:
    @staticmethod
    def format_line(line):
        if not isinstance(line, str):
            return False

        line = Formatter.remove_ending(line)
        line = Formatter.remove_comments(line)
        line = Formatter.remove_empty(line)

        return line

    @staticmethod
    def remove_ending(line):
        return line.rstrip('\n')

    @staticmethod
    def remove_comments(line):
        cut_line = line.find("#")
        if cut_line == -1:
            return line.strip()
        return line[:cut_line].strip()

    @staticmethod
    def remove_empty(line):
        if re.match(r"^\s*$", line):
            return None
        return line

class InputReader(Formatter):
    def __init__(self):
        self.input = []

    def get_input(self):
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            formatted_line = self.format_line(line)
            if formatted_line is not None:
                self.input.append(formatted_line)
        return self.input

class Operand:
    def __init__(self, operand, type):
        if type == OperandTypes.SYMB:
            if Validators.is_var(operand):
                self.type, self.value = "var", operand
            elif Validators.is_symb(operand):
                self.type, self.value = operand.split("@")
            else:
                pass
        else:
            self.type = type.value
            self.value = operand

class Instruction:
    general_order = 1

    def __init__(self, destructured_line):
        self.name = destructured_line.pop(0).lower()
        self.operands = []

        if self.name not in INSTRUCTION_RULES:
            ErrorHandler.exit_with_error(ErrorCodes.ERR_SRC_CODE, "instruction does not exist")

        instruction_rule = INSTRUCTION_RULES[self.name]

        if len(destructured_line) != len(instruction_rule.get_operands()):
            ErrorHandler.exit_with_error(ErrorCodes.ERR_SYNTAX, "Invalid number of operands")

        for key, operand in enumerate(instruction_rule.get_operands()):
            if operand == OperandTypes.VAR and not Validators.is_var(destructured_line[key]):
                ErrorHandler.exit_with_error(ErrorCodes.ERR_SYNTAX, "Invalid variable")
            if operand == OperandTypes.SYMB and not Validators.is_symb(destructured_line[key]):
                ErrorHandler.exit_with_error(ErrorCodes.ERR_SYNTAX, "Invalid constant")
            if operand == OperandTypes.TYPE and not Validators.is_type(destructured_line[key]):
                ErrorHandler.exit_with_error(ErrorCodes.ERR_SYNTAX, "Invalid type")
            if operand == OperandTypes.LABEL and not Validators.is_label(destructured_line[key]):
                ErrorHandler.exit_with_error(ErrorCodes.ERR_SYNTAX, "Invalid label")

            self.operands.append(Operand(destructured_line[key], operand))

        self.order = Instruction.general_order
        Instruction.general_order += 1

    def get_name(self):
        return self.name.upper()

    def get_operands(self):
        return self.operands

    def get_order(self):
        return self.order

class InputAnalyser:
    def __init__(self, input):
        self.input = input
        self.instructions = []

    def get_instructions(self):
        if len(self.input) == 0:
            ErrorHandler.exit_with_error(ErrorCodes.ERR_HEADER, "invalid header")
        if not Validators.is_header(self.input[0]):
            ErrorHandler.exit_with_error(ErrorCodes.ERR_HEADER, "invalid header")

        del self.input[0]

        for line in self.input:
            self.instructions.append(Instruction(re.split(r"\s+", line)))

        return self.instructions

class XMLGenerator:
    def __init__(self):
        self.output = ""
        self.program = ""

    def generate_instruction(self, instruction):
        instruction_template = f"<instruction order=\"{instruction.get_order()}\" opcode=\"{instruction.get_name()}\">"
        for key, operand in enumerate(instruction.get_operands()):
            operand_template = f"<arg{key+1} type=\"{operand.type}\">{operand.value}</arg{key+1}>"
            instruction_template += operand_template
        instruction_template += "</instruction>"
        self.program += instruction_template

    def generate(self, instructions):
        for instruction in instructions:
            self.generate_instruction(instruction)
        self.output = f"<program language=\"IPPcode23\">{self.program}</program>"
        return self.output

class OutputGenerator(XMLGenerator):
    def generate(self, instructions):
        for instruction in instructions:
            self.generate_instruction(instruction)
        self.output = f"<program language=\"IPPcode23\">{self.program}</program>"
        return self.output

if __name__ == "__main__":
    shortopts = "h"
    longopts = ["help"]

    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError:
        ErrorHandler.exit_with_error(ErrorCodes.ERR_PARAMETER, "Invalid options")

    if len(opts) == 1 and ("-h", "") in opts:
        print("\n   Welcome to IPPCode23 parser!\n"
              "   Script takes IPPCode23 as input, creates XML representation (encoding UTF-8)\n"
              "   and sends it to output.\n"
              "\n   Usage: python parser.py [options] < [file]\n"
              "\n   Default options:\n"
              "     --help or -h\tprints help info\n")
        sys.exit(ErrorCodes.EXIT_SUCCESS.value)

    reader = InputReader()
    input_lines = reader.get_input()

    inputAnalyser = InputAnalyser(input_lines)
    instructions = inputAnalyser.get_instructions()

    output_generator = OutputGenerator()
    output = output_generator.generate(instructions)

    print(output)
    sys.exit(ErrorCodes.EXIT_SUCCESS.value)
