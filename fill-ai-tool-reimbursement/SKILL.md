---
name: fill-ai-tool-reimbursement
description: Inspect a folder containing AI-tool subscription invoices, payment screenshots, and reimbursement requirements; match each expense, independently open the official PBOC central parity announcement page and Feishu/Lark approval, calculate CNY amounts, generate an audit Markdown file, and fill the reimbursement with original files as attachments. Use when the user asks to batch-process AI subscription reimbursements from a local folder, reconcile invoices with payment records, convert foreign-currency expenses using official PBOC rates, or prepare/save/submit the corresponding Feishu approval, whether or not the user has already opened Feishu or the PBOC website.
---

# Fill AI Tool Reimbursement

Process a reimbursement folder into a traceable calculation manifest, an audit Markdown file, and a verified Feishu draft. Treat the folder, its requirements document, and the official PBOC exchange-rate announcement as the sources of truth. Do not require the user to pre-open Feishu or the exchange-rate website.

## Load Companion Skills

Before acting, load and follow these skills when available:

- `computer-use` for launching and controlling Feishu and the exchange-rate page.
- `lark-approval` for approval safety, especially submission confirmation.
- `pdf` when inspecting invoice PDFs.

Never bypass a stricter rule from a companion skill or the user's current instructions.

## Preserve These Invariants

- Use only the China PBOC Monetary Policy Department central parity announcement index at `https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/index.html`, or a stricter official PBOC page supplied by the user. Do not substitute search results, commercial sites, card-network rates, or other exchange-rate sources.
- Use the official announcement dated on the payment date when one exists. Only when the PBOC publishes no announcement that day, use the most recent earlier announcement, unless the folder's requirements explicitly define another rule.
- Record the announcement date, rate, and official article URL for every converted expense.
- Upload each original invoice and payment record directly as separate Feishu attachments. Do not merge, convert, re-encode, or upload temporary renders.
- Include a payment-only expense only when the user explicitly allows the missing invoice.
- Never silently omit an expense or attachment. If the form limit is exceeded, report the exact count and ask which item to exclude.
- Preserve explicit exclusions, such as an item the user tells you to remove.
- Respect instructions to leave the receiving account blank or let the user complete it.
- Save a draft after verification. Never submit the approval without a fresh, explicit confirmation from the user.

## Workflow

### 0. Establish Feishu and PBOC Context

Do not ask the user to open either application in advance.

1. Check whether Feishu/Lark is running. Launch it when necessary.
2. Navigate to Approval and locate the reimbursement definition required by the folder or user. Search for `费用报销` when no more specific name is supplied.
3. Open the official PBOC central parity announcement index at `https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/index.html` when no approved PBOC page is already open.
4. Start from that index and follow only its official daily announcement links. Do not use a search engine or secondary exchange-rate page as an alternate route.
5. Continue autonomously through normal navigation. Ask the user to intervene only for login, SSO, 2FA, CAPTCHA, missing permission, or an unavailable required approval definition.

### 1. Inspect the Folder and Requirements

1. List files with `rg --files` and read requirements documents first.
2. Classify source files into invoices, payment records, requirements, and unrelated or generated files.
3. Inspect every invoice and payment image. Render PDFs only for inspection; keep renders outside the attachment set.
4. Pair invoice and payment files using filenames plus visible vendor, amount, date, and subscription details. Do not rely on filenames alone.
5. Ask only about unresolved facts that materially change the result.

For every item, extract:

- Vendor and plan.
- Subscription start and end dates.
- Foreign-currency amount and currency.
- Payment date shown by the user's payment record.
- Original invoice filename, if available.
- Original payment-record filename.
- Any explicit inclusion, exclusion, or payment-only instruction.

Flag invoice/payment amount mismatches, conflicting dates, duplicate charges, missing evidence, and unclear subscription periods before filling Feishu.

### 2. Build the Calculation Manifest

Read [references/manifest-format.md](references/manifest-format.md) before creating a manifest or running the calculator.

Create the manifest in a task-specific temporary directory unless the user asks to retain it. Keep excluded items in the manifest with `included: false` and a reason so omissions remain auditable.

Use the reimbursement requirements' exact detail format. When no stricter format is provided, use:

```text
工具或套餐-YYYYMMDD至YYYYMMDD-金额美金
```

Use the payment date, not the invoice issue date or merchant settlement date, for the Feishu date field.

### 3. Obtain Official Exchange Rates

For each foreign-currency payment:

1. Work only from the approved PBOC Monetary Policy Department page established in step 0.
2. Check the payment date itself first. When a daily announcement exists for that date, use it.
3. Only when no announcement exists on the payment date, such as some weekends or holidays, move backward to the most recent published announcement.
4. Read the rate from the official daily article and capture its URL.
5. Recheck that `rate_date <= payment_date` and that no later announcement on or before the payment date was skipped.

If the official page is unavailable or the currency is not covered, stop and ask the user. Do not improvise a rate.

### 4. Calculate and Generate the Audit File

Run the bundled deterministic calculator:

```bash
python3 <skill-directory>/scripts/calculate_reimbursements.py \
  <manifest.json> \
  --root <reimbursement-folder> \
  --output <reimbursement-folder>/汇率换算明细.md \
  --attachment-limit <limit-shown-by-feishu>
```

The script uses decimal arithmetic and `ROUND_HALF_UP`, validates payment/rate dates, checks referenced files and duplicate attachments, enforces the supplied attachment limit, and writes the audit table.

Review the generated file before entering the form. Do not upload `汇率换算明细.md` unless the user explicitly requests it; it is an audit artifact, not invoice evidence.

### 5. Run the Preflight Gate

Confirm all of the following before filling Feishu:

- Every included expense has a payment record.
- Every included expense has an invoice unless `allow_payment_only: true` is explicitly authorized.
- Every included attachment exists and appears exactly once.
- The attachment count does not exceed the current form limit.
- Every converted expense has an official PBOC URL, rate date, and rate.
- Every rate date is on or before its payment date; when the payment date has an announcement, the dates must be equal.
- Per-item amounts, subtotals, and the grand total match the audit file.
- Excluded items and generated/temporary files are absent from the upload set.

Stop on a preflight failure. Resolve it with the user rather than weakening the check.

### 6. Fill Feishu

Use current Computer Use state before every action; do not reuse stale accessibility indices after the form changes.

1. Fill reimbursement type, reason, payer company, and other required header fields from the form or requirements.
2. Add one detail per included manifest entry.
3. Fill amount in CNY, detail text, and payment date exactly as audited.
4. Re-query after adding or copying a detail because indices and scroll positions can shift.
5. Open date pickers from the current field and verify the selected date afterward.
6. Upload the exact original attachment set. If the macOS picker supports only one file, upload sequentially and wait for each upload to finish.
7. When Feishu collapses long attachment lists, expand them before final reconciliation.
8. Leave the receiving account or other user-owned fields unchanged when instructed.

### 7. Verify and Save

Perform an evidence-based final audit:

- Detail count equals the included manifest count.
- Every detail's amount, content, and date matches the manifest.
- Feishu's grand total equals the calculator total.
- Attachment filenames match the expected set exactly: no missing, extra, duplicate, temporary, or excluded files.
- No attachment still shows an uploading state.
- Reason, category, payer company, and requested blank fields are correct.
- The draft reports a saved state.

Save the draft. Do not press Submit.

### 8. Hand Off

Report concisely:

- Included item count and grand total.
- Attachment count split by invoices and payment records.
- Explicitly excluded or payment-only items.
- Fields intentionally left for the user.
- Draft saved/not submitted status.

If the user wants Codex to submit after completing their fields, request a fresh explicit confirmation such as `确认提交` and follow `lark-approval` submission rules.

## Stop Conditions

Stop and ask the user when:

- An invoice cannot be matched confidently to a payment record.
- Invoice and payment amounts conflict without an explained upgrade, credit, or tax difference.
- A required invoice or payment record is missing and no exception is authorized.
- The official PBOC index or required daily announcement cannot be opened or does not provide the needed currency.
- The attachment limit is exceeded.
- A required account, company, category, or exclusion decision cannot be inferred safely.
