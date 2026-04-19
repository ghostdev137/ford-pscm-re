#pragma once

#include "uitypes.h"
#include <QtWidgets/QLabel>
#include <QtWidgets/QToolButton>
#include <QtCore/QParallelAnimationGroup>
#include <QtCore/QPropertyAnimation>

/*!

    \ingroup uiapi
*/
class BINARYNINJAUIAPI ExpandableGroup : public QWidget
{
	Q_OBJECT

  private:
	QToolButton* m_button;
	QLabel* m_title;
	QParallelAnimationGroup* m_animation;
	QWidget* m_content;
	int m_duration = 100;
	bool m_expanded;

  private Q_SLOTS:
	void toggled(bool expanded);

  Q_SIGNALS:
	void sizeChanged();

  public:
	explicit ExpandableGroup(QLayout* contentLayout, const QString& title = "", QWidget* parent = nullptr, bool expanded = false);
	void setupAnimation(QLayout* contentLayout);
	void setTitle(const QString& title) { m_title->setText(title); }
	void toggle(bool expanded);
	bool expanded() { return m_expanded; }
	void setContentExpandable(bool expandable);
};
