# Шаг 1: Лексический анализатор
class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.current_pos = 0
        self.keywords = ['component', 'input', 'output', 'process', 'foreach', 'let', 'return']

    def tokenize(self):
        while self.current_pos < len(self.source_code):
            char = self.source_code[self.current_pos]

            if char.isspace():
                self.current_pos += 1
                continue
            
            # Обработка идентификаторов и ключевых слов
            if char.isalpha():
                start_pos = self.current_pos
                while (self.current_pos < len(self.source_code) and 
                       (self.source_code[self.current_pos].isalnum() or self.source_code[self.current_pos] == '_')):
                    self.current_pos += 1
                word = self.source_code[start_pos:self.current_pos]
                if word in self.keywords:
                    self.tokens.append(('KEYWORD', word))
                else:
                    self.tokens.append(('IDENTIFIER', word))
                continue
            
            # Обработка символов, включая двоеточие и оператор присваивания
            if char in ('{', '}', '(', ')', '>', '<', '<<', '=>', ':', '=', ';', '*', '+'):
                self.tokens.append(('SYMBOL', char))
                self.current_pos += 1
                continue
            
            # Обработка литералов (чисел)
            if char.isdigit():
                start_pos = self.current_pos
                while (self.current_pos < len(self.source_code) and 
                       self.source_code[self.current_pos].isdigit()):
                    self.current_pos += 1
                number = self.source_code[start_pos:self.current_pos]
                self.tokens.append(('NUMBER', number))
                continue

            raise Exception(f"Unexpected character: {char} at position {self.current_pos}")

        return self.tokens

# Шаг 2: Синтаксический анализатор
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_pos = 0

    def parse(self):
        components = []
        while self.current_pos < len(self.tokens):
            token = self.tokens[self.current_pos]

            if token[0] == 'KEYWORD' and token[1] == 'component':
                component = self.parse_component()
                components.append(component)
            else:
                self.current_pos += 1
        
        return components

    def parse_component(self):
        self.current_pos += 1  # Пропускаем 'component'
        component_name = self.tokens[self.current_pos][1]
        self.current_pos += 1  # Пропускаем имя компонента

        inputs = []
        outputs = []
        body = []

        while self.tokens[self.current_pos][1] != '{':
            self.current_pos += 1

        self.current_pos += 1  # Пропускаем '{'

        # Парсинг input и output
        while self.tokens[self.current_pos][1] != '}':
            token = self.tokens[self.current_pos]

            if token[0] == 'KEYWORD' and token[1] == 'input':
                self.current_pos += 1
                if self.tokens[self.current_pos][1] == ':':
                    self.current_pos += 1  # Пропускаем ':'
                    inputs.append(self.tokens[self.current_pos][1])  # Добавляем тип входа
            elif token[0] == 'KEYWORD' and token[1] == 'output':
                self.current_pos += 1
                if self.tokens[self.current_pos][1] == ':':
                    self.current_pos += 1  # Пропускаем ':'
                    outputs.append(self.tokens[self.current_pos][1])  # Добавляем тип выхода
            
            self.current_pos += 1  # Пропускаем тип

        self.current_pos += 1  # Пропускаем '}'

        # Парсинг тела компонента
        while self.current_pos < len(self.tokens):
            token = self.tokens[self.current_pos]
            if token[0] == 'KEYWORD' and token[1] == 'process':
                self.current_pos += 1  # Пропускаем 'process'
                if self.tokens[self.current_pos][1] == '=>':
                    self.current_pos += 1  # Пропускаем '=>'
                    if self.tokens[self.current_pos][1] == '{':
                        self.current_pos += 1  # Пропускаем '{'
                        
                        while self.tokens[self.current_pos][1] != '}':
                            body.append(self.tokens[self.current_pos])  # Добавляем каждую строку в тело
                            self.current_pos += 1
                        
                        self.current_pos += 1  # Пропускаем '}'
            else:
                self.current_pos += 1

        return {
            'name': component_name,
            'inputs': inputs,
            'outputs': outputs,
            'body': body
        }


# Шаг 3: Генерация кода
class CodeGenerator:
    def generate(self, components):
        low_level_code = ""
        for component in components:
            low_level_code += f"// Component: {component['name']}\n"
            low_level_code += f"// Inputs: {', '.join(component['inputs'])}\n"
            low_level_code += f"// Outputs: {', '.join(component['outputs'])}\n"
            low_level_code += "void " + component['name'] + "() {\n"

            for line in component['body']:
                if line[0] == 'KEYWORD' and line[1] == 'let':
                    variable = self.parse_variable(line)
                    low_level_code += f"    int {variable}; // Присваивание\n"
                elif line[0] == 'IDENTIFIER':
                    variable = self.parse_variable(line)
                    low_level_code += f"    {variable} = 0; // Присваивание\n"
                elif line[0] == 'KEYWORD' and line[1] == 'foreach':
                    # In this case, we need to extract the variable from foreach
                    item = self.tokens[self.current_pos][1]
                    self.current_pos += 2  # Skip 'in' and 'input'
                    low_level_code += f"    for (int i = 0; i < input_length; i++) {{ // Итерация по входам\n"
                    low_level_code += f"        {item} = input[i]; // Присваиваем элемент\n"
                    low_level_code += "        // Здесь будет логика обработки\n"
                    low_level_code += "    }\n"
                elif line[0] == 'KEYWORD' and line[1] == 'process':
                    # Process the block of code within the 'process' keyword
                    self.current_pos += 2  # Skip '=>'
                    if not line[2]:  # Check if there is a body for the process block
                        low_level_code += "    // Empty process block\n"
                    else:
                        while self.current_pos < len(self.tokens) and \
                              (self.tokens[self.current_pos][0] != 'KEYWORD' or \
                               self.tokens[self.current_pos][1] != 'return'):
                            body_line = self.tokens[self.current_pos]
                            low_level_code += f"        {body_line[1]}; // Присваивание\n"
                            self.current_pos += 1
                        if line[2]:  # Check if there is a return statement at the end of the process block
                            low_level_code += f"    return {line[2]}; // Example return statement\n"
                else:
                    low_level_code += f"    // Неизвестный элемент: {line}\n"

            low_level_code += "}\n\n"

        return low_level_code

    def parse_variable(self, line):
        # Parse the variable name and its type from the 'let' keyword
        if line[0] == 'KEYWORD' and line[1] == 'let':
            self.current_pos += 2  # Skip 'let'
            variable = line[1]
            return variable

        raise Exception(f"Unexpected token at position {self.current_pos}")

# Example usage
source_code = """
component MyComponent {
    input: int
    output: int
    process => {
        let result = 0;
        result += input;
        return result;
    }
}
"""


def compile_homo(source_code):
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    components = parser.parse()
    code_gen = CodeGenerator()
    low_level_code = code_gen.generate(components)
    return low_level_code


if __name__ == "__main__":
    try:
        compiled_code = compile_homo(source_code)
        print("Сгенерированный низкоуровневый код:\n")
        print(compiled_code)
    except Exception as e:
        print(f"Ошибка компиляции: {e}")

