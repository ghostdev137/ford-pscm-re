
void FUN_01072dbe(int param_1)

{
  int iVar1;
  uint in_r2;
  short sVar2;
  byte in_r12;
  int in_r15;
  undefined4 in_r17;
  code *UNRECOVERED_JUMPTABLE;
  undefined4 in_r21;
  byte in_r28;
  int in_ep;
  
  iVar1 = in_ep - in_r15;
  *(char *)(iVar1 + 0x68) = (char)in_r15;
  *(char *)(param_1 + -0x52ac) = (char)(in_r2 / (uint)(int)(short)param_1);
  *(undefined4 *)(iVar1 + 0xbc) = in_r21;
  *(byte *)(iVar1 + 0x68) = in_r12 | in_r28 | in_r28 | in_r28 | in_r28;
  *(undefined4 *)(iVar1 + 0xbc) = in_r21;
  *(undefined4 *)(iVar1 + 8) = *(undefined4 *)(iVar1 + 0x9c);
  *(undefined4 *)(iVar1 + 0xa8) = in_r17;
  UNRECOVERED_JUMPTABLE = (code *)0x1072e28;
  func_0x00f68f40();
  sVar2 = (short)param_1;
  func_0x00f68f48();
  func_0x00f63e7c();
                    /* WARNING: Could not recover jumptable at 0x01072e42. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(sVar2 * 0x2136);
  return;
}

