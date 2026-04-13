
void FUN_0109ac3e(int param_1,int param_2)

{
  undefined1 uVar1;
  int in_r19;
  int in_r25;
  
  __nop();
  uVar1 = *(undefined1 *)(param_1 + in_r19 + 0x59);
  *(char *)(in_r25 + 0x400) = (char)in_r19;
                    /* WARNING: Could not recover jumptable at 0x0109ac66. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_0109ac68 + *(short *)(&LAB_0109ac68 + param_2 * 2) * 2))
            (uVar1,*(undefined2 *)(param_1 + in_r19 + 0x3a));
  return;
}

