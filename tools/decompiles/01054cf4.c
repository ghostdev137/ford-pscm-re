
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x01054db6) */
/* WARNING: Removing unreachable block (ram,0x01054df8) */

void FUN_01054cf4(int param_1)

{
  int5 iVar1;
  ushort uVar2;
  ushort uVar3;
  uint in_r2;
  short unaff_gp;
  short sVar4;
  uint uVar5;
  short sVar6;
  int iVar7;
  uint in_r11;
  byte bVar8;
  undefined4 uVar9;
  char cVar10;
  uint uVar11;
  char *pcVar12;
  uint uVar13;
  uint in_r18;
  ushort uVar14;
  uint in_r19;
  undefined2 in_r20;
  char *pcVar15;
  uint in_r21;
  byte bVar16;
  int in_r22;
  uint uVar17;
  undefined2 uVar18;
  int in_r29;
  uint *in_ep;
  uint uVar19;
  ushort *in_CTBP;
  
  *(undefined2 *)((int)in_ep + 0xc6) = in_r20;
  cVar10 = (char)param_1;
  *(char *)((int)in_ep + 0x53) = cVar10;
  sVar4 = (short)param_1;
  *(undefined1 *)((int)in_ep + 0x66) = *(undefined1 *)((int)in_ep + 7);
  in_ep[0x2c] = in_r2;
  __nop();
  uVar18 = (undefined2)in_ep[8];
  uVar3 = (ushort)DAT_00002713;
  *(ushort *)((int)in_ep + 0xc6) = (ushort)*(byte *)((int)in_ep + 3);
  *(char *)((int)in_ep + 0x53) = cVar10;
  pcVar15 = (char *)(uint)*(byte *)((int)in_ep + 3);
  __nop();
  uVar17 = ~in_r18;
  cVar10 = cVar10 * '`';
  iVar1 = (int5)param_1 + 0x7f8e;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar9 = (undefined4)iVar1;
  if ((int)in_ep < -0x80000000) {
    if ((int)in_ep < -0x80000000) {
      in_ep = (uint *)&LAB_80000000;
    }
  }
  else {
    in_ep = (uint *)&DAT_7fffffff;
  }
  iVar7 = func_0x00ee0e0c((int)(char)((char)in_r18 + '\x18'));
  sVar6 = (short)in_r18;
  *(short *)(in_ep + 0x31) = (short)uVar9;
  iVar1 = (int5)iVar7 + (int5)in_r22;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  bVar16 = (byte)iVar1;
  uVar11 = (uint)*(ushort *)((int)in_ep + 2);
  uVar5 = in_r19;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  bVar8 = (byte)uVar9;
  pcVar12 = (char *)(uVar11 ^ in_r21);
  *in_ep = uVar5;
  uVar11 = func_0x00f1610e();
  uVar14 = (ushort)uVar5;
  uVar2 = sVar4 * unaff_gp ^ uVar14;
  in_r19 = in_r19 ^ uVar11;
  if (-1 < (int)in_r19) {
    *(char *)((int)in_ep + 0x66) = (char)param_1;
    *pcVar12 = cVar10;
    uVar5 = (uint)(ushort)in_ep[0x27];
    uVar19 = (uint)*(ushort *)((int)in_ep + 0xf2);
    bVar8 = 0xb2;
    func_0x00f861d8(uVar5);
    *(char *)((int)in_ep + 0x62) = (char)param_1;
    *(ushort *)(in_ep + 0x32) = uVar2 & uVar14;
    uVar13 = (uint)(ushort)in_ep[0xe];
    in_ep[2] = in_r11;
    if ((int)((uint)pcVar12 ^ uVar13) < 0) {
      *(ushort *)(in_ep + 0x33) = uVar3 ^ (ushort)uVar11;
      if (param_1 + -1 != 0) {
        in_ep[0x2b] = in_ep[0x2a];
        in_ep[0x28] = uVar13;
        in_ep[0x29] = in_ep[0x2a];
        in_ep[0x28] = uVar13;
                    /* WARNING: Could not recover jumptable at 0x0104ce60. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        (*(code *)(&LAB_0104ce62 + *(short *)(&LAB_0104ce62 + uVar17 * 2) * 2))
                  (param_1 + -1,(uint)(int)(char)uVar5 / (uint)(int)(short)in_r19,
                   (uint)(sVar6 * 6) / (uint)(int)(short)in_r19);
        return;
      }
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
      halt_unimplemented();
    }
    __nop();
    cVar10 = (char)*(undefined2 *)((int)in_ep + 2);
    bVar8 = bVar16 & 1 | bVar8;
    *(undefined1 *)((int)in_ep + 1) = 0;
    __nop();
    in_ep[0x3c] = uVar19;
    *(undefined2 *)(in_r29 + 0x5be8) = uVar18;
  }
  *pcVar15 = cVar10;
  *(byte *)((int)in_ep + 0x33) = bVar8;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

