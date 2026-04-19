#pragma once

#include <QtWidgets/QDialog>
#include "binaryninjaapi.h"
#include "uitypes.h"
#include "clickablelabel.h"

/*!

    \defgroup logmessagedialog LogMessageDialog
    \ingroup uiapi
*/

/*!
    \ingroup logmessagedialog
*/
class BINARYNINJAUIAPI LogMessageDialog : public QDialog
{
	Q_OBJECT

	QString m_stackTrace;
	ClickableLabel* m_showStackTraceLabel = nullptr;
	QVBoxLayout* m_stackTraceLayout = nullptr;
	bool m_stackTraceVisible = false;

	static constexpr int MAX_WIDTH = 720;
	static constexpr int STACK_TRACE_HEIGHT = 300;

	void init(BNLogLevel level, const QString& stackTrace, const QString& message);

public:
	LogMessageDialog(QWidget* parent, BNLogLevel level, const std::optional<std::string>& stackTrace,
		const std::string& message);
	LogMessageDialog(QWidget* parent, BNLogLevel level, const QString& stackTrace, const QString& message);

public Q_SLOTS:
	void requestStackTrace();
};
