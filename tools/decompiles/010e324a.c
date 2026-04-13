
void FUN_010e324a(uint param_1,int param_2,short param_3)

{
  int in_r10;
  undefined4 in_r19;
  code *UNRECOVERED_JUMPTABLE_00;
  int in_r27;
  int in_ep;
  
  *(undefined4 *)(in_ep + 0xa0) = in_r19;
  if (-1 < in_r10) {
    *(undefined4 *)(in_ep + 0xa8) = in_r19;
    *(int *)(in_ep + 0xac) = param_2 + in_r27;
    *(int *)(in_ep + 0xac) = in_r27;
    *(int *)(in_ep + 0xac) = in_r27;
                    /* WARNING: Could not recover jumptable at 0x010e32d4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*UNRECOVERED_JUMPTABLE_00)((short)param_1 * 2);
    return;
  }
  *(undefined4 *)(in_ep + 0xa8) = in_r19;
  *(int *)(in_ep + 0xac) = param_2 + in_r27;
  *(int *)(in_ep + 0xac) = in_r27;
  *(int *)(in_ep + 0xac) = in_r27;
                    /* WARNING: Could not recover jumptable at 0x010e3286. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*UNRECOVERED_JUMPTABLE_00)(param_1 / (uint)(int)param_3);
  return;
}

