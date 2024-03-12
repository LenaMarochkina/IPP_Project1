## IPPcode24 to XML Converter

This script serves as a tool to convert IPPcode24 instructions into XML format. Below is a comprehensive overview of how the program works, along with usage instructions and examples.


### Usage

`python parse.py < IPPcode24.txt`

### Input Processing

The program reads IPPcode24 instructions from standard input, preprocesses them to remove comments and unnecessary whitespace, and verifies the correctness of the input header.

### Lexical Analysis (Tokenization):
- The `TOKEN_REGEX` variable defines a regular expression pattern for tokenizing the code. This pattern captures the opcode and up to three arguments from each line of code.
- Regular expressions are used to match specific patterns in the code, such as variable names (`VAR_NAME_REGEX`), and to recognize various types of literals (integers, booleans, strings, nil).
- The `recognize_arg_type` function identifies the type of each argument based on its format (`E_ARG_TYPE` enum). It recognizes variable references (`GF@`, `LF@`, `TF@`), literals with prefixes (`int@`, `bool@`, `string@`, `nil@`), and types (`int`, `bool`, `string`). If an argument does not match any recognized format, it returns `None`.
- Tokenization is done in the `parse_instruction` function, which splits each line of code into tokens and verifies their validity.

### Syntax Analysis (Parsing):
- The `parse_instruction` function parses each line of code, ensuring it adheres to the syntax rules of the language.
- It checks if each line contains only one opcode and if the number of arguments matches the expected number for that opcode.
- It validates the types of arguments using the `check_type` function, comparing them against the expected argument types defined in the `CODE_COMMANDS` dictionary.
- The `parse_code` function processes the preprocessed lines of code (the input lines of code after removing comments, empty lines, and stripping leading/trailing whitespace), ensuring that each line is parsed correctly and generating a structured representation of the code.

### XML Generation

Upon successful parsing and validation, the script generates XML output using the `xml.etree.ElementTree` module in Python. This module allows for the creation of XML documents by representing XML elements as objects and arranging them in a tree structure. Sub-elements are added to parent elements, and attributes can be set for each element. Finally, the XML tree is serialized to a string using the `tostring` function.


### Help

For additional information and usage details, run:

`python parse.py --help`
