#pragma once

#include <QtCore/QModelIndex>
#include "binaryninjaapi.h"
#include "uicontext.h"
#include "viewframe.h"

class SplitPaneContainer;
class SplitPaneWidget;

class BINARYNINJAUIAPI CrossReferenceState
{
	struct Selection
	{
		SelectionInfoForXref selectionInfo;
		std::optional<int> previousDialogSelection;
	};

	std::map<SplitPaneContainer*, std::map<QString, Selection>> m_selections;
	SplitPaneContainer* m_currentContainer = nullptr;
	QString m_currentDataType;

public:
	CrossReferenceState();

	std::optional<SelectionInfoForXref> getCurrentSelection() const;
	std::optional<int> getPreviousDialogSelection() const;

	void updateCrossReferences(ViewFrame* frame, const SelectionInfoForXref& selection);
	void beginNavigationForCrossReference(ViewFrame* frame, const SelectionInfoForXref& selection);

	void setActiveContext(ViewFrame* frame);
	void destroyContext(SplitPaneWidget* splitPane);

	void newPinnedTab();
	void newPinnedPane();
	void modalDialog();
	void focusSidebar();

	void bindActions(UIContext* context);
};
