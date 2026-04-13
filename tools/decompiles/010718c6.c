
void FUN_010718c6(uint param_1,uint param_2)

{
  byte *pbVar1;
  ushort uVar2;
  char cVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  undefined1 in_r2;
  short in_r11;
  uint in_r13;
  uint in_r23;
  uint in_r24;
  uint uVar7;
  uint *in_ep;
  
  in_ep[0x1b] = in_r13;
  uVar2 = *(ushort *)((int)in_ep + 0x52);
  (&DAT_00006137)[param_1] = in_r2;
  uVar7 = in_ep[0x1a];
  in_ep[0x14] = (uint)uVar2;
  in_ep[6] = param_1;
  in_ep[0x2b] = param_2;
  uVar6 = in_ep[0x2a];
  uVar4 = in_ep[0x31];
  in_ep[0x2b] = param_2;
  uVar2 = *(ushort *)((int)in_ep + 0x56);
  *(undefined1 *)(in_ep + 0x10) = 0;
  uVar5 = in_ep[0x15];
  *in_ep = param_1 & in_r23;
  (&DAT_00002136)[param_1 & in_r23] = 0;
  cVar3 = *(char *)(uVar6 - 0x487);
  pbVar1 = (byte *)(~(uint)(ushort)uVar4 - 0x12c9);
  *pbVar1 = *pbVar1 ^ 0x10;
  in_ep[0x2b] = uVar7;
                    /* WARNING: Could not recover jumptable at 0x01071942. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(in_r24 & (uint)&stack0x00000000))
            ((short)uVar5,(uint)uVar2 / (uint)(int)in_r11,(int)cVar3,uVar6);
  return;
}

