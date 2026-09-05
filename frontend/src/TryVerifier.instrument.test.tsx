import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { TryVerifier } from "./TryVerifier";

afterEach(() => vi.unstubAllGlobals());

function sandbox(status: "PASS" | "BLOCK") {
  const mismatch = status === "BLOCK";
  return {
    run_id: `sandbox_${status.toLowerCase()}`,
    request_sha256: "a".repeat(64),
    raw_reason_code: "sample_normal",
    profile_id: "refund_not_processed_v1",
    status,
    semantic_status: "SUCCESS",
    claims: [
      {
        claim_id: "claim_1",
        claim_type: "refund_claimed_processed",
        source_quote: "Your INR 2,500 refund was processed on 28 August 2026.",
        span_start: 0,
        span_end: 58,
        grounding_status: "GROUNDED",
        amount_minor: 250000,
        currency: "INR",
        normalization_status: "NORMALIZED",
      },
    ],
    findings: mismatch
      ? [
          {
            code: "F_REFUND_AMOUNT_MISMATCH",
            effect: "BLOCK",
            summary: "Claim and ledger amounts differ.",
            evidence_refs: ["claim:claim_1", "refund:refund_1"],
          },
        ]
      : [],
    ledger: {
      payment_id: "pay_1",
      payment_amount_minor: 250000,
      currency: "INR",
      refund_ledger_complete: true,
      refund_status: "processed",
      refund_amount_minor: mismatch ? 49900 : 250000,
    },
    proof: {
      status: mismatch ? "UNSAT" : "SAT",
      constraints: [
        {
          constraint_id: "C_SUPPORTED_FACTS_CONSISTENT",
          layer: "INVARIANT",
          expression: "claim agrees with refund state",
          state: mismatch ? "UNSAT" : "SAT",
        },
      ],
      certificate: null,
      model_override_allowed: false,
    },
    next_evidence: null,
    comparison: {
      semantic_output: "GROUNDED_RELATION",
      deterministic_output: status,
      relationship: "DIVISION_OF_AUTHORITY",
      uncertainty_basis: "VERIFICATION_COMPLETENESS",
      probability_exposed: false,
    },
    boundary: {
      runtime: "LOCAL_OFFLINE",
      ephemeral: true,
      synthetic_input: true,
      external_api_calls: false,
      razorpay_write_performed: false,
      persisted: false,
      holdout_accessed: false,
      extractor_id: "regex-baseline-v1",
      gate_authority: "DETERMINISTIC_POLICY",
    },
    disclaimer:
      "Decision support only: not a dispute outcome prediction or legal verdict.",
  };
}

test("loads a downloadable sample into the live proof pipeline", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = String(input);
      const payload = url.endsWith("/samples/normal.json")
        ? {
            request: {
              raw_reason_code: "sample_normal",
              payment_amount_inr: "2500.00",
              customer_communication:
                "Your INR 2,500 refund was processed on 28 August 2026.",
              refund_ledger_complete: true,
              refund_status: "processed",
              refund_amount_inr: "2500.00",
              simulation: "none",
            },
          }
        : sandbox(
            init?.method === "POST" && url.endsWith("/sandbox/evaluate")
              ? "PASS"
              : "BLOCK",
          );
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );

  render(<TryVerifier />);
  expect(
    screen.getByRole("heading", { name: "Add the evidence" }),
  ).toBeVisible();
  expect(
    screen.getByRole("link", { name: "Download Hinglish sample JSON" }),
  ).toHaveAttribute("download");
  fireEvent.click(screen.getByRole("button", { name: "Normal" }));
  expect(await screen.findByText(/Normal bundle loaded/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Check this case" }));
  expect(
    await screen.findByRole("heading", {
      name: "Understand the customer’s claim",
    }),
  ).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: /See the decision/ }));
  expect(
    await screen.findByText("Custom evidence observed PASS"),
  ).toBeVisible();
});

test("imports multiple evidence files, combines documents, and executes verification", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => {
      const payload = sandbox("PASS");
      return Promise.resolve(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );

  render(<TryVerifier />);
  const fileInput = document.querySelector(
    'input[name="evidence_file"]',
  ) as HTMLInputElement;
  expect(fileInput).toHaveAttribute("multiple");

  const file1 = new File(
    ["Customer email: refund of INR 2,500 was promised."],
    "email_log.txt",
    { type: "text/plain" },
  );
  const file2 = new File(
    ["Support chat transcript: confirmed refund of INR 2,500."],
    "chat_transcript.txt",
    { type: "text/plain" },
  );

  fireEvent.change(fileInput, { target: { files: [file1, file2] } });

  expect(await screen.findByText(/Files retained locally/)).toBeVisible();
  expect(screen.getByText("email_log.txt")).toBeVisible();
  expect(screen.getByText("chat_transcript.txt")).toBeVisible();

  const textarea = screen.getByRole("textbox", {
    name: /Customer communication/i,
  }) as HTMLTextAreaElement;
  expect(textarea.value).toContain(
    "Customer email: refund of INR 2,500 was promised.",
  );
  expect(textarea.value).toContain(
    "Support chat transcript: confirmed refund of INR 2,500.",
  );
  expect(
    screen.getByRole("textbox", { name: "Payment amount (INR)" }),
  ).toHaveValue("4999.00");

  fireEvent.click(screen.getByRole("button", { name: "Check this case" }));
  expect(
    await screen.findByRole("heading", {
      name: "Understand the customer’s claim",
    }),
  ).toBeVisible();
});

test("preserves the case while an evidence file is still being read", async () => {
  render(<TryVerifier />);
  let finishRead!: (content: string) => void;
  const pending = new Promise<string>((resolve) => {
    finishRead = resolve;
  });
  const file = new File(["receipt"], "receipt.txt", { type: "text/plain" });
  Object.defineProperty(file, "arrayBuffer", { value: undefined });
  Object.defineProperty(file, "text", { value: () => pending });
  const input = document.querySelector(
    'input[name="evidence_file"]',
  ) as HTMLInputElement;
  fireEvent.change(input, { target: { files: [file] } });
  expect(
    screen.getByRole("button", { name: "Check this case" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("textbox", { name: "Payment amount (INR)" }),
  ).toBeDisabled();
  expect(screen.getByRole("button", { name: "Normal" })).toBeDisabled();
  finishRead("Your refund was processed.");
  expect(await screen.findByText(/Files retained locally/)).toBeVisible();
  expect(screen.getByRole("button", { name: "Check this case" })).toBeEnabled();
});
