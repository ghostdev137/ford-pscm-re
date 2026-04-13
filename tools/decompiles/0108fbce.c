
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Removing unreachable block (ram,0x0108fc32) */

void FUN_0108fbce(uint param_1,undefined2 param_2)

{
  int iVar1;
  bool bVar2;
  bool bVar3;
  ushort uVar4;
  undefined1 in_r1;
  undefined2 in_r2;
  undefined1 unaff_tp;
  uint uVar5;
  uint in_r12;
  short in_r16;
  int in_ep;
  uint in_PSW;
  
  *(undefined1 *)(in_ep + 0x61) = in_r1;
  uVar4 = *(ushort *)(in_ep + 0x44);
  if (((byte)(in_PSW >> 1) & 1) == ((byte)(in_PSW >> 2) & 1)) {
    uVar5 = (uint)*(ushort *)(in_ep + 0x44);
    iVar1 = uVar4 - param_1;
    bVar2 = (int)param_1 < 0;
    bVar3 = bVar2 == iVar1 < 0;
    in_r12 = (uint)*(ushort *)(in_ep + 0x44);
    if (iVar1 < 0 != (bVar2 && bVar3)) goto LAB_0108fc36;
    if (bVar2 && bVar3) {
      uVar5 = param_1;
    }
    *(undefined2 *)(uVar5 - 0x51c8) = in_r2;
    *(undefined1 *)(in_ep + 0x68) = unaff_tp;
  }
  in_r16 = (short)in_ep * 0x1de8;
  *(ushort *)(in_r12 - 0x5884) = uVar4;
LAB_0108fc36:
  *(undefined2 *)(in_ep + 0xfc) = param_2;
  *(undefined2 *)(in_ep + 0xc2) = 0;
  *(ushort *)(in_ep + 0xc2) = ~*(ushort *)(in_ep + 0x44);
  *(short *)(in_ep + 200) = in_r16 + -0xafe;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

