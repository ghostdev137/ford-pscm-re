
void FUN_010718ee(uint param_1,uint param_2)

{
  byte *pbVar1;
  ushort uVar2;
  char cVar3;
  uint uVar4;
  uint uVar5;
  int in_r1;
  short in_r11;
  uint in_r23;
  code *UNRECOVERED_JUMPTABLE;
  uint in_r29;
  uint *in_ep;
  
  uVar4 = in_ep[0x31];
  in_ep[0x2b] = param_2;
  uVar2 = *(ushort *)((int)in_ep + 0x56);
  *(undefined1 *)(in_ep + 0x10) = 0;
  uVar5 = in_ep[0x15];
  *in_ep = param_1 & in_r23;
  (&DAT_00002136)[param_1 & in_r23] = 0;
  cVar3 = *(char *)(in_r1 + -0x487);
  pbVar1 = (byte *)(~(uint)(ushort)uVar4 - 0x12c9);
  *pbVar1 = *pbVar1 ^ 0x10;
  in_ep[0x2b] = in_r29;
                    /* WARNING: Could not recover jumptable at 0x01071942. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)((short)uVar5,(uint)uVar2 / (uint)(int)in_r11,(int)cVar3,in_r1);
  return;
}

