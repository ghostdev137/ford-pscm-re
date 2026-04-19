use binaryninja::headless::Session;
use binaryninja::settings::Settings;
use binaryninja::workflow::Workflow;

// TODO: Test running a workflow activity
// TODO: Test activity insertion and removal

#[test]
fn test_workflow_clone() {
    let _session = Session::new().expect("Failed to initialize session");
    let original_workflow = Workflow::get("core.function.metaAnalysis").unwrap();
    let mut cloned_workflow = original_workflow
        .clone_to("clone_workflow")
        .register()
        .unwrap();

    assert_eq!(cloned_workflow.name().as_str(), "clone_workflow");
    assert_eq!(
        cloned_workflow.configuration(),
        original_workflow.configuration()
    );

    // `clone_to` with an empty name should re-use the original workflow's name.
    cloned_workflow = original_workflow.clone_to("").register().unwrap();
    assert_eq!(
        cloned_workflow.name().as_str(),
        original_workflow.name().as_str()
    );
}

#[test]
fn test_workflow_registration() {
    let _session = Session::new().expect("Failed to initialize session");

    // Validate new workflows can be registered
    let test_workflow = Workflow::get("core.function.baseAnalysis")
        .unwrap()
        .clone_to("test_workflow");

    let test_workflow = test_workflow
        .register()
        .expect("Failed to register workflow");
    assert!(test_workflow.registered());
    assert_eq!(
        test_workflow.size(),
        Workflow::get("core.function.baseAnalysis").unwrap().size()
    );
    Workflow::list()
        .iter()
        .find(|w| w.name() == test_workflow.name())
        .expect("Workflow not found in list");
    Settings::new()
        .get_property_string_list("analysis.workflows.functionWorkflow", "enum")
        .iter()
        .find(|&w| w == "test_workflow")
        .expect("Workflow not found in settings");
    assert!(Workflow::get("test_workflow").is_some());

    // Validate re-registration of baseAnalysis is not allowed
    let base_workflow_clone = Workflow::cloned("core.function.baseAnalysis").unwrap();
    base_workflow_clone
        .register()
        .map(|_| ())
        .expect_err("Re-registration of baseAnalysis is allowed");
}
