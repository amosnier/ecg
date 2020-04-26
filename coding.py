class Coder:
    def __init__(self):
        self.level = 0
        self.sub_level = 0
        self.peripherals = {}

    def step_forward(self):
        self.level += 1

    def step_backward(self):
        assert(self.level > 0)
        self.level -= 1

    def sub_step_forward(self):
        self.sub_level += 1

    def sub_step_backward(self):
        assert(self.sub_level > 0)
        self.sub_level -= 1

    def emit_line(self, string):
        print('{}{}'.format(self.level * '\t', string))

    def emit_mcu(self, mcu):
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(mcu['description'])))
        self.emit_line(' *')
        self.emit_dict(mcu, lambda key: key != 'description' and key != 'name' and key != 'peripherals')
        self.emit_line(' */')
        self.emit_line('struct {} {}'.format(mcu['name'], '{'))
        self.step_forward()
        # Index all peripherals on name to allow finding source of derived peripherals
        for peripheral in mcu['peripherals']['peripheral']:
            self.peripherals[peripheral['name']] = peripheral
        # Sort peripherals by base address
        for peripheral in sorted(mcu['peripherals']['peripheral'], key=lambda p: int(p['baseAddress'], 16)):
            self.emit_peripheral(peripheral)
        self.step_backward()
        self.emit_line('{} {};'.format('}', mcu['name'].lower()))

    def emit_peripheral(self, peripheral):
        detailed_info = peripheral if '@derivedFrom' not in peripheral else self.peripherals[peripheral['@derivedFrom']]
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(detailed_info['description'])))
        self.emit_line(' *')
        self.emit_dict(peripheral, lambda key: key != 'description' and key != 'name' and key != 'registers')
        self.emit_line(' */')
        self.emit_line('struct {} {}'.format(peripheral['name'], '{'))
        self.step_forward()
        # If there is just one register, ensure that it still is presented as a list
        for register in list_if_element(detailed_info['registers']['register']):
            self.emit_register(register)
        self.step_backward()
        self.emit_line('{} {};'.format('}', peripheral['name'].lower()))

    def emit_register(self, register):
        # Apparently, the SVD file sometimes contains registers without a single field! It looks like these do not
        # really exist! Maybe the vendor is planning for the future...
        if 'fields' not in register:
            return
        num_bits = int(register['size'], 16)
        bits = {}
        # If there is just one field, ensure that it still is presented as a list
        for field in list_if_element(register['fields']['field']):
            bits[int(field['bitOffset'])] = field
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(register['description'])))
        self.emit_line(' *')
        self.emit_dict(register, lambda key: key != 'description' and key != 'name' and key != 'fields')
        self.emit_line(' */')
        self.emit_line('struct {} {}'.format(register['name'], '{'))
        self.step_forward()
        bit_index = 0
        while bit_index < num_bits:
            size = 0
            while bit_index < num_bits and bit_index not in bits:
                size += 1
                bit_index += 1
            if size != 0:
                self.emit_line('int : {};'.format(size))
            if bit_index in bits:
                bit_info = bits[bit_index]
                width = int(bit_info['bitWidth'])
                self.emit_line('int {}: {}; /**< {} */'.format(bit_info['name'], width, strip(bit_info['description'])))
                bit_index += width
        self.step_backward()
        self.emit_line('{} {};'.format('}', register['name'].lower()))

    def emit_dict(self, dictionary, key_is_valid=lambda key: True):
        valid_keys = (key for key in dictionary if key_is_valid(key))
        for key in valid_keys:
            value = dictionary[key]
            if isinstance(value, str):
                self.emit_line(' * {}{}: {}'.format(self.sub_level * '\t', key, strip(value)))
            else:
                self.emit_line(' * {}{}:'.format(self.sub_level * '\t', key))
                self.sub_step_forward()
                if isinstance(value, dict):
                    self.emit_dict(value)
                elif isinstance(value, list):
                    for i, element in enumerate(value):
                        self.emit_line(' * {}{}:'.format(self.sub_level * '\t', i))
                        self.sub_step_forward()
                        self.emit_dict(element)
                        self.sub_step_backward()
                else:
                    raise
                self.sub_step_backward()


def strip(string):
    return ' '.join(string.split())


def list_if_element(element_or_list):
    return element_or_list if isinstance(element_or_list, list) else [element_or_list]