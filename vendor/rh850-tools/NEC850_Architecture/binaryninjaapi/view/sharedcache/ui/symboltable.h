#pragma once

#include <sharedcacheapi.h>
#include "viewframe.h"

#include <QTableView>
#include <QStandardItemModel>
#include "filter.h"

#ifndef BINARYNINJA_DSCSYMBOLTABLE_H
#define BINARYNINJA_DSCSYMBOLTABLE_H

class SymbolTableView;


class SymbolTableModel : public QAbstractTableModel
{
Q_OBJECT
	SymbolTableView* m_parent;
	QFont m_font;
	std::string m_filter;
	FilterOptions m_filterOptions;

	std::vector<SharedCacheAPI::CacheSymbol> m_symbols;
	std::vector<SharedCacheAPI::CacheSymbol> m_filteredSymbols;

	// A pointer to either m_symbols or m_filteredSymbols, depending on whether a filter is applied.
	std::vector<SharedCacheAPI::CacheSymbol> *m_displaySymbols = nullptr;

public:
	explicit SymbolTableModel(SymbolTableView* parent);

	int rowCount(const QModelIndex& parent) const override;
	int columnCount(const QModelIndex& parent) const override;
	QVariant data(const QModelIndex& index, int role) const override;
	QVariant headerData(int section, Qt::Orientation orientation, int role) const override;
	void sort(int column, Qt::SortOrder order) override;

	void updateSymbols(std::vector<SharedCacheAPI::CacheSymbol> symbols);
	void setFilter(const std::string& text, FilterOptions options);

	const SharedCacheAPI::CacheSymbol& symbolAt(int row) const;
};


class SymbolTableView : public QTableView, public FilterTarget
{
Q_OBJECT
	friend class SymbolTableModel;

	SymbolTableModel* m_model;

public:
	explicit SymbolTableView(QWidget* parent);
	~SymbolTableView() override;

	// Call this to populate the symbols from the given view.
	void populateSymbols(BinaryNinja::BinaryView& view);

	void scrollToFirstItem() override
	{
		if (model()->rowCount() > 0) {
			QModelIndex top = indexAt(rect().topLeft());
			if (top.isValid())
				scrollTo(top);
		}
	}

	void scrollToCurrentItem() override
	{
		QModelIndex currentIndex = selectionModel()->currentIndex();
		if (currentIndex.isValid())
			scrollTo(currentIndex);
	}

	void ensureSelection() override
	{
		QModelIndex current = selectionModel()->currentIndex();
		if (current.isValid() || model()->rowCount() == 0)
			return;

		if (auto top = indexAt(rect().topLeft()); top.isValid())
		{
			selectionModel()->select(top, QItemSelectionModel::ClearAndSelect);
			setCurrentIndex(top);
		}
	}


	void activateSelection() override
	{
		ensureSelection();
		if (auto current = selectionModel()->currentIndex(); current.isValid())
			emit activated(current);
	}

	SharedCacheAPI::CacheSymbol getSymbolAtRow(int row) const
	{
		return m_model->symbolAt(row);
	}

	void setFilter(const std::string& filter, FilterOptions options) override;
};


#endif  // BINARYNINJA_DSCSYMBOLTABLE_H
