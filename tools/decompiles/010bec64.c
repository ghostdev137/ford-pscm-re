
/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Removing unreachable block (ram,0x010bec8a) */
/* WARNING: Removing unreachable block (ram,0x010becaa) */
/* WARNING: Removing unreachable block (ram,0x010becc8) */
/* WARNING: Removing unreachable block (ram,0x010beccc) */
/* WARNING: Removing unreachable block (ram,0x010becce) */
/* WARNING: Removing unreachable block (ram,0x010becd6) */
/* WARNING: Removing unreachable block (ram,0x010becde) */
/* WARNING: Removing unreachable block (ram,0x010becf8) */
/* WARNING: Removing unreachable block (ram,0x010bed02) */
/* WARNING: Removing unreachable block (ram,0x010bed08) */
/* WARNING: Removing unreachable block (ram,0x010bed0c) */
/* WARNING: Removing unreachable block (ram,0x010bed12) */
/* WARNING: Removing unreachable block (ram,0x010bed1e) */
/* WARNING: Removing unreachable block (ram,0x010bed54) */
/* WARNING: Removing unreachable block (ram,0x010bed64) */
/* WARNING: Removing unreachable block (ram,0x010bed6a) */

void FUN_010bec64(uint param_1)

{
  int5 iVar1;
  char cVar2;
  int in_r2;
  int in_r13;
  int in_r17;
  int in_r20;
  int in_r23;
  int in_r25;
  undefined4 in_r26;
  int in_r28;
  int in_ep;
  byte bVar3;
  ushort *in_CTBP;
  
  do {
    iVar1 = (int5)in_r2 - (int5)in_r13;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    iVar1 = (int5)in_r17 - (int5)(int)iVar1;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    in_r13 = (int)iVar1;
    cVar2 = *(char *)(in_ep + 0x4a);
    iVar1 = (int5)in_r25 + -0x2319;
    if (iVar1 < 0x80000000) {
      if (iVar1 < -0x80000000) {
        iVar1 = -0x80000000;
      }
    }
    else {
      iVar1 = 0x7fffffff;
    }
    in_ep = (int)iVar1;
    register0x0000000c = (BADSPACEBASE *)((uint)register0x0000000c / (uint)(int)(short)in_r17);
    *(undefined2 *)(in_r28 + 0x4040) = 0;
    if (-1 < in_r23) {
      in_r20 = *(int *)(in_ep + 0x38);
    }
    __nop();
    *(char *)(in_ep + 0x66) = (char)register0x0000000c;
    bVar3 = in_r17 == -1;
    (*(code *)((int)in_CTBP + (uint)*in_CTBP))((int)cVar2);
    if (!(bool)(bVar3 & 1)) {
      param_1 = (uint)*(short *)(in_r23 + 0x2ddc);
    }
    *(undefined1 *)(in_ep + 0x62) = 0;
    *(uint *)(in_ep + 0x6c) = param_1;
    *(undefined1 *)(in_ep + 0x62) = 0;
    (&DAT_0000102a)[in_r20] = (char)in_r20;
    *(undefined1 *)(in_ep + 0x62) = 0;
    param_1 = (uint)*(byte *)(in_ep + 0x37);
    *(short *)(in_ep + 0xcc) = (short)in_r26;
  } while( true );
}

