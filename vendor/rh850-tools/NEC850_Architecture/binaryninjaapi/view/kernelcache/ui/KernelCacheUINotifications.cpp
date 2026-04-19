//
// Created by kat on 5/8/23.
//

#include "KernelCacheUINotifications.h"
#include <kernelcacheapi.h>
#include "ui/sidebar.h"
#include "ui/linearview.h"
#include "ui/viewframe.h"
#include "progresstask.h"

using namespace BinaryNinja;
using namespace KernelCacheAPI;

UINotifications* UINotifications::m_instance = nullptr;

void UINotifications::init()
{
	m_instance = new UINotifications;
	UIContext::registerNotification(m_instance);
}

void UINotifications::OnViewChange(UIContext* context, ViewFrame* frame, const QString& type)
{
	if (!frame)
		return;

	auto view = frame->getCurrentBinaryView();
	if (!view || view->GetTypeName() != KC_VIEW_NAME)
		return;

	auto viewInt = frame->getCurrentViewInterface();
	if (!viewInt)
		return;

	auto ah = viewInt->actionHandler();
	// Check to see if we have already bound these actions.
	if (ah->isBoundAction("Load Image by Name"))
		return;

	static auto loadImageAtAddr = [](BinaryView& view, uint64_t addr) {
		auto controller = KernelCacheController::GetController(view);
		if (!controller)
			return;
		if (auto foundImage = controller->GetImageContaining(addr))
		{
			// If we did not load the image, then we don't need to run analysis.
			if (!controller->ApplyImage(view, *foundImage))
				return;
			view.AddAnalysisOption("linearsweep");
			view.UpdateAnalysis();
		}
	};

	auto loadImageAddrAction = [](const UIActionContext& ctx) {
		uint64_t addr = 0;
		if (GetAddressInput(addr, "Address", "Address"))
		{
			BackgroundThread::create(ctx.context->mainWindow())
				->thenBackground([ctx, addr]() {
					loadImageAtAddr(*ctx.binaryView, addr);
				})->start();
		}
	};

	auto loadImageTokenAction = [](const UIActionContext& ctx) {
		BackgroundThread::create(ctx.context->mainWindow())
			->thenBackground([ctx](){ loadImageAtAddr(*ctx.binaryView, ctx.token.token.value); })
			->start();
	};

	auto isValidUnloadedImageAction = [](const UIActionContext& ctx) {
		uint64_t addr = ctx.token.token.value;
		// Check if the image is already loaded in the view.
		if (!ctx.binaryView->GetSectionsAt(addr).empty())
			return false;
		auto controller = KernelCacheController::GetController(*ctx.binaryView);
		if (!controller)
			return false;
		return controller->GetImageContaining(addr).has_value();
	};

	ah->bindAction("Load Image by Address", UIAction(loadImageAddrAction));

	ah->bindAction("Load IMGHERE", UIAction(loadImageTokenAction, isValidUnloadedImageAction));

	ah->setActionDisplayName("Load IMGHERE", [](const UIActionContext& ctx) {
		auto controller = KernelCacheController::GetController(*ctx.binaryView);
		if (!controller)
			return QString("NO CONTROLLER");
		uint64_t addr = ctx.token.token.value;
		auto image = controller->GetImageContaining(addr);
		if (!image)
			return QString("NO IMAGE");
		return QString("Load ") + image->name.c_str();
	});

	// Finally add the actions to the context menu.
	if (auto linearView = qobject_cast<LinearView*>(viewInt->widget()))
	{
		constexpr auto groupOneName = KC_VIEW_NAME;
		constexpr auto groupTwoName = KC_VIEW_NAME "2";
		linearView->contextMenu().addAction("Load IMGHERE", groupOneName);
		linearView->contextMenu().addAction("Load Image by Address", groupTwoName);
		linearView->contextMenu().setGroupOrdering(groupOneName, 0);
		linearView->contextMenu().setGroupOrdering(groupTwoName, 1);
	}
}

void UINotifications::OnAfterOpenFile(UIContext* context, FileContext* file, ViewFrame* frame)
{
	UIContextNotification::OnAfterOpenFile(context, file, frame);
}
