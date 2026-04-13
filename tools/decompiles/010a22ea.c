
void FUN_010a22ea(undefined4 param_1)

{
  undefined2 *puVar1;
  int in_r16;
  int in_r25;
  int in_r29;
  int in_ep;
  undefined2 in_lp;
  
  puVar1 = (undefined2 *)(in_r29 - in_ep);
  *puVar1 = *puVar1;
  *(undefined2 *)(in_r25 + -0x3c08) = in_lp;
  if (in_r16 < -0x80000000) {
    if (in_r16 < -0x80000000) {
      in_r16 = -0x80000000;
    }
  }
  else {
    in_r16 = 0x7fffffff;
  }
  __nop();
  __nop();
                    /* WARNING: Could not recover jumptable at 0x010a2370. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010a2372 + *(short *)(&LAB_010a2372 + (uint)*(byte *)(puVar1 + 0x36) * 2) * 2))
            (in_r16,param_1);
  return;
}

