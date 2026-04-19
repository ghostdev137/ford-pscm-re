#include <progresstask.h>
#include "symboltable.h"

#include <QHeaderView>

#include "ui/fontsettings.h"

#include "binaryninjaapi.h"

using namespace BinaryNinja;
using namespace SharedCacheAPI;


SymbolTableModel::SymbolTableModel(SymbolTableView* parent) :
	QAbstractTableModel(parent), m_parent(parent), m_displaySymbols(&m_symbols)
{
	// TODO: Need to implement updating this font if it is changed by the user
	m_font = getMonospaceFont(parent);
}


int SymbolTableModel::rowCount(const QModelIndex& parent) const {
	Q_UNUSED(parent);
	return static_cast<int>(m_displaySymbols->size());
}


int SymbolTableModel::columnCount(const QModelIndex& parent) const {
	Q_UNUSED(parent);
	// We have 3 columns: Address, Type, Name
	return 3;
}


QVariant SymbolTableModel::data(const QModelIndex& index, int role) const {
	if (!index.isValid() || (role != Qt::DisplayRole && role != Qt::FontRole)) {
		return QVariant();
	}

	switch (role)
	{
	case Qt::DisplayRole:
	{
		auto symbol = symbolAt(index.row());
		auto symbolType = GetSymbolTypeAsString(symbol.type);

		switch (index.column())
		{
		case 0: // Address column
			return QString("0x%1").arg(symbol.address, 0, 16); // Display address as hexadecimal
		case 1: // Type column
			return QString::fromUtf8(symbolType.c_str(), symbolType.size());
		case 2: // Name column
			return QString::fromUtf8(symbol.name.c_str(), symbol.name.size());
		default:
			return QVariant();
		}
	}
	case Qt::FontRole:
		return m_font;
	default:
		return QVariant();
	}
}


QVariant SymbolTableModel::headerData(int section, Qt::Orientation orientation, int role) const {
	if (role != Qt::DisplayRole || orientation != Qt::Horizontal) {
		return QVariant();
	}

	switch (section) {
	case 0:
		return QString("Address");
	case 1:
		return QString("Type");
	case 2:
		return QString("Name");
	default:
		return QVariant();
	}
}


void SymbolTableModel::sort(int column, Qt::SortOrder order)
{
	beginResetModel();

	std::function<bool(const CacheSymbol&, const CacheSymbol&)> comparator;

	switch (column)
	{
	case 0: // Address column
		comparator = [](const CacheSymbol& a, const CacheSymbol& b) {
			return a.address < b.address;
		};
		break;
	case 1: // Type column
		comparator = [](const CacheSymbol& a, const CacheSymbol& b) {
			return GetSymbolTypeAsString(a.type) < GetSymbolTypeAsString(b.type);
		};
		break;
	case 2: // Name column
		comparator = [](const CacheSymbol& a, const CacheSymbol& b) {
			return a.name < b.name;
		};
		break;
	default:
		endResetModel();
		return;
	}

	if (order == Qt::DescendingOrder)
	{
		std::sort(m_displaySymbols->begin(), m_displaySymbols->end(),
			[&comparator](const CacheSymbol& a, const CacheSymbol& b) { return comparator(b, a); });
	}
	else
	{
		std::sort(m_displaySymbols->begin(), m_displaySymbols->end(), comparator);
	}

	endResetModel();
}


void SymbolTableModel::updateSymbols(std::vector<CacheSymbol> symbols)
{
	m_symbols = std::move(symbols);
	setFilter(m_filter, m_filterOptions);
}


const CacheSymbol& SymbolTableModel::symbolAt(int row) const
{
	return m_displaySymbols->at(row);
}


void SymbolTableModel::setFilter(const std::string& text, FilterOptions options)
{
	m_filter = text;
	m_filterOptions = options;
	bool caseSensitive = options.testFlag(CaseSensitiveOption);
	beginResetModel();
	// Skip filtering if no filter applied.
	if (m_filter.empty())
	{
		m_filteredSymbols = {};
		m_displaySymbols = &m_symbols;
	}
	else
	{
		// Clear the filtered symbols while preserving the capacity
		m_filteredSymbols.clear();

		for (const auto& symbol : m_symbols)
		{
			const std::string& symbolName = symbol.name;
			bool match;
			if (caseSensitive)
			{
				match = (symbolName.find(m_filter) != std::string::npos);
			}
			else
			{
				auto it = std::search(
					symbolName.begin(), symbolName.end(),
					m_filter.begin(), m_filter.end(),
					[](char c1, char c2) { return std::tolower(c1) == std::tolower(c2); }
				);

				match = (it != symbolName.end());
			}

			if (match)
			{
				m_filteredSymbols.push_back(symbol);
			}
		}

		// If the filtered vector is using less than 25% of its capacity,
		// shrink it to reduce memory usage.
		if (m_filteredSymbols.size() < m_filteredSymbols.capacity() / 4)
			m_filteredSymbols.shrink_to_fit();

		m_displaySymbols = &m_filteredSymbols;
	}

	endResetModel();
}




SymbolTableView::SymbolTableView(QWidget* parent) :
	QTableView(parent), m_model(new SymbolTableModel(this))
{
	// Set up the filter model
	setModel(m_model);

	// Configure view settings
	horizontalHeader()->setSectionResizeMode(0, QHeaderView::Fixed);
	horizontalHeader()->setSectionResizeMode(1, QHeaderView::Fixed);
	horizontalHeader()->setSectionResizeMode(2, QHeaderView::Stretch);
	setEditTriggers(QAbstractItemView::NoEditTriggers);
	setSelectionBehavior(QAbstractItemView::SelectRows);
	setSelectionMode(QAbstractItemView::SingleSelection);
	verticalHeader()->setVisible(false);

	sortByColumn(0, Qt::AscendingOrder);
	setSortingEnabled(true);
}

SymbolTableView::~SymbolTableView() = default;

void SymbolTableView::populateSymbols(BinaryView &view)
{
	if (auto controller = SharedCacheController::GetController(view)) {
		typedef std::vector<CacheSymbol> SymbolList;
		// Retrieve the symbols from the controller in a future than pass that to the model.
		QPointer<QFutureWatcher<SymbolList>> watcher = new QFutureWatcher<SymbolList>(this);
		connect(watcher, &QFutureWatcher<SymbolList>::finished, this, [watcher, this]() {
			if (watcher)
			{
				auto symbols = watcher->result();
				m_model->updateSymbols(std::move(symbols));

				// Reapply the current sort after repopulating the model
				// TODO: The model should use `QSortFilterProxyModel`, but that's a bigger change.
				setSortingEnabled(true);
			}
		});
		QFuture<SymbolList> future = QtConcurrent::run([controller]() {
			return controller->GetSymbols();
		});
		watcher->setFuture(future);
		connect(this, &QObject::destroyed, this, [watcher]() {
			if (watcher && watcher->isRunning()) {
				watcher->cancel();
				watcher->waitForFinished();
			}
		});
	}
}


void SymbolTableView::setFilter(const std::string& filter, FilterOptions options)
{
	m_model->setFilter(filter, options);
}
