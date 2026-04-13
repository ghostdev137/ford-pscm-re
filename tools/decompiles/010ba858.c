
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
/* WARNING: Removing unreachable block (ram,0x010ba936) */

void FUN_010ba858(uint param_1,uint param_2,undefined4 param_3)

{
  uint uVar1;
  uint uVar2;
  int iVar3;
  int in_r10;
  int in_r11;
  int in_r12;
  code *UNRECOVERED_JUMPTABLE;
  uint in_r21;
  uint in_r24;
  uint in_r29;
  uint uVar4;
  ushort *in_ep;
  byte bVar5;
  uint in_PSW;
  uint uVar6;
  
  do {
    if ((bool)((byte)(in_PSW >> 3) & 1) || (bool)((byte)in_PSW & 1)) {
      uVar2 = (uint)*in_ep;
      *(undefined1 *)(in_ep + 0x33) = 0;
      in_ep[0x42] = 0;
      *(undefined4 *)in_ep = param_3;
LAB_010ba988:
      if (uVar2 != 0xffffffff) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
        halt_unimplemented();
      }
      do {
      } while( true );
    }
    iVar3 = (int)*(char *)(param_1 + 0x700);
    if (!(bool)((byte)(in_PSW >> 2) & 1)) break;
    uVar4 = in_r21 - 0x10;
    *(undefined1 *)(in_ep + 0x33) = 0;
    do {
      if (0xf < in_r21) goto LAB_010ba910;
    } while (in_r21 == 0x10);
    in_r11 = in_r29 - 0x73ff;
    uVar2 = (uint)(0x73fe < in_r29) << 3;
    uVar1 = (uint)((int)in_r29 < 0 && -1 < (int)(in_r29 - 0x73ff)) << 2 | uVar2;
    uVar6 = uVar1 | (uint)((int)(in_r29 - 0x73ff) < 0) << 1;
    in_PSW = uVar6 | in_r29 == 0x73ff;
    if (((byte)(uVar6 >> 1) & 1) == ((byte)(uVar1 >> 2) & 1)) {
      uVar2 = *(uint *)(in_ep + 0x22);
      if (((byte)(uVar6 >> 1) & 1) == ((byte)(uVar1 >> 2) & 1)) {
        if ((bool)((byte)in_PSW & 1)) goto LAB_010ba988;
        param_1 = (uint)in_ep[1];
        register0x0000000c = (BADSPACEBASE *)((short)uVar2 * -0x41b0);
        in_ep[0x66] = in_ep[1];
        *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
        iVar3 = (int)*(char *)(param_1 + 0x700);
        *(char *)(in_ep + 0x34) = (char)in_ep[1];
        in_PSW = (uint)(0xf < uVar4) << 3 | (uint)(uVar4 == 0x10);
      }
      *(undefined1 *)(in_ep + 0x33) = 0;
      break;
    }
    in_PSW = uVar2 | in_r10 == -1;
    in_r21 = uVar4;
  } while (in_r10 < 0);
  do {
    bVar5 = (byte)in_PSW;
    if ((bool)((byte)(in_PSW >> 3) & 1) || (bool)(bVar5 & 1)) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
      halt_unimplemented();
    }
  } while ((bool)(bVar5 & 1));
  if (!(bool)(bVar5 & 1)) {
    in_ep[0x66] = (ushort)(byte)in_ep[0x3a];
    *(int *)(in_ep + 0x50) = iVar3;
    UNRECOVERED_JUMPTABLE = (code *)((uint)UNRECOVERED_JUMPTABLE | in_r24);
    iVar3 = (int)*(char *)(in_ep[1] + 0x700);
    in_ep[0x68] = in_ep[1];
    param_2 = (uint)(char)param_2;
LAB_010ba910:
    in_ep[0x66] = 0;
                    /* WARNING: Could not recover jumptable at 0x010ba918. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*UNRECOVERED_JUMPTABLE)(iVar3,param_2);
    return;
  }
  do {
    if ((bool)((byte)(in_PSW >> 3) & 1) || (bool)(bVar5 & 1)) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
      halt_unimplemented();
    }
  } while ((bool)(bVar5 & 1));
  if (!(bool)(bVar5 & 1)) {
    *(byte *)(in_ep + 0x33) = (byte)in_ep[0x3a];
    *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
  uVar4 = in_r29 / (uint)(int)(short)*(undefined4 *)(in_ep + 0x2c);
  *(undefined1 *)(in_ep + 0x33) = 0;
  uVar2 = (uint)(param_1 < param_2) << 3;
  do {
    uVar6 = uVar2 & 0xfffffffc | (uint)(in_r12 == -1);
    bVar5 = (byte)uVar6;
    if (SUB41(uVar2 >> 3,0) || (bool)(bVar5 & 1)) goto LAB_010baae2;
    uVar2 = uVar6;
  } while ((bool)(bVar5 & 1));
  in_r11 = uVar4 - 0x3fc;
  bVar5 = uVar4 == 0x3fc;
  in_ep[2] = 0;
  in_ep[3] = 0;
  if ((int)(uVar4 - 0x3fc) < 0 == ((int)uVar4 < 0 && -1 < (int)(uVar4 - 0x3fc))) {
LAB_010baae2:
    if ((bool)(bVar5 & 1)) {
      do {
      } while ((bool)(bVar5 & 1));
      *(int *)(in_ep + 0x50) = in_r11;
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

