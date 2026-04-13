
void FUN_010aed26(int param_1)

{
  int5 iVar1;
  byte *pbVar2;
  undefined2 uVar3;
  undefined2 in_r27;
  undefined2 *in_ep;
  
  uVar3 = *in_ep;
  iVar1 = -(int5)param_1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  in_ep[0x7f] = in_r27;
  pbVar2 = (byte *)((int)iVar1 + 0xee6);
  *pbVar2 = *pbVar2 | 1;
                    /* WARNING: Could not recover jumptable at 0x010aed58. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010aed5a + *(short *)(&LAB_010aed5a + (int)iVar1 * 2) * 2))(uVar3,0xfffffff9);
  return;
}

