#include <binaryninjaapi.h>
#include "KernelCacheView.h"
#include "transformers/KernelCacheTransforms.h"

#ifdef __cplusplus
extern "C" {
#endif
#ifdef __cplusplus
}
#endif

extern "C"
{
	BN_DECLARE_CORE_ABI_VERSION

	BINARYNINJAPLUGIN bool CorePluginInit()
	{
		KernelCacheViewType::Register();
		RegisterTransformers();
		return true;
	}
}