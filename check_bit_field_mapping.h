inline void check_bit_field_mapping()
{
	struct {
		bool flag1: 1 = true;
		unsigned value1: 4 = 11u;
		bool flag2: 1 = true;
		bool flag3: 1 = false;
		unsigned value2: 7 = 53u;
		unsigned : 17;
		bool flag4: 1 = false;
	} bit_field1{};
	if (*reinterpret_cast<const uint32_t*>(&bit_field1) != (1u | (11u << 1u) | (1u << 5u) | (53u << 7u)))
		for (;;)
			; // bit field mapping problem, halt
	struct {
		bool flag1: 1 = false;
		unsigned value1: 4 = 13u;
		bool flag2: 1 = true;
		bool flag3: 1 = false;
		unsigned : 14;
		unsigned value2: 3 = 5u;
		unsigned : 4;
		bool flag4: 1 = true;
		bool flag5: 1 = true;
		bool flag6: 1 = false;
		bool flag7: 1 = true;
	} bit_field2{};
	if (*reinterpret_cast<const uint32_t*>(&bit_field2) != ((13u << 1u) | (1u << 5u) | (5u << 21u) | (1u << 28u) |
	                                                        (1u << 29u) | (1u << 31u)))
		for (;;)
			; // bit field mapping problem, halt
}
