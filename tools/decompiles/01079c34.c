
void FUN_01079c34(uint param_1)

{
  int5 iVar1;
  undefined1 in_r12;
  int in_r17;
  int in_ep;
  int iVar2;
  ushort *in_CTBP;
  
  *(undefined2 *)(in_ep + 0xfe) = *(undefined2 *)(in_ep + 0xb0);
  *(undefined1 *)(in_ep + 0x42) = in_r12;
  iVar1 = (int5)in_r17 - (int5)in_ep;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  iVar2 = (int)iVar1;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))
            (*(undefined4 *)(in_ep + 0x90),param_1 / (uint)(int)*(short *)(in_ep + 0xb0));
  *(uint *)(iVar2 + 0xf8) = (uint)*(ushort *)(iVar2 + 0xfa);
  func_0x29486222(*(undefined2 *)(iVar2 + 2));
  (*(code *)&LAB_00000030)(0xfffffffd);
  return;
}

