
/* WARNING: This function may have set the stack pointer */

void FUN_010bcdea(undefined4 param_1)

{
  byte bVar1;
  byte bVar2;
  ushort uVar3;
  undefined2 uVar4;
  short unaff_tp;
  undefined4 uVar5;
  int in_r16;
  char cVar6;
  int in_r18;
  undefined1 *in_r22;
  undefined1 in_r23;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  undefined4 *in_ep;
  int iVar7;
  undefined2 in_lp;
  
  *(char *)(int)*(short *)(in_r18 + 0x200) = (char)in_ep;
  uVar3 = *(ushort *)((int)in_ep + 2);
  UNRECOVERED_JUMPTABLE = (code *)(uint)uVar3;
  *in_ep = in_r22;
  uVar5 = in_ep[1];
  bVar1 = *(byte *)((int)in_ep + 1);
  *(undefined2 *)(in_r25 + -0x58e8) = in_lp;
  bVar2 = *(byte *)(bVar1 + 0x2a);
  *(char *)(in_r16 + 0x400) = (char)in_r22;
  *(undefined4 *)(in_r16 + -0x6360) = 0;
  iVar7 = *(int *)(bVar1 + 8);
  *(undefined4 *)(iVar7 + 0x60) = param_1;
  cVar6 = (char)uVar3 + -0x58;
  func_0x00f3ec32(uVar5);
  *(char *)(in_r16 + 0x400) = cVar6;
  uVar4 = *(undefined2 *)(iVar7 + 0xd8);
  cVar6 = *(char *)((int)unaff_tp * (int)(short)(ushort)bVar2 + 0x607f);
  *in_r22 = in_r23;
                    /* WARNING: Could not recover jumptable at 0x010bce88. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(uVar4,(int)cVar6);
  return;
}

