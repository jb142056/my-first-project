#!/usr/bin/env python3
import json
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date

# Load config
with open(os.path.expanduser("~/.invoice-config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

# Invoice details
invoice_date = date(2026, 5, 25)
due_date = date(2026, 6, 30)
invoice_no = "INV-20260525-002"
client_name = "テスト商事"
client_address = ""
items = [
    {"name": "LP制作", "qty": 1, "unit_price": 200000},
    {"name": "バナー制作", "qty": 1, "unit_price": 50000},
]

FONT_REGULAR = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

# Tax
subtotal = sum(i["qty"] * i["unit_price"] for i in items)
tax = int(subtotal * 0.1)
total = subtotal + tax

class InvoicePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("regular", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

pdf = InvoicePDF(orientation="P", unit="mm", format="A4")
pdf.add_font("regular", fname=FONT_REGULAR)
pdf.add_font("bold", fname=FONT_BOLD)
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=20)

W = pdf.w - 40  # usable width (20mm margin each side)
LEFT = 20

# ── Title ──────────────────────────────────────────────
pdf.set_font("bold", size=22)
pdf.set_text_color(30, 30, 30)
pdf.set_xy(LEFT, 20)
pdf.cell(W, 12, "請 求 書", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Invoice No / Date line
pdf.set_font("regular", size=9)
pdf.set_text_color(80, 80, 80)
pdf.set_x(LEFT)
pdf.cell(W, 6,
    f"請求書番号: {invoice_no}　　発行日: {invoice_date.year}年{invoice_date.month}月{invoice_date.day}日",
    align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.set_draw_color(200, 200, 200)
pdf.set_line_width(0.3)
pdf.line(LEFT, pdf.get_y() + 2, LEFT + W, pdf.get_y() + 2)
pdf.ln(6)

# ── Two-column: Client (left) | Issuer (right) ─────────
col_w = W / 2 - 3
start_y = pdf.get_y()

# Left: client
pdf.set_xy(LEFT, start_y)
pdf.set_font("regular", size=9)
pdf.set_text_color(100, 100, 100)
pdf.cell(col_w, 5, "請求先", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_x(LEFT)
pdf.set_font("bold", size=14)
pdf.set_text_color(30, 30, 30)
pdf.cell(col_w, 8, client_name + " 御中", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
if client_address:
    pdf.set_x(LEFT)
    pdf.set_font("regular", size=9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(col_w, 5, client_address, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Right: issuer
right_x = LEFT + col_w + 6
issuer_lines = [
    cfg["company_name"],
    f"代表者: {cfg['representative']}",
    f"〒{cfg['postal_code']}",
    cfg["address"],
    f"TEL: {cfg['phone']}",
    cfg["email"],
    f"登録番号: {cfg['invoice_number']}",
]
pdf.set_xy(right_x, start_y)
for i, line in enumerate(issuer_lines):
    pdf.set_xy(right_x, start_y + i * 5.5)
    if i == 0:
        pdf.set_font("bold", size=11)
        pdf.set_text_color(30, 30, 30)
    else:
        pdf.set_font("regular", size=8.5)
        pdf.set_text_color(80, 80, 80)
    pdf.cell(col_w, 5.5, line, new_x=XPos.RIGHT, new_y=YPos.TOP)

# Move below both columns
pdf.set_y(start_y + len(issuer_lines) * 5.5 + 4)

pdf.set_line_width(0.3)
pdf.line(LEFT, pdf.get_y(), LEFT + W, pdf.get_y())
pdf.ln(6)

# ── Total amount box ───────────────────────────────────
pdf.set_fill_color(245, 248, 255)
pdf.set_draw_color(180, 200, 240)
pdf.set_line_width(0.5)
pdf.rect(LEFT, pdf.get_y(), W, 16, style="FD")
pdf.set_xy(LEFT, pdf.get_y() + 2)
pdf.set_font("regular", size=9)
pdf.set_text_color(100, 100, 100)
pdf.cell(W, 5, "ご請求金額（税込）", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_x(LEFT)
pdf.set_font("bold", size=16)
pdf.set_text_color(20, 60, 160)
pdf.cell(W, 8, f"¥ {total:,}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(4)

# Due date
pdf.set_font("regular", size=9)
pdf.set_text_color(80, 80, 80)
pdf.set_x(LEFT)
pdf.cell(W, 5,
    f"お支払期限: {due_date.year}年{due_date.month}月{due_date.day}日（翌月末）",
    new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(6)

# ── Items table ────────────────────────────────────────
col_widths = [W * 0.50, W * 0.10, W * 0.20, W * 0.20]
headers = ["品目", "数量", "単価（税抜）", "金額（税抜）"]

# Header row
pdf.set_fill_color(50, 80, 150)
pdf.set_text_color(255, 255, 255)
pdf.set_font("bold", size=9)
pdf.set_x(LEFT)
for i, (h, w) in enumerate(zip(headers, col_widths)):
    pdf.cell(w, 8, h, border=0, align="C", fill=True,
             new_x=XPos.RIGHT, new_y=YPos.TOP)
pdf.ln(8)

# Data rows
pdf.set_text_color(30, 30, 30)
pdf.set_font("regular", size=9)
for row_idx, item in enumerate(items):
    fill = row_idx % 2 == 0
    pdf.set_fill_color(248, 250, 255)
    pdf.set_x(LEFT)
    amount = item["qty"] * item["unit_price"]
    values = [
        item["name"],
        str(item["qty"]),
        f"¥{item['unit_price']:,}",
        f"¥{amount:,}",
    ]
    aligns = ["L", "C", "R", "R"]
    row_y = pdf.get_y()
    for val, w, align in zip(values, col_widths, aligns):
        pdf.set_xy(pdf.get_x(), row_y)
        pdf.set_fill_color(248, 250, 255) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(w, 8, val, border=0, align=align, fill=True,
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(8)
    # bottom border
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    pdf.line(LEFT, pdf.get_y(), LEFT + W, pdf.get_y())

# Summary rows (right-aligned)
summary_x = LEFT + col_widths[0] + col_widths[1]
summary_w = col_widths[2] + col_widths[3]

def summary_row(label, value, bold=False):
    pdf.set_x(summary_x)
    pdf.set_font("bold" if bold else "regular", size=9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(col_widths[2], 7, label, align="R",
             new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(col_widths[3], 7, value, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.ln(2)
summary_row("小計", f"¥{subtotal:,}")
summary_row("消費税（10%）", f"¥{tax:,}")
pdf.set_draw_color(50, 80, 150)
pdf.set_line_width(0.5)
pdf.line(summary_x, pdf.get_y(), LEFT + W, pdf.get_y())
summary_row("合計（税込）", f"¥{total:,}", bold=True)

pdf.ln(10)

# ── Bank info ──────────────────────────────────────────
pdf.set_draw_color(200, 200, 200)
pdf.set_fill_color(250, 250, 250)
pdf.set_line_width(0.3)
box_y = pdf.get_y()
pdf.rect(LEFT, box_y, W, 30, style="FD")
pdf.set_xy(LEFT + 3, box_y + 3)
pdf.set_font("bold", size=9)
pdf.set_text_color(50, 80, 150)
pdf.cell(0, 5, "お振込先", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

b = cfg["bank"]
bank_lines = [
    f"{b['bank_name']}　{b['branch_name']}",
    f"{b['account_type']}　口座番号: {b['account_number']}",
    f"口座名義: {b['account_holder']}",
]
pdf.set_font("regular", size=9.5)
pdf.set_text_color(30, 30, 30)
for line in bank_lines:
    pdf.set_x(LEFT + 3)
    pdf.cell(0, 5.5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# ──備考 ──────────────────────────────────────────────
pdf.ln(6)
pdf.set_x(LEFT)
pdf.set_font("bold", size=9)
pdf.set_text_color(50, 80, 150)
pdf.cell(0, 5, "備考", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_x(LEFT)
pdf.set_font("regular", size=9)
pdf.set_text_color(30, 30, 30)
pdf.cell(0, 5, "お振込手数料はご負担ください", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Output
out_path = "/Users/higuchi/Desktop/my-first-project/invoice_20260525_002.pdf"
pdf.output(out_path)
print(f"OK: {out_path}")
