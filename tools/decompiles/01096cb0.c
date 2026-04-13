
void FUN_01096cb0(void)

{
  int5 iVar1;
  byte bVar2;
  undefined4 uVar3;
  undefined2 uVar4;
  code *UNRECOVERED_JUMPTABLE;
  undefined1 in_r25;
  int in_r29;
  undefined2 *in_ep;
  int in_lp;
  undefined4 uVar5;
  ushort *in_CTBP;
  
  bVar2 = *(byte *)(in_ep + 0x3e);
  *(short *)(bVar2 + 0x143a) = (short)in_ep;
  iVar1 = (int5)in_r29 + 0x51e8;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar4 = (undefined2)iVar1;
  *(short *)(bVar2 - 0x51e8) = (short)in_lp;
  __nop();
  *(undefined1 *)(in_ep + 0x20) = in_r25;
  uVar3 = *(undefined4 *)(in_ep + 0x18);
  in_ep[0x66] = (short)&stack0x00000000;
  in_ep[100] = in_ep[0xd];
  iVar1 = (int5)in_lp + 1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar5 = (undefined4)iVar1;
  __nop();
  if (in_lp >= 0 && in_lp < 0 != in_lp + 1 < 0) {
    in_ep[0x18] = uVar4;
    in_ep[0x66] = (short)uVar3;
    (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
    __nop();
    *(undefined1 *)(in_ep + 0x20) = in_r25;
    *(byte *)(in_ep + 0x33) = ~(byte)uVar3;
    *(char *)(in_ep + 0x32) = (char)*(undefined4 *)(in_ep + 0x18);
    *(undefined4 *)(in_ep + 0x20) = uVar5;
    __nop();
    *in_ep = uVar4;
    __nop();
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x01096cf6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

