
void FUN_0105b778(short param_1)

{
  ushort uVar1;
  ushort uVar2;
  char in_r1;
  code *UNRECOVERED_JUMPTABLE;
  ushort *in_ep;
  undefined2 in_lp;
  
  uVar1 = in_ep[1];
  uVar2 = in_ep[0x51];
  __nop();
  *(undefined2 *)(*in_ep + 0x3afe) = in_lp;
                    /* WARNING: Could not recover jumptable at 0x0105b79e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(uVar1,param_1 * -2,(int)(char)(in_r1 + 'Q'),uVar2);
  return;
}

