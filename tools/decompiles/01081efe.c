
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_01081efe(void)

{
  int unaff_gp;
  undefined1 unaff_tp;
  int in_ep;
  
  (&DAT_ffffa47c)[unaff_gp] = unaff_tp;
                    /* WARNING: Could not recover jumptable at 0x01081f32. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)*(byte *)(*(ushort *)(in_ep + 6) + 1))();
  return;
}

