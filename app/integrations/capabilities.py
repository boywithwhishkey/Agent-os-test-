"""Canonical capability model for connectors.

CLAUDE.md's architecture invariant says core reasoning must speak in canonical
capabilities (`mail.message.send`, `commerce.orders.list`) rather than vendor
API names, so that swapping Gmail for Outlook is a routing change and not a
rewrite. Until now the connector catalog only carried free-text capability
labels ("Read email", "Send email") — good enough to print on a card, useless
to route on and impossible to classify by risk.

This module supplies the missing layer:

  provider capability label  ->  canonical capability id  ->  risk  ->  policy

Two rules keep it honest:

- **Declaring a capability is not implementing it.** A catalog-only connector
  still declares what it *would* expose, because that is what tells a user
  what connecting the account would eventually authorise. The API reports the
  declaration alongside `implemented`, and the UI must not present the two as
  the same thing.
- **Risk is a property of the capability, not of the provider.** Sending mail
  is high risk whether it goes through Gmail or Outlook. Classifying per
  capability is what makes the approval mapping uniform across providers.

Risk maps onto the existing `ToolRisk` ladder rather than inventing a second
vocabulary — the approval machinery in `app/tools/policy.py` already knows how
to gate READ / WRITE / HIGH_RISK, and a connector must not get a softer path
to a consequential action than a tool does.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.tools.models import ToolRisk


@dataclass(frozen=True, slots=True)
class Capability:
    """One canonical capability.

    `id` is a stable machine identifier in `domain.object.action` form and is
    never translated or renamed — workflows and tool definitions may reference
    it. `label` is an English fallback for surfaces that have no locale.
    """

    id: str
    label: str
    risk: ToolRisk


def _read(cid: str, label: str) -> Capability:
    return Capability(cid, label, ToolRisk.READ)


def _write(cid: str, label: str) -> Capability:
    return Capability(cid, label, ToolRisk.WRITE)


def _high(cid: str, label: str) -> Capability:
    return Capability(cid, label, ToolRisk.HIGH_RISK)


# The canonical vocabulary. Additions are cheap; renames are not — an id here
# is a contract with any workflow that references it.
#
# The risk column is the load-bearing part. Anything that leaves the system
# (a sent message, a published post), destroys data, moves money, or changes
# what runs in production is HIGH_RISK and therefore needs an approval the
# model cannot issue to itself. Reversible internal writes are WRITE. Reads
# are READ.
CAPABILITIES: dict[str, Capability] = {
    c.id: c
    for c in (
        # --- Identity -----------------------------------------------------
        _read("identity.account.read", "Read the connected account"),
        # --- Mail ---------------------------------------------------------
        _read("mail.message.list", "List messages"),
        _read("mail.message.read", "Read message contents"),
        _write("mail.draft.create", "Create a draft"),
        _high("mail.message.send", "Send mail"),
        # --- Calendar -----------------------------------------------------
        _read("calendar.event.list", "List calendar events"),
        _write("calendar.event.create", "Create a calendar event"),
        _write("calendar.event.update", "Update a calendar event"),
        _high("calendar.event.delete", "Delete a calendar event"),
        # --- Files --------------------------------------------------------
        _read("files.file.list", "List files"),
        _read("files.file.read", "Read file contents"),
        _write("files.file.write", "Create or update a file"),
        _high("files.file.delete", "Delete a file"),
        # --- Chat / messaging ---------------------------------------------
        _read("chat.channel.list", "List chat channels"),
        _read("chat.message.list", "Read channel messages"),
        _high("chat.message.send", "Post a message"),
        _high("chat.template.send", "Send a message template"),
        # --- Social publishing --------------------------------------------
        _high("social.post.publish", "Publish a social post"),
        # --- Documents / knowledge ----------------------------------------
        _read("docs.page.read", "Read pages"),
        _write("docs.page.write", "Create or update a page"),
        # --- Issue tracking -----------------------------------------------
        _read("tracker.issue.list", "List issues"),
        _write("tracker.issue.create", "Create an issue"),
        _write("tracker.issue.update", "Update an issue"),
        # --- Source control ------------------------------------------------
        _read("repo.metadata.read", "Read repository metadata"),
        _read("repo.content.read", "Read repository contents"),
        _write("repo.issue.create", "Open an issue or pull request"),
        _high("repo.branch.merge", "Merge a branch"),
        # --- Automation ----------------------------------------------------
        _read("automation.run.read", "Read an execution result"),
        _high("automation.workflow.trigger", "Trigger an external workflow"),
        # --- AI inference ---------------------------------------------------
        _read("ai.model.list", "List available models"),
        _write("ai.completion.create", "Run a model completion"),
        # --- Data ------------------------------------------------------------
        _read("data.record.read", "Read records"),
        _write("data.record.write", "Write records"),
        _read("data.search.semantic", "Semantic search"),
        _read("queue.job.read", "Read queued jobs"),
        _write("queue.job.enqueue", "Enqueue a job"),
        # --- CRM ---------------------------------------------------------------
        _read("crm.contact.list", "List CRM contacts"),
        _write("crm.contact.update", "Update a CRM contact"),
        _read("crm.deal.list", "List deals"),
        _read("crm.ticket.list", "List tickets"),
        # --- Commerce / payments -----------------------------------------------
        _read("commerce.payment.list", "List payments"),
        _read("commerce.subscription.list", "List subscriptions"),
        _read("commerce.product.list", "List products"),
        _read("commerce.order.list", "List orders"),
        _high("commerce.refund.create", "Issue a refund"),
        # --- Cloud / deployment -------------------------------------------------
        _read("cloud.service.read", "Read service status"),
        _read("cloud.dns.read", "Read DNS and edge configuration"),
        _high("cloud.deploy.trigger", "Trigger a deployment"),
        # --- Auth / storage platforms --------------------------------------------
        _read("auth.user.list", "List authenticated users"),
    )
}


class UnknownCapability(KeyError):
    """Raised when a connector declares a capability id that is not canonical.

    Deliberately fatal at import/test time rather than silently skipped: a
    typo'd id would otherwise vanish from the UI and, worse, from the risk
    classification — which is the one thing here that must never fail open.
    """


def resolve(capability_id: str) -> Capability:
    try:
        return CAPABILITIES[capability_id]
    except KeyError as exc:  # pragma: no cover - exercised via resolve_all
        raise UnknownCapability(capability_id) from exc


def resolve_all(capability_ids: list[str]) -> list[Capability]:
    return [resolve(cid) for cid in capability_ids]


def requires_approval(capability: Capability) -> bool:
    """Whether acting on this capability needs a human approval.

    Mirrors `ToolPolicy.authorize` exactly: READ passes, everything else needs
    a grant. Kept as one expression so the UI's "requires approval" list can
    never drift from what the policy actually enforces.
    """
    return capability.risk != ToolRisk.READ
