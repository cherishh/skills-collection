#!/usr/bin/env python3
"""Validate a reimbursement manifest and render a Markdown audit table."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


CENT = Decimal("0.01")
PBOC_PREFIX = "https://www.pbc.gov.cn/"


def decimal_value(value: Any, field: str, row_number: int, errors: list[str]) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"entry {row_number}: {field} is not a decimal: {value!r}")
        return None


def date_value(value: Any, field: str, row_number: int, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        errors.append(f"entry {row_number}: {field} must use YYYY-MM-DD: {value!r}")
        return None


def markdown_text(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def money(value: Decimal) -> str:
    return f"{value.quantize(CENT, rounding=ROUND_HALF_UP):,.2f}"


def analyze(
    manifest: dict[str, Any], root: Path | None, attachment_limit: int | None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Decimal], Decimal, list[str]]:
    errors: list[str] = []
    raw_entries = manifest.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        return [], [], {}, Decimal("0"), ["manifest.entries must be a non-empty array"]

    rows: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    attachments: list[str] = []
    subtotals: dict[str, Decimal] = {}
    total = Decimal("0")

    for row_number, entry in enumerate(raw_entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"entry {row_number}: entry must be an object")
            continue

        item = str(entry.get("item", "")).strip()
        if not item:
            errors.append(f"entry {row_number}: item is required")
            item = f"Entry {row_number}"

        if entry.get("included", True) is False:
            excluded.append(
                {
                    "item": item,
                    "reason": str(entry.get("exclusion_reason", "not specified")).strip(),
                }
            )
            continue

        detail = str(entry.get("detail", "")).strip()
        if not detail:
            errors.append(f"entry {row_number}: detail is required")

        payment_date = date_value(entry.get("payment_date"), "payment_date", row_number, errors)
        foreign_amount = decimal_value(
            entry.get("foreign_amount"), "foreign_amount", row_number, errors
        )
        currency = str(entry.get("currency", "")).upper().strip()
        if not currency:
            errors.append(f"entry {row_number}: currency is required")

        invoice = entry.get("invoice")
        payment_record = entry.get("payment_record")
        invoice = str(invoice).strip() if invoice else None
        payment_record = str(payment_record).strip() if payment_record else None

        if not payment_record:
            errors.append(f"entry {row_number}: payment_record is required")
        if not invoice and entry.get("allow_payment_only") is not True:
            errors.append(
                f"entry {row_number}: invoice is required unless allow_payment_only is true"
            )

        for attachment in (invoice, payment_record):
            if not attachment:
                continue
            attachments.append(attachment)
            if root is not None:
                attachment_path = root / attachment
                if not attachment_path.is_file():
                    errors.append(
                        f"entry {row_number}: attachment does not exist: {attachment_path}"
                    )

        rate_date: date | None = None
        rate_url = str(entry.get("rate_url", "")).strip()
        if currency == "CNY":
            rate = Decimal("1")
        else:
            rate = decimal_value(
                entry.get("cny_per_unit"), "cny_per_unit", row_number, errors
            )
            rate_date = date_value(entry.get("rate_date"), "rate_date", row_number, errors)
            if payment_date and rate_date and rate_date >= payment_date:
                errors.append(
                    f"entry {row_number}: rate_date {rate_date} must be before payment_date {payment_date}"
                )
            if not rate_url.startswith(PBOC_PREFIX):
                errors.append(
                    f"entry {row_number}: rate_url must be a direct official PBOC URL"
                )

        if foreign_amount is None or rate is None:
            continue

        cny_amount = (foreign_amount * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        expected_cny = entry.get("cny_amount")
        if expected_cny is not None:
            expected_value = decimal_value(expected_cny, "cny_amount", row_number, errors)
            if expected_value is not None and expected_value.quantize(CENT) != cny_amount:
                errors.append(
                    f"entry {row_number}: cny_amount {expected_value} does not match calculated {cny_amount}"
                )

        category = str(entry.get("category") or item).strip()
        subtotals[category] = subtotals.get(category, Decimal("0")) + cny_amount
        total += cny_amount
        rows.append(
            {
                "item": item,
                "category": category,
                "detail": detail,
                "payment_date": payment_date.isoformat() if payment_date else "",
                "foreign_amount": foreign_amount,
                "currency": currency,
                "rate_date": rate_date.isoformat() if rate_date else "-",
                "rate": rate,
                "rate_url": rate_url,
                "cny_amount": cny_amount,
                "invoice": invoice,
                "payment_record": payment_record,
                "payment_only": invoice is None,
            }
        )

    duplicate_attachments = sorted(
        name for name, count in Counter(attachments).items() if count > 1
    )
    if duplicate_attachments:
        errors.append(
            "duplicate attachment references: " + ", ".join(duplicate_attachments)
        )

    if attachment_limit is not None and len(attachments) > attachment_limit:
        errors.append(
            f"attachment count {len(attachments)} exceeds limit {attachment_limit}"
        )

    return rows, excluded, subtotals, total, errors


def render_markdown(
    title: str,
    rows: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    subtotals: dict[str, Decimal],
    total: Decimal,
) -> str:
    lines = [
        f"# {markdown_text(title)}",
        "",
        "换算规则：使用付款日前最近一期中国人民银行货币政策司公布的人民币汇率中间价；每笔结果按四舍五入保留两位小数。",
        "",
        "| 项目 | 付款日 | 外币金额 | 汇率公告日 | 汇率 | 人民币 |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        rate_date = markdown_text(row["rate_date"])
        if row["rate_url"]:
            rate_date = f"[{rate_date}]({row['rate_url']})"
        lines.append(
            "| {item} | {payment_date} | {foreign_amount} {currency} | {rate_date} | {rate} | ¥{cny} |".format(
                item=markdown_text(row["item"]),
                payment_date=row["payment_date"],
                foreign_amount=money(row["foreign_amount"]),
                currency=markdown_text(row["currency"]),
                rate_date=rate_date,
                rate=row["rate"],
                cny=money(row["cny_amount"]),
            )
        )

    lines.extend(["", "## 分类小计", ""])
    for category, subtotal in subtotals.items():
        lines.append(f"- {markdown_text(category)}：¥{money(subtotal)}")
    lines.append(f"- **合计：¥{money(total)}**")

    lines.extend(
        [
            "",
            "## 附件核对",
            "",
            "| 项目 | Invoice | 付款记录 |",
            "|---|---|---|",
        ]
    )
    for row in rows:
        invoice = row["invoice"] or "缺失（已授权仅付款记录）"
        lines.append(
            f"| {markdown_text(row['item'])} | {markdown_text(invoice)} | {markdown_text(row['payment_record'])} |"
        )

    attachment_count = sum(
        (1 if row["invoice"] else 0) + (1 if row["payment_record"] else 0)
        for row in rows
    )
    lines.extend(["", f"附件总数：**{attachment_count}**"])

    if excluded:
        lines.extend(["", "## 未纳入项目", ""])
        for entry in excluded:
            lines.append(
                f"- {markdown_text(entry['item'])}：{markdown_text(entry['reason'])}"
            )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a reimbursement manifest and render a Markdown audit file."
    )
    parser.add_argument("manifest", type=Path, help="Path to the manifest JSON file")
    parser.add_argument("--root", type=Path, help="Folder containing referenced attachments")
    parser.add_argument("--output", type=Path, help="Write Markdown to this path")
    parser.add_argument("--attachment-limit", type=int, help="Maximum allowed attachments")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: cannot read manifest: {error}", file=sys.stderr)
        return 2

    if not isinstance(manifest, dict):
        print("error: manifest root must be an object", file=sys.stderr)
        return 2

    root = args.root.resolve() if args.root else None
    rows, excluded, subtotals, total, errors = analyze(
        manifest, root, args.attachment_limit
    )
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    document = render_markdown(
        str(manifest.get("title") or "AI 工具订阅报销汇率换算明细"),
        rows,
        excluded,
        subtotals,
        total,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
    else:
        sys.stdout.write(document)

    summary = {
        "included_entries": len(rows),
        "attachments": sum(
            (1 if row["invoice"] else 0) + (1 if row["payment_record"] else 0)
            for row in rows
        ),
        "total_cny": money(total),
        "output": str(args.output) if args.output else None,
    }
    print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
