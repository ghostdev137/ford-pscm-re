
void FUN_0106fc66(void)

{
  int5 iVar1;
  int in_r1;
  undefined2 in_r25;
  code *UNRECOVERED_JUMPTABLE;
  undefined2 *in_ep;
  
  *in_ep = in_r25;
  *in_ep = *in_ep;
  iVar1 = (int5)in_r1 + 0x7f8f;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined2 *)((int)iVar1 + 0x80) = 0;
                    /* WARNING: Could not recover jumptable at 0x0106fcae. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

