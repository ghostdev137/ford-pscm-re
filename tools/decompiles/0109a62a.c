
/* WARNING: Removing unreachable block (ram,0x0109a654) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0109a62a(int param_1)

{
  undefined2 uVar1;
  undefined2 uVar2;
  undefined4 in_r10;
  int in_r19;
  int in_r24;
  int in_r25;
  int in_ep;
  undefined4 in_lp;
  
  *(undefined1 *)(in_ep + 0x68) = 0;
  *(undefined4 *)((in_ep - in_r24) + 0x3c) = in_r10;
  *(undefined4 *)(in_r25 + 0x65ee) = in_lp;
  uVar1 = Ram00000001;
  uVar2 = Ram00000001;
  __nop();
  DAT_00000066 = 0;
                    /* WARNING: Could not recover jumptable at 0x0109a674. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_0109a676 + *(short *)(&LAB_0109a676 + (char)uVar1 * 2) * 2))
            (param_1 + in_r19,_DAT_00000045);
  return;
}

