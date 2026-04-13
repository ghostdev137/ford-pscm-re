
/* WARNING: Removing unreachable block (ram,0x0100f042) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_0100f068(short param_1,undefined2 param_2)

{
  bool bVar1;
  byte bVar2;
  int5 iVar3;
  int5 iVar4;
  int5 iVar5;
  int5 iVar6;
  int5 iVar7;
  uint in_r1;
  uint in_r2;
  uint unaff_gp;
  short unaff_tp;
  int in_r10;
  int in_r11;
  undefined2 in_r18;
  int in_r19;
  undefined2 in_r20;
  int in_r21;
  undefined2 in_r22;
  short in_r27;
  undefined2 in_r28;
  undefined2 *in_ep;
  int iVar8;
  int in_lp;
  uint in_PSW;
  ushort *in_CTBP;
  
  do {
    if (!(bool)((byte)(in_PSW >> 3) & 1) && !(bool)((byte)in_PSW & 1)) goto LAB_0100f056;
LAB_0100f06a:
    iVar3 = -(int5)in_r10;
    bVar1 = in_r10 != 0;
    in_PSW = (uint)bVar1 << 3 | (uint)(in_r10 == 0);
    if (iVar3 < 0x80000000) {
      if (iVar3 < -0x80000000) {
        iVar3 = -0x80000000;
      }
    }
    else {
      iVar3 = 0x7fffffff;
    }
    in_r10 = (int)iVar3;
    if (!bVar1 && !(bool)((byte)in_PSW & 1)) goto LAB_0100f05a;
LAB_0100f06e:
    *in_ep = (short)iVar3;
    if (!SUB41(in_PSW >> 3,0) && !(bool)((byte)in_PSW & 1)) goto LAB_0100f05e;
LAB_0100f072:
    iVar4 = -(int5)in_r11;
    bVar1 = in_r11 != 0;
    in_PSW = (uint)bVar1 << 3 | (uint)(in_r11 == 0);
    if (iVar4 < 0x80000000) {
      if (iVar4 < -0x80000000) {
        iVar4 = -0x80000000;
      }
    }
    else {
      iVar4 = 0x7fffffff;
    }
    in_r11 = (int)iVar4;
    if (bVar1 || (bool)((byte)in_PSW & 1)) {
LAB_0100f076:
      *in_ep = (short)iVar4;
      if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
LAB_0100f07a:
        *in_ep = in_r18;
        if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
LAB_0100f07e:
          iVar5 = -(int5)in_r19;
          bVar1 = in_r19 != 0;
          in_PSW = (uint)bVar1 << 3 | (uint)(in_r19 == 0);
          if (iVar5 < 0x80000000) {
            if (iVar5 < -0x80000000) {
              iVar5 = -0x80000000;
            }
          }
          else {
            iVar5 = 0x7fffffff;
          }
          in_r19 = (int)iVar5;
          if (bVar1 || (bool)((byte)in_PSW & 1)) {
LAB_0100f082:
            *in_ep = (short)iVar5;
            if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
LAB_0100f086:
              *in_ep = in_r20;
              if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
LAB_0100f08a:
                iVar6 = -(int5)in_r21;
                bVar1 = in_r21 != 0;
                in_PSW = (uint)bVar1 << 3 | (uint)(in_r21 == 0);
                if (iVar6 < 0x80000000) {
                  if (iVar6 < -0x80000000) {
                    iVar6 = -0x80000000;
                  }
                }
                else {
                  iVar6 = 0x7fffffff;
                }
                in_r21 = (int)iVar6;
                if (bVar1 || (bool)((byte)in_PSW & 1)) {
LAB_0100f08e:
                  *in_ep = (short)iVar6;
                  if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
LAB_0100f092:
                    *in_ep = in_r22;
                    if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
LAB_0100f096:
                      *in_ep = in_r28;
                      if (SUB41(in_PSW >> 3,0) || (bool)((byte)in_PSW & 1)) {
                        while( true ) {
                          iVar7 = -(int5)in_lp;
                          bVar1 = in_lp != 0;
                          in_PSW = (uint)bVar1 << 3 | (uint)(in_lp == 0);
                          if (iVar7 < 0x80000000) {
                            if (iVar7 < -0x80000000) {
                              iVar7 = -0x80000000;
                            }
                          }
                          else {
                            iVar7 = 0x7fffffff;
                          }
                          in_lp = (int)iVar7;
                          if (!bVar1 && !(bool)((byte)in_PSW & 1)) break;
                          while( true ) {
                            in_ep[1] = (short)in_r1;
                            if (!SUB41(in_PSW >> 3,0) && !(bool)((byte)in_PSW & 1))
                            goto LAB_0100f08e;
                            iVar7 = (int5)(int)in_r1 - (int5)(int)in_r2;
                            bVar1 = in_r1 < in_r2;
                            in_PSW = (uint)bVar1 << 3 | (uint)(in_r1 == in_r2);
                            if (iVar7 < 0x80000000) {
                              if (iVar7 < -0x80000000) {
                                iVar7 = -0x80000000;
                              }
                            }
                            else {
                              iVar7 = 0x7fffffff;
                            }
                            in_r2 = (uint)iVar7;
                            bVar2 = (byte)in_PSW;
                            if (!bVar1 && !(bool)(bVar2 & 1)) goto LAB_0100f092;
                            in_ep[1] = (short)iVar7;
                            if (!bVar1 && !(bool)(bVar2 & 1)) goto LAB_0100f096;
                            in_ep[1] = (short)&stack0x00000000;
                            if (!bVar1 && !(bool)(bVar2 & 1)) break;
                            iVar7 = (int5)(int)in_r1 - (int5)(int)unaff_gp;
                            bVar1 = in_r1 < unaff_gp;
                            in_PSW = (uint)bVar1 << 3 | (uint)(in_r1 == unaff_gp);
                            if (iVar7 < 0x80000000) {
                              if (iVar7 < -0x80000000) {
                                iVar7 = -0x80000000;
                              }
                            }
                            else {
                              iVar7 = 0x7fffffff;
                            }
                            unaff_gp = (uint)iVar7;
                            if (bVar1 || (bool)((byte)in_PSW & 1)) {
                              in_ep[1] = (short)iVar7;
                              in_ep[0x3f] = in_ep[0x7f];
                              iVar8 = in_r27 * -0x301;
                              *(undefined2 *)(iVar8 + 0x7e) = *(undefined2 *)(iVar8 + 0xfe);
                              *(undefined2 *)(iVar8 + 0xfe) = *(undefined2 *)(iVar8 + 0xfe);
                              (*(code *)((int)in_CTBP + (uint)*in_CTBP))();
                              return 0;
                            }
                          }
                        }
                        goto LAB_0100f08a;
                      }
                      goto LAB_0100f086;
                    }
                    goto LAB_0100f082;
                  }
                  goto LAB_0100f07e;
                }
                goto LAB_0100f07a;
              }
              goto LAB_0100f076;
            }
            goto LAB_0100f072;
          }
          goto LAB_0100f06e;
        }
        goto LAB_0100f06a;
      }
      goto LAB_0100f066;
    }
LAB_0100f062:
    *in_ep = (short)unaff_gp;
    if (!SUB41(in_PSW >> 3,0) && !(bool)((byte)in_PSW & 1)) {
      do {
        iVar3 = -(int5)(int)unaff_gp;
        if (iVar3 < 0x80000000) {
          if (iVar3 < -0x80000000) {
            iVar3 = -0x80000000;
          }
        }
        else {
          iVar3 = 0x7fffffff;
        }
        unaff_gp = (uint)iVar3;
LAB_0100f056:
        iVar3 = -(int5)(int)in_r1;
        bVar1 = in_r1 != 0;
        in_PSW = (uint)bVar1 << 3 | (uint)(in_r1 == 0);
        if (iVar3 < 0x80000000) {
          if (iVar3 < -0x80000000) {
            iVar3 = -0x80000000;
          }
        }
        else {
          iVar3 = 0x7fffffff;
        }
        in_r1 = (uint)iVar3;
        if (bVar1 || (bool)((byte)in_PSW & 1)) {
LAB_0100f05a:
          *in_ep = (short)&stack0x00000000;
          if (!SUB41(in_PSW >> 3,0) && !(bool)((byte)in_PSW & 1)) goto LAB_0100f04a;
LAB_0100f05e:
          iVar3 = -(int5)(int)unaff_gp;
          bVar1 = unaff_gp != 0;
          in_PSW = (uint)bVar1 << 3 | (uint)(unaff_gp == 0);
          if (iVar3 < 0x80000000) {
            if (iVar3 < -0x80000000) {
              iVar3 = -0x80000000;
            }
          }
          else {
            iVar3 = 0x7fffffff;
          }
          unaff_gp = (uint)iVar3;
          if (bVar1 || (bool)((byte)in_PSW & 1)) goto LAB_0100f062;
        }
        else {
          in_r2 = in_r2 / (uint)(int)unaff_tp;
LAB_0100f04a:
          in_r2 = in_r2 / (uint)(int)param_1;
          *(char *)((int)in_ep + 0x7f) = (char)in_lp;
        }
        *(char *)((int)in_ep + 0x7f) = (char)in_lp;
      } while( true );
    }
LAB_0100f066:
    *in_ep = param_2;
  } while( true );
}

