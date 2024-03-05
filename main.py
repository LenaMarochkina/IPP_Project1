import re
import getopt
import sys
import xml.etree.ElementTree as ET

ERROR_HEADER = 21
ERROR_SYNTAX = 22
ERROR_OTHER_SYNTAX = 23
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
# Regular expression for a valid variable name
VAR_NAME_REGEX = r'^[a-z-A-Z_\-$&%*!?][\w_\-$&%*!?]*$'
# Regular expression to match "DEFVAR" followed by optional whitespace and "GF@"
DEFVAR_REGEX = r'^DEFVAR\s+\w+'


def check_header(preprocessed_lines):
    first_line = preprocessed_lines.split('\n')[0].strip()

    if not first_line:
        print('Empty input')
        sys.exit(ERROR_HEADER)

    if first_line != '.IPPcode24':
        print('Wrong header:', first_line)
        sys.exit(ERROR_HEADER)


def check_single_opcode(line):
    tokens = line.split()

    # Count the number of opcodes in the line
    num_opcodes = sum(1 for token in tokens if token.upper() in CODE_COMMANDS)

    # If more than one opcode is found, raise an error
    if num_opcodes > 1:
        print("Error: More than one opcode found in the line:", line)
        sys.exit(ERROR_SYNTAX)


def validate_variable_name(var):
    """
    Validate a variable name according to the specified rules.
    Returns True if the variable name is valid, False otherwise.
    """
    return bool(re.match(VAR_NAME_REGEX, var))


def recognize_arg_type(arg):
    if arg is None:
        return None
    elif arg.startswith("GF@") or arg.startswith("LF@") or arg.startswith("TF@"):
        return E_ARG_TYPE.VAR
    elif arg.startswith("int@") or arg.startswith("bool@") or arg.startswith("string@") or arg.startswith("nil@"):
        return E_ARG_TYPE.SYMB
    elif arg.startswith("label@"):
        return E_ARG_TYPE.LABEL
    elif arg in ["int", "bool", "string"]:
        return E_ARG_TYPE.TYPE
    else:
        # If the argument does not match any recognized pattern, return None
        return None


def check_type(arg, arg_number, opcode, global_vars, local_vars):
    if recognize_arg_type(arg) != CODE_COMMANDS[opcode].arg_types[arg_number]:
        print('Wrong argument type:', arg)
        sys.exit(ERROR_SYNTAX)

    if arg and recognize_arg_type(arg) == E_ARG_TYPE.VAR:
        if arg.startswith("GF@") and arg not in global_vars:
            print("Global variable not declared:", arg)
            sys.exit(ERROR_SYNTAX)
        elif arg.startswith("LF@") and arg not in local_vars:
            print("Local variable not declared:", arg)
            sys.exit(ERROR_SYNTAX)


def check_number_of_args(tokens, opcode, line):
    if len(tokens) - 1 != len(CODE_COMMANDS[opcode].arg_types):
        print('Wrong arguments number:', line)
        sys.exit(ERROR_SYNTAX)


def process_constant_string(arg):
    if arg.startswith("string@"):
        arg_value = arg[len("string@"):]  # Extract the value part of the constant string
        arg_value = re.sub(r'\\(\d{3})', lambda m: chr(int(m.group(1))), arg_value)  # Replace escape sequences
        return arg_value  # Return the processed constant string value
    else:
        return arg  # Return the argument unchanged if it's not a constant string with escape sequences


def process_args():
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


def preprocess_input(input_lines):
    preprocessed_lines = []

    # Flag to indicate if the first program line has been encountered
    program_started = False

    # Process the rest of the lines
    for line in input_lines[1:]:
        # Remove comments and strip leading/trailing whitespace
        line = re.sub(r'#.*', '', line).strip()

        # Skip empty lines before the first program line
        if not program_started and not line:
            continue

        # Mark that the first program line has been encountered
        program_started = True

        # Add non-empty lines to the preprocessed lines
        if line:
            preprocessed_lines.append(line)

    # Join the preprocessed lines with newline characters
    return '\n'.join(preprocessed_lines)



def parse_code(preprocessed_lines):
    instructions = []
    global_vars = set()
    local_vars = set()

    # Split the preprocessed lines into individual lines
    lines = preprocessed_lines.split('\n')

    for line in lines:
        # Process each line
        line = line.strip()

        # Check if the line declares global variables
        if re.match(DEFVAR_REGEX, line):
            declaring_global_vars = True
            global_var = line.split()[1]  # Extract only the variable name without 'GF@'
            if global_var:
                global_vars.add(global_var)

        instruction = parse_instruction(line, global_vars, local_vars)
        if instruction[0]:  # Check if the instruction is not None
            instructions.append(instruction)

    # Return the instructions and variable sets
    return instructions, global_vars, local_vars


def parse_instruction(line, global_vars, local_vars):
    # Check if the line contains only one opcode
    check_single_opcode(line)

    tokens = line.split()

    # Convert the opcode to uppercase
    opcode = tokens[0].upper()

    if opcode not in CODE_COMMANDS:
        return None, None, None, None

    # Check if the number of arguments is correct
    check_number_of_args(tokens, opcode, line)

    args = [tokens[i] if i < len(tokens) else None for i in range(1, 4)]

    # Recognize arg type for each arg and place it in args_type array
    arg_types = [recognize_arg_type(arg) for arg in args]

    # Check argument types after assignment
    for i, arg in enumerate(args):
        if arg is not None:
            check_type(arg, i, opcode, global_vars, local_vars)
            # Process constant string with escape sequences
            args[i] = process_constant_string(arg)
            # Validate the variable name

            if arg_types[i] == E_ARG_TYPE.VAR:
                var_name = arg.split('@')[1]  # Extract the variable name part
                if not validate_variable_name(var_name):
                    print(f"Invalid variable name: {var_name}")
                    sys.exit(ERROR_SYNTAX)

    return (opcode,) + tuple(args) + tuple(arg_types)


def generate_xml(instructions):
    root = ET.Element("program")
    root.set("language", "IPPcode24")
    order = 1
    for instruction in instructions:
        opcode, arg1, arg2, arg3, arg1_type, arg2_type, arg3_type = instruction

        instruction_element = ET.SubElement(root, "instruction")
        instruction_element.set("order", str(order))
        instruction_element.set("opcode", opcode)

        # Process argument 1
        if arg1:
            arg1_element = ET.SubElement(instruction_element, "arg1")
            arg1_element.set("type", arg1_type)
            arg1_element.text = arg1

        # Process argument 2
        if arg2:
            arg2_element = ET.SubElement(instruction_element, "arg2")
            arg2_element.set("type", arg2_type)
            arg2_element.text = arg2

        # Process argument 3
        if arg3:
            arg3_element = ET.SubElement(instruction_element, "arg3")
            arg3_element.set("type", arg3_type)
            arg3_element.text = arg3

        order += 1

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    xml_string = ET.tostring(root, encoding="unicode", xml_declaration=True)
    # Strip the trailing '%' character
    xml_string = xml_string.rstrip('%')
    xml_string = xml_string.replace('\t', '  ')
    print(xml_string)


def usage():
    print('Script for parsing IPPcode24 to XML.')
    print('Usage: parse.php [options]')
    print('Options: -h, --help ')


def main():
    process_args()

    # Read input lines
    input_lines = sys.stdin.readlines()

    # Preprocess input
    preprocessed_lines = preprocess_input(input_lines)

    # Check header
    check_header(preprocessed_lines)

    # Parse input to the file
    instructions, global_vars, local_vars = parse_code(preprocessed_lines)
    if not instructions:
        exit(ERROR_SYNTAX)

    # Generate XML
    generate_xml(instructions)

if __name__ == "__main__":
    main()
