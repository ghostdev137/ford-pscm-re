
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x01080b00) */

void FUN_01080aa2(int param_1,undefined4 param_2)

{
  int5 iVar1;
  uint5 uVar2;
  ushort uVar3;
  ushort uVar4;
  undefined4 in_r1;
  undefined2 in_r2;
  undefined4 unaff_gp;
  int iVar5;
  undefined1 uVar6;
  code *UNRECOVERED_JUMPTABLE;
  int iVar7;
  undefined4 in_r17;
  int in_r18;
  uint in_r21;
  uint uVar8;
  int in_r28;
  undefined4 uVar9;
  undefined2 *in_ep;
  ushort *puVar10;
  undefined2 in_lp;
  short sVar11;
  ushort *in_CTBP;
  
  *(uint *)(in_ep + 0x56) = in_r21;
  in_ep[0x6a] = in_r2;
  *(uint *)(in_ep + 0x52) = in_r21;
  *(undefined4 *)(param_1 + in_r18 + 0x2d54) = unaff_gp;
  *(short *)(in_r28 + 0x1442) = (short)&stack0x00000000;
  uVar9 = *(undefined4 *)(in_ep + 0x54);
  *(undefined4 *)(in_ep + 0x54) = in_r1;
  *(uint *)(in_ep + 0x56) = in_r21 / (uint)(int)(short)in_ep;
  uVar8 = (uint)(ushort)in_ep[0x5e];
  *(uint *)(in_ep + 0x56) = uVar8;
  *(undefined4 *)(in_ep + 0x54) = param_2;
  *(uint *)(in_ep + 0x54) = (uint)*(byte *)((int)in_ep + 0x7d);
  *(undefined4 *)(in_ep + 0x56) = uVar9;
  *(undefined2 *)(uVar8 + 0x57fc) = in_lp;
  *in_ep = 0;
  *(undefined2 *)(uVar8 + 0x47fc) = in_lp;
  *(undefined2 *)(uVar8 + 0x37fc) = in_lp;
  puVar10 = (ushort *)((int)in_ep + in_r18);
  uVar4 = puVar10[0x24];
  *puVar10 = 0;
  UNRECOVERED_JUMPTABLE = (code *)(uint)*puVar10;
  *(undefined2 *)(uVar8 + 0x27fc) = in_lp;
  *(undefined2 *)(*(int *)(puVar10 + 0x50) + 0x11fc) = in_lp;
  uVar2 = (int5)(int)(uint)*puVar10 + 5;
  if (uVar2 < 0x80000000) {
    if ((int5)uVar2 < -0x80000000) {
      uVar2 = 0xff80000000;
    }
  }
  else {
    uVar2 = 0x7fffffff;
  }
  iVar7 = (int)uVar2;
  *(undefined4 *)(puVar10 + 0x1c) = in_r17;
  uVar8 = (uint)puVar10[0xb];
  sVar11 = 0xb;
  puVar10[0x40] = 0;
  __nop();
  __nop();
  __nop();
  __nop();
  uVar3 = puVar10[5];
  *(byte *)(uVar8 + 0x4b75) = *(byte *)(uVar8 + 0x4b75) | 0x80;
  iVar1 = (int5)iVar7 + (int5)(int)(uint)(byte)uVar4;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  iVar5 = (int)iVar1;
  __nop();
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar3,puVar10[0x31]);
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(puVar10[0x51]);
  uVar6 = *(undefined1 *)((int)puVar10 + 0x75);
  iVar1 = (int5)iVar7 + (int5)iVar5;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  (&DAT_00006c35)[uVar8] = (&DAT_00006c35)[uVar8] | 0x80;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))((int)iVar1,uVar6);
  *puVar10 = 0;
  *puVar10 = 0;
  __nop();
  __nop();
  puVar10[0x7f] = sVar11 * sVar11;
  uVar6 = (undefined1)puVar10[0x51];
  *(undefined1 *)((int)puVar10 + 0x51) = uVar6;
  *(undefined1 *)(puVar10 + 0x29) = uVar6;
  *(undefined1 *)(puVar10 + 0x28) = uVar6;
  __nop();
  puVar10[0x41] = 0;
  puVar10[0x52] = 0;
                    /* WARNING: Could not recover jumptable at 0x01080c4e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(puVar10[0x55],puVar10[0x55]);
  return;
}

