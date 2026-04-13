
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_010d81dc(int param_1,int param_2)

{
  undefined1 uVar1;
  uint uVar2;
  uint uVar3;
  int in_r20;
  undefined2 in_r24;
  int in_r28;
  uint *in_ep;
  byte bVar4;
  ushort uVar5;
  uint in_lp;
  uint uVar6;
  ushort *in_CTBP;
  
  bVar4 = *(byte *)((int)in_ep + 0x51);
  uVar1 = (undefined1)(short)*in_ep;
  *(char *)in_ep = (char)*(undefined2 *)((int)in_ep + 2);
  in_ep[6] = in_lp;
  *(undefined2 *)(in_r28 + 0x2e52) = in_r24;
  (*(code *)((int)in_CTBP + (uint)in_CTBP[1]))();
  uVar3 = (uint)*(ushort *)((int)in_ep + 0x1a);
  *(undefined1 *)(param_2 + 0xbe1) = 0;
  uVar5 = bVar4 | 0xca18;
  (*(code *)((int)in_CTBP + (uint)in_CTBP[1]))(0xfffffff9);
  uVar2 = (uint)*(ushort *)((int)in_ep + 0x1a);
  *(char *)((int)in_ep + 0x65) = (char)uVar5;
  __nop();
  *(int *)(in_r20 + -0x2f6) = in_r28;
  *(ushort *)(in_ep + 2) = uVar5;
  in_ep[6] = uVar2;
  *in_ep = uVar2;
  uVar6 = 0x10d8242;
  func_0x011269b2(0xfffffff9);
  in_ep[6] = uVar6;
  *(undefined2 *)(in_r28 + 0x2e5a) = in_r24;
  (*(code *)((int)in_CTBP + (uint)in_CTBP[1]))();
  in_ep[6] = uVar2;
  *(undefined1 *)((int)in_ep + 0x61) = uVar1;
  bVar4 = bVar4 | 0x18;
  (*(code *)((int)in_CTBP + (uint)in_CTBP[1]))();
  in_ep[6] = uVar3;
  *(byte *)((int)in_ep + 0x65) = bVar4;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  return param_1 + 0x5706;
}

