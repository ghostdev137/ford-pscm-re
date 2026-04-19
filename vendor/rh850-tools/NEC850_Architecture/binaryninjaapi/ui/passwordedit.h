#pragma once

#include <QtWidgets/QLineEdit>
#include "uitypes.h"

class ClickableIcon;

class BINARYNINJAUIAPI PasswordEdit: public QLineEdit
{
	Q_OBJECT

	ClickableIcon* m_toggleIcon;
	void updateToggleIcon();

public:
	PasswordEdit(QWidget* parent = nullptr);

protected:
	void resizeEvent(QResizeEvent* event) override;
};
