
void FUN_01084fa0(uint param_1)

{
  char cVar1;
  undefined1 in_r1;
  uint in_r21;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  *(undefined1 *)(in_ep + 0x62) = in_r1;
  cVar1 = DAT_00000018;
  func_0x00f056bc((int)cVar1,param_1 ^ in_r21);
  func_0x00f058ca();
                    /* WARNING: Could not recover jumptable at 0x01084ff2. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

