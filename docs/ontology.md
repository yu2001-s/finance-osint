# Ontology

The ontology defines the vocabulary used by claims, metrics, and relationships.
Use registered terms when they fit. Propose new terms only when the current
vocabulary cannot represent the evidence without losing meaning.

## Ontology Directories

```text
ontology/claim-predicates/
ontology/metric-definitions/
ontology/relationship-types/
ontology/*/proposals/
```

Registered records use `state: registered`. Proposed records use
`state: proposed` and should live under a `proposals/` directory when they are
not ready for registration.

## Claim Predicates

Claim predicates classify narrow assertions. Registered predicates currently
include:

```text
disclosed_relationship
forecast_statement
legal_action
management_statement
market_signal
observed_event
ownership_disclosure
product_signal
regulatory_action
reported_metric
source_attestation
transaction_disclosure
```

Use the narrowest predicate that matches the evidence. Social posts and
management statements can support attribution claims about what was said; they
do not automatically prove the underlying business fact.

If a predicate is missing, add a proposed predicate and reference it from the
claim with `proposed_predicate_definition`.

## Metric Definitions

Metric definitions constrain numeric records. Registered definitions currently
include:

```text
allocation_share_percent
backlog_value
customer_concentration_percent
gross_margin
market_cap
opportunity_pipeline_value
ownership_percent
price_to_sales_ratio
revenue
shares_outstanding
unit_shipments
```

Metrics must use the definition's allowed units, value basis, period/as-of
requirements, and contextual dimensions. Keep comparability explicit for
currency, accounting standard, consolidation scope, fiscal period, reporting
basis, and calculation method.

## Relationship Types

Relationship types define graph edges and n-ary relationships among entities.
Registered types currently include:

```text
capacity_expansion_for
competitor_relationship
customer_relationship
design_win
development_partnership
manufactures_product
manufacturing_partner
ownership_relationship
product_dependency
qualified_supplier
regulatory_exposure
substitutes_for
supplier_relationship
supports_architecture
technology_dependency
uses_component
```

Relationship instances are checked against their type definition:

- participant roles must be allowed
- participant role cardinality must fit the type
- participant entity types must match each role
- scope keys must be allowed
- qualifiers must be allowed
- materiality values must be allowed
- evidence-required types need supporting evidence or claims

## Supply-Chain Guidance

Use precise relationship types when evidence supports them:

- `supplier_relationship` and `customer_relationship`: broad buyer-seller
  relationships.
- `qualified_supplier`: approval, qualification, or AVL-like status.
- `design_win`: a product, component, technology, or service designed into a
  customer product or program.
- `manufacturing_partner`: foundry, contract manufacturing, assembly,
  packaging, or test relationship.
- `uses_component`: product, architecture, or component composition.
- `capacity_expansion_for`: capacity tied to output, market, customer, item, or
  timing.
- `supports_architecture`: product, component, or technology support for an
  architecture.
- `substitutes_for`: functional or economic substitution.

Do not turn broad product fit, ecosystem membership, segment revenue, social
attention, or valuation movement into a named customer, supplier, design-win,
qualified-supplier, or revenue-allocation edge. Add a question or challenge for
the missing bridge.

## Provisional Relationship Types

Use a provisional relationship type when existing types cannot represent the
relationship:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: ontology/relationship-types/proposals/critical_tooling_dependency.yml
```

The proposed ontology record should define:

- label and description
- directionality
- participant roles
- allowed entity types per role
- required evidence
- allowed scope keys
- allowed qualifiers
- materiality values
- examples and non-examples

Reviewers may register, rename, merge, narrow, broaden, or reject provisional
terms.

## Promotion Checklist

Before using a strong relationship type, ask:

- Does the evidence name the participants?
- Does it name the item, program, product, architecture, or market scope?
- Does it support the selected relationship type rather than a weaker one?
- Is timing clear enough for the relationship?
- Is materiality stated, observed, inferred, estimated, or unknown?
- Are revenue, allocation, order value, or qualification claims separated into
  metrics, events, questions, or challenges when not directly supported?

If any answer is no, narrow the relationship or keep the gap visible.
