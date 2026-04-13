
void FUN_010a95dc(void)

{
  undefined2 uVar1;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  undefined2 *in_ep;
  char local_7eab;
  
  uVar1 = *in_ep;
  in_ep[0xc] = uVar1;
  *(undefined2 **)(in_r25 + 0x5b6c) = in_ep;
  *(undefined4 *)(in_ep + 0x48) = 0;
  in_ep[0x28] = uVar1;
  *(undefined2 **)(in_r25 + 0x496c) = in_ep;
                    /* WARNING: Could not recover jumptable at 0x010a9614. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)((int)local_7eab);
  return;
}

