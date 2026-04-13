
/* WARNING: Removing unreachable block (ram,0x010a61e0) */

void FUN_010a6186(int param_1,int param_2)

{
  undefined2 uVar1;
  uint uVar2;
  int in_r19;
  undefined2 in_r21;
  int iVar3;
  int in_ep;
  
  iVar3 = (uint)*(byte *)(in_ep + 1) + param_1;
  param_1 = param_1 + in_r19;
  *(undefined2 *)(param_1 + 0xcc) = in_r21;
  __nop();
  uVar2 = (uint)*(byte *)(param_1 + 0xc);
  uVar1 = *(undefined2 *)(param_1 + 0xfa);
  *(undefined1 *)(param_2 + -0x87) = 0;
  func_0x697b912c(uVar1);
  *(undefined2 *)(iVar3 + 0x7010) = 0;
  *(undefined2 *)(uVar2 + in_r19 + 0x94) = 0;
  return;
}

