
/* WARNING: Instruction at (ram,0x010a9582) overlaps instruction at (ram,0x010a9580)
    */

void FUN_010a9584(void)

{
  int5 iVar1;
  ushort uVar2;
  int in_r1;
  uint in_r2;
  int in_r12;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  ushort *in_ep;
  ushort *puVar3;
  undefined4 in_lp;
  uint in_PSW;
  char cStack_7eab;
  
  while( true ) {
    while( true ) {
      *(undefined4 *)(in_ep + 0x36) = in_lp;
      if ((int)in_r2 < 0) break;
      in_r2 = (uint)*(byte *)(in_r12 + -0x888);
      in_PSW = in_PSW & 0xfffffff8;
    }
    *(undefined4 *)(in_ep + 0x36) = in_lp;
    in_r2 = (uint)*in_ep;
    if (!(bool)((byte)(in_PSW >> 4) & 1)) break;
    *(ushort **)(in_r25 + -0x2694) = in_ep;
    in_PSW = in_PSW & 0xfffffff8;
  }
  *(undefined4 *)(in_ep + 0x36) = in_lp;
  *(undefined4 *)(in_ep + 0x36) = in_lp;
  *(undefined4 *)(in_ep + 0x36) = in_lp;
  *(undefined4 *)(in_ep + 0x36) = in_lp;
  *(undefined4 *)(in_ep + 0x36) = in_lp;
  puVar3 = (ushort *)(uint)*(byte *)((int)in_ep + 1);
  iVar1 = -(int5)(int)(uint)*puVar3;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  puVar3[0x48] = 0;
  puVar3[0x49] = 0;
  uVar2 = *puVar3;
  puVar3[0xc] = uVar2;
  *(ushort **)(in_r25 + 0x5b6c) = puVar3;
  puVar3[0x48] = 0;
  puVar3[0x49] = 0;
  puVar3[0x28] = uVar2;
  *(ushort **)(in_r25 + 0x496c) = puVar3;
                    /* WARNING: Could not recover jumptable at 0x010a9614. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(in_r1 + -0xe25,(int)iVar1,(int)cStack_7eab);
  return;
}

