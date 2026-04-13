
void FUN_010e8060(undefined4 param_1)

{
  ushort uVar1;
  ushort uVar2;
  ushort uVar3;
  ushort uVar4;
  undefined4 in_r11;
  undefined4 in_r19;
  int in_r25;
  int in_r28;
  ushort *in_ep;
  
  *(int *)(in_r28 + 0x7842) = in_r28;
  uVar1 = *in_ep;
  *(undefined4 *)(in_ep + 0x50) = in_r19;
  *(undefined4 *)(in_ep + 0x54) = in_r19;
  uVar2 = in_ep[0x50];
  *(int *)(in_r25 + 0x7842) = in_r25;
  *(undefined4 *)(in_ep + 0x50) = param_1;
  *(undefined4 *)(in_ep + 0x54) = param_1;
  uVar3 = *in_ep;
  *(undefined4 *)(in_ep + 0x7c) = in_r11;
  uVar4 = in_ep[0xd];
  in_ep[0x42] = *in_ep;
  *(undefined1 *)(uVar1 + 6) = 0;
  *(undefined1 *)(in_ep + 0x33) = 0;
  *(undefined1 *)(in_ep + 0x31) = 0;
                    /* WARNING: Could not recover jumptable at 0x010e8102. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(uint)uVar2)(uVar3,uVar4);
  return;
}

