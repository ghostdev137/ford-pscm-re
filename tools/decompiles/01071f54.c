
void FUN_01071f54(undefined1 param_1,int param_2)

{
  int *piVar1;
  ushort *puVar2;
  undefined1 uVar4;
  ushort uVar5;
  char cVar6;
  ushort uVar7;
  int unaff_tp;
  short sVar8;
  ushort in_r12;
  undefined2 in_r16;
  code *UNRECOVERED_JUMPTABLE;
  int iVar9;
  ushort *in_ep;
  int iVar10;
  int5 iVar3;
  
  FUN_010ba6d0();
  uVar5 = *in_ep;
  *(int *)(in_ep + 0x54) = unaff_tp;
  in_ep[100] = in_r12;
  cVar6 = *(char *)(unaff_tp + -0x38c);
  *(undefined1 *)(cVar6 + -0x78e5) = param_1;
  iVar3 = (int5)param_2 + (int5)(int)cVar6;
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = -0x80000000;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  piVar1 = (int *)iVar3;
  uVar4 = *(undefined1 *)((int)piVar1 + 0x16);
  sVar8 = (short)param_2;
  DAT_ffff8c19 = DAT_ffff8c19 | 0x80;
  *(undefined2 *)(uVar5 + 0x5030) = 1;
  piVar1[0x2a] = sVar8 * 0x18;
  iVar9 = *piVar1;
  *(char *)(piVar1 + 0x19) = (char)param_2;
  iVar10 = (int)*(char *)(sVar8 * 0x18 + -0x38c);
  *(undefined1 *)(iVar10 + -0x7ae5) = uVar4;
  iVar3 = (int5)param_2 + (int5)iVar10;
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = -0x80000000;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  puVar2 = (ushort *)iVar3;
  uVar7 = puVar2[0xb];
  DAT_ffff8c19 = DAT_ffff8c19 | 0x80;
  *(undefined2 *)(iVar9 + 0x5030) = in_r16;
  *(int *)(puVar2 + 0x54) = sVar8 * 0x18;
  uVar5 = *puVar2;
  iVar9 = (int)*(char *)(sVar8 * 0x18 + -0x38c);
  *(char *)(iVar9 + -0x78e5) = (char)uVar7;
  iVar3 = (int5)param_2 + (int5)iVar9;
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = -0x80000000;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  uVar4 = *(undefined1 *)((int)iVar3 + 0x16);
  DAT_ffff8c19 = DAT_ffff8c19 | 0x80;
  *(undefined2 *)(uVar5 + 0x5030) = 1;
  *(int *)((int)iVar3 + 0xa8) = sVar8 * 0x18;
  FUN_010bed8c(uVar4);
  DAT_ffff8c18 = DAT_ffff8c18 | 0x80;
                    /* WARNING: Could not recover jumptable at 0x0107204a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

