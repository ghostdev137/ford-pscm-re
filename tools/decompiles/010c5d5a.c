
void FUN_010c5d5a(uint param_1)

{
  undefined1 uVar1;
  ushort in_r16;
  ushort in_r28;
  byte *in_ep;
  byte in_PSW;
  
  *(byte **)(in_ep + 0xf0) = in_ep;
  uVar1 = (&DAT_ffff8871)[param_1];
  if ((bool)(in_PSW & 1)) {
    in_r28 = (ushort)in_ep[0x49];
    in_r16 = (ushort)*in_ep;
  }
  if ((bool)(in_PSW & 1)) {
    *(byte **)(in_ep + 0xf0) = in_ep;
  }
  *(ushort *)(in_ep + 0xbe) = in_r28;
  *(undefined2 *)(in_ep + 0xc4) = *(undefined2 *)(in_ep + 0xf8);
                    /* WARNING: Could not recover jumptable at 0x010c5d96. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010c5d98 +
            *(short *)(&LAB_010c5d98 + (param_1 / (uint)(int)(short)in_r16) * 2) * 2))
            (uVar1,in_ep[0x51]);
  return;
}

