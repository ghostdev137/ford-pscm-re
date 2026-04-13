
/* WARNING: Removing unreachable block (ram,0x010839ba) */

void FUN_010838ce(int param_1,uint param_2)

{
  ushort *puVar1;
  uint5 uVar2;
  byte bVar3;
  byte bVar4;
  ushort uVar5;
  uint uVar6;
  uint uVar7;
  code *UNRECOVERED_JUMPTABLE;
  undefined4 in_r25;
  uint in_r28;
  int iVar8;
  int in_r29;
  uint uVar9;
  int in_ep;
  int in_lp;
  ushort *in_CTBP;
  
  uVar7 = ~(uint)&stack0x00000000;
  *(int *)(in_r29 + 0x2e38) = param_1;
  bVar4 = *(byte *)(in_ep + 0x19);
  *(uint *)(in_ep + 0xa8) = (uint)bVar4;
  bVar3 = *(byte *)(in_ep + 1);
  *(byte *)(in_lp + -0x72cf) = *(byte *)(in_lp + -0x72cf) ^ 0x40;
  uVar5 = *(ushort *)(in_ep + 0x32);
  DAT_ffff8d35 = DAT_ffff8d35 | 2;
  UNRECOVERED_JUMPTABLE = (code *)(in_ep + param_1 + (in_r28 | bVar3));
  puVar1 = (ushort *)(in_ep + in_lp);
  *(uint *)(puVar1 + 0x30) = (uint)bVar4;
  *(uint *)(puVar1 + 0x50) = (uint)uVar5;
  iVar8 = (int)*(char *)(*puVar1 - 0x5303);
  *(int *)(puVar1 + 0x32) = in_r29;
  uVar6 = (uint)*(byte *)((int)puVar1 + 0x4f);
  uVar2 = (int5)(int)(uint)puVar1[0xc] + 0x2c19;
  if (uVar2 < 0x80000000) {
    if ((int5)uVar2 < -0x80000000) {
      uVar2 = 0xff80000000;
    }
  }
  else {
    uVar2 = 0x7fffffff;
  }
  __nop();
  *(undefined4 *)(puVar1 + 0x52) = in_r25;
  uVar9 = (uint)puVar1[0x58];
  __nop();
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))
            ((int)uVar2,param_2 & uVar7 & uVar7 & uVar7,uVar6,puVar1[1]);
  uVar6 = uVar6 & uVar9;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(uVar6);
                    /* WARNING: Could not recover jumptable at 0x010839c6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(uVar6 - iVar8);
  return;
}

