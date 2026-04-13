
/* WARNING: Removing unreachable block (ram,0x0106643c) */

void FUN_01066306(undefined4 param_1)

{
  undefined2 uVar1;
  char cVar2;
  ushort uVar3;
  uint unaff_gp;
  int unaff_tp;
  int iVar4;
  byte bVar5;
  int in_r10;
  uint in_r11;
  int in_r13;
  undefined4 in_r14;
  int in_r16;
  uint in_r17;
  uint uVar6;
  short in_r20;
  int in_r24;
  undefined4 uVar7;
  undefined1 in_r26;
  undefined1 in_r27;
  uint in_r29;
  undefined4 uVar8;
  int in_ep;
  
  *(undefined4 *)(in_ep + 0x18) = in_r14;
  *(undefined2 *)(in_ep + 0xd0) = 0;
  cVar2 = *(char *)(in_ep + 0x48);
  *(int *)(in_ep + 0x18) = in_r13;
  uVar6 = in_r17 & in_r11;
  if (in_r10 != -1) {
    *(undefined4 *)(in_ep + 0x60) = *(undefined4 *)(in_ep + 0x60);
    *(byte *)(unaff_tp + 0xd30) = *(byte *)(unaff_tp + 0xd30) ^ 2;
    *(int *)(in_ep + 0x68) = unaff_tp;
    unaff_gp = (uint)*(ushort *)(in_ep + 0xa2);
    __nop();
    *(uint *)(in_ep + 100) = in_r29 / (uint)(int)in_r20;
    *(int *)(in_ep + 0x98) = (int)cVar2;
    *(int *)(in_ep + 0xa8) = unaff_tp;
    uVar6 = *(uint *)(in_ep + 0x60);
    *(undefined4 *)(in_ep + 0xa8) = param_1;
    in_ep = unaff_tp + 0x78;
    *(undefined4 *)(unaff_tp + 0xd8) = param_1;
  }
  *(undefined1 *)(in_r16 + 0x5400) = in_r27;
  bVar5 = (byte)in_r16 & 0x7a;
  uVar7 = *(undefined4 *)(in_ep + 0x60);
  *(byte *)(in_ep + 0x66) = bVar5;
  *(undefined1 *)(uVar6 + 0x140b) = 0;
  uVar8 = *(undefined4 *)(in_ep + 0xa0);
  *(byte *)(in_r11 - 0x7fb7) = *(byte *)(in_r11 - 0x7fb7) ^ 0x20;
  __nop();
  (&DAT_00003e48)[unaff_gp] = 0;
  iVar4 = *(int *)(in_ep + 0x6c);
  *(undefined1 *)(in_ep + 0x66) = in_r26;
  uVar1 = *(undefined2 *)(in_ep + 0x14);
  *(byte *)(iVar4 + 0x2451) = *(byte *)(iVar4 + 0x2451) ^ 2;
  __nop();
  *(undefined4 *)(in_ep + 100) = uVar8;
  *(int *)(in_ep + 0x98) = (int)(char)bVar5;
  *(int *)(in_ep + 0xa8) = iVar4;
  uVar3 = *(ushort *)(in_ep + 0x9a);
  *(undefined4 *)(in_ep + 0xa8) = 5;
  *(undefined2 *)(in_ep + 0xc2) = uVar1;
  *(byte *)(in_r11 - 0x12b0) = *(byte *)(in_r11 - 0x12b0) ^ 0x20;
  *(char *)(in_r24 + 0x1400) = (char)uVar1 * 'Q';
  *(int *)(in_r13 + -0x7f94) = in_r24;
  (&DAT_00003e48)[iVar4] = 0;
  *(undefined4 *)(in_ep + 0xa0) = uVar7;
                    /* WARNING: Could not recover jumptable at 0x01066472. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(iVar4 + 0xe2a1de6))(iVar4 + 0x78,0x4ce5969c,(short)~uVar3 * 0x1e48);
  return;
}

