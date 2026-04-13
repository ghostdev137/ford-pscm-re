
/* WARNING: Removing unreachable block (ram,0x010bf7e4) */

void FUN_010bf75a(void)

{
  int5 iVar1;
  undefined2 in_r1;
  undefined2 unaff_tp;
  undefined2 in_r15;
  undefined2 in_r16;
  undefined2 in_r27;
  undefined2 in_r28;
  int in_ep;
  int in_lp;
  
  iVar1 = (int5)in_lp + 0xf;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  *(undefined2 *)(in_ep + 0xee) = in_r16;
  *(undefined2 *)(in_ep + 0x22) = in_r1;
  __nop();
  do {
    *(undefined2 *)(in_ep + 0xee) = in_r27;
    *(undefined2 *)(in_ep + 0xee) = in_r27;
    *(undefined2 *)(in_ep + 0xf2) = unaff_tp;
    *(undefined2 *)(in_ep + 0xf2) = in_r28;
    *(undefined2 *)(in_ep + 0xf4) = unaff_tp;
    *(undefined2 *)(in_ep + 0xf4) = in_r15;
    *(int *)(in_ep + 0xf0) = (int)iVar1;
  } while( true );
}

