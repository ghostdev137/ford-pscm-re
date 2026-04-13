
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Instruction at (ram,0x010bab14) overlaps instruction at (ram,0x010bab12)
    */
/* WARNING: Removing unreachable block (ram,0x010baa72) */
/* WARNING: Removing unreachable block (ram,0x010babf8) */
/* WARNING: Removing unreachable block (ram,0x010babfa) */
/* WARNING: Removing unreachable block (ram,0x010bac00) */
/* WARNING: Removing unreachable block (ram,0x010bac16) */
/* WARNING: Removing unreachable block (ram,0x010bac1c) */
/* WARNING: Removing unreachable block (ram,0x010bac1e) */
/* WARNING: Removing unreachable block (ram,0x010baca6) */
/* WARNING: Removing unreachable block (ram,0x010bac20) */
/* WARNING: Removing unreachable block (ram,0x010bac34) */
/* WARNING: Removing unreachable block (ram,0x010bac4c) */

void FUN_010ba6d0(uint param_1,undefined4 param_2)

{
  bool bVar1;
  short unaff_100000f6;
  uint in_r2;
  uint uVar2;
  code *pcVar3;
  uint unaff_gp;
  undefined4 unaff_tp;
  uint uVar4;
  char cVar5;
  uint uVar6;
  int in_r10;
  code *pcVar7;
  int in_r12;
  undefined4 in_r15;
  ushort uVar8;
  uint in_r16;
  code *UNRECOVERED_JUMPTABLE;
  uint in_r21;
  uint in_r24;
  ushort in_r28;
  uint in_r29;
  ushort *in_ep;
  byte bVar9;
  bool bVar10;
  uint uVar12;
  uint uVar11;
  
  *(undefined1 *)(in_ep + 0x33) = 0;
  uVar6 = (uint)in_ep[1];
  pcVar7 = UNRECOVERED_JUMPTABLE + 0x8010000;
  uVar4 = in_r29 + 0x801;
  *(undefined4 *)(in_ep + 2) = unaff_tp;
  uVar2 = ~in_r2;
  if ((int)in_r2 < 0) {
    uVar11 = 0;
    if (uVar2 != 0) {
      unaff_gp = (int)(short)uVar2 * (int)(short)unaff_gp;
      in_r10 = 0x5d513be6;
      uVar2 = (uint)*in_ep;
      uVar4 = (uint)*(char *)(param_1 + 0x700);
      param_1 = (short)param_1 * 8;
      goto LAB_010ba720;
    }
LAB_010ba7b2:
    uVar2 = (uint)(uVar4 < param_1) << 3 | (uint)(uVar4 == param_1);
    if (uVar4 < param_1 || (bool)((byte)uVar2 & 1)) goto LAB_010ba86c;
    uVar2 = (uint)*in_ep;
    uVar4 = (uint)*(char *)(param_1 + 0x700);
    param_1 = (int)(short)uVar6 * (int)(short)param_1;
    bVar9 = (uVar11 & 0x42a) == 0;
LAB_010ba7ca:
    uVar8 = (ushort)in_r16;
    *(undefined1 *)(in_ep + 0x33) = 0;
    do {
    } while ((bool)(bVar9 & 1));
    *(uint *)(in_ep + 0x50) = uVar4;
    in_r28 = (short)param_1 * unaff_100000f6;
    UNRECOVERED_JUMPTABLE = (code *)((uint)UNRECOVERED_JUMPTABLE | in_r24 | in_r24);
    uVar11 = 1;
    bVar10 = false;
  }
  else {
LAB_010ba720:
    cVar5 = (char)in_ep[1];
    uVar6 = (uint)cVar5;
    in_ep[0x66] = 0;
    bVar10 = (int)&stack0x00000700 < 0;
    uVar11 = (uint)(-1 < (int)&stack0x00000000 && (int)&stack0x00000700 < 0) << 2 |
             (uint)(&stack0x00000000 == (undefined1 *)0xfffff900);
    bVar9 = (byte)uVar11;
    uVar8 = in_ep[0x2c];
    in_r16 = (uint)uVar8;
    do {
      if ((undefined1 *)0xfffff8ff < &stack0x00000000 || (bool)(bVar9 & 1)) goto LAB_010ba7ca;
    } while ((bool)(bVar9 & 1));
    if (!(bool)(bVar9 & 1)) {
      unaff_100000f6 = in_r28 * 6;
      in_r28 = in_r28 * 6;
      uVar2 = (short)param_1 * -0x41ad;
      uVar8 = *in_ep;
      bVar10 = true;
      if (in_r24 == 0x4f80) goto LAB_010ba842;
      *in_ep = uVar8;
      pcVar3 = UNRECOVERED_JUMPTABLE + -0x1c000000;
      register0x0000000c = (BADSPACEBASE *)(UNRECOVERED_JUMPTABLE + -0x1c000000);
      uVar4 = (short)uVar4 * 6;
      if (uVar2 < unaff_gp) {
        uVar4 = (uint)*(char *)(param_1 + 0x700);
      }
      uVar6 = (uint)cVar5;
      in_ep[0x66] = 0;
      bVar10 = -1 < (int)(UNRECOVERED_JUMPTABLE + -0x1c000000) &&
               (int)(UNRECOVERED_JUMPTABLE + -0x1bfff900) < 0;
      uVar2 = (uint)((undefined1 *)0xfffff8ff < UNRECOVERED_JUMPTABLE + -0x1c000000) << 3 |
              (uint)(UNRECOVERED_JUMPTABLE == (code *)0x1bfff900);
      in_r16 = in_r12 + 0x6dd3;
      while (bVar9 = (byte)uVar2, (bool)(bVar9 & 1)) {
        uVar11 = in_r21;
        if ((undefined1 *)0xfffff8ff < UNRECOVERED_JUMPTABLE + -0x1c000000 || (bool)(bVar9 & 1))
        goto code_r0x010ba85c;
      }
      if ((bool)(bVar9 & 1)) goto LAB_010ba882;
      *in_ep = uVar8;
      *(uint *)(in_ep + 0x50) = uVar4;
      UNRECOVERED_JUMPTABLE = (code *)((uint)UNRECOVERED_JUMPTABLE | in_r24);
      register0x0000000c = (BADSPACEBASE *)(UNRECOVERED_JUMPTABLE + 0x68010000);
      uVar6 = (uint)cVar5;
      uVar11 = in_r24;
      goto LAB_010ba7b2;
    }
  }
  if (bVar10 == SUB41(uVar11 >> 2,0)) {
    *(byte *)(uVar2 + 0x5e19) = *(byte *)(uVar2 + 0x5e19) | 1;
    *in_ep = uVar8;
    *(undefined4 *)in_ep = in_r15;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  in_r10 = -0x49fffc1a;
  uVar8 = *in_ep;
  in_r16 = (uint)uVar8;
  uVar6 = (uint)in_ep[1];
  do {
  } while ((bool)((byte)uVar11 & 1));
  *(byte *)(uVar2 + 0x5e19) = *(byte *)(uVar2 + 0x5e19) | 1;
  *in_ep = uVar8;
  *(undefined4 *)in_ep = in_r15;
  *(char *)(in_ep + 0x33) = (char)in_r28;
  uVar2 = ~uVar2;
  bVar10 = uVar2 == 0;
  in_ep[0x66] = (ushort)uVar2;
LAB_010ba842:
  if (!bVar10) {
    bVar1 = (int)in_r29 < 0 && -1 < (int)(in_r29 - 0x73ff);
    bVar10 = (int)(in_r29 - 0x73ff) < 0;
    uVar12 = (uint)(0x73fe < in_r29) << 3 | (uint)(in_r29 == 0x73ff);
    if (!(bool)((byte)uVar12 & 1)) {
      do {
        pcVar7 = (code *)(in_r29 - 0x73ff);
        pcVar3 = (code *)(in_r16 + 0x94010000);
        uVar2 = uVar12 & 0xfffffff8 | (uint)(in_r10 == -1);
        bVar10 = false;
        register0x0000000c = (BADSPACEBASE *)(in_r16 + 0x94010000);
        if (-1 < in_r10) goto LAB_010ba8c2;
        uVar11 = in_r21;
        if (SUB41(uVar12 >> 3,0) || (bool)((byte)uVar2 & 1)) {
LAB_010ba950:
          uVar2 = (uint)*in_ep;
          *(undefined1 *)(in_ep + 0x33) = 0;
          in_ep[0x42] = 0;
          *(undefined4 *)in_ep = param_2;
          goto LAB_010ba988;
        }
code_r0x010ba85c:
        in_r28 = (ushort)(byte)in_ep[0x3a];
        uVar4 = (uint)*(char *)(param_1 + 0x700);
        register0x0000000c = (BADSPACEBASE *)pcVar3;
        if (!bVar10) goto LAB_010ba8c2;
        in_r21 = uVar11 - 0x10;
        uVar2 = (uint)(0xf < uVar11) << 3 | (uint)(uVar11 == 0x10);
LAB_010ba86c:
        *(undefined1 *)(in_ep + 0x33) = 0;
        do {
          bVar9 = (byte)uVar2;
          if (SUB41(uVar2 >> 3,0) || (bool)(bVar9 & 1)) goto LAB_010ba910;
        } while ((bool)(bVar9 & 1));
        if ((bool)(bVar9 & 1)) {
          in_ep[0x42] = 0;
          *(undefined4 *)in_ep = param_2;
          goto LAB_010ba950;
        }
LAB_010ba882:
        bVar1 = (int)in_r29 < 0 && -1 < (int)(in_r29 - 0x73ff);
        bVar10 = (int)(in_r29 - 0x73ff) < 0;
        uVar12 = (uint)(0x73fe < in_r29) << 3 | (uint)(in_r29 == 0x73ff);
      } while (bVar10 != bVar1);
      uVar2 = *(uint *)(in_ep + 0x22);
    }
    pcVar7 = (code *)(in_r29 - 0x73ff);
    if (bVar10 == bVar1) {
      if ((bool)((byte)uVar12 & 1)) {
LAB_010ba988:
        if (uVar2 != 0xffffffff) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
          halt_unimplemented();
        }
        do {
        } while( true );
      }
      param_1 = (uint)in_ep[1];
      register0x0000000c = (BADSPACEBASE *)((short)uVar2 * -0x41b0);
      in_ep[0x66] = in_ep[1];
      *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
      uVar4 = (uint)*(char *)(param_1 + 0x700);
      *(char *)(in_ep + 0x34) = (char)in_ep[1];
      uVar12 = (uint)(0xf < in_r21) << 3 | (uint)(in_r21 == 0x10);
    }
    *(undefined1 *)(in_ep + 0x33) = 0;
    uVar2 = uVar12;
LAB_010ba8c2:
    do {
      bVar9 = (byte)uVar2;
      if (SUB41(uVar2 >> 3,0) || (bool)(bVar9 & 1)) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
        halt_unimplemented();
      }
    } while ((bool)(bVar9 & 1));
    if ((bool)(bVar9 & 1)) {
      do {
        if (SUB41(uVar2 >> 3,0) || (bool)(bVar9 & 1)) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
          halt_unimplemented();
        }
      } while ((bool)(bVar9 & 1));
      if (!(bool)(bVar9 & 1)) {
        *(char *)(in_ep + 0x33) = (char)in_r28;
        *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
        halt_unimplemented();
      }
      uVar4 = in_r29 / (uint)(int)(short)*(undefined4 *)(in_ep + 0x2c);
      *(undefined1 *)(in_ep + 0x33) = 0;
      uVar2 = (uint)(param_1 < uVar6) << 3;
      do {
        uVar6 = uVar2 & 0xfffffffc | (uint)(in_r12 == -1);
        bVar9 = (byte)uVar6;
        if (SUB41(uVar2 >> 3,0) || (bool)(bVar9 & 1)) goto LAB_010baae2;
        uVar2 = uVar6;
      } while ((bool)(bVar9 & 1));
      pcVar7 = (code *)(uVar4 - 0x3fc);
      bVar9 = uVar4 == 0x3fc;
      in_ep[2] = 0;
      in_ep[3] = 0;
      if ((int)(uVar4 - 0x3fc) < 0 == ((int)uVar4 < 0 && -1 < (int)(uVar4 - 0x3fc))) {
LAB_010baae2:
        if ((bool)(bVar9 & 1)) {
          do {
          } while ((bool)(bVar9 & 1));
          *(code **)(in_ep + 0x50) = pcVar7;
          halt_unimplemented();
        }
        *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
      }
      in_ep[0x66] = 0;
      do {
        if ((undefined1 *)0xfffff8ff < register0x0000000c) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
          halt_unimplemented();
        }
      } while ((undefined1 *)register0x0000000c == (undefined1 *)0xfffff900);
      *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
      halt_unimplemented();
    }
    param_1 = (uint)in_ep[1];
    in_ep[0x66] = in_r28;
    *(uint *)(in_ep + 0x50) = uVar4;
    UNRECOVERED_JUMPTABLE = (code *)((uint)UNRECOVERED_JUMPTABLE | in_r24);
    uVar6 = (uint)(char)uVar6;
  }
  uVar4 = (uint)*(char *)(param_1 + 0x700);
  in_ep[0x68] = (ushort)param_1;
  uVar6 = (uint)(char)uVar6;
LAB_010ba910:
  in_ep[0x66] = 0;
                    /* WARNING: Could not recover jumptable at 0x010ba918. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE)(uVar4,uVar6);
  return;
}

