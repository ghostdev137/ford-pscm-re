
void FUN_010c01c4(int param_1)

{
  int5 iVar1;
  undefined1 uVar2;
  undefined2 in_r10;
  short in_r18;
  uint in_r24;
  int in_r25;
  int in_ep;
  
  uVar2 = *(undefined1 *)(in_ep + 0x4a);
  iVar1 = (int5)in_r25 + 0x32fd;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined2 *)((int)iVar1 + 0x80) = in_r10;
  __nop();
                    /* WARNING: Could not recover jumptable at 0x010c020c. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(in_r24 / (uint)(int)in_r18))(param_1 + -0xf,uVar2,0xfffffffd);
  return;
}

