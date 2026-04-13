
void FUN_010987fa(int param_1,int param_2)

{
  uint in_r1;
  undefined4 in_r17;
  int in_r29;
  int in_ep;
  
  *(undefined4 *)(in_r29 + -0x2e3c) = in_r17;
  *(short *)((in_ep + param_1 ^ in_r1) + 0x8e) = (short)in_r17;
                    /* WARNING: Could not recover jumptable at 0x01098828. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_0109882a + *(short *)(&LAB_0109882a + param_2 * 2) * 2))();
  return;
}

