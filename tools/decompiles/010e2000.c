
void FUN_010e2000(short param_1,char param_2,uint param_3)

{
  undefined1 in_r11;
  undefined1 in_r13;
  undefined2 in_r15;
  int in_r19;
  int in_ep;
  uint uVar1;
  
  *(undefined1 *)(in_r19 + 6) = in_r11;
  uVar1 = (uint)*(byte *)(in_ep + 0x79);
  *(undefined1 *)(uVar1 + 0x6d) = in_r13;
  *(undefined2 *)(uVar1 + 0x82) = in_r15;
                    /* WARNING: Could not recover jumptable at 0x010e204c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)*(ushort *)(uVar1 + 6))(param_1 * 2,(int)param_2,param_3 | (uint)&stack0x00000000)
  ;
  return;
}

