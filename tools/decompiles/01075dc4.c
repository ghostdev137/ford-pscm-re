
void FUN_01075dc4(char param_1)

{
  undefined1 in_r16;
  int in_r17;
  uint uVar1;
  int in_r21;
  short in_r24;
  int in_ep;
  undefined2 in_lp;
  
  *(undefined1 *)(in_r21 + -0x5ffd) = in_r16;
  __nop();
  uVar1 = (in_r17 - 0xbU) / (uint)(int)in_r24;
  __nop();
  *(uint *)(in_ep + 0x38) = uVar1 & 0xff;
  *(undefined2 *)(in_ep + 0xfe) = in_lp;
  if (uVar1 != 0) {
    *(uint *)(in_ep + 0xa0) = (uint)*(byte *)(in_ep + 0x18);
  }
  __nop();
                    /* WARNING: Could not recover jumptable at 0x01075e06. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_01075e08 + *(short *)(&LAB_01075e08 + param_1 * 2) * 2))
            (*(undefined2 *)(in_ep + 0xa4));
  return;
}

