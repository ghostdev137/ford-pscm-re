
void FUN_01061df2(ushort param_1,ushort param_2)

{
  int unaff_gp;
  undefined1 unaff_tp;
  ushort in_r22;
  ushort *in_ep;
  uint in_PSW;
  
  in_ep[99] = param_1;
  *(undefined1 *)(*in_ep + 0x6408) = unaff_tp;
  in_ep[99] = param_1;
  if (!(bool)((byte)(in_PSW >> 3) & 1)) {
    in_ep[99] = in_r22;
  }
  in_ep[0x61] = param_2;
                    /* WARNING: Could not recover jumptable at 0x01061e3a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_01061e3c + *(short *)(&LAB_01061e3c + (int)in_ep * 2) * 2))
            ((int)(char)(&DAT_ffff8a18)[unaff_gp]);
  return;
}

