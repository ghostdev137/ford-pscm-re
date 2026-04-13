
void FUN_01083ecc(void)

{
  ushort uVar1;
  int unaff_gp;
  undefined1 unaff_tp;
  undefined2 in_r24;
  int in_r28;
  int in_ep;
  
  *(undefined1 *)(unaff_gp + 0x4a1d) = unaff_tp;
  uVar1 = *(ushort *)(in_ep + 6);
  *(undefined2 *)(in_r28 + -0x51d0) = in_r24;
                    /* WARNING: Could not recover jumptable at 0x01083efe. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)*(byte *)(uVar1 + 1))();
  return;
}

