inline void check_bit_field_mapping()
{
	struct {
		uint32_t flag1: 1;
		uint32_t value1: 4;
		uint32_t flag2: 1;
		uint32_t flag3: 1;
		uint32_t value2: 7;
		uint32_t : 17;
		uint32_t flag4: 1;
	} bit_fields1{
		.flag1 = 1u,
		.value1 = 11u,
		.flag2 = 1u,
		.flag3 = 0,
		.value2 = 53u,
		.flag4 = 0,
	};
	if ((*reinterpret_cast<const uint32_t*>(&bit_fields1) & 0x80003fff) != (1u | (11u << 1u) | (1u << 5u) |
	                                                                        (53u << 7u)))
		for (;;)
			; // bit field mapping problem, halt
	struct {
		uint32_t flag1: 1;
		uint32_t value1: 4;
		uint32_t flag2: 1;
		uint32_t flag3: 1;
		uint32_t : 14;
		uint32_t value2: 3;
		uint32_t : 4;
		uint32_t flag4: 1;
		uint32_t flag5: 1;
		uint32_t flag6: 1;
		uint32_t flag7: 1;
	} bit_fields2{
		.flag1 = 0,
		.value1 = 13u,
		.flag2 = 1u,
		.flag3 = 0,
		.value2 = 5u,
		.flag4 = 1u,
		.flag5 = 1u,
		.flag6 = 0,
		.flag7 = 1u,
	};
	if ((*reinterpret_cast<const uint32_t*>(&bit_fields2) & 0xf0e0007f) != ((13u << 1u) | (1u << 5u) |
	                                                                        (5u << 21u) | (1u << 28u) |
	                                                                        (1u << 29u) | (1u << 31u)))
		for (;;)
			; // bit field mapping problem, halt
}
