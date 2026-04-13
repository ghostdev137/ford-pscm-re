
/* WARNING: Instruction at (ram,0x010b2972) overlaps instruction at (ram,0x010b2970)
    */

void FUN_010b2902(int param_1,uint param_2)

{
  byte *pbVar1;
  ushort uVar2;
  undefined2 uVar3;
  char cVar4;
  ushort uVar5;
  short in_r2;
  uint unaff_gp;
  uint uVar6;
  short unaff_tp;
  char cVar7;
  int in_r10;
  uint in_r24;
  int in_r25;
  uint in_r26;
  uint in_r29;
  int in_ep;
  int iVar8;
  undefined2 in_lp;
  uint uVar9;
  bool bVar10;
  uint in_PSW;
  
  cVar7 = (char)param_2;
  if (-1 < unaff_tp * -0x61cf) {
    *(undefined2 *)(in_r25 + -0x7618) = in_lp;
  }
  *(char *)(in_ep + 0x62) = (char)in_r2;
  uVar6 = (uint)*(byte *)(in_ep + 0x48);
  *(ushort *)(in_r25 + 0x43f8) = (ushort)in_r29 | 0xe97;
  uVar9 = in_r26 | 0x802c;
  bVar10 = (int)in_r2 * (int)in_r2 == -1;
  if (&stack0x00000000 < (undefined1 *)0x165) {
    if (-1 < (int)(in_r24 | 0xc18)) {
      *(short *)(in_r25 + 0x3de8) = (short)(in_r24 | 0xc18);
    }
    uVar9 = in_r29 | 0xff79;
    bVar10 = uVar9 == 0;
    if ((bool)((byte)(in_PSW >> 4) & 1) || unaff_gp < param_2) {
      *(uint *)(in_r25 + -0x204) = uVar9;
    }
    uVar6 = (short)cVar7 * 0x7e59;
  }
  __nop();
  if (bVar10) {
    uVar2 = *(ushort *)(in_ep + 0xa2);
    uVar3 = *(undefined2 *)(in_ep + 0xa2);
    uVar5 = *(ushort *)(in_r10 + -0x313a);
    iVar8 = (short)in_ep * 6;
    *(char *)(iVar8 + 0x41) = cVar7;
    *(short *)(iVar8 + 0x68) = (short)uVar9;
                    /* WARNING: Could not recover jumptable at 0x010bc7d0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*(code *)(uint)uVar2)(*(undefined2 *)(iVar8 + 4),uVar5 & 0x5ec6,uVar3);
    return;
  }
  pbVar1 = (byte *)(cVar7 + 0x1ce6);
  *pbVar1 = *pbVar1 | 2;
  cVar4 = *(char *)(uVar6 + 0xb18);
  *(short *)(in_ep + 0x50) = *(short *)(cVar7 + 0x6b18) * 2 - (short)cVar7;
                    /* WARNING: Could not recover jumptable at 0x010b29ae. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(param_1 + -0x7f8effe0))((int)cVar4);
  return;
}

