#ifdef __GNUC__
#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Unsupported byte order"
#endif
#else
/*
 * Byte order check is necessary because the bit-fields used in this file assume little-endianness. If you use a
 * compiler for which the compile time check is not implemented, you could implement it and send a pull request to
 * the ecg repository, or you could rely on the runtime check below.
 */
#warning "Endianness compile time check not implemented for your compiler! "
"Please implement it or use the runtime check!"
#endif
