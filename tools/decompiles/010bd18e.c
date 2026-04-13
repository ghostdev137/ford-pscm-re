
void FUN_010bd18e(int param_1)

{
  undefined1 in_r1;
  undefined2 in_r15;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  int in_ep;
  undefined2 in_lp;
  
  *(undefined2 *)(in_r25 + 0x3316) = in_lp;
  *(undefined2 *)(in_ep + 0xc4) = in_r15;
  *(undefined1 *)(in_ep + 0x24) = in_r1;
  (&DAT_00005348)[param_1] = (char)*(undefined2 *)(in_ep + 2);
                    /* WARNING: Could not recover jumptable at 0x010bd1ce. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

