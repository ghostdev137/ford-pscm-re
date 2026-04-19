use binaryninja::{function::InlineDuringAnalysis, workflow::AnalysisContext};

use crate::{metadata::GlobalState, Error};

// If this function is within a section known to contain Objective-C stubs,
// mark it as being inlined during analysis.
pub fn process(ac: &AnalysisContext) -> Result<(), Error> {
    let view = ac.view();
    if GlobalState::should_ignore_view(&view) {
        return Ok(());
    }

    let func = ac.function();
    let Some(objc_stubs) = GlobalState::analysis_info(&view)
        .as_ref()
        .and_then(|info| info.objc_stubs.clone())
    else {
        return Ok(());
    };

    if objc_stubs.contains(&func.start()) {
        func.set_auto_inline_during_analysis(InlineDuringAnalysis::InlineUsingCallAddress);
    }

    Ok(())
}
