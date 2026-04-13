
void FUN_0109a6a6(short param_1,short param_2)

{
  int5 iVar1;
  undefined1 unaff_gp;
  undefined4 in_r13;
  int in_r25;
  int in_r28;
  int in_ep;
  uint uVar2;
  undefined4 in_lp;
  
  uVar2 = (uint)*(byte *)(in_ep + 3);
  *(undefined4 *)(in_r25 + 0x59f0) = in_lp;
  *(undefined4 *)(uVar2 + 4) = in_r13;
  iVar1 = (int5)in_r28 + -0x40e8;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined1 *)(uVar2 + 0x62) = unaff_gp;
  do {
    *(undefined1 *)(uVar2 + 0x48) = 0;
  } while (-(int)iVar1 < 0);
                    /* WARNING: Could not recover jumptable at 0x0109a6da. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)*(ushort *)(uVar2 + 0x30))((int)param_2 * (int)param_1);
  return;
}

