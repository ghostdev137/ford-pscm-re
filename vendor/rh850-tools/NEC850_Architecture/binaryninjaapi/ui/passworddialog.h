#pragma once

#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QCheckBox>
#include <QDialogButtonBox>
#include "uitypes.h"
#include "passwordedit.h"


class BINARYNINJAUIAPI PasswordDialog : public QDialog
{
	Q_OBJECT

	PasswordEdit* m_passwordEdit = nullptr;
	QDialogButtonBox* m_buttons = nullptr;
	QCheckBox* m_saveCheckBox = nullptr;

public:
	PasswordDialog(QWidget* parent, const QString& resource, bool showSaveOption = false);

	QString password() const;
	bool shouldSavePassword() const;
	void notifyInvalid();

signals:
	void validate(const QString& password, bool shouldSave);

private slots:
	void onTextChanged();
};
