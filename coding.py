from collections import defaultdict


class Coder:
    def __init__(self, namespace):
        self.namespace = namespace
        self.level = 0
        self.sub_level = 0
        self.peripherals_by_name = {}
        self.unions_by_register = {}

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
            self.index_and_emit_incomplete_peripheral(peripheral)
        self.emit_line()
        # Sort peripherals by name
        mcu['peripherals']['peripheral'] = sorted(mcu['peripherals']['peripheral'], key=lambda p: p['name'])
        self.emit_line('struct Mcu {')
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
        self.emit_line('#ifdef {}_RUNTIME_CHECK'.format(self.namespace.upper()))
        self.emit_line('inline void check_mcu_map_at_runtime()')
        self.emit_line('{')
        self.step_forward()
        for peripheral in mcu['peripherals']['peripheral']:
            self.emit_peripheral_check(peripheral)
        self.step_backward()
        self.emit_line('}')
        self.emit_line('#endif // {}_RUNTIME_CHECK'.format(self.namespace.upper()))
        self.emit_line()
        self.emit_line('}')

    def emit_peripheral_member_init(self, peripheral):
        name = peripheral['name']
        line = '.{} = *reinterpret_cast<volatile {}*>({}),'
        self.emit_line(line.format(name.lower(), name, peripheral['baseAddress']))

    def emit_peripheral_member(self, peripheral):
        name = peripheral['name']
        self.emit_line('volatile {}& {};'.format(name, name.lower()))

    def index_and_emit_incomplete_peripheral(self, peripheral):
        # Index peripherals by name in order to support peripherals that are derived from another one, which could lie
        # further in the alphabet.
        self.peripherals_by_name[peripheral['name']] = peripheral

        if '@derivedFrom' in peripheral:
            self.emit_line('using {} = {};'.format(peripheral['name'],
                                                   self.peripherals_by_name[peripheral['@derivedFrom']]['name']))
        else:
            self.emit_line('struct {};'.format(peripheral['name']))

    def emit_peripheral(self, peripheral):
        detailed_info = peripheral if '@derivedFrom' not in peripheral else self.peripherals_by_name[
            peripheral['@derivedFrom']]
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
        if '@derivedFrom' in peripheral:
            self.emit_line()
            return
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
                self.emit_line('char padding_{}[{:#02x}];\n'.format(padding_index, num_unused_bytes))
                padding_index += 1
            if offset in registers_by_offset:
                registers_at_offset = registers_by_offset[offset]
                emitted_size = 0
                if len(registers_at_offset) == 1:
                    member_name, emitted_size = self.emit_register(registers_at_offset[0])
                else:
                    name = '{}_variants'.format(registers_at_offset[0]['name'])
                    self.emit_line('union {} {}'.format(name, '{'))
                    self.step_forward()
                    for register in registers_at_offset:
                        # Remember union name for that register, for future reference. Note: the peripheral name is
                        # necessary in the key to ensure unambiguous register identification
                        self.unions_by_register[(peripheral_name, register['name'])] = name
                        emitted_size = max(self.emit_register(register)[1], emitted_size)
                    self.step_backward()
                    member_name = '{}_'.format(name.lower())
                    self.emit_line('{} {};\n'.format('}', member_name))
                static_assert = 'static_assert(offsetof({}, {}) == {:#02x}, "padding error");'
                static_asserts.append(static_assert.format(peripheral_name, member_name, offset))
                offset += emitted_size
        self.step_backward()
        self.emit_line('};\n')
        for static_assert in static_asserts:
            self.emit_line(static_assert)
        self.emit_line()

    def emit_peripheral_check(self, peripheral):
        if '@derivedFrom' in peripheral:
            return
        for register in list_if_item(peripheral['registers']['register']):
            self.emit_register_check(register, peripheral['name'])

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

    def emit_register_check(self, register, peripheral_name):
        register_num_bits = int(register['size'], 0)
        # The procedure below will use a standard type to represent the register, so we need to check that this will
        # work, but it should not be a practical limitation.
        assert register_num_bits == 8 or register_num_bits == 16 or register_num_bits == 32 or register_num_bits == 64
        if 'fields' not in register:
            return  # sometimes, there are no fields, and therefore nothing to check
        try:
            reset_value = int(register['resetValue'], 0)
        except ValueError:
            # SVD files sometimes specify the reset value in binary format (instead of hex, typically), but they do not
            # use any standard way to flag that (like '0b'). E.g., '00000010' could mean two. We choose to ignore
            # anything Python cannot interpret without help, since any ad-hoc heuristic would probably be somewhat
            # unreliable.
            return
        if is_bin_symmetrical(reset_value, register_num_bits):
            # Getting it right on a symmetrical number does not mean much, so we do not select symmetrical number for
            # the check. Note: this includes all zero-values, which is good.
            return
        self.emit_line('if (')
        self.step_forward()
        self.emit_line('(')
        self.step_forward()
        register_name = register['name']
        register_field_name = '{}_'.format(register_name.lower())
        try:
            union_part = '.{}_'.format(self.unions_by_register[(peripheral_name, register_name)].lower())
        except KeyError:
            union_part = ''
        num_fields = len(list_if_item(register['fields']['field']))
        for i, field in enumerate(list_if_item(register['fields']['field'])):
            string = '(static_cast<uint{}_t>(mcu.{}{}.{}.{}) << {}u){}'
            terminator = ' |' if i < (num_fields - 1) else ''
            self.emit_line(string.format(register_num_bits, peripheral_name.lower(), union_part, register_field_name,
                                         field['name'], int(field['bitOffset'], 0), terminator))
        self.step_backward()
        self.emit_line(') != {:#x}u)'.format(reset_value))
        self.emit_line('for (;;)')
        self.step_forward()
        self.emit_line('; // halt')
        self.step_backward()
        self.step_backward()

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


def revert_number(number, num_bits):
    reverted_number = 0
    for bit in range(num_bits):
        reverted_number |= (number & 1) << (num_bits - bit - 1)
        number >>= 1
    return reverted_number


def is_bin_symmetrical(number, num_bits):
    assert num_bits % 2 == 0
    half_num_bits = num_bits // 2
    high_half = number >> half_num_bits
    half_mask = (1 << half_num_bits) - 1
    low_half = number & half_mask
    return high_half == revert_number(low_half, half_num_bits)
