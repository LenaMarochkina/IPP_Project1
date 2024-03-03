import re
import getopt
import sys
import xml.etree.ElementTree as ET

ERROR_HEADER = 21
ERROR_OPCODE = 22
ERROR_SYNTAX = 23
ERROR_OPEN_FILE = 11


# Enum for argument types
class E_ARG_TYPE:
    VAR = 'var'
    SYMB = 'symb'
    LABEL = 'label'
    TYPE = 'type'


# Class to represent command with opcode and expected argument types
class CodeCommand:
    def __init__(self, opcode, arg_types):
        self.opcode = opcode
        self.arg_types = arg_types


# Dictionary to store predefined commands with their argument types
CODE_COMMANDS = {
    'MOVE': CodeCommand('MOVE', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'CREATEFRAME': CodeCommand('CREATEFRAME', []),
    'PUSHFRAME': CodeCommand('PUSHFRAME', []),
    'POPFRAME': CodeCommand('POPFRAME', []),
    'DEFVAR': CodeCommand('DEFVAR', [E_ARG_TYPE.VAR]),
    'CALL': CodeCommand('CALL', [E_ARG_TYPE.LABEL]),
    'RETURN': CodeCommand('RETURN', []),
    'PUSHS': CodeCommand('PUSHS', [E_ARG_TYPE.SYMB]),
    'POPS': CodeCommand('POPS', [E_ARG_TYPE.VAR]),
    'ADD': CodeCommand('ADD', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'SUB': CodeCommand('SUB', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'MUL': CodeCommand('MUL', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'IDIV': CodeCommand('IDIV', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'LT': CodeCommand('LT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'GT': CodeCommand('GT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'EQ': CodeCommand('EQ', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'AND': CodeCommand('AND', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'OR': CodeCommand('OR', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'NOT': CodeCommand('NOT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'INT2CHAR': CodeCommand('INT2CHAR', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'STRI2INT': CodeCommand('STRI2INT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'READ': CodeCommand('READ', [E_ARG_TYPE.VAR, E_ARG_TYPE.TYPE]),
    'WRITE': CodeCommand('WRITE', [E_ARG_TYPE.SYMB]),
    'CONCAT': CodeCommand('CONCAT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'STRLEN': CodeCommand('STRLEN', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'GETCHAR': CodeCommand('GETCHAR', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'SETCHAR': CodeCommand('SETCHAR', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'TYPE': CodeCommand('TYPE', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'LABEL': CodeCommand('LABEL', [E_ARG_TYPE.LABEL]),
    'JUMP': CodeCommand('JUMP', [E_ARG_TYPE.LABEL]),
    'JUMPIFEQ': CodeCommand('JUMPIFEQ', [E_ARG_TYPE.LABEL, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'JUMPIFNEQ': CodeCommand('JUMPIFNEQ', [E_ARG_TYPE.LABEL, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
    'EXIT': CodeCommand('EXIT', [E_ARG_TYPE.SYMB]),
    'DPRINT': CodeCommand('DPRINT', [E_ARG_TYPE.SYMB]),
    'BREAK': CodeCommand('BREAK', [])
}

# Regular expressions for tokenizing the code
TOKEN_REGEX = r'(DEFVAR|MOVE|LABEL|JUMPIFEQ|WRITE|CONCAT|CREATEFRAME|PUSHFRAME|POPFRAME|CALL|RETURN|PUSHS|POPS|ADD|SUB|MUL|IDIV|LT|GT|EQ|AND|OR|NOT|INT2CHAR|STRI2INT|READ|STRLEN|GETCHAR|SETCHAR|TYPE|JUMP|JUMPIFEQ|JUMPIFNEQ|EXIT|DPRINT|BREAK)\s+([^\s]+)\s*([^\s]+)?\s*([^\s#]+)?'
LABEL_REGEX = r'^[^\s]+$'
STRING_REGEX = r'^string@(.+)$'


def recognize_arg_type(arg):
    if arg.startswith("GF@") or arg.startswith("LF@") or arg.startswith("TF@"):
        return E_ARG_TYPE.VAR
    elif arg.startswith("int@") or arg.startswith("bool@") or arg.startswith("string@"):
        return E_ARG_TYPE.SYMB
    elif arg.startswith("label@"):
        return E_ARG_TYPE.LABEL
    elif arg in ["int", "bool", "string"]:
        return E_ARG_TYPE.TYPE
    else:
        # If the argument does not match any recognized pattern, return None
        return None


def check_type(arg, arg_number, opcode):
    if recognize_arg_type(arg) != CODE_COMMANDS[opcode].arg_types[arg_number]:
        print('Wrong argument type:', arg)
        sys.exit(ERROR_OPCODE)


def parse_instruction(line):
    tokens = line.split()

    if tokens[0] not in CODE_COMMANDS:
        return None, None, None, None

    opcode = tokens[0]

    if len(tokens) - 1 != len(CODE_COMMANDS[opcode].arg_types):
        print('Wrong arguments number:', line)
        sys.exit(ERROR_OPCODE)

    args = [tokens[i] if i < len(tokens) else None for i in range(1, 4)]

    # Check argument types after assignment
    for i, arg in enumerate(args):
        if arg is not None:
            check_type(arg, i, opcode)

    return (opcode,) + tuple(args)


def parse_code():
    instructions = []
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        opcode, arg1, arg2, arg3 = parse_instruction(line)
        if opcode:
            instructions.append((opcode, arg1, arg2, arg3))
    return instructions


def convert_string(string):
    match = re.match(STRING_REGEX, string)
    if match:
        return match.group(1)
    else:
        return None


def generate_xml(instructions):
    root = ET.Element("program")
    root.set("language", "IPPcode24")
    order = 1
    for opcode, arg1, arg2, arg3 in instructions:
        instruction = ET.SubElement(root, "instruction")
        instruction.set("order", str(order))
        instruction.set("opcode", opcode)

        # Process argument 1
        if arg1:
            arg1_element = ET.SubElement(instruction, "arg1")
            arg1_element.set("type", "string" if convert_string(arg1) else "var")
            if convert_string(arg1):
                arg1_element.text = convert_string(arg1)
            else:
                arg1_element.text = arg1

        # Process argument 2
        if arg2:
            arg2_element = ET.SubElement(instruction, "arg2")
            arg2_element.set("type", "string" if convert_string(arg2) else "var")
            if convert_string(arg2):
                arg2_element.text = convert_string(arg2)
            else:
                arg2_element.text = arg2

        # Process argument 3
        if arg3:
            arg3_element = ET.SubElement(instruction, "arg3")
            arg3_element.set("type", "string" if convert_string(arg3) else "var")
            if convert_string(arg3):
                arg3_element.text = convert_string(arg3)
            else:
                arg3_element.text = arg3

        order += 1

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(sys.stdout, encoding="unicode", xml_declaration=True)


def remove_comments(lines):
    return [re.sub(r'#.*', '', line).strip() for line in lines]


def usage() :
    print('Script for parsing IPPcode24 to XML.')
    print('Usage: parse.php [options]')
    print('Options: -h, --help ')


def process_args() :
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()


def check_header():
    try:
        first_line = input().strip()
    except EOFError:
        print('Empty input')
        sys.exit(ERROR_HEADER)

    if first_line != '.IPPcode24':
        print('Wrong header:', first_line)
        sys.exit(ERROR_HEADER)


def main() :
    process_args()

    # Check the first line is correct
    try:
        check_header()
    except (ValueError, IOError) as e:
        print("Error:", str(e))
        sys.exit(ERROR_OPEN_FILE)

    # Parse input to the file
    instructions = parse_code()
    if not instructions:
        exit(ERROR_SYNTAX)

    # Generate XML
    generate_xml(instructions)


if __name__ == "__main__":
    main()
