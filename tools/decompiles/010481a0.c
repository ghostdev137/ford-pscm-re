
void FUN_010481a0(int param_1)

{
  int in_r12;
  undefined4 in_r17;
  int in_ep;
  
  if (in_r12 < 0) {
    param_1 = (int)(char)param_1;
    func_0x072e81f6();
  }
  *(undefined1 *)(in_ep + 0x66) = 0;
  __nop();
  *(undefined4 *)(in_ep + 0x68) = in_r17;
  *(undefined2 *)(in_ep + 0xcc) = 0;
                    /* WARNING: Could not recover jumptable at 0x010481e0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010481e2 + *(short *)(&LAB_010481e2 + param_1 * 2) * 2))
            (~(uint)*(ushort *)(in_ep + 0x98));
  return;
}

