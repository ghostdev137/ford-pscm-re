
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0100d18c(uint param_1)

{
  int5 iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  code *UNRECOVERED_JUMPTABLE;
  int in_CTBP;
  
  uVar3 = (uint)_DAT_00005101 >> 0x10;
  _DAT_00005101 = &DAT_ffffaaaa + uVar3;
  __nop();
  __nop();
  __nop();
  __nop();
  uVar2 = (uint)(char)(&DAT_ffffaaaa)[(char)(&DAT_ffffaaaa)[uVar3]];
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  _DAT_00001501 = (int)(char)(&DAT_ffffaaaa)[uVar2];
  __nop();
  __nop();
  __nop();
  __nop();
  uVar4 = (uint)(char)(&DAT_ffffaaaa)[uVar2];
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  _DAT_00001201 = 0;
  iVar1 = (int5)(int)((uint)(&DAT_ffffaaaa + uVar2) >> 0x10) + -0xf;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  __nop();
  __nop();
  uVar3 = (int)(short)(char)(&DAT_ffffaaaa)[uVar3] * (int)(short)iVar1;
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  __nop();
  (*(code *)(in_CTBP + (uint)*(ushort *)(in_CTBP + 2)))
            (param_1 | uVar2 | uVar3 | uVar2 | uVar2 | uVar2 | uVar4 | uVar3 | uVar2 | uVar4 | uVar3
             | uVar2 | uVar3 | uVar4 | uVar2 | uVar3 | uVar4,(int)DAT_00004800,
             (int)*(char *)(uVar2 + 0x5c01));
  (*(code *)(in_CTBP + (uint)*(ushort *)(in_CTBP + 2)))();
  __nop();
                    /* WARNING: Could not recover jumptable at 0x0100d542. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)();
  return;
}

