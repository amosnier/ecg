inline void check_bit_field_mapping()
{
	struct {
		uint32_t flag1: 1 = 1u;
		uint32_t value1: 4 = 11u;
		uint32_t flag2: 1 = 1u;
		uint32_t flag3: 1 = 0;
		uint32_t value2: 7 = 53u;
		uint32_t : 17;
		uint32_t flag4: 1 = 0;
	} bit_fields1{};
	if (*reinterpret_cast<const uint32_t*>(&bit_fields1) != (1u | (11u << 1u) | (1u << 5u) | (53u << 7u)))
		for (;;)
			; // bit field mapping problem, halt
	struct {
		uint32_t flag1: 1 = 0;
		uint32_t value1: 4 = 13u;
		uint32_t flag2: 1 = 1u;
		uint32_t flag3: 1 = 0;
		uint32_t : 14;
		uint32_t value2: 3 = 5u;
		uint32_t : 4;
		uint32_t flag4: 1 = 1u;
		uint32_t flag5: 1 = 1u;
		uint32_t flag6: 1 = 0;
		uint32_t flag7: 1 = 1u;
	} bit_fields2{};
	if (*reinterpret_cast<const uint32_t*>(&bit_fields2) != ((13u << 1u) | (1u << 5u) | (5u << 21u) | (1u << 28u) |
	                                                        (1u << 29u) | (1u << 31u)))
		for (;;)
			; // bit field mapping problem, halt
}
