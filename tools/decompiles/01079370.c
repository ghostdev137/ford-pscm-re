
void FUN_01079370(code *UNRECOVERED_JUMPTABLE,uint param_2)

{
  undefined4 in_r13;
  undefined4 in_r17;
  short in_r20;
  uint in_ep;
  
  *(undefined2 *)(in_ep + 0xc4) = 0;
  __nop();
  *(undefined4 *)(in_ep + 0x68) = in_r17;
  *(undefined4 *)(in_ep + 0xa8) = in_r17;
  *(undefined4 *)(in_ep + 0xa0) = in_r13;
  *(undefined4 *)(in_ep + 0xa0) = in_r13;
  *(byte *)(in_ep + 0x65) = ~(byte)in_ep;
  *(undefined2 *)(in_ep + 0xc4) = 0;
  __nop();
  *(uint *)(in_ep + 0x68) = (uint)*(ushort *)(in_ep + 0xa2);
  *(uint *)(in_ep + 0xa8) = (uint)*(ushort *)(in_ep + 0xa2);
  *(uint *)(in_ep + 0xa0) = ~in_ep;
  __nop();
                    /* WARNING: Could not recover jumptable at 0x01079412. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(param_2 / (uint)(int)in_r20,*(undefined1 *)(in_ep + 4));
  return;
}

