
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0106da7e(void)

{
  int5 iVar1;
  undefined4 in_r11;
  undefined4 in_r12;
  undefined4 in_r14;
  int in_r28;
  int in_ep;
  uint uVar2;
  undefined4 *puVar3;
  ushort *in_CTBP;
  
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  *(char *)(in_ep + 0x3e) = (char)in_r14;
  *(undefined4 *)(in_ep + 0x60) = in_r14;
  *(undefined1 *)(in_ep + 0x28) = 0;
  *(undefined1 *)(in_ep + 0x62) = 0;
  *(undefined4 *)(in_ep + 0x60) = in_r14;
  *(undefined4 *)(in_ep + 8) = in_r12;
  *(undefined4 *)(in_ep + 100) = 0xfffffff8;
  iVar1 = (int5)in_ep + 0xd;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar2 = (uint)*(byte *)((int)iVar1 + 0x2d);
  puVar3 = (undefined4 *)(uint)*(ushort *)(uVar2 + 0x5a);
  DAT_00006d34 = (undefined1)*(undefined4 *)(uVar2 + 0x60);
  *puVar3 = in_r11;
  if (in_r28 != 0) {
    puVar3[0x18] = 5;
    puVar3[0x1a] = 5;
  }
  *(undefined1 *)((int)puVar3 + 0x66) = 0;
  *(undefined1 *)((int)puVar3 + 0x62) = 0;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

