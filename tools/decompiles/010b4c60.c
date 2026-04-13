
void FUN_010b4c60(char param_1)

{
  ushort uVar1;
  undefined4 unaff_gp;
  short in_r16;
  undefined1 *in_r17;
  undefined1 in_r19;
  uint in_r25;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  undefined2 in_lp;
  
  *(undefined2 *)(in_r25 + 0x74fe) = in_lp;
  uVar1 = *(ushort *)(in_ep + 0xa0);
  __nop();
  __nop();
  *(undefined4 *)(in_ep + 0xa0) = unaff_gp;
  __nop();
  *(char *)((int)(short)in_ep * (int)in_r16 + -0x2fa6) = (char)uVar1;
  *(undefined4 *)(in_ep + 0xa0) = 0;
  *(undefined2 *)((in_r25 & uVar1) + 0x2efe) = in_lp;
  *in_r17 = in_r19;
                    /* WARNING: Could not recover jumptable at 0x010b4cbe. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)((int)param_1);
  return;
}

