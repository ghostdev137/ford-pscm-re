
void FUN_01096cde(undefined2 param_1)

{
  int5 iVar1;
  undefined2 in_r1;
  undefined2 in_r2;
  code *UNRECOVERED_JUMPTABLE;
  undefined1 in_r25;
  undefined2 *in_ep;
  int in_lp;
  undefined4 uVar2;
  ushort *in_CTBP;
  
  in_ep[100] = in_r1;
  iVar1 = (int5)in_lp + 1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar2 = (undefined4)iVar1;
  __nop();
  if (in_lp >= 0 && in_lp < 0 != in_lp + 1 < 0) {
    in_ep[0x18] = param_1;
    in_ep[0x66] = in_r2;
    (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
    __nop();
    *(undefined1 *)(in_ep + 0x20) = in_r25;
    *(byte *)(in_ep + 0x33) = ~(byte)in_r2;
    *(char *)(in_ep + 0x32) = (char)*(undefined4 *)(in_ep + 0x18);
    *(undefined4 *)(in_ep + 0x20) = uVar2;
    __nop();
    *in_ep = param_1;
    __nop();
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x01096cf6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

