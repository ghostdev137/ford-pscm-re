
uint FUN_010e05be(uint param_1)

{
  uint uVar1;
  int5 iVar2;
  undefined1 in_r2;
  undefined2 unaff_gp;
  uint in_r10;
  undefined1 in_r12;
  short in_r16;
  int in_r17;
  int in_r28;
  undefined2 *in_ep;
  undefined2 in_lp;
  
  *(byte *)(in_r10 + 0xc7c) = *(byte *)(in_r10 + 0xc7c) ^ 4;
  uVar1 = (uint)(short)param_1;
  *(undefined1 *)(in_r17 + 0x1800) = in_r12;
  if ((param_1 != 0x80000000 || uVar1 != 0xffffffff) && uVar1 != 0) {
    in_r10 = in_r10 / (uint)(int)(short)(param_1 / uVar1);
    iVar2 = (int5)in_r28 + -0x711c;
    if (iVar2 < 0x80000000) {
      if (iVar2 < -0x80000000) {
        iVar2 = 0;
      }
    }
    else {
      iVar2 = 0x7fffffff;
    }
    in_r16 = (short)iVar2;
    in_r2 = (undefined1)*in_ep;
    iVar2 = -(int5)(int)(uint)(ushort)in_ep[10];
    if (iVar2 < 0x80000000) {
      if (iVar2 < -0x80000000) {
        iVar2 = -0x80000000;
      }
    }
    else {
      iVar2 = 0x7fffffff;
    }
    iVar2 = -(int5)(int)iVar2;
    if (iVar2 < 0x80000000) {
      if (iVar2 < -0x80000000) {
        iVar2 = 0;
      }
    }
    else {
      iVar2 = 0x7fffffff;
    }
    unaff_gp = (undefined2)iVar2;
    in_ep[0x60] = in_ep[0x7c];
    in_ep[4] = in_lp;
    __nop();
    *in_ep = 0;
  }
  in_ep[0x60] = unaff_gp;
  *(undefined1 *)(in_ep + 0x33) = in_r2;
  *(undefined2 **)(in_ep + 0x24) = in_ep;
  return in_r10 / (uint)(int)in_r16;
}

