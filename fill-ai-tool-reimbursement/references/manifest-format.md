# Reimbursement manifest format

Create a UTF-8 JSON object with a top-level `title` and `entries` array.

```json
{
  "title": "AI 工具订阅报销汇率换算明细",
  "entries": [
    {
      "item": "Claude Max plan 5x",
      "category": "Claude",
      "detail": "Claude Max plan 5x-20260103至20260203-100美金",
      "payment_date": "2026-01-03",
      "foreign_amount": "100.00",
      "currency": "USD",
      "rate_date": "2025-12-31",
      "cny_per_unit": "7.0288",
      "rate_url": "https://www.pbc.gov.cn/.../index.html",
      "invoice": "claude-1-invoice.pdf",
      "payment_record": "claude-1.jpg",
      "included": true
    }
  ]
}
```

## Fields

- `item`: Short human-readable item name. Required.
- `category`: Optional subtotal group, normally the vendor.
- `detail`: Exact content to enter in the Feishu detail field. Required.
- `payment_date`: Payment date in `YYYY-MM-DD`. Required.
- `foreign_amount`: Decimal amount as a JSON string. Required.
- `currency`: ISO-like currency code such as `USD`. Required.
- `rate_date`: Official announcement date in `YYYY-MM-DD`. Required for non-CNY expenses.
- `cny_per_unit`: CNY received for one unit of foreign currency, as a JSON string. Required for non-CNY expenses.
- `rate_url`: Direct official PBOC daily announcement URL. Required for non-CNY expenses and must use `https://www.pbc.gov.cn/`.
- `invoice`: Original invoice filename relative to the reimbursement folder. Required unless a payment-only exception is authorized.
- `payment_record`: Original payment screenshot/record filename relative to the reimbursement folder. Required.
- `allow_payment_only`: Set to `true` only with explicit user authorization when `invoice` is absent.
- `included`: Defaults to `true`. Set to `false` for a documented exclusion.
- `exclusion_reason`: Required in practice when `included` is `false`.
- `cny_amount`: Optional expected result. When supplied, the calculator checks it against its own result.

For a CNY-native expense, set `currency` to `CNY`; omit rate fields and the calculator uses a rate of `1`.

## Calculator behavior

The calculator:

- Includes only entries where `included` is not `false`.
- Uses `Decimal(foreign_amount) * Decimal(cny_per_unit)`.
- Rounds each entry to two decimals with `ROUND_HALF_UP`.
- Requires `rate_date <= payment_date` for non-CNY entries. Use the payment-date announcement when it exists; otherwise use the most recent earlier announcement.
- Checks that invoice/payment files exist when `--root` is supplied.
- Rejects duplicate attachment references.
- Rejects an attachment count above `--attachment-limit`.
- Writes per-item calculations, category subtotals, a grand total, attachment reconciliation, and exclusions to Markdown.
