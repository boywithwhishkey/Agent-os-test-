"""The canonical capability layer — the thing every connector routes through.

These tests exist because the failure modes here are silent. A typo'd
capability id, a capability nobody classified, or a UI that lists "requires
approval" from its own hardcoded guess would all still render a perfectly
convincing connector page while quietly misrepresenting what THYNACT is
authorised to do with someone's account.
"""

from __future__ import annotations

import pytest

from app.integrations.capabilities import (
    CAPABILITIES,
    UnknownCapability,
    requires_approval,
    resolve,
    resolve_all,
)
from app.integrations.catalog import list_catalog
from app.integrations.models import ConnectorKind
from app.tools.approvals import InMemoryApprovalStore
from app.tools.models import ToolRisk
from app.tools.policy import ToolPolicy


def test_every_catalog_entry_declares_only_canonical_capabilities() -> None:
    # A typo'd id must fail loudly here rather than disappear from the UI and
    # from the risk classification.
    for spec in list_catalog():
        assert spec.canonical_capabilities, f"{spec.id} declares no capabilities"
        resolve_all(spec.canonical_capabilities)


def test_unknown_capability_raises_rather_than_defaulting() -> None:
    # Failing open would hand an unclassified capability the READ path.
    with pytest.raises(UnknownCapability):
        resolve("mail.message.launch_missiles")


def test_capability_ids_are_dotted_machine_identifiers() -> None:
    for cid in CAPABILITIES:
        assert cid == cid.lower(), cid
        assert cid.count(".") >= 1, cid
        assert " " not in cid, cid


@pytest.mark.parametrize(
    "capability_id",
    [
        "mail.message.send",
        "chat.message.send",
        "calendar.event.delete",
        "files.file.delete",
        "repo.branch.merge",
        "commerce.refund.create",
        "cloud.deploy.trigger",
        "automation.workflow.trigger",
    ],
)
def test_consequential_capabilities_are_high_risk(capability_id: str) -> None:
    # CLAUDE.md: sending, publishing, deleting, merging, refunding and
    # deploying are never things a model may do on its own recognisance.
    assert resolve(capability_id).risk is ToolRisk.HIGH_RISK


@pytest.mark.parametrize(
    "capability_id",
    ["identity.account.read", "mail.message.read", "calendar.event.list", "repo.content.read"],
)
def test_reads_do_not_require_approval(capability_id: str) -> None:
    assert requires_approval(resolve(capability_id)) is False


@pytest.mark.anyio
async def test_requires_approval_matches_what_the_policy_actually_enforces() -> None:
    """The UI's "requires approval" list is derived, not authored.

    If these two ever disagree, the connector page tells a user an action is
    gated while the policy waves it through — the worst possible direction for
    the discrepancy to run.
    """
    policy = ToolPolicy(InMemoryApprovalStore())
    for capability in CAPABILITIES.values():
        decision = await policy.authorize(tool_name=capability.id, risk=capability.risk)
        assert decision.approval_required == requires_approval(capability), capability.id


def test_every_catalog_capability_is_backed_by_an_adapter_foundation() -> None:
    """The connector catalog has no metadata-only entries at this checkpoint.

    Implemented means a real adapter foundation and focused tests exist; it
    does not mean every declared mutation is enabled or live-credentialed.
    """
    catalog = list_catalog()
    declared_and_built = [s for s in catalog if s.canonical_capabilities and s.implemented]
    declared_not_built = [s for s in catalog if s.canonical_capabilities and not s.implemented]
    assert declared_and_built
    assert declared_not_built == []


def test_thynacts_own_infrastructure_is_not_presented_as_a_user_connector() -> None:
    # PostgreSQL and Redis are the running system, not an account anyone
    # connects. Listing them as ordinary SaaS inflates the connector count and
    # invites an operator to "connect" something already in use.
    kinds = {s.id: s.kind for s in list_catalog()}
    assert kinds["postgresql"] is ConnectorKind.SYSTEM_INFRASTRUCTURE
    assert kinds["redis"] is ConnectorKind.SYSTEM_INFRASTRUCTURE
    assert kinds["slack"] is ConnectorKind.USER_CONNECTOR
    assert kinds["stripe"] is ConnectorKind.USER_CONNECTOR
