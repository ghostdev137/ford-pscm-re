
/* WARNING: Removing unreachable block (ram,0x01072176) */
/* WARNING: Removing unreachable block (ram,0x010720f6) */

void FUN_01072134(void)

{
  ushort uVar1;
  undefined1 uVar2;
  ushort uVar3;
  char cVar4;
  uint unaff_gp;
  undefined1 unaff_tp;
  short in_r11;
  uint in_r15;
  int in_r17;
  code *UNRECOVERED_JUMPTABLE;
  code *UNRECOVERED_JUMPTABLE_00;
  int in_ep;
  
  cVar4 = *(char *)((unaff_gp & (uint)UNRECOVERED_JUMPTABLE_00) + 0x97c);
  *(undefined1 *)(in_ep + 0x60) = 0;
  uVar1 = *(ushort *)(in_ep + 10);
  uVar2 = *(undefined1 *)(in_ep + 0x7d);
  *(undefined1 *)(in_ep + 0x61) = unaff_tp;
  *(int *)(in_ep + 0xa0) = in_r17;
  uVar3 = *(ushort *)(in_ep + 100);
  *(uint *)(in_r17 + -0x191a) = in_r15 / (uint)(int)in_r11;
  *(uint *)(uVar3 + 0xa8) = (uint)uVar1;
  if (in_r17 + 0x1bfa < 0) {
                    /* WARNING: Could not recover jumptable at 0x01072190. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*UNRECOVERED_JUMPTABLE_00)();
    return;
  }
                    /* WARNING: Could not recover jumptable at 0x0107210a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)((int)cVar4,uVar2);
  return;
}

