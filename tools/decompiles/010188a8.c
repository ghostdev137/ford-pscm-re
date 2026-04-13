
void FUN_010188a8(int param_1,undefined4 param_2)

{
  uint in_r1;
  undefined2 in_r19;
  int in_ep;
  
  while (__nop(), -1 < (int)(in_r1 << 0x17)) {
    param_1 = *(int *)(in_ep + 0x1c) << 0x13;
    uRam000064bb = (undefined1)in_r19;
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
    __nop();
    in_r19 = *(undefined2 *)(in_ep + 0xe);
    __nop();
    *(undefined4 *)(in_ep + 0x78) = param_2;
    in_r1 = (uint)*(ushort *)(in_ep + 0x7c);
  }
  (*(code *)0x0)(0,param_1);
  return;
}

