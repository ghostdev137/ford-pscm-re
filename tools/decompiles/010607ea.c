
void FUN_010607ea(int param_1,undefined4 param_2)

{
  undefined1 in_r2;
  undefined4 in_r17;
  uint in_r21;
  uint uVar1;
  undefined4 in_r25;
  undefined4 in_r29;
  int in_ep;
  
  *(uint *)(in_ep + 0xac) = in_r21;
  *(undefined4 *)(in_ep + 0xac) = in_r29;
  uVar1 = in_r21 / (uint)(int)(short)in_r29;
  *(short *)(in_ep + 0xd0) = (short)&stack0x00000000;
  (&DAT_00002136)[param_1] = in_r2;
  *(char *)(in_ep + 0x5a) = (char)uVar1;
  *(undefined4 *)(in_ep + 0x6c) = in_r25;
  *(uint *)(in_ep + 0xac) = uVar1;
  *(undefined4 *)(in_ep + 0x6c) = in_r17;
  *(undefined4 *)(in_ep + 0xac) = *(undefined4 *)(in_ep + 0x68);
  *(undefined4 *)(in_ep + 0x60) = param_2;
  return;
}

