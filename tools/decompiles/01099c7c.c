
/* WARNING: Removing unreachable block (ram,0x01099d0e) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_01099c7c(int param_1,undefined2 param_2)

{
  int5 iVar1;
  undefined2 uVar2;
  char cVar3;
  uint unaff_gp;
  int iVar4;
  undefined1 in_r15;
  int in_r17;
  uint uVar5;
  int in_r19;
  short *psVar6;
  undefined2 in_r22;
  uint in_r24;
  int in_r25;
  ushort uVar7;
  int in_ep;
  uint uVar8;
  undefined4 in_lp;
  
  __nop();
  psVar6 = (short *)(in_r25 + 0xc50);
  *(undefined2 *)(in_ep + 0x8e) = in_r22;
  *(undefined1 *)(in_r17 + 0x400) = in_r15;
  *(undefined2 *)(in_ep + 0x8e) = in_r22;
  __nop();
  param_1 = param_1 + in_r19;
  uVar2 = *(undefined2 *)(param_1 + 2);
  iVar1 = (int5)(int)(unaff_gp | in_r24) - (int5)(int)in_r24;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  *(short *)(param_1 + 0xc4) = (short)*(char *)(in_r25 + 0x1c8);
  uVar7 = (ushort)*(byte *)(param_1 + 0x1f);
  *(short *)(in_r17 + 0x290) = (short)&stack0x00000000;
  FUN_0109cd18(uVar2);
  *(undefined2 *)(param_1 + 0xc0) = param_2;
  __nop();
  uVar8 = (uint)*(byte *)(param_1 + 7);
  *(undefined4 *)(in_r25 + 0x3dfe) = in_lp;
  *(ushort *)(uVar8 + 0x6e) = uVar7;
  cVar3 = *(char *)((int)iVar1 + -0x568d);
  uVar5 = (uint)*(byte *)(uVar8 + 0x1d);
  uVar2 = *(undefined2 *)(uVar8 + 0xa2);
  __nop();
  *(short *)(in_r25 + -0x4606) = (short)in_lp;
  FUN_0109a66c((int)cVar3,uVar2);
  iVar4 = *(int *)(uVar8 + 0xd0);
  *(int *)(&stack0x00000000 + uVar8) = (int)*psVar6;
  *(short *)(uVar5 + 0x290) = (short)&stack0x00000000;
                    /* WARNING: Could not recover jumptable at 0x01099d98. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(iVar4 + 0x2e0a870))();
  return;
}

