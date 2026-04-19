use thiserror::Error;

/// A marker type for workflow registration errors
#[derive(Debug, Error)]
#[error("Failed to register workflow activity")]
pub struct WorkflowRegistrationError;

impl From<()> for WorkflowRegistrationError {
    fn from(_: ()) -> Self {
        WorkflowRegistrationError
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ILLevel {
    Low,
    Medium,
    High,
}

#[derive(Error, Debug)]
pub enum Error {
    #[error("Unable to retrieve {level:?} IL for function at {func_start:#x}")]
    MissingIL { level: ILLevel, func_start: u64 },

    #[error("Unable to retrieve {level:?} SSA IL for function at {func_start:#x}")]
    MissingSsaForm { level: ILLevel, func_start: u64 },

    #[error("Unexpected LLIL operation at address {address:#x} (expected {expected})")]
    UnexpectedLlilOperation { address: u64, expected: String },

    #[error("Invalid selector at address {address:#x}")]
    InvalidSelector { address: u64 },

    #[error(transparent)]
    WorkflowRegistrationFailed(#[from] WorkflowRegistrationError),
}
