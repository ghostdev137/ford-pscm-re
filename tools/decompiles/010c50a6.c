
void FUN_010c50a6(int param_1)

{
  int5 iVar1;
  undefined2 uVar2;
  uint in_r1;
  int unaff_tp;
  int in_r17;
  code *UNRECOVERED_JUMPTABLE;
  undefined1 in_r20;
  int in_r24;
  int in_r27;
  int in_ep;
  int iVar3;
  undefined4 in_lp;
  
  *(undefined4 *)(in_ep + 0xf0) = in_lp;
  iVar3 = (in_ep + param_1 ^ in_r1) + in_r27;
  uVar2 = *(undefined2 *)(iVar3 + 2);
  iVar1 = (int5)in_r17 + -0xf;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  UNRECOVERED_JUMPTABLE = (code *)iVar1;
  *(undefined1 *)(in_r24 * 2 + 0x454) = 0;
  func_0x00ed529e(uVar2);
  iVar3 = iVar3 + unaff_tp;
  *(int *)(iVar3 + 0xf0) = iVar3;
  *(undefined1 *)(iVar3 + 0x34) = in_r20;
  *(int *)(iVar3 + 0xf0) = iVar3;
                    /* WARNING: Could not recover jumptable at 0x010c510c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(*(undefined1 *)(iVar3 + 0x4a));
  return;
}

