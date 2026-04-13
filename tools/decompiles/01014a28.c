
void FUN_01014a28(int param_1,undefined4 param_2)

{
  undefined2 in_r19;
  int in_ep;
  
  while( true ) {
    __nop();
    *(undefined4 *)(in_ep + 0x78) = param_2;
    __nop();
    if ((int)((uint)*(ushort *)(in_ep + 0x7c) << 0x17) < 0) break;
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
  }
  (*(code *)0x0)(0,param_1);
  return;
}

