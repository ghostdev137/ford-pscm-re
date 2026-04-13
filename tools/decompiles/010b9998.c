
/* WARNING: Control flow encountered unimplemented instructions */

void FUN_010b9998(uint param_1)

{
  short in_r16;
  
  if (param_1 / (uint)(int)in_r16 == 0) {
                    /* WARNING: Unimplemented instruction - Truncating control flow here */
    halt_unimplemented();
  }
                    /* WARNING: Could not recover jumptable at 0x010b99b4. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&LAB_010b99b6 + *(short *)(&LAB_010b99b6 + ~(param_1 / (uint)(int)in_r16) * 2) * 2))();
  return;
}

