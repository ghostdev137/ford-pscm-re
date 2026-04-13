
void FUN_01035b16(void)

{
  undefined4 unaff_tp;
  uint in_r17;
  uint in_r20;
  uint in_r21;
  uint in_r26;
  int in_ep;
  
  *(undefined4 *)(in_ep + 0x20) = 0;
  __nop();
  *(undefined4 *)(in_ep + 0xa8) = unaff_tp;
                    /* WARNING: Could not recover jumptable at 0x01035b8e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(~in_r26 & in_r20))
            (*(undefined1 *)(in_ep + 3),in_r17 & in_r21,
             (uint)*(ushort *)(in_ep + 2) / (uint)(int)*(short *)(in_ep + 2));
  return;
}

