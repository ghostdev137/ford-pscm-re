
void FUN_010e4aa8(int param_1,int param_2)

{
  ushort uVar1;
  ushort uVar2;
  int in_r21;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  *(byte *)(param_1 + 0x5e51) = *(byte *)(param_1 + 0x5e51) | 2;
  *(byte *)(param_2 + -0x1b0) = *(byte *)(param_2 + -0x1b0) | 2;
  uVar1 = *(ushort *)(in_ep + 0x32);
  uVar2 = *(ushort *)(in_ep + 0xfa);
  *(undefined1 *)(uVar2 + 0x2400) = 0;
  *(uint *)(uVar1 + 0x7842) = (uint)uVar1;
  *(char *)(uVar2 + 0x2800) = (char)in_r21;
                    /* WARNING: Could not recover jumptable at 0x010e4b14. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(in_r21 + 0x1000);
  return;
}

