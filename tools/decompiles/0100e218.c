
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0100e218(uint param_1)

{
  int5 iVar1;
  int5 iVar2;
  int5 iVar3;
  int5 iVar4;
  int5 iVar5;
  int5 iVar6;
  uint uVar7;
  uint unaff_tp;
  short sVar8;
  undefined2 uVar10;
  uint uVar11;
  short sVar12;
  ushort uVar13;
  uint uVar14;
  int in_r11;
  undefined2 in_r12;
  int in_r13;
  int iVar15;
  int in_r14;
  uint in_r17;
  undefined2 uVar16;
  uint in_r20;
  uint in_r21;
  undefined2 in_r23;
  int in_r24;
  int in_r25;
  int in_r26;
  int in_ep;
  uint uVar17;
  ushort *in_CTBP;
  undefined4 uVar9;
  
  *(short *)(in_ep + 10) = (short)in_r14;
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  iVar4 = (int5)in_r26 + -1;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = 0;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  __nop();
  iVar5 = (int5)in_r25 + -2;
  if (iVar5 < 0x80000000) {
    if (iVar5 < -0x80000000) {
      iVar5 = -0x80000000;
    }
  }
  else {
    iVar5 = 0x7fffffff;
  }
  uVar14 = (uint)iVar5;
  __nop();
  __nop();
  __nop();
  uVar7 = (uint)*(ushort *)(in_ep + 0xf6);
  __nop();
  iVar6 = (int5)in_r26 + -2;
  if (iVar6 < 0x80000000) {
    if (iVar6 < -0x80000000) {
      iVar6 = -0x80000000;
    }
  }
  else {
    iVar6 = 0x7fffffff;
  }
  __nop();
  __nop();
  iVar1 = (int5)(int)param_1 - (int5)(int)in_r17;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 0xc) = (short)iVar1;
  __nop();
  __nop();
  __nop();
  iVar1 = (int5)in_r24 + -1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  __nop();
  uVar11 = (uint)iVar6 | 1;
  __nop();
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 0xe) = (short)(param_1 >> 6);
  __nop();
  __nop();
  iVar2 = (int5)(int)uVar11 - (int5)(int)uVar11;
  if (iVar2 < 0x80000000) {
    if (iVar2 < -0x80000000) {
      iVar2 = -0x80000000;
    }
  }
  else {
    iVar2 = 0x7fffffff;
  }
  __nop();
  __nop();
  *(short *)(in_ep + 0xe) = (short)iVar2;
  __nop();
  __nop();
  iVar3 = (int5)(int)(uint)iVar2 - (int5)(int)(param_1 >> 6 | 1);
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = 0;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  __nop();
  __nop();
  *(short *)(in_ep + 0xe) = (short)iVar3;
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
  uVar10 = (undefined2)((uint5)iVar2 >> 8);
  *(undefined2 *)(in_ep + 0x20) = uVar10;
  __nop();
  uVar11 = in_r17 >> 0x11 | 1;
  __nop();
  __nop();
  *(undefined2 *)(in_ep + 0x20) = in_r23;
  __nop();
  *(short *)(in_ep + 0x20) = (short)iVar1;
  __nop();
  __nop();
  __nop();
  __nop();
  iVar3 = (int5)(int)(in_r17 >> 0x11) - (int5)(int)(uint)*(ushort *)(in_ep + 0x10);
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = 0;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 0x20) = (short)iVar3;
  __nop();
  __nop();
  *(short *)(in_ep + 0x12) = (short)(unaff_tp | 1);
  __nop();
  *(short *)(in_ep + 4) = (short)iVar1;
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 4) = (short)iVar3;
  __nop();
  *(short *)(in_ep + 6) = (short)iVar4;
  __nop();
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 0x16) = (short)iVar6;
  __nop();
  __nop();
  iVar4 = (int5)in_r11 - (int5)(int)(uint)iVar6;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = -0x80000000;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  __nop();
  uVar13 = (ushort)iVar5;
  *(ushort *)(in_ep + 0x16) = uVar13;
  __nop();
  iVar5 = (int5)(int)uVar7 - (int5)(int)(unaff_tp | 1);
  if (iVar5 < 0x80000000) {
    if (iVar5 < -0x80000000) {
      iVar5 = 0;
    }
  }
  else {
    iVar5 = 0x7fffffff;
  }
  __nop();
  *(ushort *)(in_ep + 6) = *(ushort *)(in_ep + 0xf6);
  __nop();
  __nop();
  *(short *)(in_ep + 6) = (short)iVar5;
  __nop();
  *(short *)(in_ep + 0x1c) = (short)(in_r21 >> 8);
  __nop();
  __nop();
  uVar16 = (undefined2)(in_r20 >> 0xc);
  __nop();
  __nop();
  iVar5 = (int5)in_r14 - (int5)(int)(in_r21 >> 8);
  if (iVar5 < 0x80000000) {
    if (iVar5 < -0x80000000) {
      iVar5 = 0;
    }
  }
  else {
    iVar5 = 0x7fffffff;
  }
  __nop();
  *(ushort *)(in_ep + 0x1a) = uVar13;
  __nop();
  __nop();
  __nop();
  *(short *)(in_ep + 6) = (short)uVar11;
  __nop();
  *(undefined2 *)(in_ep + 6) = uVar10;
  __nop();
  iVar6 = (int5)(int)uVar7 - (int5)(int)uVar11;
  if (iVar6 < 0x80000000) {
    if (iVar6 < -0x80000000) {
      iVar6 = -0x80000000;
    }
  }
  else {
    iVar6 = 0x7fffffff;
  }
  __nop();
  iVar1 = (int5)(int)uVar7 - (int5)(int)((uint)iVar2 >> 8);
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
  __nop();
  *(short *)(in_ep + 6) = (short)iVar4;
  __nop();
  iVar4 = (int5)(int)uVar7 - (int5)(int)iVar4;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = -0x80000000;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  uVar9 = (undefined4)iVar4;
  __nop();
  iVar4 = (int5)(int)uVar7 - (int5)in_r13;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = -0x80000000;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  iVar15 = (int)iVar4;
  __nop();
  *(undefined2 *)(in_ep + 6) = in_r12;
  __nop();
  __nop();
  *(short *)(in_ep + 6) = (short)iVar4;
  __nop();
  __nop();
  __nop();
  uVar11 = (uint)iVar6 >> 9;
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
  uVar17 = uVar14 | 1;
  __nop();
  __nop();
  *(short *)(uVar17 + 0x14) = (short)iVar5;
  __nop();
  (*(code *)((int)in_CTBP + (uint)in_CTBP[1]))((int)iVar1,uVar9);
  sVar12 = (short)uVar9;
  __nop();
  iVar4 = (int5)iVar15 - (int5)(int)uVar11;
  if (iVar4 < 0x80000000) {
    if (iVar4 < -0x80000000) {
      iVar4 = -0x80000000;
    }
  }
  else {
    iVar4 = 0x7fffffff;
  }
  uVar9 = (undefined4)iVar4;
  *(short *)(uVar17 + 0x1c) = (short)uVar14;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar9);
  sVar8 = (short)uVar9;
  __nop();
  *(undefined2 *)(uVar17 + 0x1c) = uVar16;
  __nop();
  *(ushort *)(uVar17 + 0x24) = uVar13 | 1;
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
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))((int)sVar12 * (int)sVar8);
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

