
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_01082208(undefined4 param_1)

{
  ushort uVar1;
  int in_r20;
  char cVar2;
  uint in_r23;
  uint uVar3;
  ushort *in_ep;
  ushort *in_CTBP;
  
  __synchronize();
  uVar1 = *in_ep;
  *(undefined4 *)(in_ep + 0x52) = param_1;
  *(undefined1 *)(in_r20 + 0x2001) = 0;
  cVar2 = (char)*in_ep;
  uVar3 = uVar1 - 8;
  uVar1 = in_ep[0x59];
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))(*in_ep);
  __nop();
  in_ep[0x24] = 0;
  in_ep[0x20] = 0;
  cVar2 = cVar2 + -8;
  (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
  *(uint *)(in_ep + 0x32) = uVar3;
  (&DAT_ffffe137)[uVar1 & uVar3 ^ in_r23] = cVar2;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

