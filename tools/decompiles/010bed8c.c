
/* WARNING: Removing unreachable block (ram,0x010bed9e) */

void FUN_010bed8c(undefined4 param_1)

{
  undefined4 unaff_gp;
  ushort *in_ep;
  
  *(undefined4 *)(in_ep + 0x30) = param_1;
  *(uint *)(in_ep + 0x30) = (uint)*in_ep;
  *(uint *)(in_ep + 0x30) = (uint)in_ep[0x7d];
  *(undefined4 *)(in_ep + 0x36) = unaff_gp;
  return;
}

