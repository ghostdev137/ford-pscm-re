
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_0105e672(int param_1)

{
  int5 iVar1;
  undefined1 uVar2;
  int in_r10;
  undefined2 in_r21;
  int in_r24;
  ushort in_r27;
  ushort *in_ep;
  
  in_ep[99] = (ushort)in_r10;
  *(undefined1 *)(in_ep + 0x21) = 0xf8;
  iVar1 = -8 - (int5)in_r10;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar2 = (undefined1)iVar1;
  if (-8 - in_r10 < 0 == (in_r10 >= 0 && in_r10 < 0 == -8 - in_r10 < 0)) {
    *(undefined2 *)(in_r24 + 0x1fe8) = in_r21;
    in_ep[0x61] = in_r27;
    in_ep = (ushort *)(uint)*in_ep;
    *(int *)(in_ep + 0x48) = param_1;
    __nop();
    in_ep[0x60] = in_ep[0x65];
    uVar2 = (undefined1)
            ((ulonglong)((double)(longlong)(int)(uint)(byte)in_ep[0x2a] * (double)(longlong)param_1)
            >> 0x20);
  }
  in_ep[0x60] = 0;
  *(undefined1 *)(in_ep + 0x21) = uVar2;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

