
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0108adf8(int param_1)

{
  undefined1 uVar1;
  char cVar2;
  byte bVar3;
  undefined1 in_r11;
  undefined1 uVar4;
  undefined1 in_r14;
  undefined1 uVar5;
  uint uVar6;
  int iVar7;
  int iVar8;
  int in_r20;
  int in_r21;
  int in_r22;
  int in_r23;
  undefined1 in_r27;
  undefined1 *in_r29;
  ushort *in_CTBP;
  
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  iVar7 = (int)*(short *)(in_r21 + 0x200);
  func_0x011bb948();
  bVar3 = *(byte *)(in_r20 + -0x688);
  *(undefined1 *)(in_r23 + 0x1c5) = in_r14;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))
            ((int)*(char *)(bVar3 + 0x1d5),*(undefined1 *)(param_1 + iVar7 + 0x4a));
  iVar7 = (int)*(short *)(in_r21 + 0x200);
  func_0x011bb994();
  cVar2 = *(char *)(*(byte *)(in_r20 + -0x688) + 0x1d5);
  uVar4 = *(undefined1 *)(param_1 + iVar7 + 0x4a);
  (&DAT_00006871)[in_r23] = 0;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))((int)cVar2,uVar4);
  iVar7 = (int)*(short *)(in_r21 + 0x200);
  func_0x011bb9e0();
  bVar3 = *(byte *)(in_r20 + -0x688);
  *(undefined1 *)(in_r22 + 0x1c5) = in_r27;
  iVar7 = param_1 + iVar7;
  uVar4 = *(undefined1 *)(iVar7 + 0x1d);
  uVar5 = (undefined1)*(undefined2 *)(iVar7 + 0x8a);
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))
            ((int)*(char *)(bVar3 + 0x1d5),*(undefined1 *)(iVar7 + 0x4a));
  iVar7 = (int)*(short *)(in_r21 + 0x200);
  func_0x011bba2c();
  iVar7 = param_1 + iVar7;
  cVar2 = *(char *)(*(byte *)(in_r20 + -0x688) + 0x1d5);
  uVar1 = *(undefined1 *)(iVar7 + 0x4a);
  (&DAT_00006871)[in_r22] = uVar4;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))((int)cVar2,uVar1);
  iVar8 = (int)*(short *)(in_r21 + 0x200);
  func_0x011bba78();
  bVar3 = *(byte *)(in_r20 + -0x688);
  *(undefined1 *)(in_r22 + 0x1c5) = *(undefined1 *)(iVar7 + 0x4a);
  uVar4 = *(undefined1 *)(bVar3 + 0x1d5);
  bRam00000651 = bRam00000651 ^ 0x80;
  *(undefined1 *)(in_r21 + 0x400) = 0;
  *(undefined1 *)(in_r21 + 0x800) = uVar4;
  *(undefined1 *)(in_r21 + 0xc00) = in_r11;
  *(char *)(in_r21 + 0x1400) = (char)iVar8;
  *(byte *)(in_r22 + -0x687) = *(byte *)(in_r22 + -0x687) | 2;
  *(char *)(in_r21 + 0x1c5) = (char)in_r29;
  uVar6 = (uint)*(ushort *)(param_1 + iVar8 + 0x3a);
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))
            ((int)*(char *)(bVar3 + 0x1d5),*(undefined1 *)(param_1 + iVar8 + 0x4a));
  *in_r29 = uVar5;
  bVar3 = *(byte *)(uVar6 - 0x687);
  *(char *)(in_r21 + 0x1c5) = (char)in_r22;
  uVar6 = (uint)*(ushort *)(param_1 + iVar8 + 0x3a);
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))
            ((int)*(char *)(bVar3 + 0x1d5),*(undefined1 *)(param_1 + iVar8 + 0x4a));
  *in_r29 = uVar5;
  bVar3 = *(byte *)(uVar6 - 0x687);
  *(undefined1 *)(in_r21 + 0x1c5) = uVar5;
                    /* WARNING: Could not recover jumptable at 0x0108b040. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_0108b042 + _LAB_0108b042 * 2))
            ((int)*(char *)(bVar3 + 0x1d5),*(undefined1 *)(param_1 + iVar8 + 0x4a));
  return;
}

