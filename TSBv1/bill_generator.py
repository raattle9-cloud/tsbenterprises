"""
PDF Bill/Invoice generator for TSB Enterprises.
Generates a professional booking receipt using ReportLab.

Rs. is used instead of the Unicode rupee sign (U+20B9) because
ReportLab's built-in PDF fonts (Helvetica/Times/Courier) do not
include that glyph and would render it as a black square.
"""
import io
import os
import logging
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, Image
)

logger = logging.getLogger('TSBv1')

# ── Brand colours ────────────────────────────────────────────────────────────
C_NAVY    = colors.HexColor('#0d3b6e')
C_BLUE    = colors.HexColor('#1565c0')
C_TEAL    = colors.HexColor('#0097a7')
C_GREEN   = colors.HexColor('#2e7d32')
C_AMBER   = colors.HexColor('#f57f17')
C_RED     = colors.HexColor('#c62828')
C_WHITE   = colors.white
C_LIGHT   = colors.HexColor('#f0f4ff')
C_GREY    = colors.HexColor('#616161')
C_LTGREY  = colors.HexColor('#e0e0e0')
C_DARKGRY = colors.HexColor('#212121')

W, H = A4  # 595 x 842 pt


def _logo_path():
    """Return absolute path to the TSB logo, or None if not found."""
    from django.conf import settings
    candidates = [
        os.path.join(settings.STATIC_ROOT, 'app', 'images', 'product', 'tsb_logo.png'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'app', 'images', 'product', 'tsb_logo.png'),
        os.path.join(settings.BASE_DIR, 'static', 'app', 'images', 'product', 'tsb_logo.png'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _styles():
    base = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    return {
        'company': S('company',
                     fontName='Helvetica-Bold', fontSize=22,
                     textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=1*mm),
        'tagline': S('tagline',
                     fontName='Helvetica-Oblique', fontSize=9,
                     textColor=colors.HexColor('#b3d4f5'), alignment=TA_CENTER),
        'receipt_title': S('receipt_title',
                           fontName='Helvetica-Bold', fontSize=13,
                           textColor=C_NAVY, alignment=TA_CENTER,
                           spaceBefore=3*mm, spaceAfter=1*mm),
        'section': S('section',
                     fontName='Helvetica-Bold', fontSize=10,
                     textColor=C_WHITE, alignment=TA_LEFT),
        'label': S('label',
                   fontName='Helvetica-Bold', fontSize=9,
                   textColor=C_GREY),
        'value': S('value',
                   fontName='Helvetica', fontSize=9,
                   textColor=C_DARKGRY),
        'table_hdr': S('table_hdr',
                       fontName='Helvetica-Bold', fontSize=9,
                       textColor=C_WHITE, alignment=TA_CENTER),
        'total_lbl': S('total_lbl',
                       fontName='Helvetica-Bold', fontSize=10,
                       textColor=C_DARKGRY, alignment=TA_RIGHT),
        'grand_lbl': S('grand_lbl',
                       fontName='Helvetica-Bold', fontSize=12,
                       textColor=C_NAVY, alignment=TA_RIGHT),
        'grand_val': S('grand_val',
                       fontName='Helvetica-Bold', fontSize=13,
                       textColor=C_GREEN, alignment=TA_RIGHT),
        'status': S('status',
                    fontName='Helvetica-Bold', fontSize=14,
                    alignment=TA_CENTER, spaceBefore=2*mm, spaceAfter=2*mm),
        'footer': S('footer',
                    fontName='Helvetica', fontSize=7.5,
                    textColor=C_GREY, alignment=TA_CENTER),
        'footer_bold': S('footer_bold',
                         fontName='Helvetica-Bold', fontSize=7.5,
                         textColor=C_NAVY, alignment=TA_CENTER),
    }


def _section_header(title, styles):
    """A full-width navy bar used as a section title row."""
    data = [[Paragraph(title, styles['section'])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_NAVY),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    return t


def generate_bill_pdf(service, customer_name, quantity, total_amount=None,
                      booking_code=None, advance_paid=None, remaining_amount=None,
                      booking_date=None, order_id=None):
    """
    Generate a professional PDF booking receipt.
    Returns bytes (PDF content).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=12*mm, bottomMargin=15*mm
    )

    styles = _styles()
    elems = []

    # ── HEADER BANNER ─────────────────────────────────────────────────────────
    logo_path = _logo_path()
    if logo_path:
        logo_cell = Image(logo_path, width=18*mm, height=18*mm)
    else:
        logo_cell = Paragraph('', styles['company'])

    header_inner = Table(
        [[logo_cell,
          [Paragraph('TSB ENTERPRISES', styles['company']),
           Paragraph('Book. Visit. Enjoy.', styles['tagline'])]]],
        colWidths=[22*mm, 148*mm]
    )
    header_inner.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',   (1, 0), (1, 0),   'CENTER'),
    ]))

    header_wrapper = Table([[header_inner]], colWidths=[170*mm])
    header_wrapper.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_NAVY),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elems.append(header_wrapper)
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph('BOOKING RECEIPT', styles['receipt_title']))
    elems.append(HRFlowable(width='100%', thickness=1.5, color=C_BLUE, spaceAfter=3*mm))

    # ── META ROW (Invoice No + Date) ──────────────────────────────────────────
    now = datetime.now()
    invoice_label = order_id or f"TSB-{now.strftime('%Y%m%d%H%M%S')}"
    meta = Table(
        [['Invoice No:', invoice_label,
          'Date:', now.strftime('%d %b %Y'),
          'Time:', now.strftime('%I:%M %p')]],
        colWidths=[25*mm, 55*mm, 12*mm, 35*mm, 12*mm, 31*mm]
    )
    meta.setStyle(TableStyle([
        ('FONTNAME',    (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',    (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME',    (4, 0), (4, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR',   (0, 0), (0, -1), C_GREY),
        ('TEXTCOLOR',   (2, 0), (2, -1), C_GREY),
        ('TEXTCOLOR',   (4, 0), (4, -1), C_GREY),
        ('TEXTCOLOR',   (1, 0), (1, -1), C_DARKGRY),
        ('TEXTCOLOR',   (3, 0), (3, -1), C_DARKGRY),
        ('TEXTCOLOR',   (5, 0), (5, -1), C_DARKGRY),
        ('BACKGROUND',  (0, 0), (-1, -1), C_LIGHT),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('BOX',         (0, 0), (-1, -1), 0.5, C_LTGREY),
    ]))
    elems.append(meta)
    elems.append(Spacer(1, 4*mm))

    # ── CUSTOMER DETAILS ─────────────────────────────────────────────────────
    elems.append(_section_header('  CUSTOMER DETAILS', styles))
    elems.append(Spacer(1, 2*mm))

    cust_rows = [['Customer Name', customer_name]]
    if booking_code:
        cust_rows.append(['Booking Code', booking_code])
    if booking_date:
        cust_rows.append(['Visit Date', str(booking_date)])

    cust_table = Table(cust_rows, colWidths=[45*mm, 125*mm])
    cust_table.setStyle(TableStyle([
        ('FONTNAME',  (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), C_GREY),
        ('TEXTCOLOR', (1, 0), (1, -1), C_DARKGRY),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [C_WHITE, C_LIGHT]),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, C_LTGREY),
        ('BOX',       (0, 0), (-1, -1), 0.5, C_LTGREY),
    ]))
    elems.append(cust_table)
    elems.append(Spacer(1, 4*mm))

    # ── ORDER DETAILS TABLE ───────────────────────────────────────────────────
    elems.append(_section_header('  ORDER DETAILS', styles))
    elems.append(Spacer(1, 2*mm))

    try:
        unit_price = float(service.discounted_price)
    except (TypeError, ValueError, AttributeError):
        unit_price = 0.0

    item_total = unit_price * quantity

    thead = [['#', 'Service / Product', 'Qty', 'Unit Price', 'Total']]
    trow  = [['1', str(service.title), str(quantity),
              f'Rs. {unit_price:,.2f}', f'Rs. {item_total:,.2f}']]

    order_table = Table(thead + trow,
                        colWidths=[10*mm, 85*mm, 15*mm, 30*mm, 30*mm])
    order_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND',   (0, 0), (-1, 0), C_BLUE),
        ('TEXTCOLOR',    (0, 0), (-1, 0), C_WHITE),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('ALIGN',        (0, 0), (-1, 0), 'CENTER'),
        # Data rows
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN',        (0, 1), (0,  -1), 'CENTER'),
        ('ALIGN',        (2, 1), (2,  -1), 'CENTER'),
        ('ALIGN',        (3, 1), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT]),
        # Grid
        ('GRID',         (0, 0), (-1, -1), 0.4, C_LTGREY),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
    ]))
    elems.append(order_table)
    elems.append(Spacer(1, 4*mm))

    # ── PAYMENT SUMMARY ───────────────────────────────────────────────────────
    elems.append(_section_header('  PAYMENT SUMMARY', styles))
    elems.append(Spacer(1, 2*mm))

    shipping_gst = 40.0
    is_advance = advance_paid is not None

    if is_advance:
        # total_amount here is the FULL booking value (passed from booking.total_amount)
        full_value = float(total_amount) if total_amount is not None else item_total + shipping_gst
        adv = float(advance_paid)
        rem = float(remaining_amount) if remaining_amount is not None else max(0.0, full_value - adv)

        pay_rows = [
            ['Subtotal (services)',      f'Rs. {item_total:,.2f}'],
            ['Handling / Convenience',   f'Rs. {shipping_gst:,.2f}'],
            ['TOTAL BOOKING VALUE',      f'Rs. {full_value:,.2f}'],
            ['Advance Paid (Online)',     f'Rs. {adv:,.2f}'],
            ['Balance Due at Venue',     f'Rs. {rem:,.2f}'],
        ]
        # Row indices for special styling
        booking_val_idx = 2   # TOTAL BOOKING VALUE  — bold navy/navy
        advance_idx     = 3   # Advance Paid         — bold blue/blue
        venue_idx       = 4   # Balance Due          — bold amber/amber

        ts = [
            ('FONTNAME',  (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE',  (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), C_GREY),
            ('TEXTCOLOR', (1, 0), (1, -1), C_DARKGRY),
            ('ALIGN',     (0, 0), (-1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 0), (1, 1), [C_WHITE, C_LIGHT]),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BOX',       (0, 0), (-1, -1), 0.5, C_LTGREY),
            ('LINEBELOW', (0, 0), (-1, -2), 0.3, C_LTGREY),
            # TOTAL BOOKING VALUE row
            ('LINEABOVE',     (0, booking_val_idx), (-1, booking_val_idx), 1.5, C_NAVY),
            ('BACKGROUND',    (0, booking_val_idx), (-1, booking_val_idx), C_LIGHT),
            ('FONTNAME',      (0, booking_val_idx), (-1, booking_val_idx), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, booking_val_idx), (-1, booking_val_idx), 10),
            ('TEXTCOLOR',     (0, booking_val_idx), (0, booking_val_idx), C_NAVY),
            ('TEXTCOLOR',     (1, booking_val_idx), (1, booking_val_idx), C_NAVY),
            ('TOPPADDING',    (0, booking_val_idx), (-1, booking_val_idx), 6),
            ('BOTTOMPADDING', (0, booking_val_idx), (-1, booking_val_idx), 6),
            # Advance Paid row — highlighted in blue
            ('FONTNAME',  (0, advance_idx), (-1, advance_idx), 'Helvetica-Bold'),
            ('FONTSIZE',  (0, advance_idx), (-1, advance_idx), 10),
            ('TEXTCOLOR', (0, advance_idx), (-1, advance_idx), C_BLUE),
            ('BACKGROUND',(0, advance_idx), (-1, advance_idx), colors.HexColor('#e3f2fd')),
            ('TOPPADDING',    (0, advance_idx), (-1, advance_idx), 6),
            ('BOTTOMPADDING', (0, advance_idx), (-1, advance_idx), 6),
            # Balance Due row — highlighted in amber
            ('FONTNAME',  (0, venue_idx), (-1, venue_idx), 'Helvetica-Bold'),
            ('FONTSIZE',  (0, venue_idx), (-1, venue_idx), 10),
            ('TEXTCOLOR', (0, venue_idx), (-1, venue_idx), C_AMBER),
            ('BACKGROUND',(0, venue_idx), (-1, venue_idx), colors.HexColor('#fff8e1')),
            ('TOPPADDING',    (0, venue_idx), (-1, venue_idx), 6),
            ('BOTTOMPADDING', (0, venue_idx), (-1, venue_idx), 6),
        ]
    else:
        grand_total = float(total_amount) if total_amount is not None else item_total + shipping_gst
        pay_rows = [
            ['Subtotal',        f'Rs. {item_total:,.2f}'],
            ['Handling / GST',  f'Rs. {shipping_gst:,.2f}'],
            ['TOTAL PAID',      f'Rs. {grand_total:,.2f}'],
        ]
        grand_idx = 2
        ts = [
            ('FONTNAME',  (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE',  (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), C_GREY),
            ('TEXTCOLOR', (1, 0), (1, -1), C_DARKGRY),
            ('ALIGN',     (0, 0), (-1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 0), (-1, grand_idx - 1), [C_WHITE, C_LIGHT]),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE',    (0, grand_idx), (-1, grand_idx), 1.5, C_NAVY),
            ('BACKGROUND',   (0, grand_idx), (-1, grand_idx), colors.HexColor('#e8f5e9')),
            ('FONTNAME',     (0, grand_idx), (-1, grand_idx), 'Helvetica-Bold'),
            ('FONTSIZE',     (0, grand_idx), (-1, grand_idx), 11),
            ('TEXTCOLOR',    (0, grand_idx), (0, grand_idx), C_NAVY),
            ('TEXTCOLOR',    (1, grand_idx), (1, grand_idx), C_GREEN),
            ('BOX',          (0, 0), (-1, -1), 0.5, C_LTGREY),
            ('LINEBELOW',    (0, 0), (-1, grand_idx - 1), 0.3, C_LTGREY),
            ('TOPPADDING',    (0, grand_idx), (-1, grand_idx), 6),
            ('BOTTOMPADDING', (0, grand_idx), (-1, grand_idx), 6),
        ]

    pay_table = Table(pay_rows, colWidths=[110*mm, 60*mm])
    pay_table.setStyle(TableStyle(ts))
    elems.append(pay_table)
    elems.append(Spacer(1, 5*mm))

    # ── STATUS BADGE ─────────────────────────────────────────────────────────
    if advance_paid is not None:
        status_txt   = 'ADVANCE PAYMENT CONFIRMED'
        status_color = C_AMBER
        status_bg    = colors.HexColor('#fff8e1')
    else:
        status_txt   = 'PAYMENT CONFIRMED'
        status_color = C_GREEN
        status_bg    = colors.HexColor('#e8f5e9')

    status_style = ParagraphStyle(
        'StatusBadge', parent=getSampleStyleSheet()['Normal'],
        fontName='Helvetica-Bold', fontSize=13,
        textColor=status_color, alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0,
    )
    badge = Table([[Paragraph(f'✓  {status_txt}', status_style)]],
                  colWidths=[170*mm])
    badge.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), status_bg),
        ('BOX',           (0, 0), (-1, -1), 1.2, status_color),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elems.append(badge)
    elems.append(Spacer(1, 6*mm))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    elems.append(HRFlowable(width='100%', thickness=0.8, color=C_LTGREY,
                             spaceBefore=2*mm, spaceAfter=3*mm))
    elems.append(Paragraph('TSB Enterprises — Book. Visit. Enjoy.', styles['footer_bold']))
    elems.append(Paragraph(
        'For support: support@tsbenterprises.com  |  gowaterpark.in',
        styles['footer']
    ))
    elems.append(Paragraph(
        f'Generated on {now.strftime("%d %b %Y at %I:%M %p")}  •  This is a computer-generated receipt.',
        styles['footer']
    ))

    doc.build(elems)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    print(f"[BILL_GEN] PDF generated: {len(pdf_bytes)} bytes for {service.title}")
    logger.info(f"[BILL_GEN] PDF generated: {len(pdf_bytes)} bytes for {service.title}")
    return pdf_bytes


def generate_invoice_pdf(invoice):
    """Generate a PDF from an Invoice model instance (for on-demand download)."""
    booking = invoice.advance_booking
    kwargs = dict(
        service=invoice.service,
        customer_name=invoice.customer.name,
        quantity=invoice.quantity,
        total_amount=invoice.amount,
        order_id=invoice.invoice_no,
    )
    if booking:
        try:
            kwargs['booking_code']     = booking.booking_code
            kwargs['advance_paid']     = float(str(booking.advance_paid))
            kwargs['remaining_amount'] = float(str(booking.remaining_amount))
            kwargs['booking_date']     = str(booking.booking_date)
            # Pass the FULL booking value so the PDF shows correct totals,
            # not invoice.amount which is only the advance paid.
            kwargs['total_amount']     = float(str(booking.total_amount))
        except Exception:
            pass
    return generate_bill_pdf(**kwargs)


def save_bill_pdf(pdf_bytes, filename=None):
    """Save PDF to a temp file and return the path."""
    import tempfile
    if not filename:
        filename = f"TSB_Invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)
    print(f"[BILL_GEN] PDF saved to: {filepath}")
    return filepath
