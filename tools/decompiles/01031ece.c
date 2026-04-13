
void FUN_01031ece(int param_1)

{
  int5 iVar1;
  int unaff_tp;
  int in_r22;
  code *UNRECOVERED_JUMPTABLE_00;
  int in_ep;
  
  iVar1 = (int5)unaff_tp - (int5)param_1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  if (in_r22 == 0 && *(char *)(in_ep + 0x54) == '\0') {
    __nop();
    *(undefined1 *)(in_ep + 0x62) = 0;
                    /* WARNING: Could not recover jumptable at 0x01031f40. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*UNRECOVERED_JUMPTABLE_00)(*(undefined2 *)(in_ep + 2),0xffff8151);
    return;
  }
  *(int *)(in_ep + 0x60) = (int)iVar1;
                    /* WARNING: Could not recover jumptable at 0x01031f20. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE_00)(*(undefined2 *)(in_ep + 4),(int)(char)param_1);
  return;
}

