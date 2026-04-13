
/* WARNING: This function may have set the stack pointer */
/* WARNING: Removing unreachable block (ram,0x0107b7d0) */
/* WARNING: Removing unreachable block (ram,0x0107b7cc) */
/* WARNING: Removing unreachable block (ram,0x0107b7a0) */
/* WARNING: Removing unreachable block (ram,0x0107b74e) */

void FUN_0107b6ce(int param_1,undefined1 param_2)

{
  int5 iVar1;
  byte bVar2;
  ushort uVar3;
  undefined1 in_r15;
  uint uVar4;
  undefined1 in_r19;
  code *UNRECOVERED_JUMPTABLE;
  undefined4 in_r23;
  undefined1 in_r27;
  uint uVar5;
  int iVar6;
  int in_r29;
  ushort *in_ep;
  ushort *puVar7;
  int in_lp;
  int in_CTBP;
  
  *(undefined1 *)(in_r29 + 0x2e20) = in_r19;
  uVar5 = (uint)in_ep[0x70];
  (*(code *)(in_CTBP + (uint)*(ushort *)(in_CTBP + 0x40)))(0xffffffff);
  bVar2 = *(byte *)((int)in_ep + 0x5d);
  uVar3 = in_ep[0x2e];
  in_ep[0x2c] = 0;
  in_ep[0x2d] = 0;
  uVar4 = (uint)*in_ep;
  (&DAT_ffffdf70)[bVar2] = 0;
  UNRECOVERED_JUMPTABLE = (code *)&LAB_000019a4;
  *(undefined1 *)(in_lp + -0x4fe0) = in_r27;
  *(undefined1 *)((byte)uVar3 - 0x4de0) = 0xa4;
  *(undefined1 *)(uVar5 - 0x43e0) = in_r15;
  *(char *)(uVar5 - 0x5fe0) = (char)in_r23;
  *(char *)(uVar5 - 0x47e0) = (char)in_r23;
  *(undefined1 *)(in_lp + -0x5de0) = in_r27;
  *(undefined1 *)(in_lp + -0x45e0) = in_r27;
  *(undefined1 *)(bVar2 - 0x20a1) = param_2;
  *(undefined4 *)(uVar4 - 0x3d1e) = in_r23;
  *(undefined1 *)(uVar5 - 0x41e0) = 0xa4;
  *(undefined1 **)(uVar4 - 0x3d1a) = &LAB_000019a4;
  puVar7 = (ushort *)(uint)*in_ep;
  *(uint *)(uVar4 + 0x402) = (uint)puVar7[0x5c];
  iVar6 = *(int *)(puVar7 + 0x5c);
  *(int *)(uVar4 + 0x302) = iVar6;
  iVar1 = (int5)param_1 - (int5)(int)uVar4;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(char *)(iVar6 + -0x51e0) = (char)in_lp;
  *(int *)(puVar7 + 0x5c) = (int)iVar1;
  __nop();
  iVar6 = *puVar7 + 0x2c000000;
  *(int *)(puVar7 + 0x5e) = iVar6;
  *(int *)(puVar7 + 0x5e) = iVar6;
  *(int *)(puVar7 + 0x5e) = iVar6;
  *(int *)(puVar7 + 0x5e) = iVar6;
  *(int *)(puVar7 + 0x5e) = iVar6;
  func_0x2f289d42(0xffffffff,0xffffe770,puVar7[1]);
  *(undefined1 *)(puVar7 + 0x34) = 0;
  func_0xcd83de40(0x107b7fe);
  *puVar7 = 0;
  *(undefined1 *)puVar7 = 0;
                    /* WARNING: Could not recover jumptable at 0x0107b824. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(puVar7[0x48]);
  return;
}

