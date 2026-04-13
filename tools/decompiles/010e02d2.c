
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Instruction at (ram,0x010e0556) overlaps instruction at (ram,0x010e0554)
    */
/* WARNING: Removing unreachable block (ram,0x010e045a) */
/* WARNING: Removing unreachable block (ram,0x010e049e) */
/* WARNING: Removing unreachable block (ram,0x010e04a4) */
/* WARNING: Removing unreachable block (ram,0x010e04cc) */
/* WARNING: Removing unreachable block (ram,0x010e04e4) */
/* WARNING: Removing unreachable block (ram,0x010e04e8) */
/* WARNING: Removing unreachable block (ram,0x010e0532) */
/* WARNING: Removing unreachable block (ram,0x010e053a) */
/* WARNING: Removing unreachable block (ram,0x010e055c) */
/* WARNING: Removing unreachable block (ram,0x010e0564) */
/* WARNING: Removing unreachable block (ram,0x010e056c) */
/* WARNING: Removing unreachable block (ram,0x010e057e) */
/* WARNING: Removing unreachable block (ram,0x010e0580) */
/* WARNING: Removing unreachable block (ram,0x010e0582) */
/* WARNING: Removing unreachable block (ram,0x010e0584) */
/* WARNING: Removing unreachable block (ram,0x010e0606) */
/* WARNING: Removing unreachable block (ram,0x010e0608) */
/* WARNING: Removing unreachable block (ram,0x010e060a) */
/* WARNING: Removing unreachable block (ram,0x010e060c) */
/* WARNING: Removing unreachable block (ram,0x010e060e) */
/* WARNING: Removing unreachable block (ram,0x010e0630) */
/* WARNING: Removing unreachable block (ram,0x010e0638) */
/* WARNING: Removing unreachable block (ram,0x010e0556) */

undefined4 FUN_010e02d2(int param_1)

{
  int5 iVar1;
  short in_r2;
  int unaff_gp;
  undefined4 uVar2;
  undefined4 in_r12;
  uint uVar3;
  uint in_r17;
  int in_r28;
  int in_ep;
  undefined2 in_lp;
  uint in_PSW;
  
  if (!(bool)((byte)(in_PSW >> 3) & 1)) {
    *(undefined4 *)(in_ep + 0x18) = in_r12;
    uVar2 = (*(code *)&LAB_75d00748)();
    return uVar2;
  }
  *(int *)(in_ep + 0x40) = in_ep;
  *(undefined4 *)(in_ep + 0x18) = in_r12;
  iVar1 = -(int5)unaff_gp;
  if (iVar1 < 0x80000000) {
    if (iVar1 < -0x80000000) {
      iVar1 = 0;
    }
  }
  else {
    iVar1 = 0x7fffffff;
  }
  uVar3 = (uint)*(byte *)(in_ep + 0x19);
  *(undefined2 *)(in_ep + 8) = in_lp;
  *(undefined4 *)(in_ep + 0x18) = in_r12;
  *(char *)(in_ep + 100) = (char)in_lp;
  func_0x0112ea0a(*(undefined4 *)(in_ep + 0x40));
  *(short *)(param_1 + 0x720) = (short)iVar1;
  *(short *)(in_r28 + 0x711c) = (short)in_r28;
  in_r17 = in_r17 & 0x207a;
  *(undefined1 *)(in_r17 + 0x76d0) = 0;
  do {
  } while ((int)(uVar3 + 0x6e0) < 0);
  __synchronize();
  func_0x0112ea64(0x560d / (uint)(int)(short)(in_r2 * 6),0);
  *(short *)(in_r17 + 0x720) = (short)iVar1;
  *(short *)(in_r28 + 0x711c) = (short)in_r28;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

