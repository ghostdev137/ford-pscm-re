
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Removing unreachable block (ram,0x0107f2e0) */
/* WARNING: Removing unreachable block (ram,0x0107f34a) */
/* WARNING: Removing unreachable block (ram,0x0107f2e2) */
/* WARNING: Removing unreachable block (ram,0x0107f2e4) */
/* WARNING: Removing unreachable block (ram,0x0107f2e6) */

undefined4 FUN_0107f36a(undefined2 param_1,undefined4 param_2)

{
  int5 iVar1;
  int5 iVar2;
  int5 iVar3;
  byte bVar4;
  int iVar5;
  int in_r10;
  undefined4 in_r11;
  byte in_r28;
  byte *in_ep;
  
  in_ep[0x66] = 0;
  in_ep[0x66] = 0;
  *(undefined4 *)(in_ep + 0x60) = param_2;
  iVar3 = (int5)in_r10 + 5;
  if (iVar3 < 0x80000000) {
    if (iVar3 < -0x80000000) {
      iVar3 = -0x80000000;
    }
  }
  else {
    iVar3 = 0x7fffffff;
  }
  bVar4 = *in_ep;
  *(undefined4 *)in_ep = in_r11;
  iVar1 = -(int5)(int)(bVar4 + 8);
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = -0x80000000;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  iVar5 = (int)iVar1;
  in_ep[0x28] = 0;
  do {
    iVar1 = -(int5)iVar5;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    iVar5 = (int)iVar1;
    in_ep[0x28] = 0;
    *(undefined2 *)(in_ep + 0xcc) = param_1;
    iVar1 = -(int5)iVar5;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    in_ep[0x28] = 0;
    if (-iVar5 < 0 != (iVar5 < 0 && iVar5 < 0 == -iVar5 < 0)) {
      in_ep[0x62] = in_r28;
      return (int)iVar3;
    }
    iVar1 = -(int5)(int)iVar1;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    in_ep[0x28] = 0;
    iVar2 = -(int5)(int)iVar1;
    if (iVar2 < 0x80000000) {
      if (iVar2 < -0x80000000) {
        iVar2 = -0x80000000;
      }
    }
    else {
      iVar2 = 0x7fffffff;
    }
    iVar5 = (int)iVar2;
    in_ep[0x28] = 0;
  } while ((int)iVar1 == 0);
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

