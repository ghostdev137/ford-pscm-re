
void FUN_010e4a78(char param_1)

{
  byte *pbVar1;
  ushort uVar2;
  ushort uVar3;
  undefined2 in_r1;
  int unaff_gp;
  undefined4 uVar4;
  short in_r17;
  int in_r21;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  uVar4 = *(undefined4 *)(in_ep + 0x54);
  *(undefined2 *)(in_ep + 0xcc) = in_r1;
  *(byte *)(in_ep + 0x59) = (byte)in_r1 | (byte)UNRECOVERED_JUMPTABLE;
  *(byte *)(unaff_gp + 0x3024) = *(byte *)(unaff_gp + 0x3024) ^ 0x80;
  pbVar1 = (byte *)((int)(short)param_1 * (int)(short)(in_r17 + 0x1000) + 0x5e51);
  *pbVar1 = *pbVar1 | 2;
  *(byte *)(param_1 + -0x1b0) = *(byte *)(param_1 + -0x1b0) | 2;
  uVar2 = *(ushort *)(in_ep + 0x32);
  uVar3 = *(ushort *)(in_ep + 0xfa);
  *(undefined1 *)(uVar3 + 0x2400) = 0;
  *(uint *)(uVar2 + 0x7842) = (uint)uVar2;
  *(char *)(uVar3 + 0x2800) = (char)in_r21;
                    /* WARNING: Could not recover jumptable at 0x010e4b14. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(uVar4,in_r21 + 0x1000);
  return;
}

