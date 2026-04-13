
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010c210c(int param_1,undefined4 param_2)

{
  char cVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  undefined4 in_r11;
  undefined1 in_r15;
  uint in_r17;
  uint in_r19;
  int in_r21;
  int in_r23;
  uint in_r24;
  undefined1 in_r29;
  int in_ep;
  int iVar5;
  undefined2 in_lp;
  
  uVar4 = in_r21 + 0xc000000;
  *(undefined1 *)(in_ep + 100) = in_r15;
  uVar2 = in_r21 + 0x8000000U | in_r24 & in_r19;
  iVar5 = in_ep + in_r23;
  do {
    uVar3 = uVar2 | in_r24 & in_r19;
    *(undefined4 *)(iVar5 + 0xa0) = param_2;
    *(char *)(in_r19 + 0x30a2) = (char)in_lp;
    __nop();
    *(undefined1 *)(in_r17 - 0x7400) = in_r15;
    *(char *)(in_r17 + 0x1800) = (char)in_r19;
    *(char *)(in_r19 - 0x3000) = (char)in_r23;
    __nop();
    __nop();
    *(undefined4 *)(iVar5 + 0x60) = in_r11;
    __nop();
    in_lp = *(undefined2 *)(iVar5 + 0xf2);
    uVar4 = (uint)(short)-(short)uVar4;
    uVar2 = uVar3 / uVar4;
    if ((uVar3 != 0x80000000 || uVar4 != 0xffffffff) && uVar4 != 0) {
      *(int *)(iVar5 + 0xf0) = iVar5;
      in_r17 = (uint)*(ushort *)(iVar5 + 2);
    }
    *(int *)(iVar5 + 0xf0) = iVar5;
    *(undefined1 *)(iVar5 + 99) = in_r29;
    *(undefined1 *)(in_r17 + 0x1800) = in_r15;
    cVar1 = *(char *)(iVar5 + 0x37);
    iVar5 = iVar5 + param_1 + in_r23;
    uVar4 = (uint)*(byte *)(iVar5 + 0x4a);
    *(int *)(iVar5 + 0xf0) = iVar5;
  } while (cVar1 == '\0');
  *(undefined1 *)(uVar4 - 0x18c9) = 0xf0;
  *(int *)(iVar5 + 0xf0) = iVar5;
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
  halt_unimplemented();
}

