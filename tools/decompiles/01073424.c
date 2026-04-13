
void FUN_01073424(uint param_1,undefined4 param_2)

{
  undefined4 unaff_tp;
  int in_r20;
  int in_ep;
  
  *(undefined4 *)(in_ep + 0x60) = unaff_tp;
  *(int *)(in_ep + 0xa0) = in_r20 + 0x10000000;
  *(undefined4 *)(in_ep + 0xa0) = param_2;
                    /* WARNING: Could not recover jumptable at 0x0107348e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_01073490 +
            *(short *)(&LAB_01073490 +
                      (param_1 & *(uint *)(in_ep + 0xa0) ^ *(uint *)(in_ep + 0xa0)) * 2) * 2))();
  return;
}

