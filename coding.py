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
        self.emit_line('namespace mcu {')
        for peripheral in mcu['peripherals']['peripheral']:
            self.emit_peripheral(peripheral)
        self.emit_line('}')

    def emit_peripheral(self, peripheral):
        if '@derivedFrom' not in peripheral:
            self.peripherals[peripheral['name']] = peripheral
        detailed_info = peripheral if '@derivedFrom' not in peripheral else self.peripherals[peripheral['@derivedFrom']]
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(detailed_info['description'])))
        self.emit_line(' *')
        self.emit_dict(peripheral, lambda key: key != 'description' and key != 'name' and key != 'registers')
        self.emit_line(' */')
        self.emit_line('struct {} {}'.format(peripheral['name'], '{'))
        self.step_forward()
        # If there is just one register, ensure that it still is presented as a list
        for register in list_if_item(detailed_info['registers']['register']):
            self.emit_register(register)
        self.step_backward()
        self.emit_line('};\n')

    def emit_register(self, register):
        # Apparently, the SVD file sometimes contains registers without a single field! It looks like these do not
        # really exist! Maybe the vendor is planning for the future...
        if 'fields' not in register:
            return
        # Note: do not assume hex. The source files are inconsistent (32 means 32, not 50!)
        register_num_bits = int(register['size'], 0)
        bits = {}
        # If there is just one field, ensure that it still is presented as a list
        for field in list_if_item(register['fields']['field']):
            bits[int(field['bitOffset'])] = field
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(register['description'])))
        self.emit_line(' *')
        self.emit_dict(register, lambda key: key != 'description' and key != 'name' and key != 'fields')
        self.emit_line(' */')
        self.emit_line('struct {} {}'.format(register['name'], '{'))
        self.step_forward()
        bit_index = 0
        while bit_index < register_num_bits:
            num_unused_bits = 0
            while bit_index < register_num_bits and bit_index not in bits:
                num_unused_bits += 1
                bit_index += 1
            if num_unused_bits != 0:
                self.emit_line('unsigned : {};'.format(num_unused_bits))
            if bit_index in bits:
                bit_info = bits[bit_index]
                width = int(bit_info['bitWidth'], 0)
                field_type = "bool" if width == 1 else "unsigned"
                self.emit_line('{} {}: {}; /**< {} */'.format(field_type, bit_info['name'], width,
                                                              strip(bit_info['description'])))
                bit_index += width
        self.step_backward()
        # Emit member name with a trailing underscore, because some have been seen to actually conflict with C++
        # reserved words!
        self.emit_line('{} {}_;'.format('}', register['name'].lower()))

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


def list_if_item(element_or_list):
    return element_or_list if isinstance(element_or_list, list) else [element_or_list]
