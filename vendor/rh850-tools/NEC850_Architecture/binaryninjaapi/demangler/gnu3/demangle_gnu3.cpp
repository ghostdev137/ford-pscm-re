// Copyright 2016-2026 Vector 35 Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Includes snippets from LLVM, which is under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.

#include "demangle_gnu3.h"
#include <stdarg.h>
#include <algorithm>
#include <memory>


#ifdef BINARYNINJACORE_LIBRARY
using namespace BinaryNinjaCore;
#define GetClass GetTypeClass
#else
using namespace BinaryNinja;
using namespace std;
#endif


#define MAX_DEMANGLE_LENGTH    262144
#define hash(x,y) (64 * x + y)

#undef GNUDEMANGLE_DEBUG
#ifdef GNUDEMANGLE_DEBUG  // This makes it not thread safe!
static string _indent = "";
#define indent() _indent += " ";
#define dedent() do {if (_indent.size() > 0) _indent = _indent.substr(1);}while(0);

void MyLogDebug(const char* fmt, ...)
{
	va_list args;
	va_start(args, fmt);
	PerformLog(0, DebugLog, "", 0, (_indent + fmt).c_str(), args);
	va_end(args);
}
#else
#define indent()
#define dedent()
#define MyLogDebug(...) do {} while(0)
#endif

static inline void rtrim(string &s)
{
	s.erase(find_if(s.rbegin(), s.rend(), [](int c) { return !isspace(c); }).base(), s.end());
}


static size_t TotalStringSize(const _STD_VECTOR<_STD_STRING>& v)
{
	size_t n = 0;
	for (const auto& s : v)
		n += s.size();
	return n;
}


static string GetTemplateString(const vector<string>& args)
{
	// Pre-calculate total length to avoid reallocations
	size_t total = 2; // "<" + ">"
	for (size_t i = 0; i < args.size(); i++)
	{
		if (i != 0)
			total += 2; // ", "
		total += args[i].size();
	}
	total += 1; // possible " " before ">"

	string name;
	name.reserve(total);
	name += '<';
	for (size_t i = 0; i < args.size(); i++)
	{
		if (i != 0)
			name += ", ";
		name += args[i];
	}
	rtrim(name);
	if (name.back() == '>')
		name += " "; //Be c++03 compliant where we can
	name += '>';
	return name;
}


static string GetOperator(char elm1, char elm2)
{
	switch (hash(elm1, elm2))
	{
	case hash('d','c'): return "dynamic_cast";
	case hash('s','c'): return "static_cast";
	case hash('c','c'): return "const_cast";
	case hash('r','c'): return "reinterpret_cast";
	case hash('t','i'): return "typeid";
	case hash('t','e'): return "typeid";
	case hash('s','t'): return "sizeof";
	case hash('s','z'): return "sizeof";
	case hash('a','t'): return "alignof";
	case hash('a','z'): return "alignof";
	case hash('n','x'): return "noexcept";
	case hash('s','Z'): return "sizeof...";
	case hash('s','P'): return "sizeof...";
	case hash('s','p'): return "";
	case hash('t','w'): return "throw";
	case hash('t','r'): return "throw";
	case hash('l','s'): return "<<";  // <<
	case hash('r','s'): return ">>";  // >>
	case hash('a','S'): return "=";   // =
	case hash('n','t'): return "!";   // !
	case hash('e','q'): return "==";  // ==
	case hash('n','e'): return "!=";  // !=
	case hash('i','x'): return "[]";  // []
	case hash('d','t'): return ".";   // .
	case hash('p','t'): return "->";  // ->
	case hash('m','l'): return "*";   // *
	case hash('p','p'): return "++";  // ++ (postfix in <expression> context)
	case hash('m','m'): return "--";  // -- (postfix in <expression> context)
	case hash('n','g'): return "-";   // - (unary)
	case hash('m','i'): return "-";   // -
	case hash('p','s'): return "+";   // + (unary)
	case hash('p','l'): return "+";   // +
	case hash('a','d'): return "&";   // & (unary)
	case hash('a','n'): return "&";   // &
	case hash('p','m'): return "->*"; // ->*
	case hash('d','v'): return "/";   // /
	case hash('r','m'): return "%";   // %
	case hash('l','t'): return "<";   // <
	case hash('l','e'): return "<=";  // <=
	case hash('g','t'): return ">";   // >
	case hash('g','e'): return ">=";  // >=
	case hash('c','m'): return ",";   // ,
	case hash('c','l'): return "()";  // ()
	case hash('c','o'): return "~";   // ~
	case hash('e','o'): return "^";   // ^
	case hash('o','r'): return "|";   // |
	case hash('a','a'): return "&&";  // &&
	case hash('o','o'): return "||";  // ||
	case hash('d','e'): return "*";   // * (unary)
	case hash('m','L'): return "*=";  // *=
	case hash('p','L'): return "+=";  // +=
	case hash('m','I'): return "-=";  // -=
	case hash('d','V'): return "/=";  // /=
	case hash('r','M'): return "%=";  // %=
	case hash('r','S'): return ">>="; // >>=
	case hash('l','S'): return "<<="; // <<=
	case hash('a','N'): return "&=";  // &=
	case hash('o','R'): return "|=";  // |=
	case hash('e','O'): return "^=";  // ^=
	case hash('s','s'): return "<=>"; // <=>
	case hash('d','l'): return "delete";   // delete
	case hash('d','a'): return "delete[]"; // delete[]
	case hash('n','w'): return "new";      // new
	case hash('n','a'): return "new[]";    // new []
	default: return "";
	}
}

static BNNameType GetNameType(char elm1, char elm2)
{
	switch (hash(elm1, elm2))
	{
	case hash('n','t'): return OperatorNotNameType;              // !
	case hash('n','g'): return OperatorMinusNameType;       // - (unary)
	case hash('p','s'): return OperatorPlusNameType;        // + (unary)
	case hash('a','d'): return OperatorBitAndNameType;      // & (unary)
	case hash('d','e'): return OperatorStarNameType;        // * (unary)
	case hash('i','x'): return OperatorArrayNameType;            // []
	case hash('p','p'): return OperatorIncrementNameType;        // ++ (postfix in <expression> context)
	case hash('m','m'): return OperatorDecrementNameType;        // -- (postfix in <expression> context)
	case hash('l','s'): return OperatorLeftShiftNameType;        // <<
	case hash('r','s'): return OperatorRightShiftNameType;       // >>
	case hash('a','S'): return OperatorAssignNameType;           // =
	case hash('e','q'): return OperatorEqualNameType;            // ==
	case hash('n','e'): return OperatorNotEqualNameType;         // !=
	case hash('p','t'): return OperatorArrowNameType;            // ->
	case hash('m','l'): return OperatorStarNameType;             // *
	case hash('m','i'): return OperatorMinusNameType;            // -
	case hash('p','l'): return OperatorPlusNameType;             // +
	case hash('a','n'): return OperatorBitAndNameType;           // &
	case hash('p','m'): return OperatorArrowStarNameType;        // ->*
	case hash('d','v'): return OperatorDivideNameType;           // /
	case hash('r','m'): return OperatorModulusNameType;          // %
	case hash('l','t'): return OperatorLessThanNameType;         // <
	case hash('l','e'): return OperatorLessThanEqualNameType;    // <=
	case hash('g','t'): return OperatorGreaterThanNameType;      // >
	case hash('g','e'): return OperatorGreaterThanEqualNameType; // >=
	case hash('c','m'): return OperatorCommaNameType;           // ,
	case hash('c','l'): return OperatorParenthesesNameType;     // ()
	case hash('c','o'): return OperatorTildeNameType;           // ~
	case hash('e','o'): return OperatorXorNameType;             // ^
	case hash('o','r'): return OperatorBitOrNameType;           // |
	case hash('a','a'): return OperatorLogicalAndNameType;      // &&
	case hash('o','o'): return OperatorLogicalOrNameType;       // ||
	case hash('m','L'): return OperatorStarEqualNameType;       // *=
	case hash('p','L'): return OperatorPlusEqualNameType;       // +=
	case hash('m','I'): return OperatorMinusEqualNameType;      // -=
	case hash('d','V'): return OperatorDivideEqualNameType;     // /=
	case hash('r','M'): return OperatorModulusEqualNameType;    // %=
	case hash('r','S'): return OperatorRightShiftEqualNameType; // >>=
	case hash('l','S'): return OperatorLeftShiftEqualNameType;  // <<=
	case hash('a','N'): return OperatorAndEqualNameType;        // &=
	case hash('o','R'): return OperatorOrEqualNameType;         // |=
	case hash('e','O'): return OperatorXorEqualNameType;        // ^=
	case hash('d','l'): return OperatorDeleteNameType;          // delete
	case hash('d','a'): return OperatorDeleteArrayNameType;     // delete[]
	case hash('n','w'): return OperatorNewNameType;             // new
	case hash('n','a'): return OperatorNewArrayNameType;        // new []
	// Note: C1-C5 (constructor) and D0-D5 (destructor) are handled directly
	// by DemangleUnqualifiedName with their own case blocks, so they never
	// reach GetNameType.
	default:
		return NoNameType;
	}
}




// Decode a big-endian hex string into a float or double.
// Returns the decimal string representation, or the raw hex with a type
// prefix if decoding fails or the result is NaN/Inf.
static string DecodeHexFloat(const string& hex, size_t byteCount)
{
	if (hex.size() != byteCount * 2)
		return hex;

	// Parse big-endian hex into an integer, then reinterpret as float/double
	uint64_t bits = 0;
	for (size_t i = 0; i < hex.size(); i++)
	{
		char c = hex[i];
		uint64_t nibble;
		if (c >= '0' && c <= '9')      nibble = c - '0';
		else if (c >= 'a' && c <= 'f') nibble = c - 'a' + 10;
		else if (c >= 'A' && c <= 'F') nibble = c - 'A' + 10;
		else return hex;
		bits = (bits << 4) | nibble;
	}

	if (byteCount == 4)
	{
		union { uint32_t i; float f; } u;
		u.i = (uint32_t)bits;
		if (std::isnan(u.f) || std::isinf(u.f))
			return "(float)" + hex;
		return to_string(u.f);
	}
	else if (byteCount == 8)
	{
		union { uint64_t i; double d; } u;
		u.i = bits;
		if (std::isnan(u.d) || std::isinf(u.d))
			return "(double)" + hex;
		return to_string(u.d);
	}
	return hex;
}


// ===== Reader implementation (non-templated) =====

DemangleGNU3Reader::DemangleGNU3Reader(const string& data): m_data(data), m_offset(0)
{}


void DemangleGNU3Reader::Reset(const string& data)
{
	m_data = data;
	m_offset = 0;
}


string DemangleGNU3Reader::PeekString(size_t count)
{
	if (count > Length())
		return "\0";
	return m_data.substr(m_offset, count);
}



#ifdef GNUDEMANGLE_DEBUG
string DemangleGNU3Reader::GetRaw()
{
	return m_data.substr(m_offset);
}
#endif



string DemangleGNU3Reader::ReadString(size_t count)
{
	if (count > Length())
		throw DemangleException();

	const string out = m_data.substr(m_offset, count);
	m_offset += count;
	return out;
}




// ===== DemangleGNU3 implementation =====

DemangleGNU3::DemangleGNU3(Architecture* arch, const string& mangledName) :
	m_reader(mangledName),
	m_arch(arch),
	m_isParameter(false),
	m_shouldDeleteReader(true),
	m_topLevel(true),
	m_isOperatorOverload(false),
	m_permitForwardTemplateRefs(false)
{
	MyLogDebug("%s : %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
}


void DemangleGNU3::Reset(Architecture* arch, const string& mangledName)
{
	m_reader.Reset(mangledName);
	m_arch = arch;
	m_varName.clear();
	m_substitute.clear();
	m_templateSubstitute.clear();
	m_functionSubstitute.clear();
	m_lastName.clear();
	m_nameType = {};
	m_localType = {};
	m_hasReturnType = {};
	m_isParameter = false;
	m_shouldDeleteReader = true;
	m_topLevel = true;
	m_isOperatorOverload = false;
	m_permitForwardTemplateRefs = false;
	m_pendingForwardRefs.clear();
	m_inLocalName = false;
}


DemangledTypeNode DemangleGNU3::CreateUnknownType(const QualifiedName& s)
{
	return DemangledTypeNode::NamedType(UnknownNamedTypeClass, s);
}


DemangledTypeNode DemangleGNU3::CreateUnknownType(const string& s)
{
	return DemangledTypeNode::NamedType(UnknownNamedTypeClass, _STD_VECTOR<_STD_STRING>{s});
}


void DemangleGNU3::ExtendTypeName(DemangledTypeNode& type, const string& extend)
{
	if (type.NameStringSize() + extend.size() > MAX_DEMANGLE_LENGTH)
		throw DemangleException("Detected adversarial mangled string");

	{
		auto& qn = type.GetMutableTypeName();
		if (qn.size() > 0)
			qn.back() += extend;
		else
			qn.push_back(extend);
	}
}


void DemangleGNU3::PushTemplateType(const DemangledTypeNode& type)
{
	m_templateSubstitute.push_back(type);
}


#ifdef GNUDEMANGLE_DEBUG
const DemangledTypeNode& DemangleGNU3::GetTemplateType(size_t ref)
{
	if (ref >= m_templateSubstitute.size())
		throw DemangleException();
	return m_templateSubstitute[ref];
}
#endif


void DemangleGNU3::PushType(const DemangledTypeNode& type)
{
	m_substitute.push_back(type);
}


const DemangledTypeNode& DemangleGNU3::GetType(size_t ref)
{
	if (ref >= m_substitute.size())
		throw DemangleException();
	return m_substitute[ref];
}


#ifdef GNUDEMANGLE_DEBUG
void DemangleGNU3::PrintTables()
{
	LogDebug("Substitution Table\n");
	for (int i = 0; (size_t)i < m_substitute.size(); i++)
	{
		LogDebug("[%d] %s\n", i-1, GetType(i).GetString().c_str());
	}

	LogDebug("Template Table\n");
	for (int i = 0; (size_t)i < m_templateSubstitute.size(); i++)
	{
		LogDebug("[%d] %s\n", i-1, GetTemplateType(i).GetString().c_str());
	}
}
#endif


void DemangleGNU3::DemangleCVQualifiers(bool& cnst, bool& vltl, bool& rstrct)
{
	cnst = false; vltl = false; rstrct = false;
	//[<cv-qualifier>]
	while (1)
	{
		switch (m_reader.Peek())
		{
		case 'r': rstrct = true; break;
		case 'V': vltl = true; break;
		case 'K': cnst = true; break;
		default: return;
		}
		m_reader.Consume(1);
	}
}


string DemangleGNU3::DemangleSourceName()
{
	indent();
	MyLogDebug("%s : %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
	m_lastName = m_reader.ReadString(DemangleNumber());
	dedent();
	return m_lastName;
}


DemangledTypeNode DemangleGNU3::DemangleFunction(bool cnst, bool vltl)
{
	indent();
	MyLogDebug("%s : %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
	bool old_isparam;
	if (m_reader.Peek() == 'Y')
	{
		// TODO: This function is external, should we do anything with that info?
		m_reader.Consume();
	}

	DemangledTypeNode retType = DemangleType();

	ParamList params;
	old_isparam = m_isParameter;
	m_isParameter = true;
	m_functionSubstitute.push_back({});
	[[maybe_unused]] int i = 0;
	while (m_reader.Peek() != 'E')
	{
		DemangledTypeNode param = DemangleType();
		if (param.GetClass() == VoidTypeClass)
			continue;
		MyLogDebug("Var_%d - %s\n", i++, param.GetString().c_str());
		m_functionSubstitute.back().push_back(param);
		params.push_back({"", std::make_shared<DemangledTypeNode>(std::move(param))});
	}
	m_reader.Consume();
	m_functionSubstitute.pop_back();
	m_isParameter = old_isparam;
	DemangledTypeNode newType = DemangledTypeNode::FunctionType(std::move(retType), nullptr, std::move(params));
	PushType(newType);

	newType.SetConst(cnst);
	newType.SetVolatile(vltl);

	if (cnst || vltl)
		PushType(newType);
	MyLogDebug("After %s : %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
	dedent();
	return newType;
}


string DemangleGNU3::ForwardRefPlaceholder(size_t index)
{
	return "\x01FWDREF:" + to_string(index) + "\x01";
}


void DemangleGNU3::ResolveForwardTemplateRefs(DemangledTypeNode& type, const vector<string>& args)
{
	if (m_pendingForwardRefs.empty())
		return;
	auto& segs = type.GetMutableTypeName();
	bool resolved = false;
	for (const auto& fr : m_pendingForwardRefs)
	{
		string placeholder = ForwardRefPlaceholder(fr.index);
		string replacement = (fr.index < args.size()) ? args[fr.index] : "auto";
		for (auto& seg : segs)
		{
			size_t pos;
			while ((pos = seg.find(placeholder)) != string::npos)
			{
				seg.replace(pos, placeholder.size(), replacement);
				resolved = true;
			}
		}
	}
	// Only clear the pending list when we actually resolved something.  Inner
	// nested-name 'I' handlers (e.g. template args of types nested inside the
	// cv-operator result type) may call here with a type that does not contain
	// the placeholder; we must not discard the pending entry in that case so
	// that the correct outer 'I' handler can still resolve it.
	if (resolved)
		m_pendingForwardRefs.clear();
}


DemangledTypeNode DemangleGNU3::DemangleTemplateSubstitution()
{
	indent();
	MyLogDebug("%s : %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
	size_t number = 0;
	char elm = m_reader.Peek();
	if (elm == '_')
	{
		number = 0;
	}
	else if (isdigit(elm))
	{
		size_t n = 0;
		while (isdigit(m_reader.Peek()))
			n = n * 10 + (m_reader.Read() - '0');
		number = n + 1;
	}
	else if (isupper(elm))
	{
		m_reader.Consume();
		number = elm - 'A' + 11;
	}
	else
	{
		throw DemangleException();
	}

	if (m_reader.Read() != '_')
	{
		throw DemangleException();
	}
	dedent();

	if (number < m_templateSubstitute.size())
		return m_templateSubstitute[number];

	// If forward template references are permitted (e.g. inside a cv conversion
	// operator type), return a placeholder that will be resolved once the outer
	// template args are known.
	if (m_permitForwardTemplateRefs)
	{
		m_pendingForwardRefs.push_back({number});
		return CreateUnknownType(ForwardRefPlaceholder(number));
	}

	throw DemangleException();
}


DemangledTypeNode DemangleGNU3::DemangleType()
{
	indent();
	MyLogDebug("%s : %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
	DemangledTypeNode type;
	bool cnst = false, vltl = false, rstrct = false;
	bool substitute = false;
	QualifiedName name;

	DemangleCVQualifiers(cnst, vltl, rstrct);

	if (cnst || vltl || rstrct)
	{
		type = DemangleType();
		if (cnst)
			type.SetConst(true);
		if (vltl)
			type.SetVolatile(true);
		if (rstrct)
			type.SetPointerSuffix({RestrictSuffix});
		PushType(type);
		return type;
	}

	switch(m_reader.Read())
	{
	case 'S':
	{
		if (isdigit(m_reader.Peek()) || m_reader.Peek() == '_' || isupper(m_reader.Peek()))
		{
			type = DemangleSubstitution();
			if (m_reader.Peek() == 'I')
			{
				m_reader.Consume();
				vector<string> args;
				DemangleTemplateArgs(args);
				ExtendTypeName(type, GetTemplateString(args));
				type.SetHasTemplateArguments(true);
				substitute = true;
			}
		}
		else
		{
			if (m_reader.Peek() == 't')
			{
				m_reader.Consume(1);
				type = DemangleUnqualifiedName();
				auto qn = type.GetTypeName();
				qn.insert(qn.begin(), "std");
				type.SetTypeName(std::move(qn));
				substitute = true;
			}
			else
			{
				type = DemangleSubstitution();
			}
			if (m_reader.Peek() == 'I')
			{
				m_reader.Consume();
				if (substitute)
					PushType(type);
				vector<string> args;
				DemangleTemplateArgs(args);
				ExtendTypeName(type, GetTemplateString(args));
				type.SetHasTemplateArguments(true);
				substitute = true;
			}
		}
		break;
	}
	case 'T':
	{
		/*  <class-enum-type> ::= <name>     # non-dependent type name, dependent type name, or dependent typename-specifier
		                      ::= Ts <name>  # dependent elaborated type specifier using 'struct' or 'class'
		                      ::= Tu <name>  # dependent elaborated type specifier using 'union'
		                      ::= Te <name>  # dependent elaborated type specifier using 'enum'
		*/
		if (m_reader.Peek() == 's')
		{
			m_reader.Consume();
			type = DemangledTypeNode::NamedType(StructNamedTypeClass, _STD_VECTOR<_STD_STRING>{DemangleSourceName()});
			break;
		}
		else if (m_reader.Peek() == 'u')
		{
			m_reader.Consume();
			type = DemangledTypeNode::NamedType(UnionNamedTypeClass, _STD_VECTOR<_STD_STRING>{DemangleSourceName()});
			break;
		}
		else if (m_reader.Peek() == 'e')
		{
			m_reader.Consume();
			type = DemangledTypeNode::NamedType(EnumNamedTypeClass, QualifiedName({DemangleSourceName()}),
				m_arch->GetDefaultIntegerSize(), m_arch->GetDefaultIntegerSize());
			break;
		}

		//Template Substitution
		type = DemangleTemplateSubstitution();
		// In forward-ref mode (cv conversion operator type parsing), do not consume
		// trailing I<args>E — it belongs to the enclosing nested-name and will be
		// processed by DemangleNestedName's 'I' case, which resolves forward refs.
		substitute = !m_permitForwardTemplateRefs;
		if (!m_permitForwardTemplateRefs && m_reader.Peek() == 'I')
		{
			m_reader.Consume();
			if (substitute)
				PushType(type);
			vector<string> args;
			DemangleTemplateArgs(args);
			ExtendTypeName(type, GetTemplateString(args));
			type.SetHasTemplateArguments(true);
		}
		break;
	}
	case 'P':
	{
		DemangledTypeNode child = DemangleType();
		type = DemangledTypeNode::PointerType(m_arch, std::move(child), cnst, vltl, PointerReferenceType);
		substitute = true;
		break;
	}
	case 'R':
	{
		DemangledTypeNode child = DemangleType();
		type = DemangledTypeNode::PointerType(m_arch, std::move(child), cnst, vltl, ReferenceReferenceType);
		substitute = true;
		break;
	}
	case 'O':
	{
		DemangledTypeNode child = DemangleType();
		type = DemangledTypeNode::PointerType(m_arch, std::move(child), cnst, vltl, RValueReferenceType);
		substitute = true;
		break;
	}
	case 'C': //TODO:complex
	case 'G': //TODO:imaginary
		throw DemangleException();
	case 'U':
	{
		// Vendor-extended type: U <source-name> [<template-args>] <type>
		// Commonly used for Objective-C block pointers:
		//   U13block_pointer <function-type>  ->  "void (params...) block_pointer"
		string extName = DemangleSourceName();
		if (m_reader.Peek() == 'I')
		{
			m_reader.Consume();
			vector<string> targs;
			DemangleTemplateArgs(targs);
			if (!targs.empty())
				extName += GetTemplateString(targs);
		}
		DemangledTypeNode inner = DemangleType();
		type = CreateUnknownType(inner.GetString() + " " + extName);
		substitute = true;
		break;
	}
	case 'u':
	{
		// Vendor extended type: u <source-name> [<template-args>]
		// e.g. u14__remove_cvref, u20__remove_reference_t
		string extName = DemangleSourceName();
		if (m_reader.Peek() == 'I')
		{
			m_reader.Consume();
			vector<string> targs;
			DemangleTemplateArgs(targs);
			if (!targs.empty())
				extName += GetTemplateString(targs);
		}
		type = CreateUnknownType(extName);
		substitute = true;
		break;
	}
	case 'v': type = DemangledTypeNode::VoidType(); break;
	case 'w': type = DemangledTypeNode::IntegerType(4, false, "wchar_t"); break; //TODO: verify
	case 'b': type = DemangledTypeNode::BoolType(); break;
	case 'c': type = DemangledTypeNode::IntegerType(1, true, "char"); break;
	case 'a': type = DemangledTypeNode::IntegerType(1, true, "signed char"); break;
	case 'h': type = DemangledTypeNode::IntegerType(1, false); break;
	case 's': type = DemangledTypeNode::IntegerType(2, true); break;
	case 't': type = DemangledTypeNode::IntegerType(2, false); break;
	case 'i': type = DemangledTypeNode::IntegerType(4, true); break;
	case 'j': type = DemangledTypeNode::IntegerType(4, false); break;
	case 'l': type = DemangledTypeNode::IntegerType(m_arch->GetAddressSize(), true); break; //long
	case 'm': type = DemangledTypeNode::IntegerType(m_arch->GetAddressSize(), false); break; //ulong
	case 'x': type = DemangledTypeNode::IntegerType(8, true); break;
	case 'y': type = DemangledTypeNode::IntegerType(8, false); break;
	case 'n': type = DemangledTypeNode::IntegerType(16, true); break;
	case 'o': type = DemangledTypeNode::IntegerType(16, false); break;
	case 'f': type = DemangledTypeNode::FloatType(4); break;
	case 'd': type = DemangledTypeNode::FloatType(8); break;
	case 'e': type = DemangledTypeNode::FloatType(10); break;
	case 'g': type = DemangledTypeNode::FloatType(16); break;
	case 'z': type = DemangledTypeNode::VarArgsType(); break;
	case 'M': // TODO: Make into pointer to function member
	{
		DemangledTypeNode memberName = DemangleType();
		DemangledTypeNode member = DemangleType();
		string fullName = member.GetStringBeforeName() + "(" + memberName.GetString() + "::*)" + member.GetStringAfterName();
		//member.SetScope(NonStaticScope);
		//DemangledTypeNode ptr = DemangledTypeNode::PointerType(m_arch, member, cnst, vltl);
		//QualifiedName qn({memberName.GetString(), "*"});
		type = CreateUnknownType(fullName);
		substitute = true;
		break;
	}
	case 'F': type = DemangleFunction(cnst, vltl); break;
	case 'D':
		switch (m_reader.Read())
		{
		case 'd': type = DemangledTypeNode::FloatType(8, "decimal64"); break;
		case 'e': type = DemangledTypeNode::FloatType(16, "decimal128"); break;
		case 'f': type = DemangledTypeNode::FloatType(4, "decimal32"); break;
		case 'h': type = DemangledTypeNode::FloatType(2); break;
		case 'i': type = DemangledTypeNode::IntegerType(4, true, "char32_t"); break;
		case 's': type = DemangledTypeNode::IntegerType(2, true, "char16_t"); break;
		case 'a': type = CreateUnknownType("auto"); break; //auto type
		case 'c': type = CreateUnknownType("decltype(auto)"); break; //decltype(auto)
		case 'n':
		{
			static const QualifiedName stdNullptrTName(vector<string>{"std", "nullptr_t"});
			type = CreateUnknownType(stdNullptrTName);
			break;
		}
		case 'p':
		{
			DemangledTypeNode inner = DemangleType();
			type = CreateUnknownType(inner.GetString() + "...");
			break;
		}
		case 't':
		case 'T':
			type = CreateUnknownType("decltype(" + DemangleExpression() + ")");
			if (m_reader.Read() != 'E')
				throw DemangleException();
			break;
		case 'v':
		{
			// vector of size
			uint64_t size = DemangleNumber();
			if (m_reader.Read() != '_')
				throw DemangleException();
			DemangledTypeNode child = DemangleType();
			type = DemangledTypeNode::ArrayType(std::move(child), size);
			break;
		}
		default:
			MyLogDebug("Unsupported type: %s:'%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
			throw DemangleException();
		}
		break;
	case 'N':
		type = DemangleNestedName();
		substitute = true;
		break;
	case 'A':
		//  <array-type> ::= A <positive dimension number> _ <element type>
		//               ::= A [<dimension expression>] _ <element type>
		if (isdigit(m_reader.Peek()))
		{
			//<positive dimension number> _ <element type>
			uint64_t size = DemangleNumber();
			if (m_reader.Read() != '_')
				throw DemangleException();
			DemangledTypeNode child = DemangleType();
			type = DemangledTypeNode::ArrayType(std::move(child), size);
		}
		else
		{
			//[<dimension expression>] _ <element type>
			//Since our type system doesn't support expressions as dimensions
			//we instead demangle this as just a string.
			string dimension = "[]";
			if (m_reader.Peek() != '_')
			{
				dimension = "[" + DemangleExpression() + "]";
			}
			if (m_reader.Read() != '_')
				throw DemangleException();

			const string typeString = DemangleType().GetString() + dimension;
			type = CreateUnknownType(typeString);
		}
		substitute = true;
		break;
	default:
	{
		m_reader.UnRead();

		type = DemangleName();
		auto nameList = type.GetTypeName();
		if (nameList.size() < 1)
			throw DemangleException();
		m_lastName = nameList.back();
		substitute = true;

		if (m_reader.Peek() == 'I')
		{
			substitute = false;
			m_reader.Consume();
			PushType(type);
			vector<string> args;
			DemangleTemplateArgs(args);
			ExtendTypeName(type, GetTemplateString(args));
			type.SetHasTemplateArguments(true);
			PushType(type);
		}
	}
	}

	if (substitute)
		PushType(type);

	dedent();
	return type;
}


DemangledTypeNode DemangleGNU3::DemangleSubstitution()
{
	static const QualifiedName stdAllocatorName(vector<string>{"std", "allocator"});
	static const QualifiedName stdBasicStringName(vector<string>{"std", "basic_string"});
	static const QualifiedName stdIostreamName(vector<string>{"std", "iostream"});
	static const QualifiedName stdIstreamName(vector<string>{"std", "istream"});
	static const QualifiedName stdOstreamName(vector<string>{"std", "ostream"});
	static const QualifiedName stdStringName(vector<string>{"std", "string"});
	static const QualifiedName stdName(vector<string>{"std"});

	indent()
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	char elm;
	elm = m_reader.Read();
	QualifiedName name;
	size_t number = 0;
	switch (elm)
	{
	case 'a': name = stdAllocatorName; break;
	case 'b': name = stdBasicStringName; break;
	case 'd': name = stdIostreamName; break;
	case 'i': name = stdIstreamName; break;
	case 'o': name = stdOstreamName; break;
	case 's': name = stdStringName; break;
	case 't': name = stdName; break;
	default:
		if (elm == '_')
		{
			m_reader.UnRead(1);
			number = 0;
		}
		else if (isdigit(elm) || isupper(elm))
		{
			// Seq-id is encoded in base 36 using 0-9 A-Z.
			// The actual substitution index = base36_value + 1.
			// This handles both single-char (S0_ ... SZ_) and
			// multi-char (S10_, S11_, ...) seq-ids.
			size_t base36 = isdigit(elm) ? (size_t)(elm - '0') : (size_t)(elm - 'A' + 10);
			while (m_reader.Peek() != '_')
			{
				char c = m_reader.Read();
				if (isdigit(c))
					base36 = base36 * 36 + (size_t)(c - '0');
				else if (isupper(c))
					base36 = base36 * 36 + (size_t)(c - 'A' + 10);
				else
					throw DemangleException();
			}
			number = base36 + 1;
		}
		else
		{
			// PrintTables();
			throw DemangleException();
		}

		if (m_reader.Read() != '_')
		{
			throw DemangleException();
		}

		dedent();
		const DemangledTypeNode& resolved = GetType(number);
		const auto& segs = resolved.GetTypeName();
		if (!segs.empty())
			m_lastName = segs.back();
		return resolved;
	}
	m_lastName = name.back();
	dedent();
	return CreateUnknownType(name);
}

string DemangleGNU3::DemangleNumberAsString()
{
	bool negativeFactor = false;
	if (m_reader.Peek() == 'n')
	{
		negativeFactor = true;
		m_reader.Consume();
	}

	string number;
	while (isdigit(m_reader.Peek()))
	{
		number += m_reader.Read();
	}
	if (negativeFactor)
		return "-" + number;
	return number;
}

// number ::= [n] <decimal>
int64_t DemangleGNU3::DemangleNumber()
{
	bool negative = false;
	if (m_reader.Peek() == 'n')
	{
		negative = true;
		m_reader.Consume();
	}

	if (!isdigit(m_reader.Peek()))
		throw DemangleException();

	int64_t result = 0;
	do
	{
		result = result * 10 + (m_reader.Read() - '0');
	} while (isdigit(m_reader.Peek()));
	return negative ? -result : result;
}


string DemangleGNU3::DemanglePrimaryExpression()
{
	indent();
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	char elm1 = '\0';
	string out;
	QualifiedName tmpList;
	bool oldTopLevel;
	//expr-primary
	if (m_reader.PeekString(2) == "_Z")
	{
		m_reader.Consume(2);
		// The embedded _Z... is an independent mangled name with its own
		// template scope.  Save and clear the template substitution table
		// so inner T_ / T0_ etc. resolve within this symbol, not the outer
		// one.  Set m_topLevel = true so template args get pushed properly.
		auto savedTemplateSubstitute = m_templateSubstitute;
		m_templateSubstitute.clear();
		oldTopLevel = m_topLevel;
		m_topLevel = true;
		DemangledTypeNode t = DemangleSymbol(tmpList);
		m_topLevel = oldTopLevel;
		m_templateSubstitute = std::move(savedTemplateSubstitute);
		out += t.GetTypeAndName(tmpList);
		dedent()
		return out;
	}
	// LZ<encoding>E: function address template arg (GCC/Clang, without leading underscore)
	if (m_reader.Peek() == 'Z')
	{
		m_reader.Consume(); // 'Z'
		auto savedTemplateSubstitute2 = m_templateSubstitute;
		m_templateSubstitute.clear();
		oldTopLevel = m_topLevel;
		m_topLevel = true;
		DemangledTypeNode t2 = DemangleSymbol(tmpList);
		m_topLevel = oldTopLevel;
		m_templateSubstitute = std::move(savedTemplateSubstitute2);
		out += t2.GetTypeAndName(tmpList);
		dedent();
		return out;
	}
	switch (m_reader.Read())
	{
	case 'b':
		elm1 = m_reader.Read();
		if (elm1 == '0')
			out += "false";
		else if (elm1 == '1')
			out += "true";
		else
			throw DemangleException();
		break;
	case 'd': //double (16 hex chars = 8 bytes)
		out += DecodeHexFloat(m_reader.ReadString(16), 8);
		break;
	case 'e': //long double (20 hex chars = 10 bytes, platform-dependent layout)
		out += "(long double)" + m_reader.ReadString(20);
		break;
	case 'f': //float (8 hex chars = 4 bytes)
		out += DecodeHexFloat(m_reader.ReadString(8), 4);
		break;
	case 'g': //float_128 (32 hex chars = 16 bytes)
		out += "(__float128)" + m_reader.ReadString(32);
		break;
	case 'l': out = DemangleNumberAsString() + "l"; break;  //long
	case 'x': out = DemangleNumberAsString() + "ll"; break;  //long long
	case 's': out = "(short)" + DemangleNumberAsString(); break; //short
	case 'n': out = "(__int128)" + DemangleNumberAsString(); break;  //__int128
	case 'i': out = DemangleNumberAsString(); break;       // int
	case 'm': out = DemangleNumberAsString() + "ul"; break;  //unsigned long
	case 't': out = "(unsigned short)" + DemangleNumberAsString(); break; //unsigned short
	case 'y': out = DemangleNumberAsString() + "ull"; break;  //unsigned long long
	case 'j': out = DemangleNumberAsString() + "u"; break; // unsigned int
		break;
	default:
	{
		m_reader.UnRead(1);
		const string castType = DemangleTypeString();
		const string castVal = DemangleNumberAsString();
		out = "(" + castType + ")" + castVal;
		break;
	}
	}
	if (m_reader.Read() != 'E')
		throw DemangleException();

	dedent();
	return out;
}


string DemangleGNU3::DemangleUnarySuffixExpression(const string& op)
{
	return "(" + DemangleExpression() + ")" + op;
}


string DemangleGNU3::DemangleUnaryPrefixExpression(const string& op)
{
	return op + "(" + DemangleExpression() + ")";
}


string DemangleGNU3::DemangleBinaryExpression(const string& op)
{
	indent();
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	const string lhs = "(" + DemangleExpression() + ")";
	const string rhs = "(" + DemangleExpression() + ")";
	dedent();
	return lhs + " " + op + " " + rhs;
}


string DemangleGNU3::DemangleUnaryPrefixType(const string& op)
{
	return op + "(" + DemangleTypeString() + ")";
}


string DemangleGNU3::DemangleTypeString()
{
	return DemangleType().GetString();
}


string DemangleGNU3::DemangleExpressionList()
{
	indent();
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	string expr;
	bool first = true;
	m_functionSubstitute.push_back({});
	while (m_reader.Peek() != 'E')
	{
		if (!first)
			expr += ", ";
		const string e = DemangleExpression();
		expr += e;
		m_functionSubstitute.back().push_back(CreateUnknownType(e));
		first = false;
	}
	m_functionSubstitute.pop_back();
	m_reader.Consume();
	dedent();
	return expr;
}


DemangledTypeNode DemangleGNU3::DemangleUnqualifiedName()
{
	indent()
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());

	DemangledTypeNode outType;
	char elm1 = m_reader.Read();
	char elm2 = m_reader.Read();
	switch (hash(elm1, elm2))
	{
	case hash('n','t'): // !
	case hash('n','g'): // - (unary)
	case hash('p','s'): // + (unary)
	case hash('a','d'): // & (unary)
	case hash('d','e'): // * (unary)
	case hash('i','x'): // []
	case hash('p','p'): // ++ (postfix in <expression> context)
	case hash('m','m'): // -- (postfix in <expression> context)
	case hash('l','s'): // <<
	case hash('r','s'): // >>
	case hash('a','S'): // =
	case hash('e','q'): // ==
	case hash('n','e'): // !=
	case hash('p','t'): // ->
	case hash('d','t'): // .
	case hash('m','l'): // *
	case hash('m','i'): // -
	case hash('p','l'): // +
	case hash('a','n'): // &
	case hash('p','m'): // ->*
	case hash('d','v'): // /
	case hash('r','m'): // %
	case hash('l','t'): // <
	case hash('l','e'): // <=
	case hash('g','t'): // >
	case hash('g','e'): // >=
	case hash('c','m'): // ,
	case hash('c','l'): // ()
	case hash('c','o'): // ~
	case hash('e','o'): // ^
	case hash('o','r'): // |
	case hash('a','a'): // &&
	case hash('o','o'): // ||
	case hash('m','L'): // *=
	case hash('p','L'): // +=
	case hash('m','I'): // -=
	case hash('d','V'): // /=
	case hash('r','M'): // %=
	case hash('r','S'): // >>=
	case hash('l','S'): // <<=
	case hash('a','N'): // &=
	case hash('o','R'): // |=
	case hash('e','O'): // ^=
	case hash('s','s'): // <=>
		outType = CreateUnknownType("operator" + GetOperator(elm1, elm2));
		outType.SetNameType(GetNameType(elm1, elm2));
		break;
	case hash('t','i'):
	case hash('t','e'):
	case hash('s','t'):
	case hash('s','z'):
	case hash('a','t'):
	case hash('a','z'):
	case hash('n','x'):
	case hash('s','Z'):
	case hash('s','P'):
	case hash('s','p'):
	case hash('d','l'): // delete
	case hash('d','a'): // delete[]
	case hash('n','w'): // new
	case hash('n','a'): // new []
		outType = CreateUnknownType("operator " + GetOperator(elm1, elm2));
		outType.SetNameType(GetNameType(elm1, elm2));
		break;
	case hash('v','0'):
	case hash('v','1'):
	case hash('v','2'):
	case hash('v','3'):
	case hash('v','4'):
	case hash('v','5'):
	case hash('v','6'):
	case hash('v','7'):
	case hash('v','8'):
	case hash('v','9'):
		//TODO: Unsupported vendor extended types
		throw DemangleException();
	case hash('C','1'): //Construtor
	case hash('C','2'):
	case hash('C','3'):
	case hash('C','4'):
	case hash('C','5'):
		outType = CreateUnknownType(m_lastName);
		outType.SetNameType(ConstructorNameType);
		break;
	case hash('C','I'): // Inheriting constructor: CI1 <type> or CI2 <type>
	{
		char kind = m_reader.Read(); // '1' or '2'
		if (kind != '1' && kind != '2')
			throw DemangleException();
		// Save m_lastName: parsing the inherited-class type will overwrite it
		string savedLastName = m_lastName;
		DemangleType();
		m_lastName = savedLastName;
		outType = CreateUnknownType(m_lastName);
		outType.SetNameType(ConstructorNameType);
		break;
	}
	case hash('D','0'): //Destructor
	case hash('D','1'):
	case hash('D','2'):
	case hash('D','3'):
	case hash('D','4'):
	case hash('D','5'):
		outType = CreateUnknownType("~" + m_lastName);
		outType.SetNameType(DestructorNameType);
		break;
	case hash('D','t'):
	case hash('D','T'):
		outType = CreateUnknownType(DemangleExpression());
		// if (m_reader.Read() != 'E')
		// 	throw DemangleException();
		break;
	case hash('U','l'): //Lambda
	{
		string name;
		name = "'lambda";
		vector<DemangledTypeNode> lambdaParams;
		// Generic lambdas encode 'auto' params as T_, T0_, T1_... which reference
		// the lambda's own operator() template params, not any outer template scope.
		// Save and replace the template substitution table with 'auto' placeholders.
		auto savedTemplateSubstitute = m_templateSubstitute;
		m_templateSubstitute.clear();
		for (int autoIdx = 0; autoIdx < 16; autoIdx++)
			m_templateSubstitute.push_back(CreateUnknownType("auto"));
		do
		{
			DemangledTypeNode param = DemangleType();
			if (param.GetClass() == VoidTypeClass)
				break;
			lambdaParams.push_back(std::move(param));
		}while (m_reader.Peek() != 'E');
		m_reader.Consume();
		m_templateSubstitute = std::move(savedTemplateSubstitute);

		if (isdigit(m_reader.Peek()))
		{
			name += DemangleNumberAsString();
		}
		if (m_reader.Read() != '_')
			throw DemangleException();

		name += "'(";
		for (size_t i = 0; i < lambdaParams.size(); i++)
		{
			if (i != 0)
				name += ", ";
			name += lambdaParams[i].GetString();
		}
		name += ")";
		m_lastName = name;
		outType = CreateUnknownType(name);
		break;
	}
	case hash('U','t'):
	{
		string name;
		name = "'unnamed";

		if (isdigit(m_reader.Peek()))
		{
			name += DemangleNumberAsString();
		}
		name += "\'";

		if (m_reader.Read() != '_')
			throw DemangleException();

		m_lastName = name;
		outType = CreateUnknownType(name);
		break;
	}
	case hash('c','v'): //type (expression)
	{
		// The conversion operator type may reference template params (T_, T0_, ...)
		// that aren't yet in m_templateSubstitute (they're defined by a following
		// I<args>E in the enclosing nested name).  Set m_permitForwardTemplateRefs so
		// that DemangleTemplateSubstitution() returns a placeholder instead of
		// throwing, and don't consume trailing I<args>E in the T case of DemangleType.
		// The outer DemangleNestedName case 'I' will parse those args and call
		// ResolveForwardTemplateRefs() to patch the placeholders.
		bool savedPermit = m_permitForwardTemplateRefs;
		m_pendingForwardRefs.clear();
		m_permitForwardTemplateRefs = true;
		DemangledTypeNode cvType = DemangleType();
		m_permitForwardTemplateRefs = savedPermit;
		outType = CreateUnknownType("operator " + cvType.GetString());
		break;
	}
	default:
		m_reader.UnRead(2);
		if (isdigit(m_reader.Peek()) || m_reader.Read() == 'L')
		{
			string name = DemangleSourceName();
			if (name.size() > 11 && name.substr(0, 11) == "_GLOBAL__N_")
				name = "(anonymous namespace)";
			m_lastName = name;
			outType = CreateUnknownType(name);
		}
		else
		{
			throw DemangleException();
		}
	}
	// Consume ABI tags: B <source-name>  =>  [abi:tagname]
	// Applies to source names, operator names, and unnamed types.
	while (m_reader.Peek() == 'B')
	{
		m_reader.Consume();
		string tag = "[abi:" + DemangleSourceName() + "]";
		auto qn = outType.GetTypeName();
		if (!qn.empty())
			qn.back() += tag;
		outType.SetTypeName(std::move(qn));
		m_lastName = qn.empty() ? tag : qn.back();
	}
	dedent();
	return outType;
}


QualifiedName DemangleGNU3::DemangleBaseUnresolvedName()
{
	// <base-unresolved-name> ::= <simple-id>                                # unresolved name
	//                        ::= on <operator-name>                         # unresolved operator-function-id
	//                        ::= on <operator-name> <template-args>         # unresolved operator template-id
	//                        ::= dn <destructor-name>                       # destructor or pseudo-destructor;
	//                                                                       # e.g. ~X or ~X<N-1>

	indent()
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	QualifiedName out;
	if (m_reader.Length() > 1)
	{
		const string str = m_reader.PeekString(2);
		if (str == "on")
		{
			m_reader.Consume(); m_reader.Consume(); // skip 'o','n' prefix
			char op1 = m_reader.Read();
			char op2 = m_reader.Read();
			out.push_back(GetOperator(op1, op2));
			if (m_reader.Peek() == 'I')
			{
				m_reader.Consume();
				vector<string> args;
				DemangleTemplateArgs(args);
				out.back() += GetTemplateString(args);
				PushType(CreateUnknownType(out));
			}
		}
		else if (str == "dn")
		{
			string name = DemangleUnresolvedType().GetString();
			if (name.empty())
				out.push_back("~" + DemangleSourceName());
			else
				out.push_back("~" + name);
		}
		else
		{
			// <simple-id>
			out.push_back(DemangleSourceName());
			if (m_reader.Peek() == 'I')
			{
				m_reader.Consume();
				vector<string> args;
				DemangleTemplateArgs(args);
				out.back() += GetTemplateString(args);
			}
		}
	}
	dedent();
	return out;
}


DemangledTypeNode DemangleGNU3::DemangleUnresolvedType()
{
	indent();
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	//<unresolved-type> ::= <template-param> [ <template-args> ]            # T:: or T<X,Y>::
	//                  ::= <decltype>                                      # decltype(p)::
	//                  ::= <substitution>
	DemangledTypeNode type;
	if (m_reader.Peek() == 'T')
	{
		m_reader.Consume();
		type = DemangleTemplateSubstitution();
		if (m_reader.Peek() == 'I')
		{
			PushType(type);
			m_reader.Consume();
			vector<string> args;
			DemangleTemplateArgs(args);
			ExtendTypeName(type, GetTemplateString(args));
			type.SetHasTemplateArguments(true);
			PushType(type);
		}
		else
		{
			// Template param used as scope qualifier (e.g. sr T_ name) is a substitution
			// candidate: the compiler adds it to the main sub table so subsequent
			// occurrences can use Sn_ instead of T_.
			PushType(type);
		}
	}
	else if (m_reader.Length() > 2 && (m_reader.PeekString(2) == "Dt" || m_reader.PeekString(2) == "DT"))
	{
		m_reader.Consume(); // 'D'
		m_reader.Consume(); // 't' or 'T'
		const string name = "decltype(" + DemangleExpression() + ")";
		if (m_reader.Read() != 'E')
			throw DemangleException();
		type = CreateUnknownType(name);
	}
	else if (m_reader.Peek() == 'S')
	{
		m_reader.Consume();
		type = DemangleSubstitution();
	}
	else
	{
		throw DemangleException();
	}
	dedent();
	return type;
}


string DemangleGNU3::DemangleExpression()
{
	MyLogDebug("%s: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	/*
	<expression> ::= <unary operator-name> <expression>
	               ::= <binary operator-name> <expression> <expression>
	               ::= <ternary operator-name> <expression> <expression> <expression>
	               ::= pp_ <expression>                                     # prefix ++
	               ::= mm_ <expression>                                     # prefix --
	               ::= cl <expression>+ E                                   # expression (expr-list), call
	               ::= cv <type> <expression>                               # type (expression), conversion with one argument
	               ::= cv <type> _ <expression>* E                          # type (expr-list), conversion with other than one argument
	               ::= tl <type> <expression>* E                            # type {expr-list}, conversion with braced-init-list argument
	               ::= il <expression> E                                    # {expr-list}, braced-init-list in any other context
	               ::= [gs] nw <expression>* _ <type> E                     # new (expr-list) type
	               ::= [gs] nw <expression>* _ <type> <initializer>         # new (expr-list) type (init)
	               ::= [gs] na <expression>* _ <type> E                     # new[] (expr-list) type
	               ::= [gs] na <expression>* _ <type> <initializer>         # new[] (expr-list) type (init)
	               ::= [gs] dl <expression>                                 # delete expression
	               ::= [gs] da <expression>                                 # delete[] expression
	               ::= dc <type> <expression>                               # dynamic_cast<type> (expression)
	               ::= sc <type> <expression>                               # static_cast<type> (expression)
	               ::= cc <type> <expression>                               # const_cast<type> (expression)
	               ::= rc <type> <expression>                               # reinterpret_cast<type> (expression)
	               ::= ti <type>                                            # typeid (type)
	               ::= te <expression>                                      # typeid (expression)
	               ::= st <type>                                            # sizeof (type)
	               ::= sz <expression>                                      # sizeof (expression)
	               ::= at <type>                                            # alignof (type)
	               ::= az <expression>                                      # alignof (expression)
	               ::= nx <expression>                                      # noexcept (expression)
	               ::= <template-param>
	               ::= <function-param>
	               ::= dt <expression> <unresolved-name>                    # expr.name
	               ::= pt <expression> <unresolved-name>                    # expr->name
	               ::= ds <expression> <expression>                         # expr.*expr
	               ::= sZ <template-param>                                  # sizeof...(T), size of a template parameter pack
	               ::= sZ <function-param>                                  # sizeof...(parameter), size of a function parameter pack
	               ::= sP <template-arg>* E                                 # sizeof...(T), size of a captured template parameter pack from an alias template
	               ::= sp <expression>                                      # expression..., pack expansion
	               ::= tw <expression>                                      # throw expression
	               ::= tr                                                   # throw with no operand (rethrow)
	               ::= <unresolved-name>                                    # f(p), N::f(p), ::f(p),
	                                                                        # freestanding dependent name (e.g., T::x),
	                                                                        # objectless nonstatic member reference
	               ::= <expr-primary>
	*/
	char elm1 = '\0', elm2 = '\0';
	string gs, out;
	elm1 = m_reader.Read();
	if (elm1 == 'L')
	{
		out = DemanglePrimaryExpression();
		return out;
	}
	else if (elm1 == 'T') //<template-param>
	{
		return DemangleTemplateSubstitution().GetString();
	}

	elm2 = m_reader.Read();
	if (hash(elm1, elm2) == hash('g', 's'))
	{
		elm1 = m_reader.Read();
		elm2 = m_reader.Read();
		switch (hash(elm1, elm2))
		{
		case hash('s','r'):
		case hash('n','w'):
		case hash('n','a'):
		case hash('d','l'):
		case hash('d','a'): break;
		default:
			throw DemangleException();
		}
		gs = "::";
	}

	switch (hash(elm1, elm2))
	{
	case hash('d','c'):
	case hash('s','c'):
	case hash('c','c'):
	case hash('r','c'):
	{
		const string op = GetOperator(elm1, elm2);
		const string castType = DemangleTypeString();
		const string castExpr = DemangleExpression();
		return op + "<" + castType + ">(" + castExpr + ")";
	}
	case hash('t','i'):
	case hash('t','e'):
	case hash('s','t'):
	case hash('s','z'):
	case hash('a','t'):
	case hash('a','z'):
	case hash('n','x'):
		return GetOperator(elm1, elm2) + "(" + DemangleTypeString() + ")";
	case hash('s','Z'):
		return GetOperator(elm1, elm2) + "(" + DemangleTypeString() + ")";
	case hash('s','P'):
	{
		vector<string> args;
		DemangleTemplateArgs(args);
		return "sizeof...(" + GetTemplateString(args) + ")...";
	}
	case hash('s','p'):
		return "(" + DemangleExpression() + ")...";
	case hash('t','w'):
		return GetOperator(elm1, elm2) + DemangleExpression();
	case hash('t','r'):
		return GetOperator(elm1, elm2); //rethrow
	case hash('n','t'): // !
	case hash('n','g'): // - (unary)
	case hash('p','s'): // + (unary)
	case hash('a','d'): // & (unary)
	case hash('d','e'): // * (unary)
		return DemangleUnaryPrefixExpression(GetOperator(elm1, elm2));
	case hash('i','x'): // []
	case hash('p','p'): // ++ (postfix in <expression> context)
	case hash('m','m'): // -- (postfix in <expression> context)
		return DemangleUnarySuffixExpression(GetOperator(elm1, elm2));
	case hash('d','t'): // .
	{
		const string dtObj = DemangleExpression();
		const string dtMem = DemangleExpression();
		return dtObj + "." + dtMem;
	}
	case hash('p','t'): // ->
	{
		const string ptObj = DemangleExpression();
		const string ptMem = DemangleExpression();
		return ptObj + "->" + ptMem;
	}
	case hash('l','s'): // <<
	case hash('r','s'): // >>
	case hash('a','S'): // =
	case hash('e','q'): // ==
	case hash('n','e'): // !=
	case hash('m','l'): // *
	case hash('m','i'): // -
	case hash('p','l'): // +
	case hash('a','n'): // &
	case hash('p','m'): // ->*
	case hash('d','v'): // /
	case hash('r','m'): // %
	case hash('l','t'): // <
	case hash('l','e'): // <=
	case hash('g','t'): // >
	case hash('g','e'): // >=
	case hash('c','m'): // ,
	case hash('c','o'): // ~
	case hash('e','o'): // ^
	case hash('o','r'): // |
	case hash('a','a'): // &&
	case hash('o','o'): // ||
	case hash('m','L'): // *=
	case hash('p','L'): // +=
	case hash('m','I'): // -=
	case hash('d','V'): // /=
	case hash('r','M'): // %=
	case hash('r','S'): // >>=
	case hash('l','S'): // <<=
	case hash('a','N'): // &=
	case hash('o','R'): // |=
	case hash('e','O'): // ^=
		return DemangleBinaryExpression(GetOperator(elm1, elm2));
	case hash('d','l'): // delete
	case hash('d','a'): // delete[]
	case hash('n','w'): // new
	case hash('n','a'): // new []
		return gs + DemangleUnaryPrefixType(GetOperator(elm1, elm2));
	case hash('q','u'): // ternary
	{
		const string cond = DemangleExpression();
		const string then_expr = DemangleExpression();
		const string else_expr = DemangleExpression();
		return cond + "?" + then_expr + ":" + else_expr;
	}
	case hash('c','l'): // ()
	{
		const string callable = DemangleExpression();
		string args;
		bool firstArg = true;
		m_functionSubstitute.push_back({});
		while (m_reader.Peek() != 'E')
		{
			if (!firstArg) args += ", ";
			const string e = DemangleExpression();
			args += e;
			m_functionSubstitute.back().push_back(CreateUnknownType(e));
			firstArg = false;
		}
		m_functionSubstitute.pop_back();
		m_reader.Consume(); // 'E'
		return callable + "(" + args + ")";
	}
	case hash('c','v'): //type (expression)
	{
		DemangledTypeNode type = DemangleType();
		out = type.GetString();
		if (m_reader.Peek() == '_')
		{
			m_reader.Consume(); // consume '_' delimiter before expression list
			out += " (" + DemangleExpressionList() + ")";
		}
		else
			out += " (" + DemangleExpression() + ")";
		return out;
	}
	case hash('t','l'): //type {expression}
	{
		const string tlType = DemangleTypeString();
		const string tlExprs = DemangleExpressionList();
		return tlType + " {" + tlExprs + "}";
	}
	case hash('i', 'l'): //{expr-list}, braced-init-list in any other context
		out = DemangleExpression();
		if (m_reader.Read() != 'E')
			throw DemangleException();
		return out;
	case hash('f','p'):
	case hash('f','L'):
	{
		//<function-param> ::= fp <CV> _                         # L == 0, first parameter
		//                 ::= fp <CV> <prm-2 num> _             # L == 0, second and later parameters
		//                 ::= fL <L-1 num> p <CV> _             # L  > 0, first parameter
		//                 ::= fL <L-1 num> p <CV> <prm-2 num> _ # L  > 0, second and later parameters

		bool cnst = false, vltl = false, rstrct = false;
		DemangledTypeNode type;
		int64_t listNumber = 0;
		int64_t elementNum = 0;
		char elm;
		if (elm2 == 'L')
		{
			// fL <L-1 num> p <CV> [<prm-2 num>] _
			// When listNumber is out of range (e.g. fL used inside a decltype return
			// type before function params are known), the fallback paths below produce
			// a placeholder string "fp" / "fpN".
			listNumber = DemangleNumber() + 1;
			if (listNumber < 0 || m_reader.Read() != 'p')
				throw DemangleException();
		}
		DemangleCVQualifiers(cnst, vltl, rstrct);
		elm = m_reader.Peek();
		if (elm == '_')
		{
			m_reader.Consume(1);
			if ((uint64_t)listNumber >= (uint64_t)m_functionSubstitute.size() ||
			    (size_t)elementNum >= m_functionSubstitute[listNumber].size())
			{
				// fp_ used before params are known (e.g., in decltype return type)
				out = (elementNum == 0) ? "fp" : "fp" + std::to_string(elementNum - 1);
				break;
			}
			type = m_functionSubstitute[listNumber][elementNum];
		}
		else if (isdigit(elm) || isupper(elm))
		{
			elementNum = DemangleNumber() + 1;
			if (m_reader.Read() != '_')
				throw DemangleException();
			if (elementNum < 0 ||
			    (uint64_t)listNumber >= (uint64_t)m_functionSubstitute.size() ||
			    (size_t)elementNum >= m_functionSubstitute[listNumber].size())
			{
				// fpN_ used before params are known
				out = "fp" + std::to_string(elementNum - 1);
				break;
			}
			type = m_functionSubstitute[listNumber][elementNum];
		}
		else
		{
			throw DemangleException();
		}
		out = type.GetString();
		break;
	}
	case hash('s','r'):
		/*
		<unresolved-name> ::=
		                  ::=   <unresolved-type> <base-unresolved-name>                  # T::x / decltype(p)::x
		                  ::= N <unresolved-type> <unresolved-qualifier-level>+ E <base-unresolved-name>
		                                                                                    # T::N::x /decltype(p)::N::x
		                  ::=                     <unresolved-qualifier-level>+ E <base-unresolved-name>
		                                                            # A::x, N::y, A<T>::z; "gs" means leading "::"

		<unresolved-type> ::= <template-param> [ <template-args> ]            # T:: or T<X,Y>::
		                  ::= <decltype>                                      # decltype(p)::
		                  ::= <substitution>

		<unresolved-qualifier-level> ::= <simple-id>
		<base-unresolved-name> ::= <simple-id>                                # unresolved name
		                       ::= on <operator-name>                         # unresolved operator-function-id
		                       ::= on <operator-name> <template-args>         # unresolved operator template-id
		                       ::= dn <destructor-name>                       # destructor or pseudo-destructor;
		                                                                      # e.g. ~X or ~X<N-1>
		*/
		if (m_reader.Peek() == 'N')
		{
			m_reader.Consume();
			// Standard form: N <unresolved-type> <qualifier-levels>+ E <base>
			// where <unresolved-type> is T_, Dt, or S.
			// GCC extension: N <source-name-qualifier>+ E <base>
			// When the first component is a digit (source name), skip the
			// unresolved-type and let the loop below handle all qualifiers.
			if (!isdigit(m_reader.Peek()))
				out += DemangleUnresolvedType().GetString() + "::";
			do
			{
				out += DemangleSourceName();
				// Push bare name (before template args) to substitution table.
				PushType(DemangledTypeNode::NamedType(UnknownNamedTypeClass, _STD_VECTOR<_STD_STRING>{out}));
				if (m_reader.Peek() == 'I')
				{
					vector<string> args;
					m_reader.Consume();
					//<tmplate-args>
					DemangleTemplateArgs(args);
					out += GetTemplateString(args);
					// Also push the template instantiation (name+args).
					PushType(DemangledTypeNode::NamedType(UnknownNamedTypeClass, _STD_VECTOR<_STD_STRING>{out}));
				}
				out += "::";
			}while (m_reader.Peek() != 'E');
			m_reader.Consume();

			out += DemangleBaseUnresolvedName().GetString();
			return out;
		}
		if (isdigit(m_reader.Peek()))
		{
			// <unresolved-qualifier-level>+ E <base-unresolved-name>
			// GCC sometimes omits the explicit qualifier-list 'E' when the last
			// qualifier ends with template-args (the template-args 'E' serves double
			// duty). Break out of the loop immediately after any qualifier with
			// template-args rather than waiting for a standalone 'E'.
			//
			// Each qualifier level adds to the substitution table:
			//   - the bare name (before template-args) as a substitution candidate
			//   - the template instantiation (name + args) as another candidate
			// This mirrors how the compiler builds the substitution table during encoding.
			bool hadTemplateArgs = false;
			do
			{
				hadTemplateArgs = false;
				const string segName = DemangleSourceName();
				out += segName;
				// Push bare name to substitution table.
				PushType(CreateUnknownType(out));
				if (m_reader.Peek() == 'I')
				{
					vector<string> args;
					m_reader.Consume();
					DemangleTemplateArgs(args); // consumes the trailing 'E'
					out += GetTemplateString(args);
					// Also push the template instantiation.
					PushType(CreateUnknownType(out));
					hadTemplateArgs = true;
				}
				out += "::";
			}while (!hadTemplateArgs && m_reader.Peek() != 'E');
			// Consume qualifier-list 'E' if present. GCC sometimes omits it when
			// the last qualifier had template-args whose 'E' served double duty,
			// so check rather than unconditionally consuming.
			if (m_reader.Peek() == 'E')
				m_reader.Consume();
			out += DemangleBaseUnresolvedName().GetString();
			return out;
		}
		else
		{
			out += DemangleUnresolvedType().GetString() + "::";
			// GCC may encode multi-level scoped names without the 'N' qualifier
			// prefix, e.g. "sr St 6__and_I<T>E 5value" for std::__and_<T>::value.
			// Process any digit-started names: if a name has template args AND
			// another source name follows, it is an intermediate qualifier level;
			// otherwise it is the final base-unresolved-name.
			while (isdigit(m_reader.Peek()))
			{
				const string segName = DemangleSourceName();
				if (m_reader.Peek() == 'I')
				{
					vector<string> args;
					m_reader.Consume();
					DemangleTemplateArgs(args);
					if (isdigit(m_reader.Peek()))
					{
						// Another source name follows — intermediate qualifier.
						// Push to the substitution table, mirroring what the
						// N-prefix sr branch does for each nested qualifier.
						PushType(CreateUnknownType(out + segName + GetTemplateString(args)));
						out += segName + GetTemplateString(args) + "::";
					}
					else
					{
						// No more source names — this template-id is the final name.
						out += segName + GetTemplateString(args);
						return out;
					}
				}
				else
				{
					// Plain source name with no template args — final base name.
					out += segName;
					return out;
				}
			}
			// peek is not a digit: fall back for operator-names ("on") / destructor-names ("dn").
			out += DemangleBaseUnresolvedName().GetString();
		}
		return out;
	default:
		m_reader.UnRead(2);
		out = DemangleSourceName();
		if (m_reader.Peek() == 'I')
		{
			vector<string> args;
			m_reader.Consume();
			//<tmplate-args>
			DemangleTemplateArgs(args);
			out += GetTemplateString(args);
		}
		break;
	}
	return out;
}


void DemangleGNU3::DemangleTemplateArgs(vector<string>& args, bool* hadNonTypeArg)
{
	indent();
	MyLogDebug("%s:: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	DemangledTypeNode tmp;
	bool tmpValid = false;
	string expr;
	bool topLevel;
	const string lastName = m_lastName;
	while (m_reader.Peek() != 'E')
	{
		switch (m_reader.Read())
		{
		case 'L':
			expr = DemanglePrimaryExpression();
			args.push_back(expr);
			tmp = CreateUnknownType(expr);
			tmpValid = true;
			if (hadNonTypeArg) *hadNonTypeArg = true;
			break;
		case 'X':
			args.push_back(DemangleExpression());
			if (m_reader.Read() != 'E')
				throw DemangleException();
			if (hadNonTypeArg) *hadNonTypeArg = true;
			break;
		case 'I': // GCC sometimes uses I...E for argument packs instead of J...E
		case 'J':
		{
			size_t prevTemplateSize = m_templateSubstitute.size();
			DemangleTemplateArgs(args);
			if (m_topLevel && m_templateSubstitute.size() == prevTemplateSize)
				PushTemplateType(CreateUnknownType("auto"));
			break;
		}
		default:
			m_reader.UnRead();
			topLevel = m_topLevel;
			m_topLevel = false;
			tmp = DemangleType();
			m_topLevel = topLevel;
			args.push_back(tmp.GetString());
			tmpValid = true;
		}
		if (m_topLevel && tmpValid)
		{
			MyLogDebug("Adding template ref: %s\n", tmp.GetString().c_str());
			PushTemplateType(tmp);
		}
	}
	m_reader.Consume();
	m_lastName = lastName;
	dedent();
	return;
}


DemangledTypeNode DemangleGNU3::DemangleNestedName(bool* allTypeTemplateArgs)
{
	/*
	This can be either a qualified name like: "foo::bar::bas"
	or it can be a qualified type like: "foo::bar::bas & const" thus we return either
	a name or a type.

	<nested-name> ::= N [<CV-qualifiers>] [<ref-qualifier>] <prefix> <unqualified-name> E
	              ::= N [<CV-qualifiers>] [<ref-qualifier>] <template-prefix> <template-args> E

	<prefix> ::= <unqualified-name>                 # global class or namespace
	         ::= <prefix> <unqualified-name>        # nested class or namespace
	         ::= <template-prefix> <template-args>  # class template specialization
	         ::= <template-param>                   # template type parameter
	         ::= <decltype>                         # decltype qualifier
	         ::= <prefix> <data-member-prefix>      # initializer of a data member
	         ::= <substitution>

	<template-prefix> ::= <template unqualified-name>           # global template
	                  ::= <prefix> <template unqualified-name>  # nested template
	                  ::= <template-param>                      # template template parameter
	                  ::= <substitution>

	<unqualified-name> ::= <operator-name>
	                   ::= <ctor-dtor-name>
	                   ::= <source-name>
	                   ::= <unnamed-type-name>

	<source-name> ::= <positive length number> <identifier>
	<identifier>  ::= <unqualified source code identifier>
	*/

	indent();
	MyLogDebug("%s:: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	DemangledTypeNode type = DemangledTypeNode::NamedType(UnknownNamedTypeClass, QualifiedName());
	bool cnst = false, vltl = false, rstrct = false;
	bool ref = false;
	bool rvalueRef = false;
	bool substitute = true;
	DemangledTypeNode newType;
	bool base = false;
	bool isTemplate = false;
	//[<CV-qualifiers>]
	DemangleCVQualifiers(cnst, vltl, rstrct);

	//[<ref-qualifier>]
	if (m_reader.Peek() == 'R')
	{
		m_reader.Consume();
		ref = true;
	}
	else if (m_reader.Peek() == 'O')
	{
		m_reader.Consume();
		ref = true;
		rvalueRef = true;
	}

	while (m_reader.Peek() != 'E')
	{
		isTemplate = false;
		substitute = true;
		size_t startSize = m_templateSubstitute.size();
		switch (m_reader.Read())
		{
		case 'M': // <data-member-prefix>: closure/lambda inside a data member initializer
			// 'M' follows the member name and marks that subsequent components are
			// scoped inside that data member. Just consume it; the name is already captured.
			continue;
		case 'S': //<substitution>
			newType = DemangleSubstitution();
			substitute = false;
			break;
		case 'T': //<template-param>
			newType = DemangleTemplateSubstitution();
			break;
		case 'I': //<template-prefix> <template-args>
		{
			if (!base)
				throw DemangleException();
			vector<string> args;
			bool hadNonType = false;
			DemangleTemplateArgs(args, allTypeTemplateArgs ? &hadNonType : nullptr);
			if (allTypeTemplateArgs)
				*allTypeTemplateArgs = !hadNonType;
			// Resolve any forward template refs created while parsing a cv
			// conversion operator type (e.g. cv T_ where T_ wasn't yet known).
			// Only do this in the outer context (not while still inside the cv
			// type parsing itself where m_permitForwardTemplateRefs is true).
			if (!m_permitForwardTemplateRefs)
				ResolveForwardTemplateRefs(type, args);
			ExtendTypeName(type, GetTemplateString(args));
			type.SetHasTemplateArguments(true);
			isTemplate = true;
			break;
		}
		default:  //<unqualified-name> || <decltype>
			m_reader.UnRead(1);
			newType = DemangleUnqualifiedName();
			break;
		}

		base = true;
		if (!isTemplate)
		{
			type.SetNameType(newType.GetNameType());
			auto aNames = type.GetTypeName();
			auto bNames = newType.GetTypeName();
			_STD_VECTOR<_STD_STRING> newName;
			newName.reserve(aNames.size() + bNames.size());
			newName.insert(newName.end(), aNames.begin(), aNames.end());
			newName.insert(newName.end(), bNames.begin(), bNames.end());
			if (TotalStringSize(newName) > MAX_DEMANGLE_LENGTH)
				throw DemangleException("Detected adversarial mangled string");
			type.SetNTR(type.GetNTRClass(), newName);
			type.SetHasTemplateArguments(false);
		}
		// Consume any ABI tags (B <source-name>) following this name component.
		// These appear as suffixes on <unqualified-name> in the Itanium ABI:
		//   <abi-tags> ::= <abi-tag> [<abi-tags>]
		//   <abi-tag>  ::= B <source-name>
		// We append them as "[abi:tag]" to the last name segment for display.
		// Save/restore m_lastName so that a following C1/D1 ctor/dtor name
		// still resolves to the class name, not the ABI tag string.
		while (m_reader.Peek() == 'B')
		{
			m_reader.Consume();
			string savedLastName = m_lastName;
			string abiTag = DemangleSourceName();
			m_lastName = savedLastName;
			auto& segs = type.GetMutableTypeName();
			if (!segs.empty())
				segs.back() += "[abi:" + abiTag + "]";
		}
		if (substitute && m_reader.Peek() != 'E')
		{
			//Those template arguments were not the primary arguments so clear them from the sub listType
			while (m_templateSubstitute.size() > startSize)
			{
				m_templateSubstitute.pop_back();
			}
			PushType(type);
		}
		MyLogDebug("%s:: '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	}
	m_reader.Consume();

	if (cnst || vltl || rstrct)
	{
		type.SetConst(cnst);
		type.SetVolatile(vltl);
		if (rstrct)
			type.AddPointerSuffix(RestrictSuffix);
	}

	if (ref)
	{
		type.AddPointerSuffix(rvalueRef?LvalueSuffix:ReferenceSuffix);
		PushType(type);
	}
	dedent();
	return type;
}


DemangledTypeNode DemangleGNU3::DemangleLocalName()
{
	indent();
	MyLogDebug("%s '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	DemangledTypeNode type;
	QualifiedName varName;
	// The local function has its own template scope. Save the outer template
	// substitution table and set m_topLevel = true so that when the local
	// function's template args are parsed (e.g. handleMessageDelayed<T, T0, T1>),
	// they populate m_templateSubstitute and are available for T_/T0_/T1_
	// references in the function's parameter types.
	auto savedTemplateSubstitute = m_templateSubstitute;
	m_templateSubstitute.clear();
	bool oldTopLevel = m_topLevel;
	m_topLevel = true;
	bool savedInLocalName = m_inLocalName;
	m_inLocalName = true;
	type = DemangleSymbol(varName);
	m_inLocalName = savedInLocalName;
	m_topLevel = oldTopLevel;
	m_templateSubstitute = std::move(savedTemplateSubstitute);

	if (varName.size() > 0)
		varName.back() += (type.GetStringAfterName());
	else
		varName.push_back(type.GetString());

	if (m_reader.Peek() != 's')
	{
		// Handle default argument context: d [<number>] _ <name>
		if (m_reader.Peek() == 'd')
		{
			m_reader.Consume();
			if (isdigit(m_reader.Peek()))
				DemangleNumber();
			if (m_reader.Peek() == '_')
				m_reader.Consume();
		}
		//<entity name>
		DemangledTypeNode tmpType = DemangleName();
		type = DemangledTypeNode::NamedType(UnknownNamedTypeClass, varName);
		auto aNames = type.GetTypeName();
		auto bNames = tmpType.GetTypeName();
		_STD_VECTOR<_STD_STRING> newName;
		newName.reserve(aNames.size() + bNames.size());
		newName.insert(newName.end(), aNames.begin(), aNames.end());
		newName.insert(newName.end(), bNames.begin(), bNames.end());
		if (TotalStringSize(newName) > MAX_DEMANGLE_LENGTH)
			throw DemangleException("Detected adversarial mangled string");
		type.SetTypeName(std::move(newName));
		type.SetConst(tmpType.IsConst());
		type.SetVolatile(tmpType.IsVolatile());
		type.SetPointerSuffix(tmpType.GetPointerSuffix());
	}
	else
	{
		m_reader.Consume();
		type = DemangledTypeNode::NamedType(UnknownNamedTypeClass, varName);
	}
	// [<discriminator>]
	//TODO: What do we do with discriminators?
	if (m_reader.Peek() == '_')
	{
		m_reader.Consume();
		if (m_reader.Peek() == '_')
		{
			m_reader.Consume();
			DemangleNumberAsString();
			if (m_reader.Read() != '_')
				throw DemangleException();
		}
		else
		{
			DemangleNumberAsString();
		}
	}
	dedent();
	return type;
}


DemangledTypeNode DemangleGNU3::DemangleName()
{
	indent();
	MyLogDebug("%s '%s'\n", __FUNCTION__, m_reader.GetRaw().c_str());
	/*
	<name> ::= <nested-name>
	       ::= <unscoped-name>
	       ::= <unscoped-template-name> <template-args>
	       ::= <local-name>	# See Scope Encoding below

	<unscoped-name> ::= <unqualified-name>
	                ::= St <unqualified-name>   # ::std::

	<unscoped-template-name> ::= <unscoped-name>
	                         ::= <substitution>
	*/
	DemangledTypeNode type;
	bool substitute = false;
	switch (m_reader.Read())
	{
	case 'S':
		if (m_reader.Peek() == 't')
		{
			m_reader.Consume(1);
			type = DemangleUnqualifiedName();
			auto qn = type.GetTypeName();
			qn.insert(qn.begin(), "std");
			type.SetTypeName(std::move(qn));
			substitute = true;
		}
		else
		{
			type = DemangleSubstitution();
		}

		if (m_reader.Peek() == 'I')
		{
			m_reader.Consume();
			if (substitute)
				PushType(type);
			vector<string> args;
			DemangleTemplateArgs(args);
			ExtendTypeName(type, GetTemplateString(args));
			type.SetHasTemplateArguments(true);
			// Push the template instantiation (e.g. std::swap<T>) so that the
			// substitution table matches what the encoder built.  The encoder adds
			// both the unscoped-template-name (prefix, already pushed above) and
			// the full template-id (instantiation).
			PushType(type);
		}
		break;
	case 'N': //<nested-name>
	{
		bool allTypeArgs = false;
		type = DemangleNestedName(&allTypeArgs);
		if (!m_inLocalName && allTypeArgs)
			PushType(type);
		break;
	}
	case 'Z': //<local-name>
		type = DemangleLocalName();
		break;
	default: //<unscoped-name> | <substitution>
		/*
		<unscoped-name> ::= <unqualified-name>
		                ::= St <unqualified-name>   # ::std::
		<unscoped-template-name> ::= <unscoped-name>
		                         ::= <substitution>
		*/
		m_reader.UnRead();
		if (m_reader.Peek() == 'L')
			m_reader.Consume();
		type = DemangleUnqualifiedName();
		if (m_reader.Peek() == 'I')
		{
			PushType(type);
			//<unscoped-template-name>
			vector<string> args;
			m_reader.Consume();
			//<tmplate-args>
			DemangleTemplateArgs(args);
			LogDebug("Typename: %s", type.GetTypeName()[0].c_str());
			ExtendTypeName(type, GetTemplateString(args));
			LogDebug("Typename: %s", type.GetTypeName()[0].c_str());
			type.SetHasTemplateArguments(true);
		}
	}
	dedent();
	return type;
}


DemangledTypeNode DemangleGNU3::DemangleSymbol(QualifiedName& varName)
{
	indent();
	MyLogDebug("%s: %s\n", __FUNCTION__, m_reader.GetRaw().c_str());
	DemangledTypeNode returnType;
	bool isReturnTypeUnknown = false;
	DemangledTypeNode type;
	ParamList params;
	bool cnst = false, vltl = false, rstrct = false;
	bool oldTopLevel;
	QualifiedName name;

	/*
	<encoding> ::= <function name> <bare-function-type>
	           ::= <data name>
	           ::= <special-name>
	*/
	//<special-name>
	switch (m_reader.Peek())
	{
	case 'G':
		m_reader.Consume();
		switch (m_reader.Read())
		{
		case 'A': //TODO hidden alias
			LogWarn("Unsupported demangle type: hidden alias\n");
			throw DemangleException();
		case 'R': // GR <object name> [<seq-id>] _  # reference temporary
		{
			// <object name> is a <name> production (nested, local, or unscoped).
			// For local names (Z prefix), DemangleLocalName consumes the trailing '_'
			// as a zero-discriminator, so we only consume '_' if it's still present.
			DemangledTypeNode nameNode = DemangleName();
			// Consume optional base-36 seq-id (digits + uppercase A-Z) before '_'.
			string seqId;
			while (m_reader.Length() > 0 && m_reader.Peek() != '_')
				seqId += m_reader.Read();
			if (m_reader.Length() > 0)
				m_reader.Consume(); // consume '_'
			string result = "reference_temporary_for_" + nameNode.GetString();
			if (!seqId.empty())
				result += "[" + seqId + "]";
			varName.push_back(result);
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass, varName);
		}
		case 'T': // transaction clone: GTt<encoding> (safe) or GTn<encoding> (non-safe)
		{
			// consume the 't' (transaction-safe) or 'n' (non-transaction-safe) qualifier
			char kind = m_reader.Read();
			if (kind != 't' && kind != 'n')
				throw DemangleException();
			oldTopLevel = m_topLevel;
			m_topLevel = false;
			DemangledTypeNode t = DemangleSymbol(name);
			m_topLevel = oldTopLevel;
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{name.GetString() + " [transaction clone]" + t.GetStringAfterName()});
		}
		case 'V':
		{
			// Disambiguate: Intel Vector Function ABI (_ZGV<isa>...) vs guard variable (_ZGV<symbol>).
			// Intel Vector ABI isa codes: b c d e x y Y z Z
			// Guard variable encoding starts with: N (nested), L (local), S (substitution), digit, etc.
			char peekChar = m_reader.Peek();
			bool isVectorABI = (peekChar == 'b' || peekChar == 'c' || peekChar == 'd' || peekChar == 'e' ||
			                    peekChar == 'x' || peekChar == 'y' || peekChar == 'Y');
			// 'z'/'Z' are ambiguous: also used as Z-local-name prefix in guard variables
			// (e.g. _ZGVZN1A1BEvE1A = guard variable for A::B()::A).
			// Disambiguate by verifying the full Vector ABI parameter pattern:
			// <isa><mask(M|N)><vlen(digits)><vparams><'_'>  where vparams are only
			// from {v, l, u, R, L, s, 0-9} and are immediately followed by '_'.
			// A guard variable's inner symbol would have source-name chars (e.g. 'm', 'a', etc.)
			// that don't appear in valid vparameter sequences.
			if (!isVectorABI && (peekChar == 'z' || peekChar == 'Z'))
			{
				_STD_STRING ahead = m_reader.PeekString(std::min((size_t)32, m_reader.Length()));
				if (ahead.size() >= 3 && (ahead[1] == 'M' || ahead[1] == 'N'))
				{
					size_t pos = 2;
					while (pos < ahead.size() && isdigit((unsigned char)ahead[pos]))
						pos++;
					if (pos > 2) // had at least one vlen digit
					{
						// Scan through vparameter chars; valid ones are v/l/u/R/L and
						// optional stride digits/'s'. Anything else means guard variable.
						bool allVparam = true;
						while (pos < ahead.size() && ahead[pos] != '_')
						{
							char c = ahead[pos];
							if (c == 'v' || c == 'l' || c == 'u' || c == 'R' ||
							    c == 'L' || c == 's' || isdigit((unsigned char)c))
								pos++;
							else
							{
								allVparam = false;
								break;
							}
						}
						isVectorABI = allVparam && pos < ahead.size() && ahead[pos] == '_';
					}
				}
			}
			if (!isVectorABI)
			{
				// Guard variable (original behavior)
				DemangledTypeNode t = DemangleSymbol(name);
				varName.push_back("guard_variable_for_" + t.GetTypeAndName(name));
				type = DemangledTypeNode::IntegerType(1, false);
				if (m_reader.Length() == 0)
					return type;
				//function parameters
				string paramList;
				paramList += "(";
				bool first = true;
				do
				{
					if (m_reader.Peek() == 'v')
					{
						m_reader.Consume();
						break;
					}
					if (!first)
						paramList += ", ";
					paramList += DemangleTypeString();
				}while (m_reader.Peek() != 'E');
				m_reader.Consume();
				varName.back() += paramList + ")";
				varName.push_back(DemangleSourceName());

				return type;
			}



			// Intel Vector Function ABI:
			// GV <isa> <mask> <vlen> <vparameters> '_' <routine_name>

			// Parse ISA
			char isa = m_reader.Read();
			const char* isaName;
			switch (isa)
			{
			case 'b': isaName = "SSE2"; break;
			case 'c': isaName = "SSE4.2"; break;
			case 'd': isaName = "AVX"; break;
			case 'e': isaName = "AVX512"; break;
			case 'x': isaName = "SSE2"; break;
			case 'y': isaName = "AVX"; break;
			case 'Y': isaName = "AVX2"; break;
			case 'z': isaName = "MIC"; break;
			case 'Z': isaName = "AVX512"; break;
			default:  isaName = "unknown"; break;
			}

			// Parse mask: 'M' (mask) or 'N' (nomask)
			char maskChar = m_reader.Read();
			if (maskChar != 'M' && maskChar != 'N')
				throw DemangleException();
			const char* maskName = (maskChar == 'M') ? "mask" : "nomask";

			// Parse vlen: non-negative decimal integer
			if (!isdigit(m_reader.Peek()))
				throw DemangleException();
			string vlenStr;
			while (isdigit(m_reader.Peek()))
				vlenStr += m_reader.Read();

			// Parse vparameters until '_' separator
			// <vparameter> <opt-align>
			// <vparameter> ::= ('l'|'R'|'U'|'L') <stride>  |  'u'  |  'v'
			// <stride>     ::= empty | 's' <decimal> | <number>
			// <opt-align>  ::= empty | 'a' <decimal>
			string paramsStr;
			bool firstParam = true;
			while (m_reader.Length() > 0 && m_reader.Peek() != '_')
			{
				if (!firstParam)
					paramsStr += ',';
				firstParam = false;

				char pc = m_reader.Read();
				bool hasStride = false;
				switch (pc)
				{
				case 'l': paramsStr += "linear"; hasStride = true; break;
				case 'R': paramsStr += "linear(ref)"; hasStride = true; break;
				case 'U': paramsStr += "linear(uval)"; hasStride = true; break;
				case 'L': paramsStr += "linear(val)"; hasStride = true; break;
				case 'u': paramsStr += "uniform"; break;
				case 'v': paramsStr += "vector"; break;
				default:  throw DemangleException();
				}

				if (hasStride)
				{
					if (m_reader.Peek() == 's')
					{
						// linear_step passed as another argument at given 0-based position
						m_reader.Consume();
						string argPos;
						while (isdigit(m_reader.Peek()))
							argPos += m_reader.Read();
						paramsStr += "(step=arg" + argPos + ")";
					}
					else if (isdigit(m_reader.Peek()) || m_reader.Peek() == 'n')
					{
						// Literal stride; 'n' prefix means negative
						string stride = DemangleNumberAsString();
						paramsStr += "(step=" + stride + ")";
					}
					// else: empty stride means step of 1
				}

				// Optional alignment: 'a' <non-negative-decimal>
				if (m_reader.Peek() == 'a')
				{
					m_reader.Consume();
					while (isdigit(m_reader.Peek()))
						m_reader.Read();
				}
			}

			// Consume the '_' separator between parameters and routine name
			if (m_reader.Length() == 0 || m_reader.Read() != '_')
				throw DemangleException();

			// Remainder is the scalar routine name (may be a plain C name or a _Z mangled name)
			string routineName = m_reader.ReadString(m_reader.Length());

			// Build the human-readable annotation
			string annotation = " [SIMD:";
			annotation += isaName;
			annotation += ',';
			annotation += maskName;
			annotation += ",N=";
			annotation += vlenStr;
			if (!paramsStr.empty())
			{
				annotation += ",(";
				annotation += paramsStr;
				annotation += ')';
			}
			annotation += ']';

			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{routineName + annotation});
		}
		default:
			throw DemangleException();
		}
	case 'T':
		/*
		<special-name> ::= TV <type>	# virtual table
		               ::= TT <type>	# VTT structure (construction vtable index)
		               ::= TI <type>	# typeinfo structure
		               ::= TS <type>	# typeinfo name (null-terminated byte string)
		               ::= T <call-offset> <base encoding>
		                   # base is the nominal target function of thunk
		<call-offset>  ::= h <nv-offset> _
		               ::= v <v-offset> _
		<nv-offset>    ::= <offset number> # non-virtual base override
		<v-offset>     ::= <offset number> _ <virtual offset number>
		                   # virtual base override, with vcall offset
		*/
		m_reader.Consume();
		switch (m_reader.Read())
		{
		case 'c': // covariant return thunk: Tc <call-offset> <call-offset> <encoding>
		{
			// consume a call-offset: h <number> _  or  v <number> _ <number> _
			auto consumeCallOffset = [&]() {
				char kind = m_reader.Read();
				if (kind == 'h')
				{
					DemangleNumberAsString();
					if (m_reader.Read() != '_')
						throw DemangleException();
				}
				else if (kind == 'v')
				{
					DemangleNumberAsString();
					if (m_reader.Read() != '_')
						throw DemangleException();
					DemangleNumberAsString();
					if (m_reader.Read() != '_')
						throw DemangleException();
				}
				else
					throw DemangleException();
			};
			consumeCallOffset(); // this-pointer adjustment
			consumeCallOffset(); // return-value adjustment
			oldTopLevel = m_topLevel;
			m_topLevel = false;
			DemangledTypeNode t = DemangleSymbol(name);
			m_topLevel = oldTopLevel;
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"covariant_return_thunk_to_" + name.GetString() + t.GetStringAfterName()});
		}
		case 'C':
		{
			DemangledTypeNode t = DemangleType();
			DemangleNumberAsString();
			if (m_reader.Read() != '_')
				throw DemangleException();

			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"construction_vtable_for_" + DemangleTypeString() + "-in-" + t.GetString()});
		}
		case 'D':
			LogWarn("Unsupported: 'typeinfo common proxy'\n");
			throw DemangleException();
		case 'F':
			LogWarn("Unsupported: 'typeinfo fn'\n");
			throw DemangleException();
		case 'h': //TODO: Convert to whatever the actual type is!
		{
			DemangleNumberAsString();
			if (m_reader.Read() != '_')
				throw DemangleException();
			oldTopLevel = m_topLevel;
			m_topLevel = false;
			DemangledTypeNode t = DemangleSymbol(name);
			m_topLevel = oldTopLevel;
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"non-virtual_thunk_to_" + name.GetString() + t.GetStringAfterName()});
		}
		case 'H': // TLS init function
		{
			oldTopLevel = m_topLevel;
			m_topLevel = false;
			DemangledTypeNode t = DemangleSymbol(name);
			m_topLevel = oldTopLevel;
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"tls_init_function_for_" + t.GetTypeAndName(name)});
		}
		case 'I':
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"typeinfo_for_" + DemangleTypeString()});
		case 'J':
			LogWarn("Unsupported: 'java class'\n");
			throw DemangleException();
		case 'S':
		{
			DemangledTypeNode t = DemangleType();
			varName = vector<string>{"typeinfo_name_for_" + t.GetString()};
			DemangledTypeNode elemType = DemangledTypeNode::IntegerType(1, true);
			return DemangledTypeNode::ArrayType(std::move(elemType), 0);
		}
		case 'T': //VTT
		{
			DemangledTypeNode t = DemangleType();
			return DemangledTypeNode::NamedType(StructNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"VTT_for_" + t.GetString()});
		}
		case 'v': // virtual thunk
		{
			DemangleNumberAsString();
			if (m_reader.Read() != '_')
				throw DemangleException();
			DemangleNumberAsString();
			if (m_reader.Read() != '_')
				throw DemangleException();
			oldTopLevel = m_topLevel;
			m_topLevel = false;
			DemangledTypeNode t = DemangleSymbol(name);
			m_topLevel = oldTopLevel;
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"virtual_thunk_to_" + name.GetString() + t.GetStringAfterName()});
		}
		case 'V': //Vtable
			return DemangledTypeNode::NamedType(StructNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"vtable_for_" + DemangleTypeString()});
		case 'W': // TLS wrapper function
		{
			oldTopLevel = m_topLevel;
			m_topLevel = false;
			DemangledTypeNode t = DemangleSymbol(name);
			m_topLevel = oldTopLevel;
			return DemangledTypeNode::NamedType(UnknownNamedTypeClass,
				_STD_VECTOR<_STD_STRING>{"tls_wrapper_function_for_" + t.GetTypeAndName(name)});
		}
		default:
			throw DemangleException();
		}
	default: break;
	}

	//<function name> or <data name>
	type = DemangleName();
	if (m_reader.Length() == 0)
	{
		return type;
	}

	if (m_reader.Peek() == 'E')
	{
		m_reader.Consume();
		return type;
	}

	varName = type.GetTypeName();
	cnst = type.IsConst();
	vltl = type.IsVolatile();
	auto suffix = type.GetPointerSuffix();
	if (m_reader.Peek() == 'J')
	{
		m_reader.Consume();
		// TODO: If we get here we have a return type. What can we do with this info?
	}
	// Consume any ABI tags on the function/data name (e.g. B5cxx11).
	// For nested names these are already consumed inside DemangleNestedName();
	// this handles the global-scope case.
	while (m_reader.Peek() == 'B')
	{
		m_reader.Consume();
		string savedLastName = m_lastName;
		string abiTag = DemangleSourceName();
		m_lastName = savedLastName;
		auto& segs = type.GetMutableTypeName();
		if (!segs.empty())
			segs.back() += "[abi:" + abiTag + "]";
	}
	if (m_isOperatorOverload ||
		type.GetNameType() == ConstructorNameType ||
		type.GetNameType() == DestructorNameType)
	{
		returnType = DemangledTypeNode::VoidType();
	}
	else if (m_isParameter || type.HasTemplateArguments())
	{
		returnType = DemangleType();
	}
	else
	{
		isReturnTypeUnknown = true;
		returnType = DemangledTypeNode::IntegerType(m_arch->GetAddressSize(), true);
	}

	m_functionSubstitute.push_back({});
	while (m_reader.Length() > 0)
	{
		if (m_reader.Peek() == 'E')
		{
			m_reader.Consume();
			break;
		}
		if (m_reader.Peek() == '.')
		{
			// Extension, consume the rest
			string ext = m_reader.ReadString(m_reader.Length());

			if (ext == ".eh") ext = "exception handler";
			else if (ext == ".eh_frame") ext = "exception handler frame";
			else if (ext == ".eh_frame_hdr") ext = "exception handler frame header";
			else if (ext == ".debug_frame") ext = "debug frame";

			// On the off chance some invalid mangled string is passed in.
			if (varName.size() > 0)
				varName.back() += " " + ext;
			break;
		}

		m_isParameter = true;
		MyLogDebug("Var: %s\n", m_reader.GetRaw().c_str());
		if (m_reader.PeekString(2) == "@@")
			break;
		DemangledTypeNode param = DemangleType();
		if (param.GetClass() == VoidTypeClass)
		{
			if (m_reader.Peek() == 'E')
			{
				m_reader.Consume();
				break;
			}
			break;
		}
		m_functionSubstitute.back().push_back(param);
		bool isVarArgs = param.GetClass() == VarArgsTypeClass;
		params.push_back({"", std::make_shared<DemangledTypeNode>(std::move(param))});
		if (isVarArgs)
		{
			if (m_reader.Peek() == 'E')
			{
				m_reader.Consume();
			}

			break;
		}
	}

	m_functionSubstitute.pop_back();
	m_isParameter = false;
	type = DemangledTypeNode::FunctionType(std::move(returnType), nullptr, std::move(params));
	if (isReturnTypeUnknown)
		type.SetReturnTypeConfidence(BN_MINIMUM_CONFIDENCE);

	type.SetPointerSuffix(suffix);
	type.SetConst(cnst);
	type.SetVolatile(vltl);
	if (rstrct)
		type.SetPointerSuffix({RestrictSuffix});

	// PrintTables();
	MyLogDebug("Done: %s%s%s\n", type.GetStringBeforeName().c_str(), varName.GetString().c_str(),
		type.GetStringAfterName().c_str());

	dedent();
	return type;
}


// ===== Non-templated static methods =====

bool DemangleGNU3Static::IsGNU3MangledString(const string& name)
{
	string headerless = name;
	string header;
	if (DemangleGlobalHeader(headerless, header))
		return true;

	if (!headerless.compare(0, 2, "_Z") || !headerless.compare(0, 3, "__Z"))
		return true;

	return false;
}


bool DemangleGNU3Static::DemangleGlobalHeader(string& name, string& header)
{
	size_t strippedCount = 0;
	string encoded = name;
	while (encoded[0] == '_')
	{
		encoded.erase(0, 1);
		strippedCount ++;
	}

	if (strippedCount == 0)
		return false;

	static const vector<pair<string, string>> headers = {
		{"GLOBAL__sub_I_", "(static initializer)"},
		{"GLOBAL__I_", "(global initializer)"},
		{"GLOBAL__D_", "(global destructor)"},
	};

	for (auto& i: headers)
	{
		if (encoded.size() > i.first.size() && encoded.substr(0, i.first.size()) == i.first)
		{
			name = name.substr(i.first.size() + strippedCount);
			header = i.second;
			return true;
		}
	}

	return false;
}


bool DemangleGNU3Static::DemangleStringGNU3(Architecture* arch, const string& name, Ref<Type>& outType, QualifiedName& outVarName)
{
	// Handle _block_invoke[.N] and _block_invoke_N suffixes (Clang/Apple block invocations).
	// E.g. ____ZN4dyld5_mainEPK12macho_headermiPPKcS5_S5_Pm_block_invoke.110
	//   -> "invocation_function_for_block_in_dyld::_main(...)"
	static const string blockInvokeSuffix = "_block_invoke";
	size_t blockPos = name.rfind(blockInvokeSuffix);
	if (blockPos != string::npos)
	{
		// Verify the suffix is _block_invoke optionally followed by [._]<digits> only
		string tail = name.substr(blockPos + blockInvokeSuffix.size());
		bool validSuffix = tail.empty();
		if (!validSuffix && (tail[0] == '.' || tail[0] == '_'))
		{
			size_t i = 1;
			while (i < tail.size() && isdigit((unsigned char)tail[i]))
				i++;
			validSuffix = (i == tail.size() && i > 1);
		}
		if (validSuffix)
		{
			// Extract the base symbol: everything before _block_invoke
			string base = name.substr(0, blockPos);
			// Normalize leading underscores: find 'Z' after underscores, keep one '_' before it
			size_t zPos = base.find_first_not_of('_');
			if (zPos != string::npos && base[zPos] == 'Z')
			{
				string normalized = "_" + base.substr(zPos);
				Ref<Type> baseType;
				QualifiedName baseName;
				if (DemangleStringGNU3(arch, normalized, baseType, baseName))
				{
					outVarName.clear();
					outVarName.push_back("invocation_function_for_block_in_" + baseName.GetString());
					outType = baseType;
					return true;
				}
			}
		}
	}

	// Handle macOS thread-local variable initializer suffix: $tlv$init
	// E.g. __ZL9recursive$tlv$init -> demangle "__ZL9recursive" then annotate.
	static const string tlvInitSuffix = "$tlv$init";
	if (name.size() > tlvInitSuffix.size() &&
	    name.compare(name.size() - tlvInitSuffix.size(), tlvInitSuffix.size(), tlvInitSuffix) == 0)
	{
		string base = name.substr(0, name.size() - tlvInitSuffix.size());
		Ref<Type> baseType;
		QualifiedName baseName;
		if (DemangleStringGNU3(arch, base, baseType, baseName))
		{
			outVarName = baseName;
			if (outVarName.size() > 0)
				outVarName[outVarName.size() - 1] += "$tlv$init";
			else
				outVarName.push_back("$tlv$init");
			outType = baseType;
			return true;
		}
	}

	string encoding = name;
	string header;
	bool foundHeader = DemangleGlobalHeader(encoding, header);

	if (!encoding.compare(0, 2, "_Z"))
		encoding = encoding.substr(2);
	else if (!encoding.compare(0, 3, "__Z"))
		encoding = encoding.substr(3);
	else if (foundHeader && !header.empty())
	{
		outVarName.clear();
		outVarName.push_back(header);
		outVarName.push_back(encoding);
		outType = DemangledTypeNode::NamedType(UnknownNamedTypeClass, outVarName).Finalize();
		return true;
	}
	else
		return false;

	thread_local DemangleGNU3 demangle(arch, encoding);
	demangle.Reset(arch, encoding);
	try
	{
		outType = demangle.DemangleSymbol(outVarName).Finalize();

		if (outVarName.size() == 0)
		{
			if (outType->GetClass() == NamedTypeReferenceClass && outType->GetNamedTypeReference()->GetTypeReferenceClass() == UnknownNamedTypeClass)
			{
				outVarName = outType->GetTypeName();
				outType = nullptr;
			}
			else if (outType->GetClass() == NamedTypeReferenceClass)
			{
				auto typeName = outType->GetTypeName();
				if (typeName.size() > 0)
					outVarName = "_" + typeName[typeName.size() - 1];
			}
		}

		if (foundHeader && !header.empty())
		{
			outVarName.insert(outVarName.begin(), header);
		}
	}
	catch (std::exception&)
	{
		return false;
	}
	return true;
}


// ===== Explicit template instantiation =====


// ===== Demangler plugin registration =====

class GNU3Demangler: public Demangler
{
public:
	GNU3Demangler(): Demangler("GNU3")
	{
	}
	~GNU3Demangler() override {}

	virtual bool IsMangledString(const string& name) override
	{
		return DemangleGNU3Static::IsGNU3MangledString(name);
	}

#ifdef BINARYNINJACORE_LIBRARY
	virtual bool Demangle(Architecture* arch, const string& name, Ref<Type>& outType, QualifiedName& outVarName,
	                      BinaryView* view) override
#else
	virtual bool Demangle(Ref<Architecture> arch, const string& name, Ref<Type>& outType, QualifiedName& outVarName,
	                      Ref<BinaryView> view) override
#endif
	{
		return DemangleGNU3Static::DemangleStringGNU3(arch, name, outType, outVarName);
	}
};


extern "C"
{
#ifndef BINARYNINJACORE_LIBRARY
	BN_DECLARE_CORE_ABI_VERSION
#endif

#ifdef BINARYNINJACORE_LIBRARY
	bool DemangleGNU3PluginInit()
#elif defined(DEMO_EDITION)
	bool DemangleGNU3PluginInit()
#else
	BINARYNINJAPLUGIN bool CorePluginInit()
#endif
	{
		static GNU3Demangler* demangler = new GNU3Demangler();
		Demangler::Register(demangler);
		return true;
	}
}
