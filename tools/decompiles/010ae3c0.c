
void FUN_010ae3c0(uint param_1)

{
  int5 iVar1;
  byte *pbVar2;
  ushort uVar3;
  char cVar4;
  short in_r1;
  int iVar5;
  undefined4 uVar6;
  int unaff_tp;
  uint uVar7;
  short in_r21;
  ushort uVar8;
  int in_r28;
  int in_r29;
  short *in_ep;
  
  *(undefined1 *)((int)in_ep + 0x59) = 0;
  uVar3 = in_ep[1];
  uVar7 = (uint)*(char *)(unaff_tp + -0x33b0);
  __nop();
  cVar4 = *(char *)(in_r28 + 0x20db);
  uVar8 = (ushort)cVar4;
  iVar5 = (int)(short)*(char *)(unaff_tp + -0x33b0) * (int)in_r1;
  if (*in_ep != 0x277c) {
    uVar7 = param_1 & 0x6a35;
    __nop();
    iVar5 = 0;
    in_r21 = in_ep[0x50];
    *(char *)(in_ep + 0x29) = (char)*(undefined4 *)(in_ep + 0x48);
    uVar8 = (short)cVar4 + 0x5080;
  }
  uVar6 = *(undefined4 *)(in_ep + 0x48);
  *(char *)((ushort)in_ep[0x2c] + 0xfcfe9401) = (char)in_ep[0x2c];
  cVar4 = *(char *)(iVar5 + 0x127a);
  *(ushort *)(in_r29 + 0x7008) = (ushort)uVar6 | uVar8;
  do {
  } while ((int)(uint)uVar3 < -1);
  uVar7 = (uint)*(byte *)(*(byte *)(*(byte *)(*(byte *)(*(byte *)(*(byte *)(*(byte *)(*(byte *)(*(
                                                  byte *)(*(byte *)(*(byte *)(*(byte *)(*(byte *)(*(
                                                  byte *)(*(byte *)(*(byte *)(uVar7 + 0xd) + 1) +
                                                         0xd) + 1) + 0xd) + 1) + 0xd) + 1) + 0xd) +
                                                  1) + 0xd) + 1) + 0xd) + 1) + 0xd) + 1);
  iVar1 = -(int5)((short)cVar4 * -0x6083);
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(short *)(uVar7 + 0xfe) = in_r21;
  pbVar2 = (byte *)((int)iVar1 + 0xfe6);
  *pbVar2 = *pbVar2 | 1;
  (*(code *)&LAB_00000030)(*(short *)(uVar7 + 0xd8) * -0x6083,iVar5);
  return;
}

