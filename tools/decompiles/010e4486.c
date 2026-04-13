
void FUN_010e4486(char param_1)

{
  uint unaff_tp;
  uint uVar1;
  short sVar2;
  int iVar3;
  undefined2 in_r15;
  undefined1 in_r19;
  int in_r20;
  int in_r21;
  char in_r23;
  uint in_r25;
  uint uVar4;
  undefined2 *in_ep;
  undefined1 in_lp;
  uint in_PSW;
  ushort *in_CTBP;
  
  iVar3 = (int)param_1;
  in_ep[0x66] = (ushort)(((byte)(in_PSW >> 1) & 1) != ((byte)(in_PSW >> 2) & 1));
  if (iVar3 != 0) {
    func_0x012adcce(in_ep[1],in_r21 + 0x4000000);
    *in_ep = in_r15;
    *in_ep = in_r15;
    in_r23 = (char)in_ep[1] * in_r23;
    unaff_tp = (short)unaff_tp * 8 | in_r25;
  }
  sVar2 = (short)iVar3;
  *(byte *)(unaff_tp - 0x2ffe) = *(byte *)(unaff_tp - 0x2ffe) ^ 0x80;
  uVar1 = in_r21 + 0x4000000;
  uVar4 = 0x10e44e2;
  func_0x012adcf6(uVar1);
  *in_ep = in_r15;
  *in_ep = in_r15;
  in_ep[100] = (short)in_r20;
  *(undefined1 *)(in_r20 + -0x1fe7) = in_lp;
  *(char *)(in_r20 + -0x17e7) = in_r23;
  *(undefined1 *)(in_r21 + -0x23e7) = in_r19;
  iVar3 = (int)sVar2;
  *in_ep = in_r15;
  *in_ep = in_r15;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar1 | uVar4 | uVar4);
  *(char *)(in_r20 + -0x17e7) = in_r23;
                    /* WARNING: Could not recover jumptable at 0x010e4538. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010e453a + *(short *)(&LAB_010e453a + iVar3 * 2) * 2))();
  return;
}

