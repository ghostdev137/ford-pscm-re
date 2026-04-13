
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010105fc(void)

{
  int5 iVar1;
  uint in_r2;
  uint uVar2;
  int unaff_tp;
  undefined2 in_r11;
  undefined4 uVar3;
  int in_r29;
  int in_ep;
  uint uVar4;
  
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  uVar2 = in_r2 & (uint)&stack0x00000000;
  __nop();
  __nop();
  if ((int)uVar2 < 0) {
    __nop();
    uVar4 = (uint)*(ushort *)(in_ep + 2);
    __nop();
    __nop();
    __nop();
    __nop();
    *(undefined1 *)(uVar2 - 0x69be) = 0;
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
    *(undefined2 *)(uVar4 + 0x1e) = in_r11;
    uVar3 = *(undefined4 *)(*(byte *)(uVar4 + 0x3d) + 0x4a3c);
    iVar1 = (int5)unaff_tp - (int5)(int)uVar4;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    *(int *)((int)iVar1 + 0x78) = (int)*(short *)(in_r29 + -0x34f0);
    *(undefined4 *)((int)iVar1 + 0xd8) = uVar3;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  __nop();
  __nop();
                    /* WARNING: Could not recover jumptable at 0x010105bc. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&DAT_010105be + *(short *)(&DAT_010105be + uVar2 * 2) * 2))
            (*(undefined2 *)(in_ep + 0x7e));
  return;
}

