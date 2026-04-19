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

#include "demangled_type_node.h"
#include <cinttypes>

#ifdef BINARYNINJACORE_LIBRARY
using namespace BinaryNinjaCore;
#define GetClass GetTypeClass
#else
using namespace BinaryNinja;
using namespace std;
#endif


DemangledTypeNode::DemangledTypeNode()
	: m_typeClass(VoidTypeClass), m_width(0), m_alignment(0),
	  m_const(false), m_volatile(false), m_signed(false),
	  m_hasTemplateArgs(false), m_nameType(NoNameType),
	  m_ntrClass(UnknownNamedTypeClass),
	  m_pointerReference(PointerReferenceType), m_elements(0),
	  m_returnTypeConfidence(BN_DEFAULT_CONFIDENCE)
{
}


DemangledTypeNode DemangledTypeNode::VoidType()
{
	DemangledTypeNode n;
	n.m_typeClass = VoidTypeClass;
	return n;
}


DemangledTypeNode DemangledTypeNode::BoolType()
{
	DemangledTypeNode n;
	n.m_typeClass = BoolTypeClass;
	n.m_width = 1;
	return n;
}


DemangledTypeNode DemangledTypeNode::IntegerType(size_t width, bool isSigned, const string& altName)
{
	DemangledTypeNode n;
	n.m_typeClass = IntegerTypeClass;
	n.m_width = width;
	n.m_signed = isSigned;
	n.m_altName = altName;
	return n;
}


DemangledTypeNode DemangledTypeNode::FloatType(size_t width, const string& altName)
{
	DemangledTypeNode n;
	n.m_typeClass = FloatTypeClass;
	n.m_width = width;
	n.m_altName = altName;
	return n;
}


DemangledTypeNode DemangledTypeNode::VarArgsType()
{
	DemangledTypeNode n;
	n.m_typeClass = VarArgsTypeClass;
	return n;
}


DemangledTypeNode DemangledTypeNode::PointerType(Architecture* arch, DemangledTypeNode child,
	bool cnst, bool vltl, BNReferenceType refType)
{
	DemangledTypeNode n;
	n.m_typeClass = PointerTypeClass;
	n.m_width = arch->GetAddressSize();
	n.m_childType = std::make_shared<DemangledTypeNode>(std::move(child));
	n.m_const = cnst;
	n.m_volatile = vltl;
	n.m_pointerReference = refType;
	return n;
}


DemangledTypeNode DemangledTypeNode::ArrayType(DemangledTypeNode child, uint64_t count)
{
	DemangledTypeNode n;
	n.m_typeClass = ArrayTypeClass;
	n.m_childType = std::make_shared<DemangledTypeNode>(std::move(child));
	n.m_elements = count;
	return n;
}


DemangledTypeNode DemangledTypeNode::FunctionType(DemangledTypeNode retType,
	std::nullptr_t, vector<Param> params)
{
	DemangledTypeNode n;
	n.m_typeClass = FunctionTypeClass;
	n.m_childType = std::make_shared<DemangledTypeNode>(std::move(retType));
	n.m_params = std::move(params);
	return n;
}


DemangledTypeNode DemangledTypeNode::NamedType(BNNamedTypeReferenceClass cls,
	vector<string> nameSegments, size_t width, size_t align)
{
	DemangledTypeNode n;
	n.m_typeClass = NamedTypeReferenceClass;
	n.m_ntrClass = cls;
	n.m_nameSegments = std::make_shared<vector<string>>(std::move(nameSegments));
	n.m_width = width;
	n.m_alignment = align;
	return n;
}


DemangledTypeNode DemangledTypeNode::NamedType(BNNamedTypeReferenceClass cls,
	const QualifiedName& name, size_t width, size_t align)
{
	return NamedType(cls, vector<string>(name.begin(), name.end()), width, align);
}


void DemangledTypeNode::SetNTR(BNNamedTypeReferenceClass cls, vector<string> nameSegments)
{
	m_ntrClass = cls;
	m_nameSegments = std::make_shared<vector<string>>(std::move(nameSegments));
}


void DemangledTypeNode::SetNTR(BNNamedTypeReferenceClass cls, const QualifiedName& name)
{
	SetNTR(cls, vector<string>(name.begin(), name.end()));
}


string DemangledTypeNode::GetTypeNameString() const
{
	if (!m_nameSegments)
		return {};
	const auto& segs = *m_nameSegments;
	size_t n = segs.size();
	if (n == 0)
		return {};
	if (n == 1)
		return segs[0];

	// Pre-reserve: sum of segments + (n-1) * 2 for "::" separators
	size_t total = (n - 1) * 2;
	for (const auto& s : segs)
		total += s.size();

	string result;
	result.reserve(total);
	result += segs[0];
	for (size_t i = 1; i < n; i++)
	{
		result += "::";
		result += segs[i];
	}
	return result;
}


size_t DemangledTypeNode::NameStringSize() const
{
	if (!m_nameSegments)
		return 0;
	size_t total = 0;
	for (const auto& s : *m_nameSegments)
		total += s.size();
	return total;
}


string DemangledTypeNode::GetModifierString() const
{
	if (m_const && m_volatile)
		return "const volatile";
	if (m_const)
		return "const";
	if (m_volatile)
		return "volatile";
	return "";
}


string DemangledTypeNode::GetPointerSuffixString() const
{
	static const char* suffixStrings[] = {
		"__ptr64",
		"__unaligned",
		"__restrict",
		"&",
		"&&"
	};

	string out;
	for (auto& s : m_pointerSuffix)
	{
		if (!out.empty() && out.back() != ' ')
			out += ' ';
		out += suffixStrings[s];
	}
	return out;
}


string DemangledTypeNode::GetStringBeforeName() const
{
	string out;
	AppendBeforeName(out);
	return out;
}


string DemangledTypeNode::GetStringAfterName() const
{
	string out;
	AppendAfterName(out);
	return out;
}


void DemangledTypeNode::AppendBeforeName(string& out, const DemangledTypeNode* parentType) const
{
	string modifiers = GetModifierString();
	string ptrSuffix = GetPointerSuffixString();

	switch (m_typeClass)
	{
	case FunctionTypeClass:
		// Return type before name
		if (m_childType)
		{
			if (!out.empty() && out.back() != ' ')
				out += " ";
			m_childType->AppendBeforeName(out, this);
		}
		// If parent is a pointer, add "(" for function pointer syntax
		if (parentType && parentType->m_typeClass == PointerTypeClass)
		{
			if (!out.empty() && out.back() != ' ')
				out += " ";
			out += "(";
		}
		break;

	case IntegerTypeClass:
		if (!m_altName.empty())
			out += m_altName;
		else if (m_signed && m_width == 1)
			out += "char";
		else if (m_signed)
			out += "int" + to_string(m_width * 8) + "_t";
		else
			out += "uint" + to_string(m_width * 8) + "_t";
		if (!modifiers.empty())
			out += " " + modifiers;
		break;

	case FloatTypeClass:
		if (!m_altName.empty())
			out += m_altName;
		else switch (m_width)
		{
		case 2: out += "float16"; break;
		case 4: out += "float"; break;
		case 8: out += "double"; break;
		case 10: out += "long double"; break;
		default: out += "float" + to_string(m_width * 8); break;
		}
		if (!modifiers.empty())
			out += " " + modifiers;
		break;

	case BoolTypeClass:
		out += "bool";
		if (!modifiers.empty())
			out += " " + modifiers;
		break;

	case VoidTypeClass:
		out += "void";
		if (!modifiers.empty())
			out += " " + modifiers;
		break;

	case VarArgsTypeClass:
		out += "...";
		break;

	case PointerTypeClass:
		if (m_childType)
			m_childType->AppendBeforeName(out, this);
		switch (m_pointerReference)
		{
		case ReferenceReferenceType: out += "&"; break;
		case PointerReferenceType:   out += "*"; break;
		case RValueReferenceType:    out += "&&"; break;
		default: break;
		}
		if (!ptrSuffix.empty())
			out += " " + ptrSuffix;
		if (!modifiers.empty())
			out += " " + modifiers;
		break;

	case ArrayTypeClass:
		if (m_childType)
			m_childType->AppendBeforeName(out, this);
		if (parentType && parentType->m_typeClass == PointerTypeClass)
		{
			out += " (";
		}
		break;

	case NamedTypeReferenceClass:
		switch (m_ntrClass)
		{
		case ClassNamedTypeClass:  out += "class "; break;
		case StructNamedTypeClass: out += "struct "; break;
		case UnionNamedTypeClass:  out += "union "; break;
		case EnumNamedTypeClass:   out += "enum "; break;
		default: break;
		}
		out += GetTypeNameString();
		if (!modifiers.empty())
			out += " " + modifiers;
		break;

	default:
		break;
	}
}


static string FormatArrayCount(uint64_t elements)
{
	return string(fmt::format("{:#x}", elements));
}


void DemangledTypeNode::AppendAfterName(string& out, const DemangledTypeNode* parentType) const
{
	string modifiers = GetModifierString();
	string ptrSuffix = GetPointerSuffixString();

	switch (m_typeClass)
	{
	case FunctionTypeClass:
	{
		// Close the "(" from before-name if parent is pointer
		if (parentType && parentType->m_typeClass == PointerTypeClass)
			out += ")";

		out += "(";
		for (size_t i = 0; i < m_params.size(); i++)
		{
			if (i != 0)
				out += ", ";
			if (m_params[i].type)
				out += m_params[i].type->GetString();
		}
		out += ")";
		if (!modifiers.empty())
			out += " " + modifiers;
		if (!ptrSuffix.empty())
			out += ptrSuffix;
		// Return type's after-name tokens
		if (m_childType)
			m_childType->AppendAfterName(out, this);
		break;
	}
	case PointerTypeClass:
		if (m_childType)
			m_childType->AppendAfterName(out, this);
		break;
	case ArrayTypeClass:
		if (parentType && parentType->m_typeClass == PointerTypeClass)
			out += ")";
		out += "[" + FormatArrayCount(m_elements) + "]";
		if (m_childType)
			m_childType->AppendAfterName(out, this);
		break;
	default:
		break;
	}
}


string DemangledTypeNode::GetString() const
{
	const string before = GetStringBeforeName();
	const string after = GetStringAfterName();
	if (!before.empty() && !after.empty() && before.back() != ' ' && before.back() != '*'
		&& before.back() != '&' && after.front() != ' ' && after.front() != '['
		&& m_childType && m_childType->m_typeClass != FunctionTypeClass)
	{
		return before + " " + after;
	}
	return before + after;
}


string DemangledTypeNode::GetTypeAndName(const QualifiedName& name) const
{
	const string before = GetStringBeforeName();
	const string qName = name.GetString();
	const string after = GetStringAfterName();
	if ((!before.empty() && !qName.empty() && before.back() != ' ' && qName.front() != ' ')
		|| (!before.empty() && !after.empty() && before.back() != ' ' && after.front() != ' '))
		return before + " " + qName + after;
	return before + qName + after;
}


Ref<Type> DemangledTypeNode::Finalize() const
{
	switch (m_typeClass)
	{
	case VoidTypeClass:
	{
		if (!m_const && !m_volatile)
			return Type::VoidType();
		TypeBuilder tb = TypeBuilder::VoidType();
		tb.SetConst(m_const);
		tb.SetVolatile(m_volatile);
		return tb.Finalize();
	}

	case BoolTypeClass:
	{
		if (!m_const && !m_volatile)
			return Type::BoolType();
		TypeBuilder tb = TypeBuilder::BoolType();
		tb.SetConst(m_const);
		tb.SetVolatile(m_volatile);
		return tb.Finalize();
	}

	case IntegerTypeClass:
	{
		if (!m_const && !m_volatile)
			return Type::IntegerType(m_width, m_signed, m_altName);
		TypeBuilder tb = TypeBuilder::IntegerType(m_width, m_signed, m_altName);
		tb.SetConst(m_const);
		tb.SetVolatile(m_volatile);
		return tb.Finalize();
	}

	case FloatTypeClass:
	{
		if (!m_const && !m_volatile)
			return Type::FloatType(m_width, m_altName);
		TypeBuilder tb = TypeBuilder::FloatType(m_width, m_altName);
		tb.SetConst(m_const);
		tb.SetVolatile(m_volatile);
		return tb.Finalize();
	}

	case VarArgsTypeClass:
		return TypeBuilder::VarArgsType().Finalize();

	case PointerTypeClass:
	{
		Ref<Type> child = m_childType ? m_childType->Finalize() : Ref<Type>(Type::VoidType());
		return TypeBuilder::PointerType(m_width, child, m_const, m_volatile, m_pointerReference).Finalize();
	}

	case ArrayTypeClass:
	{
		Ref<Type> child = m_childType ? m_childType->Finalize() : Ref<Type>(Type::VoidType());
		TypeBuilder tb = TypeBuilder::ArrayType(child, m_elements);
		if (m_const)
			tb.SetConst(m_const);
		if (m_volatile)
			tb.SetVolatile(m_volatile);
		return tb.Finalize();
	}

	case FunctionTypeClass:
	{
		Ref<Type> retType = m_childType ? m_childType->Finalize() : Ref<Type>(Type::VoidType());
		vector<FunctionParameter> finalParams;
		finalParams.reserve(m_params.size());
		for (auto& p : m_params)
		{
			Ref<Type> pType = p.type ? p.type->Finalize() : Ref<Type>(Type::VoidType());
			finalParams.push_back({p.name, pType, true, Variable()});
		}
		TypeBuilder tb = TypeBuilder::FunctionType(retType->WithConfidence(m_returnTypeConfidence), nullptr, finalParams);
		tb.SetConst(m_const);
		tb.SetVolatile(m_volatile);
		for (auto ps : m_pointerSuffix)
			tb.AddPointerSuffix(ps);
		tb.SetNameType(m_nameType);
		return tb.Finalize();
	}

	case NamedTypeReferenceClass:
	{
		TypeBuilder tb = TypeBuilder::NamedType(
			NamedTypeReference::GenerateAutoDemangledTypeReference(
				m_ntrClass, QualifiedName(m_nameSegments ? *m_nameSegments : vector<string>{})),
			m_width, m_alignment > 0 ? m_alignment : 1);
		tb.SetConst(m_const);
		tb.SetVolatile(m_volatile);
		for (auto ps : m_pointerSuffix)
			tb.AddPointerSuffix(ps);
		tb.SetNameType(m_nameType);
		tb.SetHasTemplateArguments(m_hasTemplateArgs);
		return tb.Finalize();
	}

	default:
		return Type::VoidType();
	}
}
