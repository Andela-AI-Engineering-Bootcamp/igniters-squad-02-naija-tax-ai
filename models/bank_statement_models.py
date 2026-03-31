from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BankTransaction(BaseModel):
    """Extract a single row from the statement transaction table."""

    date: str = Field(
        ...,
        description="Transaction date, preferably YYYY-MM-DD.",
    )
    description: str = Field(..., description="Transaction narration or description.")
    deposit: float = Field(
        ...,
        description="Credit amount for this row; use 0.0 if none.",
    )
    withdrawal: float = Field(
        ...,
        description="Debit amount for this row; use 0.0 if none.",
    )
    balance: float = Field(..., description="Account balance after this transaction.")


class BankStatementSummary(BaseModel):
    """Header and transaction list extracted from a bank statement PDF."""

    model_config = ConfigDict(populate_by_name=True)

    account_holder: str = Field(
        ...,
        description="Name of the account holder.",
        max_length=100,
    )
    branch: str = Field(..., description="Bank branch name or code.", max_length=100)
    account_no: str = Field(..., description="Account number.")
    account_type: str = Field(..., description="Account type (e.g. savings, current).")
    currency: Optional[str] = Field(
        default=None,
        description="Account currency (e.g. NGN).",
    )
    statement_date: Optional[str] = Field(
        default=None,
        description="Statement period end or print date if shown.",
    )
    branch_address: Optional[str] = Field(
        default=None,
        description="Bank branch address if present.",
    )
    transactions: list[BankTransaction] = Field(default_factory=list)


class BankStatementDocument(BaseModel):
    """Top-level bank statement structure for structured extraction."""

    bank_statement_summary: BankStatementSummary
