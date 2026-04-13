
/* WARNING: This function may have set the stack pointer */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0108310a(undefined4 param_1)

{
  int5 iVar1;
  undefined2 *puVar2;
  undefined1 in_r1;
  uint in_r12;
  uint uVar3;
  undefined4 in_r16;
  uint in_r23;
  uint in_r24;
  int in_r25;
  code *UNRECOVERED_JUMPTABLE;
  uint in_r29;
  int in_ep;
  undefined4 in_lp;
  ushort *in_CTBP;
  
  *(undefined1 *)(in_ep + 0x22) = in_r1;
  *(undefined4 *)(in_ep + 0xa8) = in_r16;
  uVar3 = in_r12 & in_r29;
  *(undefined4 *)(in_ep + 100) = param_1;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(&DAT_ffff9b59,*(undefined1 *)(in_ep + 0x4f));
  puVar2 = _LAB_00000030;
  *(undefined1 *)(_LAB_00000030 + 0x10) = in_r1;
  iVar1 = (int5)(int)((uVar3 | in_r24) ^ in_r23) + -0x134;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *puVar2 = *puVar2;
  *(undefined4 *)(in_r25 + -0x5c18) = in_lp;
                    /* WARNING: Could not recover jumptable at 0x010831a4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(0,(uint)iVar1 ^ in_r23);
  return;
}

