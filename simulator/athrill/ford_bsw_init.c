/*
 * AUTOSAR BSW Init State Values for Ford PSCM emulation.
 * Derived from autoas/as source code + EP access pattern analysis.
 *
 * These values replicate what EcuM_Init → CanIf_Init → Com_Init etc.
 * write to the BSW context structures in RAM during normal boot.
 */

static void ford_init_bsw_state(void) {
    /* Specific AUTOSAR module states at known EP offsets */
    bus_put_data32(0, 0x40010100, 0x00030003); /* EP+0x000: Com/CanIf states */
    bus_put_data16(0, 0x40010102, 0x0003);     /* EP+0x002: started */
    bus_put_data32(0, 0x40010104, 0x00010001); /* EP+0x004: additional state */
    bus_put_data16(0, 0x40010106, 0x0002);     /* EP+0x006: ComM = FULL_COMMUNICATION */
    bus_put_data32(0, 0x40010108, 0x00020001); /* EP+0x008: CanIf/PduR */
    bus_put_data8(0, 0x4001010C, 0x01);        /* EP+0x00C: init */
    bus_put_data8(0, 0x4001010E, 0x03);        /* EP+0x00E: CanIf = STARTED */
    bus_put_data8(0, 0x40010110, 0x01);        /* EP+0x010: init */
    bus_put_data8(0, 0x40010112, 0x02);        /* EP+0x012: Com state */
    bus_put_data16(0, 0x40010118, 0x0003);     /* EP+0x018: state */
    bus_put_data8(0, 0x4001011E, 0x01);        /* EP+0x01E: init */
    bus_put_data8(0, 0x40010120, 0x01);        /* EP+0x020: init */
    bus_put_data8(0, 0x4001012A, 0xFF);        /* EP+0x02A: group mask (all active) */
    bus_put_data8(0, 0x4001012E, 0x01);        /* EP+0x02E: init */
    bus_put_data16(0, 0x40010138, 0x0001);     /* EP+0x038: state */
    bus_put_data8(0, 0x40010140, 0x02);        /* EP+0x040: EcuM = RUN */
    bus_put_data8(0, 0x40010142, 0x01);        /* EP+0x042: SchM running */
    bus_put_data8(0, 0x40010145, 0x03);        /* EP+0x045: BSW main = running */
    bus_put_data8(0, 0x40010146, 0x01);        /* EP+0x046: init */
    bus_put_data8(0, 0x40010150, 0xFF);        /* EP+0x050: group mask */
    bus_put_data8(0, 0x4001015E, 0x01);        /* EP+0x05E: init */
    bus_put_data8(0, 0x40010160, 0x02);        /* EP+0x060: ComM full */
    bus_put_data8(0, 0x40010161, 0x01);        /* EP+0x061: init */
    bus_put_data8(0, 0x40010165, 0x04);        /* EP+0x065: CanSM = FULLCOM */
    bus_put_data8(0, 0x40010168, 0x01);        /* EP+0x068: init */
    bus_put_data8(0, 0x4001016E, 0x01);        /* EP+0x06E: init */
    bus_put_data8(0, 0x40010170, 0x03);        /* EP+0x070: main loop guard = RUNNING */
    bus_put_data8(0, 0x40010174, 0x01);        /* EP+0x074: init */
    bus_put_data8(0, 0x40010178, 0x01);        /* EP+0x078: init */
    bus_put_data8(0, 0x4001017E, 0x01);        /* EP+0x07E: init */
    bus_put_data32(0, 0x40010180, 0x00030002); /* EP+0x080: state word */
    bus_put_data16(0, 0x40010182, 0x0003);     /* EP+0x082: state */
    bus_put_data16(0, 0x40010184, 0x0001);     /* EP+0x084: state */
    bus_put_data16(0, 0x400101A0, 0x0001);     /* EP+0x0A0: state */
    bus_put_data16(0, 0x400101C4, 0x0003);     /* EP+0x0C4: state */

    /* Fill gaps with 0x01 (generic initialized) without overwriting set values */
    uint32 a;
    for (a = 0x40010100; a < 0x40010500; a++) {
        uint8 v;
        bus_get_data8(0, a, &v);
        if (v == 0) bus_put_data8(0, a, 0x01);
    }
}
