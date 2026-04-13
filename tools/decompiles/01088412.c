
/* WARNING: Removing unreachable block (ram,0x0108846a) */
/* WARNING: Removing unreachable block (ram,0x01088472) */

void FUN_01088412(undefined4 param_1)

{
  int5 iVar1;
  undefined2 uVar2;
  int in_r1;
  int iVar3;
  undefined4 in_r15;
  code *UNRECOVERED_JUMPTABLE;
  int in_r28;
  int in_ep;
  ushort *in_CTBP;
  
  UNRECOVERED_JUMPTABLE = (code *)(uint)*(ushort *)(in_ep + 0x8a);
  *(undefined4 *)(in_ep + 0xfc) = param_1;
  uVar2 = *(undefined2 *)(in_ep + 2);
  iVar1 = (int5)in_r1 + -0x10;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(short *)(in_ep + 0xac) = (short)iVar1;
  iVar3 = -3;
  *(short *)(in_ep + 0xac) = (short)iVar1;
  *(undefined4 *)(&DAT_ffffae00 + in_r28) = in_r15;
  *(undefined4 *)(&DAT_ffffae00 + in_r28) = in_r15;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar2);
  *(undefined4 *)(in_r28 + -0x51b8) = in_r15;
  *(undefined4 *)(in_r28 + -0x51a8) = in_r15;
  *(undefined4 *)(&DAT_ffffae00 + in_r28) = in_r15;
  *(undefined4 *)(in_r28 + -0x51b8) = in_r15;
  *(undefined4 *)(in_r28 + -0x51b8) = in_r15;
  *(undefined4 *)(&DAT_ffffae00 + in_r28) = in_r15;
  *(undefined4 *)(in_r28 + -0x51c0) = in_r15;
  iVar1 = (int5)iVar3 + -0xf;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined4 *)(in_r28 + -0x51b0) = in_r15;
                    /* WARNING: Could not recover jumptable at 0x010884a2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)((&stack0x00000001)[in_ep],(int)iVar1);
  return;
}

