
void FUN_010c4ea4(undefined4 param_1)

{
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  *(undefined4 *)(in_ep + 0x68) = param_1;
  *(undefined4 *)(in_ep + 0x68) = param_1;
  *(undefined4 *)(in_ep + 0x68) = param_1;
                    /* WARNING: Could not recover jumptable at 0x010c4ef6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(*(undefined2 *)(in_ep + 0x6a));
  return;
}

