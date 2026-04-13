
/* WARNING: This function may have set the stack pointer */

void FUN_010b80ce(uint param_1,uint param_2)

{
  ushort uVar1;
  byte bVar2;
  ushort uVar3;
  ushort uVar4;
  undefined4 in_r11;
  int in_r12;
  undefined4 in_r15;
  undefined4 in_r19;
  uint in_r21;
  undefined2 in_r24;
  ushort in_r29;
  ushort *in_ep;
  ushort *puVar5;
  uint in_PSW;
  
  param_2 = param_2 & in_r21;
  *(undefined4 *)(in_ep + 0x50) = in_r15;
  uVar3 = in_ep[0x5a];
  in_ep[0x5a] = uVar3;
  if (!(bool)((byte)(in_PSW >> 3) & 1) && param_2 != 0) {
    uVar4 = in_ep[0x44];
    uVar3 = in_ep[0xc];
    uVar1 = in_ep[1];
    *(uint *)(in_r12 + 0x4a1c) = (uint)uVar4;
    *(ushort *)(uVar3 + 0x14da) = uVar4;
    in_ep[0x61] = uVar3;
    func_0x01108832(uVar1,param_2 & in_r21);
    (*(code *)&LAB_00000030)();
    return;
  }
  *(char *)(in_ep + 0x34) = (char)in_r12;
  *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
  uVar4 = in_ep[0x28];
  uVar1 = *in_ep;
  in_ep[0x5a] = (ushort)*(undefined4 *)(in_ep + 2);
  if (0xfffffff9 < uVar3) {
    *(BADSPACEBASE **)(in_ep + 0x50) = register0x0000000c;
    bVar2 = *(byte *)((int)in_ep + 0x1d);
    puVar5 = (ushort *)~param_1;
    puVar5[0x5a] = in_ep[0x42];
    *(undefined4 *)(puVar5 + 0x50) = in_r19;
    uVar3 = puVar5[0x62];
    *(char *)(puVar5[0xd] - 0x5384) = (char)param_1;
    puVar5[0x5a] = uVar3;
    if (bVar2 < 0xb) {
      *(BADSPACEBASE **)(puVar5 + 0x50) = register0x0000000c;
      puVar5[0x5a] = puVar5[0x42];
      puVar5[0x61] = in_r29;
      *(undefined4 *)(puVar5 + 0x50) = in_r11;
      *(undefined4 *)(puVar5 + 0x54) = in_r15;
      *(char *)(puVar5 + 0x14) = (char)uVar4;
                    /* WARNING: Could not recover jumptable at 0x010b8294. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (*(code *)(uint)*puVar5)(puVar5[0xd]);
      return;
    }
    *(undefined2 *)(uVar1 + 0x7010) = in_r24;
    return;
  }
  __nop();
                    /* WARNING: Could not recover jumptable at 0x010b82e4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)in_ep[0xd])(param_2 + 0xab7c0000);
  return;
}

