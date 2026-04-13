
/* WARNING: Removing unreachable block (ram,0x01075798) */
/* WARNING: Removing unreachable block (ram,0x010757a8) */

void FUN_0107575e(undefined1 param_1,undefined4 param_2)

{
  undefined4 uVar1;
  undefined4 unaff_tp;
  undefined4 in_r13;
  undefined1 in_r14;
  undefined1 in_r18;
  undefined1 in_r22;
  int in_ep;
  
  *(undefined1 *)(in_ep + 0x11) = param_1;
  *(undefined1 *)(in_ep + 0x12) = in_r22;
  uVar1 = 0x5393;
  *(undefined1 *)(in_ep + 0x14) = in_r14;
  *(undefined1 *)(in_ep + 0x15) = in_r18;
  *(undefined4 *)(in_ep + 0x6c) = in_r13;
  do {
    *(undefined4 *)(in_ep + 0x6c) = unaff_tp;
    *(undefined4 *)(in_ep + 0x68) = uVar1;
    uVar1 = *(undefined4 *)(in_ep + 0x68);
    *(undefined4 *)(in_ep + 0x68) = param_2;
  } while( true );
}

