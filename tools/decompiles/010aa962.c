
/* WARNING: This function may have set the stack pointer */

void FUN_010aa962(uint param_1)

{
  undefined2 uVar1;
  short in_r2;
  byte unaff_gp;
  byte in_r24;
  int in_r25;
  
  *(uint *)(in_r25 + 0x5360) = param_1;
  uVar1 = *(undefined2 *)(param_1 + 0xa2);
  *(byte *)(*(ushort *)(param_1 + 0x3a) + 0x2444) = unaff_gp | in_r24;
  (*(code *)0x0)(param_1 / (uint)(int)in_r2,uVar1);
  return;
}

