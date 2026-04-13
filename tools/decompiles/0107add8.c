
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0107add8(undefined2 param_1)

{
  ushort uVar1;
  byte bVar2;
  undefined4 in_r11;
  int in_r17;
  int iVar3;
  uint uVar4;
  int in_r18;
  uint in_r21;
  uint in_r29;
  byte *in_ep;
  
  *(undefined2 *)(in_r17 + 0xae4) = param_1;
  bVar2 = DAT_00006070;
  __nop();
  *(undefined4 *)(in_r17 + -0x81e) = in_r11;
  iVar3 = (int)DAT_ffff8a35;
  in_ep[0x40] = 0;
  in_ep[0x40] = 0;
  *(undefined4 *)(iVar3 + -0x3d1a) = in_r11;
  *(ushort *)(iVar3 + 0xae4) = (ushort)bVar2;
  __nop();
  uVar1 = *(ushort *)(in_ep + 0x24);
  *(int *)((*(ushort *)(in_ep + 0x24) & in_r21) - 0x81e) = in_r18 + 0x70;
  uVar4 = (uint)in_ep[0x35];
  in_ep[0x80] = 0;
  in_ep[0x81] = 0;
  in_ep[0x80] = 0;
  in_ep[0x81] = 0;
  *(undefined4 *)(uVar4 - 0x3d1a) = in_r11;
  *(ushort *)(uVar4 + 0xae4) = (ushort)bVar2;
  __nop();
  *(undefined4 *)
   ((uVar4 & in_r29 & uVar1 - 0x76ab & (uint)*(ushort *)(in_ep + 0x24) & in_r29) - 0x81e) = in_r11;
  __nop();
  *(short *)(*in_ep + 0xae4) = (short)(in_r18 + 0x70);
  *(undefined4 *)(in_ep[0x5d] - 0x81e) = in_r11;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

