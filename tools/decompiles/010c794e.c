
void FUN_010c794e(int param_1)

{
  int5 iVar1;
  ushort uVar2;
  int in_r24;
  int in_r25;
  int in_r28;
  int in_r29;
  int in_ep;
  
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
  *(char *)(param_1 + 0x448) = (char)uVar2;
  iVar1 = (int5)(int)(uint)uVar2 - (int5)(int)iVar1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(short *)(in_r29 + -0x51e0) = (short)&stack0x00000000;
  *(short *)(&DAT_00001422 + in_r28) = (short)iVar1;
  __nop();
                    /* WARNING: Could not recover jumptable at 0x010c79a2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010c79a4 + *(short *)(&LAB_010c79a4 + in_r24 * 2) * 2))
            (*(undefined2 *)(in_ep + 0x62));
  return;
}

