
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x0107b7d0) */
/* WARNING: Removing unreachable block (ram,0x0107b7cc) */
/* WARNING: Removing unreachable block (ram,0x0107b7a0) */
/* WARNING: Removing unreachable block (ram,0x0107b74e) */
/* WARNING: Removing unreachable block (ram,0x0107b650) */

void FUN_0107b5ec(undefined4 param_1,int param_2)

{
  int5 iVar1;
  byte bVar2;
  ushort uVar3;
  ushort uVar4;
  ushort uVar5;
  uint uVar6;
  undefined1 uVar7;
  undefined1 in_r11;
  undefined2 in_r14;
  undefined4 in_r15;
  int in_r16;
  int iVar8;
  int in_r17;
  int in_r19;
  code *UNRECOVERED_JUMPTABLE;
  ushort in_r23;
  undefined4 uVar9;
  undefined1 uVar10;
  undefined4 in_r27;
  undefined4 in_r28;
  uint uVar11;
  uint uVar12;
  ushort *in_ep;
  ushort *puVar13;
  uint uVar14;
  int in_CTBP;
  
  *(undefined4 *)(in_ep + 0x72) = in_r28;
  *(int *)(in_r19 + -0x3c1e) = in_r19;
  *(undefined4 *)(in_r17 + -0x3d1a) = param_1;
  *(int *)(in_r17 + -0x3c1e) = in_r19;
  bVar2 = (byte)in_ep[0x38];
  uVar11 = (uint)bVar2;
  *(undefined4 *)(in_r16 + -0x3d1a) = in_r15;
  uVar3 = in_ep[0x5c];
  in_ep[0x20] = in_r23;
  uVar4 = in_ep[0x5d];
  *(undefined4 *)(in_r17 + -0x3d1e) = in_r15;
  iVar1 = (int5)(param_2 + -0x5ca10000) - (int5)in_r16;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar7 = (undefined1)in_ep[0x49];
  uVar9 = 0x4090;
  (&DAT_00001001)[uVar11] = (char)iVar1;
  puVar13 = (ushort *)(uint)*in_ep;
  *(undefined4 *)((int)iVar1 + -0x3c1e) = in_r27;
  iVar8 = *(int *)(puVar13 + 0x5c);
  *(BADSPACEBASE **)(in_r17 + -0x3d1a) = register0x0000000c;
  *(ushort *)(iVar8 + 0x4a00) = (ushort)bVar2;
  *(short *)(&DAT_00004800 + in_r17) = (short)iVar8;
  uVar5 = puVar13[0x5c];
  uVar14 = (uint)uVar5;
  *(undefined2 *)(iVar8 + 0x2100) = in_r14;
  uVar12 = (uint)uVar3 / (uint)(int)(short)(ushort)bVar2 & uVar14;
  *(uint *)(in_r19 + -0x3d1e) = uVar14;
  uVar6 = (uint)*puVar13;
  *(undefined1 *)(uVar14 + 0x2020) = 0x90;
  uVar3 = puVar13[0x38];
  *(char *)(uVar14 + 0x3820) = (char)in_r27;
  uVar10 = (undefined1)uVar5;
  *(undefined1 *)(uVar11 + 0x10a12220) = uVar10;
  *(undefined1 *)(uVar11 + 0x10a13a20) = uVar10;
  *(int *)(iVar8 + -0x3d1e) = in_r19;
  *(undefined1 *)(uVar12 + 0x2820) = in_r11;
  *(char *)(uVar14 + 0x3e20) = (char)in_r27;
  puVar13 = (ushort *)(uint)*(ushort *)(uint)(byte)uVar3;
  *(char *)(uVar12 + 0x2e20) = (char)in_r19;
  uVar12 = (uint)puVar13[0x70];
  (*(code *)(in_CTBP + (uint)*(ushort *)(in_CTBP + 0x40)))(0xffffffff,uVar4);
  bVar2 = *(byte *)((int)puVar13 + 0x5d);
  uVar3 = puVar13[0x2e];
  puVar13[0x2c] = 0;
  puVar13[0x2d] = 0;
  uVar11 = (uint)*puVar13;
  (&DAT_ffffdf70)[bVar2] = 0;
  UNRECOVERED_JUMPTABLE = (code *)&LAB_000019a4;
  uVar10 = (undefined1)in_r27;
  *(undefined1 *)(uVar14 - 0x4fe0) = uVar10;
  *(undefined1 *)((byte)uVar3 - 0x4de0) = 0xa4;
  *(char *)(uVar12 - 0x43e0) = (char)in_r15;
  *(char *)(uVar12 - 0x5fe0) = (char)uVar9;
  *(char *)(uVar12 - 0x47e0) = (char)uVar9;
  *(undefined1 *)(uVar14 - 0x5de0) = uVar10;
  *(undefined1 *)(uVar14 - 0x45e0) = uVar10;
  *(undefined1 *)(bVar2 - 0x20a1) = uVar7;
  *(undefined4 *)(uVar11 - 0x3d1e) = uVar9;
  *(undefined1 *)(uVar12 - 0x41e0) = 0xa4;
  *(undefined1 **)(uVar11 - 0x3d1a) = &LAB_000019a4;
  puVar13 = (ushort *)(uint)*puVar13;
  *(uint *)(uVar11 + 0x402) = (uint)puVar13[0x5c];
  iVar8 = *(int *)(puVar13 + 0x5c);
  *(int *)(uVar11 + 0x302) = iVar8;
  iVar1 = (int5)(int)uVar6 - (int5)(int)uVar11;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(char *)(iVar8 + -0x51e0) = (char)uVar14;
  *(int *)(puVar13 + 0x5c) = (int)iVar1;
  __nop();
  iVar8 = *puVar13 + 0x2c000000;
  *(int *)(puVar13 + 0x5e) = iVar8;
  *(int *)(puVar13 + 0x5e) = iVar8;
  *(int *)(puVar13 + 0x5e) = iVar8;
  *(int *)(puVar13 + 0x5e) = iVar8;
  *(int *)(puVar13 + 0x5e) = iVar8;
  func_0x2f289d42(0xffffffff,0xffffe770,puVar13[1]);
  *(undefined1 *)(puVar13 + 0x34) = 0;
  func_0xcd83de40(0x107b7fe);
  *puVar13 = 0;
  *(undefined1 *)puVar13 = 0;
                    /* WARNING: Could not recover jumptable at 0x0107b824. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(puVar13[0x48]);
  return;
}

