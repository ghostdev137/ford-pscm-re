
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0109a284(void)

{
  int in_r13;
  uint in_r16;
  int in_ep;
  uint uVar1;
  ushort *in_CTBP;
  
  uVar1 = (uint)(in_r13 < 0 && in_r13 < 0 != in_r13 + -0xf < 0) << 2 |
          (uint)(in_r13 + -0xf < 0) << 1;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  if (((byte)(uVar1 >> 1) & 1) == ((byte)(uVar1 >> 2) & 1)) {
    in_r16 = (uint)*(byte *)(in_ep + 0x1a);
  }
  *(char *)(in_ep + 100) = (char)in_r16;
  __nop();
  *(uint *)(in_ep + 0xf8) = in_r16;
  *(undefined1 *)(in_ep + 0x48) = 0;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

