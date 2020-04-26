from collections import defaultdict


class Coder:
    def __init__(self, namespace):
        self.namespace = namespace
        self.level = 0
        self.sub_level = 0
        self.peripherals = {}

    def step_forward(self):
        self.level += 1

    def step_backward(self):
        assert self.level > 0
        self.level -= 1

    def sub_step_forward(self):
        self.sub_level += 1

    def sub_step_backward(self):
        assert self.sub_level > 0
        self.sub_level -= 1

    def emit_line(self, string=''):
        print('{}{}'.format(self.level * '\t', string))

    def emit_mcu(self, mcu):
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(mcu['description'])))
        self.emit_line(' *')
        self.emit_dict(mcu, lambda key: key != 'description' and key != 'name' and key != 'peripherals')
        self.emit_line(' */')
        self.emit_line('namespace {} {}'.format(self.namespace, '{'))
        for peripheral in mcu['peripherals']['peripheral']:
            self.emit_incomplete_peripheral(peripheral)
        self.emit_line()
        self.emit_line('struct Mcu{')
        self.step_forward()
        for peripheral in mcu['peripherals']['peripheral']:
            self.emit_peripheral_member(peripheral)
        self.step_backward()
        self.emit_line('};\n')
        self.emit_line('inline const Mcu mcu{')
        self.step_forward()
        for peripheral in mcu['peripherals']['peripheral']:
            self.emit_peripheral_member_init(peripheral)
        self.step_backward()
        self.emit_line('};\n')
        for peripheral in mcu['peripherals']['peripheral']:
            self.emit_peripheral(peripheral)
        self.emit_line('}')

    def emit_peripheral_member_init(self, peripheral):
        name = peripheral['name']
        line = '.{} = *reinterpret_cast<volatile {}*>({}),'
        self.emit_line(line.format(name.lower(), name, peripheral['baseAddress']))

    def emit_peripheral_member(self, peripheral):
        name = peripheral['name']
        self.emit_line('volatile {}& {};'.format(name, name.lower()))

    def emit_incomplete_peripheral(self, peripheral):
        self.emit_line('struct {};'.format(peripheral['name']))

    def emit_peripheral(self, peripheral):
        if '@derivedFrom' not in peripheral:
            self.peripherals[peripheral['name']] = peripheral
        detailed_info = peripheral if '@derivedFrom' not in peripheral else self.peripherals[peripheral['@derivedFrom']]
        peripheral_size = int(detailed_info['addressBlock']['size'], 0)
        registers_by_offset = defaultdict(list)
        # If there is just one register, ensure that it still is presented as a list
        for register in list_if_item(detailed_info['registers']['register']):
            registers_by_offset[int(register['addressOffset'], 0)].append(register)
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(detailed_info['description'])))
        self.emit_line(' *')
        self.emit_dict(peripheral, lambda key: key != 'description' and key != 'name' and key != 'registers')
        self.emit_line(' */')
        peripheral_name = peripheral['name']
        self.emit_line('struct {} {}'.format(peripheral_name, '{'))
        self.step_forward()
        offset = 0
        padding_index = 0
        static_asserts = []
        while offset < peripheral_size:
            num_unused_bytes = 0
            while offset < peripheral_size and offset not in registers_by_offset:
                num_unused_bytes += 1
                offset += 1
            if num_unused_bytes != 0:
                self.emit_line('char padding_{}[0x{:02x}];\n'.format(padding_index, num_unused_bytes))
                padding_index += 1
            if offset in registers_by_offset:
                registers_at_offset = registers_by_offset[offset]
                emitted_size = 0
                member_name = ''
                if len(registers_at_offset) == 1:
                    member_name, emitted_size = self.emit_register(registers_at_offset[0])
                else:
                    name = '{}_variants'.format(registers_at_offset[0]['name'])
                    self.emit_line('union {} {}'.format(name, '{'))
                    self.step_forward()
                    for register in registers_at_offset:
                        emitted_size = max(self.emit_register(register)[1], emitted_size)
                    self.step_backward()
                    member_name = '{}_'.format(name.lower())
                    self.emit_line('{} {};\n'.format('}', member_name))
                static_assert = 'static_assert(offsetof({}, {}) == 0x{:02x}, "padding error");'
                static_asserts.append(static_assert.format(peripheral_name, member_name, offset))
                offset += emitted_size
        self.step_backward()
        self.emit_line('};\n')
        for static_assert in static_asserts:
            self.emit_line(static_assert)
        self.emit_line()

    def emit_register(self, register):
        # Note: do not assume hex. The source files are inconsistent (32 means 32, not 50!)
        register_num_bits = int(register['size'], 0)
        fields_by_bit_offset = {}
        # If there is just one field, ensure that it still is presented as a list
        if 'fields' in register:
            for field in list_if_item(register['fields']['field']):
                fields_by_bit_offset[int(field['bitOffset'], 0)] = field
        self.emit_line('/**')
        self.emit_line(' * @brief {}'.format(strip(register['description'])))
        self.emit_line(' *')
        self.emit_dict(register, lambda key: key != 'description' and key != 'name' and key != 'fields')
        self.emit_line(' */')
        const = 'const ' if 'access' in register and register['access'] == 'read-only' else ''
        self.emit_line('{}struct {} {}'.format(const, register['name'], '{'))
        self.step_forward()
        bit_index = 0
        while bit_index < register_num_bits:
            num_unused_bits = 0
            while bit_index < register_num_bits and bit_index not in fields_by_bit_offset:
                num_unused_bits += 1
                bit_index += 1
            if num_unused_bits != 0:
                self.emit_line('unsigned : {};'.format(num_unused_bits))
            if bit_index in fields_by_bit_offset:
                bit_info = fields_by_bit_offset[bit_index]
                width = int(bit_info['bitWidth'], 0)
                const = 'const ' if 'access' in bit_info and bit_info['access'] == 'read-only' else ''
                field_type = "bool" if width == 1 else "unsigned"
                self.emit_line('{}{} {}: {}; /**< {} */'.format(const, field_type, bit_info['name'], width,
                                                                strip(bit_info['description'])))
                bit_index += width
        self.step_backward()
        # Emit member name with a trailing underscore, because some have been seen to actually conflict with C++
        # reserved words!
        name = '{}_'.format(register['name'].lower())
        self.emit_line('{} {};\n'.format('}', name))
        return name, register_num_bits // 8

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


def list_if_item(item_or_list):
    return item_or_list if isinstance(item_or_list, list) else [item_or_list]
