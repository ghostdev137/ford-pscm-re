
/* WARNING: Removing unreachable block (ram,0x01095ab8) */

void FUN_01095a9a(undefined4 param_1)

{
  uint unaff_tp;
  int in_r16;
  uint in_r25;
  undefined2 in_r29;
  int in_ep;
  
  while( true ) {
    unaff_tp = unaff_tp | in_r25;
    *(undefined4 *)(in_ep + 0x68) = param_1;
    __nop();
    if (unaff_tp == 0) break;
    in_r29 = *(undefined2 *)(in_ep + 0x38);
    *(short *)(in_ep + 0xb4) = (short)param_1;
    *(undefined4 *)(in_r16 + 400) = 0;
    __nop();
  }
  *(uint *)(in_ep + 0xbc) = (uint)*(ushort *)(in_ep + 0x12);
  *(char *)(in_ep + 0x2a) = (char)in_r29;
  return;
}

