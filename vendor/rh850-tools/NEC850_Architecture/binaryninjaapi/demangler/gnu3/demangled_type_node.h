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

#pragma once

#ifdef BINARYNINJACORE_LIBRARY
#include "qualifiedname.h"
#include "type.h"
#include "architecture.h"
#ifndef BN
#define BN BinaryNinjaCore
#endif
#ifndef _STD_STRING
#define _STD_STRING BinaryNinjaCore::string
#endif
#ifndef _STD_VECTOR
#define _STD_VECTOR BinaryNinjaCore::vector
#endif
#else
#include "binaryninjaapi.h"
#ifndef BN
#define BN BinaryNinja
#endif
#ifndef _STD_STRING
#define _STD_STRING std::string
#endif
#ifndef _STD_VECTOR
#define _STD_VECTOR std::vector
#endif
#endif

#include <memory>
#ifdef BINARYNINJACORE_LIBRARY
#include "binaryninjacore_global.h"
#define _STD_SET BinaryNinjaCore::set
#else
#include <set>
#define _STD_SET std::set
#endif

// Lightweight type representation for the GNU3 demangler.
// This object serves as an abstraction layer between C++'s type system and our own.
// It also removes a source of a lot of reallocation of NamedTypeReference BinaryNinja::Type objects
// and only creates real Type objects when Finalize() is called.
class DemangledTypeNode
{
public:
	struct Param
	{
		_STD_STRING name;
		std::shared_ptr<DemangledTypeNode> type;
	};

	DemangledTypeNode();
	DemangledTypeNode(const DemangledTypeNode&) = default;
	DemangledTypeNode(DemangledTypeNode&&) = default;
	DemangledTypeNode& operator=(const DemangledTypeNode&) = default;
	DemangledTypeNode& operator=(DemangledTypeNode&&) = default;

	// Static factory methods matching TypeBuilder's interface
	static DemangledTypeNode VoidType();
	static DemangledTypeNode BoolType();
	static DemangledTypeNode IntegerType(size_t width, bool isSigned, const _STD_STRING& altName = "");
	static DemangledTypeNode FloatType(size_t width, const _STD_STRING& altName = "");
	static DemangledTypeNode VarArgsType();
	static DemangledTypeNode PointerType(BN::Architecture* arch, DemangledTypeNode child,
		bool cnst, bool vltl, BNReferenceType refType);
	static DemangledTypeNode ArrayType(DemangledTypeNode child, uint64_t count);
	static DemangledTypeNode FunctionType(DemangledTypeNode retType,
		std::nullptr_t, _STD_VECTOR<Param> params);
	static DemangledTypeNode NamedType(BNNamedTypeReferenceClass cls,
		_STD_VECTOR<_STD_STRING> nameSegments, size_t width = 0, size_t align = 0);
	static DemangledTypeNode NamedType(BNNamedTypeReferenceClass cls,
		const BN::QualifiedName& name, size_t width = 0, size_t align = 0);

	// Getters
	BNTypeClass GetClass() const { return m_typeClass; }
#ifdef BINARYNINJACORE_LIBRARY
	BNTypeClass GetTypeClass() const { return m_typeClass; }
#endif
	const _STD_VECTOR<_STD_STRING>& GetTypeName() const
	{
		if (!m_nameSegments)
		{
			static const _STD_VECTOR<_STD_STRING> empty;
			return empty;
		}
		return *m_nameSegments;
	}
	_STD_VECTOR<_STD_STRING>& GetMutableTypeName()
	{
		if (!m_nameSegments)
			m_nameSegments = std::make_shared<_STD_VECTOR<_STD_STRING>>();
		else if (m_nameSegments.use_count() > 1)
			m_nameSegments = std::make_shared<_STD_VECTOR<_STD_STRING>>(*m_nameSegments);
		return *m_nameSegments;
	}
	_STD_STRING GetTypeNameString() const;
	size_t NameStringSize() const;
	bool IsConst() const { return m_const; }
	bool IsVolatile() const { return m_volatile; }
	BNNameType GetNameType() const { return m_nameType; }
	bool HasTemplateArguments() const { return m_hasTemplateArgs; }
	const _STD_SET<BNPointerSuffix>& GetPointerSuffix() const { return m_pointerSuffix; }
	BNNamedTypeReferenceClass GetNTRClass() const { return m_ntrClass; }

	// Setters
	void SetTypeName(_STD_VECTOR<_STD_STRING> name) { m_nameSegments = std::make_shared<_STD_VECTOR<_STD_STRING>>(std::move(name)); }
	void SetConst(bool c) { m_const = c; }
	void SetVolatile(bool v) { m_volatile = v; }
	void SetNameType(BNNameType nt) { m_nameType = nt; }
	void SetHasTemplateArguments(bool t) { m_hasTemplateArgs = t; }
	void SetPointerSuffix(const _STD_SET<BNPointerSuffix>& s) { m_pointerSuffix = s; }
	void AddPointerSuffix(BNPointerSuffix ps) { m_pointerSuffix.insert(ps); }
	void SetReturnTypeConfidence(uint8_t c) { m_returnTypeConfidence = c; }

	// Named type reference operations
	void SetNTR(BNNamedTypeReferenceClass cls, _STD_VECTOR<_STD_STRING> nameSegments);
	void SetNTR(BNNamedTypeReferenceClass cls, const BN::QualifiedName& name);

	// String formatting
	_STD_STRING GetString() const;
	_STD_STRING GetStringBeforeName() const;
	_STD_STRING GetStringAfterName() const;
	_STD_STRING GetTypeAndName(const BN::QualifiedName& name) const;

	// Conversion to real Type
	BN::Ref<BN::Type> Finalize() const;

private:
	BNTypeClass m_typeClass;
	size_t m_width;
	size_t m_alignment;
	bool m_const;
	bool m_volatile;
	bool m_signed;
	bool m_hasTemplateArgs;
	BNNameType m_nameType;
	_STD_SET<BNPointerSuffix> m_pointerSuffix;
	_STD_STRING m_altName;

	// Named type ref data
	BNNamedTypeReferenceClass m_ntrClass;
	std::shared_ptr<_STD_VECTOR<_STD_STRING>> m_nameSegments;

	// Child type (for pointer/array/function return)
	std::shared_ptr<DemangledTypeNode> m_childType;
	BNReferenceType m_pointerReference;
	uint64_t m_elements;

	// Function params
	_STD_VECTOR<Param> m_params;
	uint8_t m_returnTypeConfidence;

	// Helpers for string formatting
	_STD_STRING GetModifierString() const;
	_STD_STRING GetPointerSuffixString() const;
	void AppendBeforeName(_STD_STRING& out, const DemangledTypeNode* parentType = nullptr) const;
	void AppendAfterName(_STD_STRING& out, const DemangledTypeNode* parentType = nullptr) const;
};
