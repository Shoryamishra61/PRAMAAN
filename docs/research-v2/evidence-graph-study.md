# Evidence graph study

## Representation

- **DESIGN DECISION:** A case graph is an auditable intermediate representation even when no GNN is used.

```text
Nodes: payment, refund, order, return, policy, communication,
       evidence_document, grounded_claim, event

Edges: refers_to, promises, supports, contradicts, same_amount_as,
       same_payment_as, precedes, generated_from, governed_by, settles
```

- **DESIGN DECISION:** Every learned node/edge retains `document_id`, exact quote, character offsets, extractor version and grounding status.
- **DESIGN DECISION:** Every deterministic node/edge retains source system, record ID, observed timestamp, completeness flag and content digest.

## Four-arm experiment

1. **DESIGN DECISION:** Flat rules: current deterministic features and lexical claims.
2. **DESIGN DECISION:** Flat semantic: sentence/span model over individual documents.
3. **DESIGN DECISION:** Structured graph: deterministic typed nodes/edges plus relational feature classifier.
4. **DESIGN DECISION:** Learned graph: GraphSAGE/GAT/HGT only after the structured graph earns lift and scale gates pass.

## Why the current graph is not yet a GNN dataset

- **RESEARCH RESULT:** Graph-fraud literature such as CARE-GNN, PC-GNN, xFraud and SEFraud obtains value from repeated cross-entity topology and large collections of labeled nodes/transactions.
- **FACT:** The current benchmark contains independent synthetic dispute cases and does not establish stable cross-case entity edges or enough labeled graph diversity.
- **DESIGN DECISION:** A visual evidence graph may be built for causal inspection, but no learned-graph performance claim is allowed from it.

## Graph-specific evaluation

- **DESIGN DECISION:** edge-label micro/macro F1 and exact provenance coverage.
- **DESIGN DECISION:** case-level false PASS/BLOCK and expected loss.
- **DESIGN DECISION:** graph deletion/insertion fidelity: remove the cited edge and verify the model score/finding changes in the expected direction.
- **DESIGN DECISION:** counterfactual repair consistency: add a matching refund node and verify only causally dependent findings change.
- **DESIGN DECISION:** component-level split to prevent the same merchant/payment/refund neighborhood crossing folds.
- **DESIGN DECISION:** latency and memory compared with relational features.

## Kill criteria

- **DESIGN DECISION:** Kill the GNN if flat relational features match it within the paired uncertainty interval.
- **DESIGN DECISION:** Kill the graph branch if edges are produced solely by the labels they predict.
- **DESIGN DECISION:** Kill any explanation that cannot map to exact source evidence or whose removal has no material influence.

