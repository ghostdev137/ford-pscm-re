
/* WARNING: Type propagation algorithm not settling */

void FUN_0109deb8(int param_1,int param_2,int param_3)

{
  int5 iVar1;
  int iVar2;
  code *UNRECOVERED_JUMPTABLE_00;
  
  iVar2 = (short)param_2 * 6;
  if (param_3 < 0 != param_2 < 0 && param_2 < 0 == param_3 - param_2 < 0) {
    __nop();
    __nop();
                    /* WARNING: Could not recover jumptable at 0x0109df08. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*UNRECOVERED_JUMPTABLE_00)(0xfffff0fd,0xffff8a13);
    return;
  }
  __nop();
  iVar1 = (int5)iVar2 - (int5)iVar2;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  iVar1 = (int5)param_1 - (int5)(int)iVar1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  __nop();
                    /* WARNING: Could not recover jumptable at 0x0109df96. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE_00)((int)iVar1,param_3 - param_2);
  return;
}

