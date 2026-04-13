
void FUN_010b93fc(uint param_1,int param_2,undefined2 param_3)

{
  char cVar1;
  undefined2 in_r15;
  int in_r19;
  code *UNRECOVERED_JUMPTABLE;
  int in_r29;
  int in_ep;
  undefined2 in_lp;
  uint in_PSW;
  
  *(int *)(in_ep + 0xb0) = param_2;
  if (!(bool)((byte)(in_PSW >> 2) & 1)) {
    cVar1 = (char)param_2;
    __nop();
    if (((byte)(in_PSW >> 1) & 1) == ((byte)(in_PSW >> 2) & 1)) {
      *(short *)(in_r29 + 0x711c) = (short)cVar1;
      *(undefined1 *)(in_ep + 0x66) = 0;
                    /* WARNING: Could not recover jumptable at 0x010b9418. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*(code *)(&LAB_010b941a + *(short *)(&LAB_010b941a + cVar1 * 2) * 2))();
      return;
    }
    param_2 = cVar1 + in_r19;
    *(short *)(in_ep + 0xcc) = (short)&stack0x00000000;
    *(undefined2 *)(in_ep + 0x84) = 0xfff8;
    *(undefined2 *)(in_ep + 0x80) = in_lp;
    param_1 = (uint)*(byte *)(in_ep + 0xc);
    *(undefined2 *)(UNRECOVERED_JUMPTABLE + 0x6e00) = in_r15;
    *(undefined2 *)(in_ep + 0x88) = param_3;
  }
  *(undefined2 *)(in_ep + 0xa8) = param_3;
  func_0x00edf648(param_1,param_2);
                    /* WARNING: Could not recover jumptable at 0x010b9494. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

