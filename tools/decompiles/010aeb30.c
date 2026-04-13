
void FUN_010aeb30(undefined4 param_1)

{
  undefined2 in_r2;
  undefined1 unaff_tp;
  code *UNRECOVERED_JUMPTABLE;
  int in_ep;
  
  *(undefined2 *)(in_ep + 0x74) = in_r2;
  *(BADSPACEBASE **)(in_ep + 0xfc) = register0x0000000c;
  *(undefined1 *)(in_ep + 0x66) = unaff_tp;
  *(undefined4 *)(in_ep + 0xfc) = param_1;
  *(undefined2 *)(in_ep + 0x94) = *(undefined2 *)(in_ep + 0x54);
                    /* WARNING: Could not recover jumptable at 0x010aeb64. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

