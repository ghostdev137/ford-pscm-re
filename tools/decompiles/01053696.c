
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_01053696(uint param_1,uint param_2)

{
  uint uVar1;
  uint in_r12;
  uint in_r14;
  uint in_r16;
  uint in_r17;
  uint in_r18;
  uint in_r19;
  uint in_r20;
  uint in_r21;
  uint in_r23;
  uint in_r28;
  uint *in_ep;
  uint in_lp;
  uint in_PSW;
  uint uVar2;
  
  do {
    if (!(bool)((byte)in_PSW & 1)) {
      uVar2 = in_PSW & 0xfffffff8 | (uint)(in_r12 == 0 && in_r28 == 0);
      while (!(bool)((byte)(uVar2 >> 3) & 1) && !(bool)((byte)uVar2 & 1)) {
        in_r20 = in_r20 | in_r28;
        uVar1 = uVar2 & 0xfffffffc | (uint)((int)in_r20 < 0) << 1;
        uVar2 = uVar1 | in_r20 == 0;
        if (!(bool)((byte)(uVar1 >> 1) & 1)) {
          in_ep[0x2a] = param_2;
          *in_ep = in_r19;
          in_ep[0x3c] = in_lp;
          FUN_010a3a26(*(undefined2 *)((int)in_ep + 0x26),param_1 & in_r17);
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
          halt_unimplemented();
        }
      }
      in_r17 = in_r17 / (uint)(int)(short)in_r17;
      *(char *)((int)in_ep + 0x42) = (char)param_1;
      in_r21 = in_ep[0x28];
      in_r19 = ~param_2;
      *(char *)(in_ep + 0x10) = (char)in_r14;
      *(undefined1 *)((int)in_ep + 0x43) = 0;
      in_ep[0x28] = param_2;
      in_r18 = (uint)*(ushort *)((int)in_ep + 0x52);
      in_r12 = (byte)in_ep[7] & in_r21;
      in_r28 = in_r28 & (ushort)in_ep[0x2d] & in_r23;
      in_r16 = (in_r16 & (ushort)in_ep[0x2d] | in_r28) & in_r23;
      param_1 = *(byte *)((int)in_ep + 1) & in_r21;
    }
    uVar2 = in_r16 & in_r21;
    in_ep[0x3c] = in_lp;
    in_r21 = ~in_r17;
    in_ep[0x28] = param_2;
    in_r17 = in_ep[0x28];
    in_r20 = (uint)*(ushort *)((int)in_ep + 0x62);
    param_1 = param_1 & in_r21;
    in_r16 = uVar2 & in_r20;
    in_PSW = (uint)(in_r18 < in_r14) << 3 | (uint)(in_r16 == 0);
    in_r14 = in_r18 - in_r14;
  } while( true );
}

