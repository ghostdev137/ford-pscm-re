mod function_type;
mod name;
mod type_reconstruction;

use binaryninja::architecture::CoreArchitecture;
use binaryninja::binary_view::BinaryView;
use binaryninja::demangle::CustomDemangler;
use binaryninja::rc::Ref;
use binaryninja::settings::{QueryOptions, Settings};
use binaryninja::types::{QualifiedName, Type};

fn should_extract_types(view: Option<&BinaryView>) -> bool {
    let mut opts = match view {
        Some(v) => QueryOptions::new_with_view(v),
        None => QueryOptions::new(),
    };
    Settings::new().get_bool_with_opts(crate::SETTING_EXTRACT_TYPES, &mut opts)
}

pub struct SwiftDemangler;

impl CustomDemangler for SwiftDemangler {
    fn is_mangled_string(&self, name: &str) -> bool {
        name.starts_with("$s")
            || name.starts_with("_$s")
            || name.starts_with("$S")
            || name.starts_with("_$S")
            || name.starts_with("$e")
            || name.starts_with("_$e")
            || name.starts_with("_T")
    }

    fn demangle(
        &self,
        arch: &CoreArchitecture,
        name: &str,
        view: Option<Ref<BinaryView>>,
    ) -> Option<(QualifiedName, Option<Ref<Type>>)> {
        let ctx = swift_demangler::Context::new();
        let symbol = swift_demangler::Symbol::parse(&ctx, name)?;

        if should_extract_types(view.as_deref()) {
            let ty = function_type::build_function_type(&symbol, arch);
            let qname = if ty.is_some() {
                name::build_short_name(&symbol)
            } else {
                None
            }
            .unwrap_or_else(|| QualifiedName::from(symbol.display()));
            Some((qname, ty))
        } else {
            let qname = QualifiedName::from(symbol.display());
            Some((qname, None))
        }
    }
}
