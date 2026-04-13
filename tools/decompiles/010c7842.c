
void FUN_010c7842(short param_1,undefined1 param_2,int param_3)

{
  int5 iVar1;
  ushort uVar2;
  undefined4 uVar3;
  int in_r10;
  code *UNRECOVERED_JUMPTABLE;
  uint in_r20;
  int in_r24;
  int in_r25;
  int in_r28;
  int in_ep;
  undefined4 in_lp;
  
  __nop();
  *(undefined4 *)(in_ep + 0xf0) = in_lp;
  *(undefined1 *)(in_ep + 0x3c) = param_2;
  *(undefined4 *)(in_ep + 0xf0) = in_lp;
  if (in_r10 < -1) {
    uVar3 = *(undefined4 *)in_ep;
    uVar2 = *(ushort *)(in_ep + 0x14);
    iVar1 = (int5)in_r25 + -0x4b24;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    *(char *)(param_3 + 0x448) = (char)uVar2;
    iVar1 = (int5)(int)(uint)uVar2 - (int5)(int)iVar1;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = 0;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    *(short *)(~in_r20 - 0x51e0) = (short)uVar3;
    *(short *)(&DAT_00001422 + in_r28) = (short)iVar1;
    __nop();
                    /* WARNING: Could not recover jumptable at 0x010c79a2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*(code *)(&LAB_010c79a4 + *(short *)(&LAB_010c79a4 + in_r24 * 2) * 2))
              ((int)(short)param_3 * (int)param_1,*(undefined2 *)(in_ep + 0x62));
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x010c7854. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

