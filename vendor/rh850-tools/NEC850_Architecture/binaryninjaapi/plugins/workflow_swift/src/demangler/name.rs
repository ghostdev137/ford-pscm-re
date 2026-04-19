use binaryninja::types::QualifiedName;
use swift_demangler::{ConstructorKind, DestructorKind, HasModule, Symbol};

/// Push a module name into the name parts, skipping `__C` (Swift's internal
/// module for C/Objective-C imports).
fn push_module(parts: &mut Vec<String>, module: Option<&str>) {
    if let Some(m) = module {
        if m != "__C" {
            parts.push(m.to_string());
        }
    }
}

/// Build a qualified name from a symbol's components, omitting parameter types
/// and return type since those are represented directly in the function's type
///
/// Returns `None` for symbol kinds that don't benefit from shortening (e.g.
/// variables, thunks), in which case the caller should fall back to `symbol.display()`.
pub fn build_short_name(symbol: &swift_demangler::Symbol) -> Option<QualifiedName> {
    let mut parts: Vec<String> = Vec::new();

    match symbol {
        Symbol::Function(f) => {
            push_module(&mut parts, f.module());
            if let Some(ct) = f.containing_type() {
                parts.push(ct.to_string());
            }
            parts.push(f.full_name());
        }
        Symbol::Constructor(c) => {
            push_module(&mut parts, c.module());
            if let Some(ct) = c.containing_type() {
                parts.push(ct.to_string());
            }
            let init_name = match c.kind() {
                ConstructorKind::Allocating => "__allocating_init",
                ConstructorKind::Regular => "init",
            };
            let labels: Vec<String> = c
                .labels()
                .iter()
                .map(|l| {
                    l.map(|s| format!("{s}:"))
                        .unwrap_or_else(|| "_:".to_string())
                })
                .collect();
            parts.push(format!("{init_name}({})", labels.join("")));
        }
        Symbol::Destructor(d) => {
            push_module(&mut parts, d.module());
            if let Some(ct) = d.containing_type() {
                parts.push(ct.to_string());
            }
            let deinit_name = match d.kind() {
                DestructorKind::Deallocating => "__deallocating_deinit",
                DestructorKind::IsolatedDeallocating => "__isolated_deallocating_deinit",
                DestructorKind::Regular => "deinit",
            };
            parts.push(deinit_name.to_string());
        }
        // Wrappers: combine the wrapper's display with the inner function's short name.
        Symbol::Attributed(_) | Symbol::Specialization(_) => {
            let inner = match symbol {
                Symbol::Attributed(a) => &*a.inner,
                Symbol::Specialization(s) => &*s.inner,
                _ => unreachable!(),
            };
            return build_short_name(inner).map(|inner_name| {
                QualifiedName::from(format!("{}{}", symbol.display(), inner_name))
            });
        }
        Symbol::Suffixed(s) => {
            return build_short_name(&s.inner)
                .map(|inner_name| QualifiedName::from(format!("{} {}", inner_name, s.suffix)));
        }
        _ => return None,
    }

    if parts.is_empty() {
        return None;
    }

    Some(QualifiedName::from(parts.join(".")))
}
