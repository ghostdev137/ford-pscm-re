#ifndef _BUS_H_
#define _BUS_H_

#include "std_types.h"
#include "std_errno.h"
#include "mpu_ops.h"
#include <stdio.h>

typedef enum {
	BUS_ACCESS_TYPE_NONE = 0,
	BUS_ACCESS_TYPE_READ,
	BUS_ACCESS_TYPE_WRITE,
} BusAccessType;
#define BUS_ACCESS_LOG_SIZE	128

extern void bus_access_set_log(BusAccessType type, uint32 size, uint32 access_addr, uint32 data);
extern Std_ReturnType bus_access_get_log(BusAccessType *type, uint32 *size, uint32 *access_addr, uint32 *data);


#ifdef DISABLE_BUS_ACCESS_LOG
#define bus_access_set_log bus_access_set_log_not_use
static inline void bus_access_set_log_not_use(BusAccessType type, uint32 size, uint32 access_addr, uint32 data)
{}
#endif

/*
 * PATCHED: All bus access functions handle unmapped regions gracefully.
 * Reads return 0, writes are silently dropped.
 * This allows running bare-metal firmware without full peripheral models.
 */

static inline Std_ReturnType bus_get_data8(CoreIdType core_id, uint32 addr, uint8 *data)
{
	Std_ReturnType err = mpu_get_data8(core_id, addr, data);
	if (err != STD_E_OK) {
		*data = 0;
		return STD_E_OK;
	}
	bus_access_set_log(BUS_ACCESS_TYPE_READ, 1U, addr, *data);
	return STD_E_OK;
}

static inline Std_ReturnType bus_get_data16(CoreIdType core_id, uint32 addr, uint16 *data)
{
	Std_ReturnType err = mpu_get_data16(core_id, addr, data);
	if (err != STD_E_OK) {
		*data = 0;
		return STD_E_OK;
	}
	bus_access_set_log(BUS_ACCESS_TYPE_READ, 2U, addr, *data);
	return STD_E_OK;
}

static inline Std_ReturnType bus_get_data32(CoreIdType core_id, uint32 addr, uint32 *data)
{
	Std_ReturnType err = mpu_get_data32(core_id, addr, data);
	if (err != STD_E_OK) {
		*data = 0;
		return STD_E_OK;
	}
	bus_access_set_log(BUS_ACCESS_TYPE_READ, 4U, addr, *data);
	return STD_E_OK;
}

static inline Std_ReturnType bus_put_data8(CoreIdType core_id, uint32 addr, uint8 data)
{
	bus_access_set_log(BUS_ACCESS_TYPE_WRITE, 1U, addr, data);
	(void)mpu_put_data8(core_id, addr, data);
	return STD_E_OK;
}

static inline Std_ReturnType bus_put_data16(CoreIdType core_id, uint32 addr, uint16 data)
{
	bus_access_set_log(BUS_ACCESS_TYPE_WRITE, 2U, addr, data);
	(void)mpu_put_data16(core_id, addr, data);
	return STD_E_OK;
}

static inline Std_ReturnType bus_put_data32(CoreIdType core_id, uint32 addr, uint32 data)
{
	bus_access_set_log(BUS_ACCESS_TYPE_WRITE, 4U, addr, data);
	(void)mpu_put_data32(core_id, addr, data);
	return STD_E_OK;
}

/*
 * PATCHED: Return a NOP for unmapped code fetch instead of failing
 */
static inline Std_ReturnType bus_get_pointer(CoreIdType core_id, uint32 addr, uint8 **data)
{
	Std_ReturnType err = mpu_get_pointer(core_id, addr, data);
	if (err != STD_E_OK) {
		/* Return a static HALT instruction for unmapped code */
		static uint8 halt_code[8] = {0x20, 0x07, 0x20, 0x07, 0x20, 0x07, 0x20, 0x07};
		*data = halt_code;
		return STD_E_OK;
	}
	return STD_E_OK;
}

#endif /* _BUS_H_ */
