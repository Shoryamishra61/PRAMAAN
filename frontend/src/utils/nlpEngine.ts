/**
 * Multilingual NLP & Entity Intelligence Engine
 * Specialized for Indian BFSI & E-Commerce Dispute Ingestion.
 * Understands:
 *   1. Multiple languages: English, Hindi (Devanagari), Hinglish (Romanized Hindi), Bengali, Tamil, Telugu, Marathi.
 *   2. Varied linguistic expressions for currency and numerical amounts (words, numerals, regional terms).
 *   3. Places & Geographic locations (Indian cities, trade hubs, states).
 *   4. Financial rails, payment systems, banks, UPI VPA handles, UTR/RRN numbers.
 *   5. Dispute intent classification & modality.
 */

export type DetectedLanguage =
  | "Hindi (Devanagari)"
  | "Hinglish (Romanized Hindi)"
  | "Bengali"
  | "Tamil"
  | "Telugu"
  | "Marathi"
  | "Kannada"
  | "English";

export type DisputeIntent =
  | "REFUND_NOT_RECEIVED"
  | "REFUND_CLAIMED_PROCESSED"
  | "DOUBLE_DEBIT"
  | "RETURN_DELIVERED_NO_REFUND"
  | "UNAUTHORIZED_TRANSACTION"
  | "GENERAL_INQUIRY";

export interface BatchStatementItem {
  id: string;
  quote: string;
  spanStart: number;
  spanEnd: number;
  language: DetectedLanguage;
  intent: DisputeIntent;
  intentSummary: string;
  amounts: { raw: string; normalizedInr: string; minorUnits: bigint }[];
}

export interface ExtractedEntities {
  language: DetectedLanguage;
  confidence: number;
  intent: DisputeIntent;
  intentSummary: string;
  claimedAmounts: { raw: string; normalizedInr: string; minorUnits: bigint }[];
  places: string[];
  banksAndRails: string[];
  transactionReferences: string[];
  datesFound: string[];
  keyTokens: string[];
  batchStatements: BatchStatementItem[];
}

// 1. Places Dictionary (Top Indian cities, tech hubs, and commercial centers)
const INDIAN_PLACES = [
  "Bengaluru", "Bangalore", "Mumbai", "Delhi", "New Delhi", "Hyderabad",
  "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow",
  "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna",
  "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut",
  "Rajkot", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar",
  "Navi Mumbai", "Allahabad", "Prayagraj", "Ranchi", "Howrah", "Coimbatore",
  "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota",
  "Chandigarh", "Guwahati", "Solapur", "Hubballi", "Hubli", "Bareilly", "Moradabad",
  "Mysore", "Mysuru", "Gurgaon", "Gurugram", "Aligarh", "Jalandhar", "Tiruchirappalli",
  "Bhubaneswar", "Salem", "Warangal", "Thiruvananthapuram", "Kochi", "Cochin",
  "Dehradun", "Noida", "Greater Noida", "Mangalore", "Mangaluru", "Udaipur", "Goa",
  "Puducherry", "Pondicherry", "Shillong", "Shimla", "Rourkela", "Durgapur"
];

// 2. Financial Institutions, Rails & Platforms
const FINANCIAL_ENTITIES = [
  "Razorpay", "UPI", "PhonePe", "Google Pay", "GPay", "GooglePay", "Paytm",
  "CRED", "BHIM", "Amazon Pay", "Mobikwik", "BharatPe", "PayU", "Cashfree",
  "HDFC", "HDFC Bank", "ICICI", "ICICI Bank", "SBI", "State Bank of India",
  "Axis Bank", "Axis", "Kotak", "Kotak Mahindra Bank", "PNB", "Punjab National Bank",
  "Bank of Baroda", "BOB", "IndusInd Bank", "Yes Bank", "IDFC FIRST Bank", "IDFC",
  "Canara Bank", "Union Bank of India", "Federal Bank", "IMPS", "NEFT", "RTGS", "NACH"
];

// 3. Hinglish & Multi-dialect keyword dictionaries
const HINGLISH_PATTERNS = [
  /\b(?:nahi|nahin|nhi|ni)\b/i,
  /\b(?:mila|mili|mile|mil|prapt)\b/i,
  /\b(?:paise|paisa|rupaye|rupiye|rakam|amount)\b/i,
  /\b(?:kat\s*gaye|cut\s*gaya|deduct\s*hua|kat\s*gaya)\b/i,
  /\b(?:wapas|vaapas|lautao|bhejo|bhej)\b/i,
  /\b(?:aaya|aaye|aayi|aya|aye)\b/i,
  /\b(?:kal|parso|aaj|today|yesterday)\b/i,
  /\b(?:khate|khata|account)\b/i,
  /\b(?:dobara|do\s*baar|twice)\b/i,
  /\b(?:kripya|bhai|sir|madam)\b/i,
  /\b(?:mera|meri|mere)\b/i,
  /\b(?:ho\s*gaya\s*tha|kar\s*diya\s*tha|chahiye)\b/i
];

// 4. Word-based numbers in Hindi / Hinglish / English
const WORD_NUMBERS: Record<string, number> = {
  ek: 1, do: 2, teen: 3, chaar: 4, char: 4, paanch: 5, panch: 5,
  chhe: 6, che: 6, saat: 7, aath: 8, ath: 8, nau: 9, das: 10,
  one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  sau: 100, hundred: 100,
  hazaar: 1000, hazar: 1000, thousand: 1000, k: 1000,
  lakh: 100000, lac: 100000,
  crore: 10000000
};

export function detectTextLanguage(text: string): { language: DetectedLanguage; confidence: number } {
  // Check Devanagari script (Hindi / Marathi)
  if (/[\u0900-\u097F]/.test(text)) {
    return { language: "Hindi (Devanagari)", confidence: 0.95 };
  }
  // Check Bengali script
  if (/[\u0980-\u09FF]/.test(text)) {
    return { language: "Bengali", confidence: 0.95 };
  }
  // Check Tamil script
  if (/[\u0B80-\u0BFF]/.test(text)) {
    return { language: "Tamil", confidence: 0.95 };
  }
  // Check Telugu script
  if (/[\u0C00-\u0C7F]/.test(text)) {
    return { language: "Telugu", confidence: 0.95 };
  }
  // Check Kannada script
  if (/[\u0C80-\u0CFF]/.test(text)) {
    return { language: "Kannada", confidence: 0.95 };
  }

  // Check Romanized Hinglish markers
  let hinglishMatches = 0;
  for (const pat of HINGLISH_PATTERNS) {
    if (pat.test(text)) hinglishMatches++;
  }

  if (hinglishMatches >= 2) {
    const confidence = Math.min(0.95, 0.5 + hinglishMatches * 0.1);
    return { language: "Hinglish (Romanized Hindi)", confidence };
  }

  // Check regional romanized markers
  if (/\b(?:panam|thirumba|kidaikkavillai)\b/i.test(text)) {
    return { language: "Tamil", confidence: 0.85 };
  }
  if (/\b(?:dabbulu|raledu|ayindi)\b/i.test(text)) {
    return { language: "Telugu", confidence: 0.85 };
  }
  if (/\b(?:taka|ferot|paini)\b/i.test(text)) {
    return { language: "Bengali", confidence: 0.85 };
  }
  if (/\b(?:paise\s+parat|aale\s+nahit)\b/i.test(text)) {
    return { language: "Marathi", confidence: 0.85 };
  }

  return { language: "English", confidence: 0.9 };
}

export function extractAmountsFromText(text: string): { raw: string; normalizedInr: string; minorUnits: bigint }[] {
  const results: { raw: string; normalizedInr: string; minorUnits: bigint }[] = [];
  const seen = new Set<string>();

  // 1. Explicit Currency Symbol / Code matching (e.g. ₹ 3,200.00, INR 4999, Rs. 500, रू 500)
  const explicitRegex = /(?:₹|INR|rs\.?|rupees?|rupaye?|रुपये|रुपए|रू|টাকা|ரூபாய்|రూపాయలు|रु)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)/gi;
  let match: RegExpExecArray | null;

  while ((match = explicitRegex.exec(text)) !== null) {
    const rawMatch = match[0];
    const numPart = match[1].replace(/,/g, "");
    if (!seen.has(numPart)) {
      seen.add(numPart);
      const [whole, dec = "00"] = numPart.split(".");
      const normalizedInr = `${whole}.${dec.padEnd(2, "0").slice(0, 2)}`;
      const minor = BigInt(whole) * 100n + BigInt(dec.padEnd(2, "0").slice(0, 2));
      results.push({ raw: rawMatch, normalizedInr, minorUnits: minor });
    }
  }

  // 2. Trailing currency matching (e.g. "3200 rupees", "500 rs", "4999 rupaye", "500 रुपये")
  const trailingRegex = /(?:^|[^0-9])([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:₹|INR|rs\.?|rupees?|rupaye?|रुपये|रुपए|रू|पैसा|पैसे|টাকা|ரூபாய்|రూపాయలు|रु|bucks|paisa)(?:\b|[\s,.!?]|$)/gi;
  while ((match = trailingRegex.exec(text)) !== null) {
    const rawMatch = match[0].trim();
    const numPart = match[1].replace(/,/g, "");
    if (!seen.has(numPart)) {
      seen.add(numPart);
      const [whole, dec = "00"] = numPart.split(".");
      const normalizedInr = `${whole}.${dec.padEnd(2, "0").slice(0, 2)}`;
      const minor = BigInt(whole) * 100n + BigInt(dec.padEnd(2, "0").slice(0, 2));
      results.push({ raw: rawMatch, normalizedInr, minorUnits: minor });
    }
  }

  // 3. Word numeral pattern matching (e.g. "do hazaar", "paanch sau", "10k")
  const wordRegex = /\b(ek|do|teen|chaar|char|paanch|panch|chhe|saat|aath|nau|das|[0-9]+)\s*(sau|hazaar|hazar|thousand|lakh|lac|crore|k)\b/gi;
  while ((match = wordRegex.exec(text)) !== null) {
    const rawMatch = match[0];
    const multStr = match[1].toLowerCase();
    const unitStr = match[2].toLowerCase();

    const mult = /^\d+$/.test(multStr) ? parseInt(multStr, 10) : (WORD_NUMBERS[multStr] ?? 1);
    const unit = WORD_NUMBERS[unitStr] ?? 1;
    const computed = mult * unit;
    const computedStr = computed.toString();

    if (!seen.has(computedStr)) {
      seen.add(computedStr);
      results.push({
        raw: rawMatch,
        normalizedInr: `${computed}.00`,
        minorUnits: BigInt(computed) * 100n,
      });
    }
  }

  return results;
}

export function extractPlaces(text: string): string[] {
  const found: string[] = [];
  const textLower = ` ${text.toLowerCase()} `;

  for (const place of INDIAN_PLACES) {
    const placeRegex = new RegExp(`\\b${place.toLowerCase()}\\b`, "i");
    if (placeRegex.test(textLower)) {
      if (!found.includes(place)) found.push(place);
    }
  }
  return found;
}

export function extractFinancialEntities(text: string): string[] {
  const found: string[] = [];

  for (const entity of FINANCIAL_ENTITIES) {
    const regex = new RegExp(`\\b${entity.replace(/\s+/g, "\\s+")}\\b`, "i");
    if (regex.test(text)) {
      if (!found.includes(entity)) found.push(entity);
    }
  }

  // Check UPI handle format (e.g. user@okhdfcbank)
  const vpaMatches = text.match(/\b[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\b/g);
  if (vpaMatches) {
    for (const vpa of vpaMatches) {
      if (!found.includes(vpa)) found.push(`UPI VPA (${vpa})`);
    }
  }

  return found;
}

export function extractTransactionReferences(text: string): string[] {
  const refs: string[] = [];

  // Razorpay style IDs (pay_..., rfnd_..., order_...)
  const rzp = text.match(/\b(?:pay|rfnd|order|disp|case)_[a-zA-Z0-9_-]{8,32}\b/gi);
  if (rzp) refs.push(...rzp);

  // UPI VPA handles (e.g. user@okhdfcbank)
  const vpas = text.match(/\b[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\b/g);
  if (vpas) refs.push(...vpas);

  // 12-digit UPI UTR / RRN (Bank transaction reference)
  const utr = text.match(/\b(?:utr|rrn|ref|reference)?[:\s#-]*([0-9]{12})\b/gi);
  if (utr) {
    for (const u of utr) {
      const digits = u.replace(/\D/g, "");
      if (digits.length === 12 && !refs.includes(`UTR: ${digits}`)) {
        refs.push(`UTR: ${digits}`);
      }
    }
  }

  // Alphanumeric reference codes (e.g. RF-HI-01, INV-2026-89)
  const customRef = text.match(/\b(?:RF|REF|INV|TXN|DISP)-[A-Z0-9-]+\b/gi);
  if (customRef) {
    for (const cr of customRef) {
      if (!refs.includes(cr)) refs.push(cr);
    }
  }

  return Array.from(new Set(refs));
}

export function classifyDisputeIntent(text: string): { intent: DisputeIntent; summary: string } {
  const lower = text.toLowerCase();

  // Double debit detection
  if (
    /\b(?:dobara|do\s*baar|twice|double\s*debit|two\s*times|kat\s*gaye\s*do\s*baar|duplicate\s*(?:charged?|debit|transaction|payment)?|duplicate)\b/i.test(lower)
  ) {
    return {
      intent: "DOUBLE_DEBIT",
      summary: "Customer reports multiple unauthorized deductions for a single transaction.",
    };
  }

  // Positive claim: refund was already processed / issued
  if (
    /\b(?:kal\s*process\s*ho\s*gaya|refund\s*was\s*processed|refund\s*has\s*been\s*processed|we\s*processed|already\s*refunded|credit\s*processed|process\s*ho\s*gaya)\b/i.test(lower)
  ) {
    return {
      intent: "REFUND_CLAIMED_PROCESSED",
      summary: "Communication states that refund was approved and credited/processed.",
    };
  }

  // Return delivered but refund missing
  if (
    /\b(?:return(?:ed)?|picked\s*up|item\s*returned|delivered\s*back|parcel\s*wapas|parcel\s*delivered)\b/i.test(lower) &&
    /\b(?:nahi|not|no\s*refund|pending|missing|paisa|withheld)\b/i.test(lower)
  ) {
    return {
      intent: "RETURN_DELIVERED_NO_REFUND",
      summary: "Customer states goods were picked up or delivered, but refund was withheld.",
    };
  }

  // Negative refund claim: refund not received / missing
  if (
    /\b(?:nahi\s*mila|not\s*received|never\s*processed|wapas\s*nahi|refund\s*kahan\s*hai|paise\s*bhejo|cut\s*gaye|deducted\s*but\s*failed|need\s*refund|want\s*refund|claim\s*refund|वापस\s*करो|रिफंड\s*वापस|पैसे\s*वापस|रिफंड\s*चाहिए|रिफंड\s*दो)\b/i.test(lower) ||
    (/[\u0900-\u097F]/.test(lower) && /(?:वापस|रिफंड|पैसे)/.test(lower))
  ) {
    return {
      intent: "REFUND_NOT_RECEIVED",
      summary: "Customer claims debited amount was not refunded or credit did not reflect in bank account.",
    };
  }

  // Unauthorized / Fraud
  if (
    /\b(?:fraud(?:ulent)?|unauthorized|not\s*authorized|unapproved|fake|scam|otp\s*nahi\s*diya)\b/i.test(
      lower,
    )
  ) {
    return {
      intent: "UNAUTHORIZED_TRANSACTION",
      summary: "Dispute alleges unauthorized charge or card/UPI security breach.",
    };
  }

  return {
    intent: "GENERAL_INQUIRY",
    summary: "Standard dispute communication needing factual evidence grounding.",
  };
}

export function extractBatchStatementsFromText(text: string): BatchStatementItem[] {
  if (!text.trim()) return [];

  let rawLines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => l.length > 0);
  if (rawLines.length <= 1) {
    const sentences = text.trim().split(/(?<=[.!?])\s+/);
    rawLines = sentences.map((s) => s.trim()).filter((s) => s.length > 0);
  }

  const items: BatchStatementItem[] = [];
  const seenQuotes = new Set<string>();

  for (let idx = 0; idx < rawLines.length; idx++) {
    const quote = rawLines[idx];
    if (!quote || seenQuotes.has(quote)) continue;
    seenQuotes.add(quote);

    const spanStart = text.indexOf(quote);
    const spanEnd = spanStart >= 0 ? spanStart + quote.length : -1;

    const { language } = detectTextLanguage(quote);
    const { intent, summary } = classifyDisputeIntent(quote);
    const amounts = extractAmountsFromText(quote);

    // Only include statement if it has an amount or non-trivial intent
    if (amounts.length === 0 && intent === "GENERAL_INQUIRY") continue;

    items.push({
      id: `stmt-${idx + 1}`,
      quote,
      spanStart,
      spanEnd,
      language,
      intent,
      intentSummary: summary,
      amounts,
    });
  }

  return items;
}

export function analyzeMultilingualDisputeText(text: string): ExtractedEntities {
  const { language, confidence } = detectTextLanguage(text);
  const { intent, summary } = classifyDisputeIntent(text);
  const claimedAmounts = extractAmountsFromText(text);
  const places = extractPlaces(text);
  const banksAndRails = extractFinancialEntities(text);
  const transactionReferences = extractTransactionReferences(text);
  const batchStatements = extractBatchStatementsFromText(text);

  // Extract dates
  const dates = text.match(
    /\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|kal|parso|today|yesterday)\b/gi
  ) ?? [];

  // Collect highlighted key tokens
  const keyTokens = [
    ...claimedAmounts.map((a) => a.raw),
    ...places,
    ...banksAndRails,
    ...transactionReferences,
  ];

  return {
    language,
    confidence,
    intent,
    intentSummary: summary,
    claimedAmounts,
    places,
    banksAndRails,
    transactionReferences,
    datesFound: Array.from(new Set(dates)),
    keyTokens: Array.from(new Set(keyTokens)),
    batchStatements,
  };
}
