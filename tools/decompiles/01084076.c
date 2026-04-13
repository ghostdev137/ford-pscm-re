
/* WARNING: Removing unreachable block (ram,0x010841b6) */
/* WARNING: Removing unreachable block (ram,0x010841d6) */
/* WARNING: Removing unreachable block (ram,0x0108420a) */
/* WARNING: Removing unreachable block (ram,0x0108420c) */
/* WARNING: Removing unreachable block (ram,0x0108421c) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_01084076(void)

{
  undefined1 uVar1;
  undefined2 uVar2;
  undefined2 uVar3;
  int in_r1;
  uint uVar4;
  undefined2 in_r12;
  undefined4 in_r13;
  ushort uVar5;
  uint in_r20;
  uint in_r23;
  ushort uVar6;
  uint in_r28;
  uint in_r29;
  int in_ep;
  uint uVar7;
  ushort *puVar8;
  undefined4 uVar9;
  ushort *in_CTBP;
  
  *(undefined2 *)(in_r29 - 0x51a8) = in_r12;
  uVar7 = (uint)*(ushort *)(in_ep + 6);
  uVar4 = *(uint *)(uVar7 + 0xa8);
  *(char *)(in_r1 + -0x1184) = (char)in_r12;
  *(uint *)(uVar7 + 0xb0) = uVar4;
  *(undefined4 *)(uVar7 + 0xb0) = 0;
  *(char *)(in_r20 + 0x2001) = (char)(in_r28 + 0x526b);
  puVar8 = (ushort *)(uint)_DAT_ffffca58;
  uVar6 = (ushort)(in_r28 + 0x526b) & (ushort)in_r28;
  *(undefined4 *)(puVar8 + 0x32) = in_r13;
  uVar7 = (uint)*(byte *)((int)puVar8 + 0x4f);
  uVar5 = *puVar8;
  uRam000000a4 = (uint)uVar5;
  __nop();
  uVar9 = 0;
  *(uint *)(*puVar8 + 0xb0) = (uVar4 ^ in_r23) & in_r29;
  __nop();
  uVar5 = uVar5 - 8;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar7);
  *(ushort *)(&DAT_00007020 + in_r29) = uVar5 ^ 0x78;
  uVar3 = uRam000000d8;
  uVar4 = (uint)bRam00000044;
  uVar2 = Ram00000000;
  *(uint *)(in_r28 + 0x7842) = in_r28;
  Ram00000000 = (ushort)DAT_00000048 | uVar6 & (ushort)in_r28;
  uVar1 = Ram00000000;
  *(undefined4 *)(uVar4 - 0x2028) = uVar9;
                    /* WARNING: Could not recover jumptable at 0x01084168. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(in_r28 ^ in_r20))(uVar7 ^ in_r23,uVar3);
  return;
}

