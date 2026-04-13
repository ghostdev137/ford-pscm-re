
/* WARNING: Control flow encountered unimplemented instructions */
/* WARNING: Instruction at (ram,0x010c1720) overlaps instruction at (ram,0x010c171e)
    */
/* WARNING: This function may have set the stack pointer */

void FUN_010c16d8(undefined4 param_1,int param_2)

{
  bool bVar1;
  bool bVar2;
  int5 iVar3;
  char cVar4;
  undefined4 unaff_gp;
  short sVar5;
  uint uVar6;
  undefined1 in_r11;
  int iVar7;
  uint in_r16;
  int in_r17;
  uint uVar8;
  undefined2 uVar9;
  undefined4 in_r20;
  uint in_r21;
  uint in_r23;
  uint in_r24;
  uint in_r26;
  uint in_r28;
  uint uVar10;
  uint in_r29;
  undefined2 *in_ep;
  byte in_PSW;
  bool bVar11;
  
  if ((bool)(in_PSW & 1)) {
    *(undefined4 *)(&DAT_ffff80e6 + (ushort)in_ep[0x51]) = unaff_gp;
                    /* WARNING: Could not recover jumptable at 0x010d0054. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*(code *)(&LAB_010d0056 + *(short *)(&LAB_010d0056 + param_2 * 2) * 2))();
    return;
  }
  do {
    func_0x012b1b24();
    uVar8 = in_r26 - in_r28;
    iVar7 = in_r26 - in_r28;
    bVar1 = (int)in_r26 < 0 != (int)in_r28 < 0;
    bVar2 = (int)in_r28 < 0 == iVar7 < 0;
    bVar11 = in_r26 != in_r28;
    if (!bVar1 || !bVar2) goto LAB_010c1720;
    *(uint *)(in_ep + 0x70) = uVar8;
    in_r28 = uVar8;
  } while (iVar7 < 0 == (bVar1 && bVar2) && bVar11);
  do {
    uVar6 = func_0x012b2436();
    uVar10 = in_r26 - uVar8;
    if ((int)(in_r26 - uVar8) < 0 !=
        ((int)in_r26 < 0 != (int)uVar8 < 0 && (int)uVar8 < 0 == (int)(in_r26 - uVar8) < 0))
    goto LAB_010c1720;
    bVar11 = in_r29 == 0;
    while (uVar8 = uVar10, (int)in_r29 < 0 || bVar11) {
      iVar3 = (int5)in_r17 + 0x61;
      if (iVar3 < 0x80000000) {
        if (iVar3 < -0x80000000) {
          iVar3 = -0x80000000;
        }
      }
      else {
        iVar3 = 0x7fffffff;
      }
      uVar10 = (uint)iVar3;
      in_r24 = in_r24 ^ in_r23;
      in_r26 = ~uVar6;
      uVar6 = in_r26 - uVar6;
      bVar11 = in_r16 == 0;
      in_r29 = in_r16;
      if (!bVar11) {
        while( true ) {
          sVar5 = (short)param_2;
          in_r24 = in_r24 ^ in_r23;
          cVar4 = (char)param_1 * 'q';
          if ((int)in_r24 < 1) break;
LAB_010c1720:
          func_0x012b1b68();
        }
        func_0x012b247a();
        in_r16 = in_r16 ^ in_r21;
        *(char *)(in_ep + 0x31) = cVar4;
        iVar7 = sVar5 * 0x6011;
        in_ep[0x62] = (short)in_r29;
        do {
          func_0x012b1b9e();
          uVar9 = (undefined2)in_r20;
          in_r16 = in_r16 ^ in_r21;
          if ((int)in_r16 < 0) {
            uVar8 = (uint)(ushort)in_ep[0x18];
            func_0x00f4a490(*in_ep);
            in_ep[0x60] = uVar9;
            *(char *)(uVar8 + 0x4c00) = (char)iVar7;
            __nop();
                    /* WARNING: Could not recover jumptable at 0x010c187e. Too many branches */
                    /* WARNING: Treating indirect jump as call */
            (*(code *)((short)in_ep[0x2a] * 0x7f53))(*(undefined1 *)((int)in_ep + 0x31));
            return;
          }
        } while ((int)(in_r29 + 0xf) < 0 == (-1 < (int)in_r29 && (int)(in_r29 + 0xf) < 0) &&
                 in_r29 != 0xfffffff1);
        *(char *)(in_r17 + 0x4c00) = (char)iVar7;
        in_ep[0x66] = (short)iVar7;
        func_0x00f4a3c4();
        *(undefined1 *)in_ep = 0;
        *(undefined1 *)(*(byte *)((int)in_ep + 0x35) + 0x4c00) = in_r11;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
        halt_unimplemented();
      }
    }
  } while( true );
}

