
/* WARNING: This function may have set the stack pointer */

void FUN_010ac7dc(undefined4 param_1)

{
  ushort uVar1;
  int in_r13;
  code *UNRECOVERED_JUMPTABLE;
  undefined2 in_r29;
  int in_ep;
  
  *(undefined2 *)(in_ep + 0xa4) = *(undefined2 *)(in_ep + 0x94);
  *(undefined2 *)(in_ep + 0xc2) = in_r29;
  uVar1 = *(ushort *)(in_ep + 0x88);
  FUN_010fcf1e();
  *(uint *)(in_ep + 0xf8) = (uint)uVar1;
  *(undefined4 *)(in_ep + 0xa8) = param_1;
  *(byte *)(in_r13 + -0x1ac) = ~(byte)UNRECOVERED_JUMPTABLE;
                    /* WARNING: Could not recover jumptable at 0x010ac826. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

