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
    INT = 'int'
    BOOL = 'bool'
    STRING = 'string'
    NIL = 'nil'
    LABEL = 'label'
    TYPE = 'type'
    SYMB = 'symb'


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
    'NOT': CodeCommand('NOT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'INT2CHAR': CodeCommand('INT2CHAR', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB]),
    'STRI2INT': CodeCommand('STRI2INT', [E_ARG_TYPE.VAR, E_ARG_TYPE.SYMB, E_ARG_TYPE.SYMB]),
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
DEFVAR_REGEX = re.compile(r'^DEFVAR\s+\w+', re.IGNORECASE)
# Regular expression to match "LABEL" followed by optional whitespace and "GF@"
LABEL_REGEX = re.compile(r'^LABEL\s+\w+', re.IGNORECASE)


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
        sys.exit(ERROR_OTHER_SYNTAX)


def validate_variable_name(var):
    """
    Validate a variable name according to the specified rules.
    Returns True if the variable name is valid, False otherwise.
    """
    return bool(re.match(VAR_NAME_REGEX, var))


def is_valid_integer(value):
    # Decimal integer regex pattern
    decimal_pattern = r'^[+-]?\d+$'
    # Octal integer regex pattern
    octal_pattern = r'^0[oO][0-7]+$'
    # Hexadecimal integer regex pattern
    hexadecimal_pattern = r'^0[xX][0-9a-fA-F]+$'

    # Check if the value matches any of the integer patterns
    if re.match(decimal_pattern, value) or re.match(octal_pattern, value) or re.match(hexadecimal_pattern, value):
        return True
    else:
        return False


def is_valid_bool(value):
    # Check if the boolean value is either 'true' or 'false'
    return value in ['true', 'false']


def is_valid_nil(value):
    # Check if the value is 'nil'
    return value == 'nil'


def recognize_arg_type(arg):
    if arg is None:
        return None
    elif arg.startswith("GF@") or arg.startswith("LF@") or arg.startswith("TF@"):
        if validate_variable_name(arg[3:]):
            return E_ARG_TYPE.VAR
        else:
            print("Invalid variable name:", arg)
            sys.exit(ERROR_OTHER_SYNTAX)
    elif arg.startswith("int@"):
        if is_valid_integer(arg[len("int@"):]):
            return E_ARG_TYPE.INT
        else:
            print("Invalid integer format:", arg)
            sys.exit(ERROR_OTHER_SYNTAX)
    elif arg.startswith("bool@"):
        if is_valid_bool(arg[len("bool@"):]):
            return E_ARG_TYPE.BOOL
        else:
            print("Invalid boolean format:", arg)
            sys.exit(ERROR_OTHER_SYNTAX)
    elif arg.startswith("string@"):
        return E_ARG_TYPE.STRING
    elif arg.startswith("nil@"):
        if is_valid_nil(arg[len("nil@"):]):
            return E_ARG_TYPE.NIL
        else:
            print("Invalid boolean format:", arg)
            sys.exit(ERROR_OTHER_SYNTAX)
    elif arg in ['int', 'bool', 'string']:
        return E_ARG_TYPE.TYPE
    elif validate_variable_name(arg):
        return E_ARG_TYPE.LABEL
    else:
        return None


def check_type(arg, arg_number, opcode):
    arg_type = recognize_arg_type(arg)
    if arg_type != CODE_COMMANDS[opcode].arg_types[arg_number]:
        # Check if the arg type is a string constant and the expected type is SYMB
        if arg_type in [E_ARG_TYPE.STRING, E_ARG_TYPE.INT, E_ARG_TYPE.BOOL, E_ARG_TYPE.NIL, E_ARG_TYPE.VAR] and CODE_COMMANDS[opcode].arg_types[arg_number] == E_ARG_TYPE.SYMB:
            return  # Allow string constants to satisfy the SYMB requirement
        else:
            print('Wrong argument type:', arg)
            sys.exit(ERROR_OTHER_SYNTAX)


def check_number_of_args(tokens, opcode, line):
    if len(tokens) - 1 != len(CODE_COMMANDS[opcode].arg_types):
        print('Wrong arguments number:', line)
        sys.exit(ERROR_OTHER_SYNTAX)


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
    for line in input_lines[0:]:
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

    # Split the preprocessed lines into individual lines
    lines = preprocessed_lines.split('\n')

    # define_var_and_labels(lines)

    for count, line in enumerate(lines):
        # Process each line
        line = line.strip()

        if count == 0 and line == '.IPPcode24':
            continue

        instruction = parse_instruction(line)
        if instruction[0]:  # Check if the instruction is not None
            instructions.append(instruction)

    # Return the instructions
    return instructions


def parse_instruction(line):
    # Check if the line contains only one opcode
    check_single_opcode(line)

    tokens = line.split()

    # Convert the opcode to uppercase
    opcode = tokens[0].upper()

    if opcode not in CODE_COMMANDS:
        return exit(ERROR_SYNTAX)

    # Check if the number of arguments is correct
    check_number_of_args(tokens, opcode, line)

    args = [tokens[i] if i < len(tokens) else None for i in range(1, 4)]

    # Recognize arg type for each arg and place it in args_type array
    arg_types = [recognize_arg_type(arg) for arg in args]

    # Check argument types after assignment
    for i, arg in enumerate(args):
        if arg is not None:
            check_type(arg, i, opcode)

    return (opcode,) + tuple(args) + tuple(arg_types)


def remove_arg_type_prefix(arg):
    if arg is not None:
        # Check if the argument starts with a recognized prefix
        if arg.startswith("int@") or arg.startswith("bool@") or arg.startswith("string@") or arg.startswith("nil@"):
            # If it does, remove the prefix and return the remaining part
            return arg.split('@', 1)[-1]
    # If the argument is None or doesn't start with a recognized prefix, return it as is
    return arg


def generate_xml(instructions):
    root = ET.Element("program")
    root.set("language", "IPPcode24")
    order = 1
    for instruction in instructions:

        opcode, arg1, arg2, arg3, arg1_type, arg2_type, arg3_type = instruction

        # Remove unnecessary argument type prefixes
        arg1 = remove_arg_type_prefix(arg1)
        arg2 = remove_arg_type_prefix(arg2)
        arg3 = remove_arg_type_prefix(arg3)

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
    instructions = parse_code(preprocessed_lines)

    # Generate XML
    generate_xml(instructions)


if __name__ == "__main__":
    main()
