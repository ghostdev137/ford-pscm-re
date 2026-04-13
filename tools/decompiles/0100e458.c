
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0100e458(int param_1,int param_2,int param_3,uint param_4)

{
  int5 iVar1;
  int5 iVar2;
  int5 iVar3;
  int5 iVar4;
  undefined2 unaff_gp;
  short sVar5;
  uint uVar6;
  short sVar8;
  ushort uVar9;
  undefined2 in_r12;
  int in_r13;
  int iVar10;
  int in_r14;
  undefined2 uVar11;
  uint in_r20;
  int in_r21;
  int in_ep;
  uint uVar12;
  ushort *in_CTBP;
  undefined4 uVar7;
  
  *(short *)(in_ep + 6) = (short)&stack0x00000000;
  __nop();
  __nop();
  *(undefined2 *)(in_ep + 6) = unaff_gp;
  __nop();
  *(short *)(in_ep + 0x1c) = (short)in_r21;
  __nop();
  __nop();
  uVar11 = (undefined2)(in_r20 >> 0xc);
  __nop();
  __nop();
  iVar1 = (int5)in_r14 - (int5)in_r21;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  uVar9 = (ushort)param_4;
  *(ushort *)(in_ep + 0x1a) = uVar9;
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 6) = (short)param_1;
  __nop();
  *(short *)(in_ep + 6) = (short)param_2;
  __nop();
  iVar2 = (int5)(int)&stack0x00000000 - (int5)param_1;
  if (iVar2 < 0x80000000) {
    if (iVar2 < -0x80000000) {
      iVar2 = -0x80000000;
    }
  }
  else {
    iVar2 = 0x7fffffff;
  }
  __nop();
  iVar3 = (int5)(int)&stack0x00000000 - (int5)param_2;
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = -0x80000000;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 6) = (short)param_3;
  __nop();
  iVar4 = (int5)(int)&stack0x00000000 - (int5)param_3;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = -0x80000000;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  uVar7 = (undefined4)iVar4;
  __nop();
  iVar4 = (int5)(int)&stack0x00000000 - (int5)in_r13;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = -0x80000000;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  iVar10 = (int)iVar4;
  __nop();
  *(undefined2 *)(in_ep + 6) = in_r12;
  __nop();
  __nop();
  *(short *)(in_ep + 6) = (short)iVar4;
  __nop();
  __nop();
  __nop();
  uVar6 = (uint)iVar2 >> 9;
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 0x12) = (short)in_ep;
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  uVar12 = param_4 | 1;
  __nop();
  __nop();
  *(short *)(uVar12 + 0x14) = (short)iVar1;
  __nop();
  (*(code *)((int)in_CTBP + (uint)in_CTBP[1]))((int)iVar3,uVar7);
  sVar8 = (short)uVar7;
  __nop();
  iVar1 = (int5)iVar10 - (int5)(int)uVar6;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar7 = (undefined4)iVar1;
  *(short *)(uVar12 + 0x1c) = (short)param_4;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar7);
  sVar5 = (short)uVar7;
  __nop();
  *(undefined2 *)(uVar12 + 0x1c) = uVar11;
  __nop();
  *(ushort *)(uVar12 + 0x24) = uVar9 | 1;
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  __nop();
  __nop();
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))((int)sVar8 * (int)sVar5);
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

