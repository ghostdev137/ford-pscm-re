
/* WARNING: Instruction at (ram,0x010e37ce) overlaps instruction at (ram,0x010e37cc)
    */

void FUN_010e37a4(int param_1,short param_2)

{
  int5 iVar1;
  byte bVar2;
  byte bVar3;
  ushort uVar4;
  undefined4 unaff_tp;
  char cVar5;
  int in_r10;
  ushort uVar6;
  int in_r12;
  undefined2 in_r13;
  undefined4 in_r15;
  int in_r17;
  undefined1 in_r19;
  int in_r20;
  int in_r21;
  code *UNRECOVERED_JUMPTABLE;
  int in_r25;
  undefined4 in_r27;
  int in_r29;
  undefined2 *in_ep;
  ushort *puVar7;
  int in_lp;
  uint in_PSW;
  undefined1 auStack_2e [46];
  
  *(undefined4 *)(in_ep + 0x56) = in_r15;
  *(undefined1 *)(in_ep + 0x33) = 0;
  *(undefined4 *)(in_ep + 0x56) = in_r15;
  *in_ep = in_r13;
  *(int *)(in_r25 + 0x4bd0) = in_lp;
  bVar2 = *(byte *)(in_ep + 0x28);
  if ((bool)((byte)(in_PSW >> 3) & 1)) {
    in_r19 = *(undefined1 *)(in_r29 + -0x337d);
  }
  else {
    *(short *)(in_r12 + 0xf04) = (short)unaff_tp;
    *(undefined4 *)(in_r12 + -0x60e4) = unaff_tp;
    in_ep[3] = (short)in_r25;
  }
  uVar4 = in_ep[0x50];
  __nop();
  *(undefined4 *)(in_ep + 0x36) = in_r27;
  *(short *)(in_r25 + -0x682e) = (short)in_lp;
  iVar1 = -(int5)param_1;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined1 *)((int)in_ep + 0x4b) = in_r19;
  uVar6 = (ushort)in_r12 | (ushort)UNRECOVERED_JUMPTABLE;
  *(char *)(in_ep + 0x25) = (char)in_r17;
  cVar5 = (char)in_ep[0x49];
  *(char *)((int)in_ep + 0x49) = (char)in_lp;
  puVar7 = (ushort *)(uint)*(byte *)((int)in_ep + 0x79);
  if (in_r10 == -1) {
    *(undefined1 *)(in_r17 + -0x1be7) = 0;
    *(byte *)(*(int *)(puVar7 + 0x7c) + -0x1fe7) = bVar2;
    *(undefined1 *)(in_r21 + -0x1be7) = 0;
    *(undefined1 *)(in_r17 + -0x17e7) = in_r19;
    uVar6 = puVar7[0x7d];
    *(undefined1 *)(in_r21 + -0x17e7) = in_r19;
    bVar3 = *(byte *)((int)puVar7 + 0x7d);
    *(short *)(uVar4 + 0x145a) = (short)auStack_2e;
    *(undefined1 *)(bVar2 - 0x4c00) = 0;
    *(undefined1 *)(puVar7 + 0x31) = 0;
    *(undefined1 *)(bVar2 - 0x4800) = 0;
    *puVar7 = (ushort)bVar3;
    *(int *)(in_r25 + -0x4640) = in_lp;
    do {
      *(undefined1 *)(uVar6 + 0x400) = 0;
      *(int *)(in_r25 + 0x5c2) = in_lp + -0x10;
      *(undefined1 *)(puVar7 + 0x25) = in_r19;
      *(char *)((int)puVar7 + 0x49) = (char)(in_lp + -0x10);
      puVar7 = (ushort *)(uint)*(byte *)((int)puVar7 + 0x79);
    } while( true );
  }
  func_0x02a66878((uint)iVar1 / (uint)(int)param_2);
  *(char *)((int)puVar7 + 0x59) = (char)puVar7[0xc];
  uVar4 = puVar7[1];
  *(ushort *)(uVar4 + 0xd0) = uVar6;
  *(int *)(uVar4 + 0x90) = (int)cVar5;
                    /* WARNING: Could not recover jumptable at 0x010e3872. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(in_r20 + 0x2c360000);
  return;
}

