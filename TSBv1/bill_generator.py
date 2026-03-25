"""
PDF Bill/Invoice generator for vendor notifications.
Uses reportlab to create a professional invoice PDF.
"""
import io
import os
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger('TSBv1')


def generate_bill_pdf(service, customer_name, quantity, total_amount=None,
                      booking_code=None, advance_paid=None, remaining_amount=None,
                      booking_date=None, order_id=None):
    """
    Generate a PDF bill/invoice for a purchase.
    
    Returns: bytes (PDF file content)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=2*mm, alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER, spaceAfter=6*mm
    )
    heading_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontSize=12, textColor=colors.HexColor('#1a1a2e'),
        spaceBefore=4*mm, spaceAfter=2*mm,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#333333'),
        spaceAfter=1*mm
    )
    bold_style = ParagraphStyle(
        'BoldNormal', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#1a1a2e'),
        fontName='Helvetica-Bold', spaceAfter=1*mm
    )
    
    elements = []
    
    # ---- Header ----
    elements.append(Paragraph("TSB ENTERPRISES", title_style))
    elements.append(Paragraph("Service Booking Invoice", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a1a2e')))
    elements.append(Spacer(1, 4*mm))
    
    # ---- Invoice info ----
    now = datetime.now()
    invoice_no = f"TSB-{now.strftime('%Y%m%d%H%M%S')}"
    if order_id:
        invoice_no = f"TSB-{order_id[-8:]}" if len(str(order_id)) > 8 else f"TSB-{order_id}"
    
    invoice_data = [
        ['Invoice No:', invoice_no, 'Date:', now.strftime('%d %b %Y')],
        ['Time:', now.strftime('%I:%M %p'), '', ''],
    ]
    invoice_table = Table(invoice_data, colWidths=[25*mm, 55*mm, 15*mm, 55*mm])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 4*mm))
    
    # ---- Customer Details ----
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("CUSTOMER DETAILS", heading_style))
    elements.append(Paragraph(f"<b>Name:</b> {customer_name}", normal_style))
    if booking_code:
        elements.append(Paragraph(f"<b>Booking Code:</b> {booking_code}", normal_style))
    if booking_date:
        elements.append(Paragraph(f"<b>Booking Date:</b> {booking_date}", normal_style))
    elements.append(Spacer(1, 4*mm))
    
    # ---- Service Details Table ----
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("ORDER DETAILS", heading_style))
    
    # Calculate amounts
    try:
        unit_price = float(service.discounted_price)
    except (TypeError, ValueError, AttributeError):
        unit_price = 0.0
    
    item_total = unit_price * quantity
    shipping_gst = 40.0
    
    if total_amount is not None:
        grand_total = float(total_amount)
    else:
        grand_total = item_total + shipping_gst
    
    # Items table
    table_data = [
        ['#', 'Service', 'Qty', 'Unit Price', 'Total'],
        ['1', str(service.title), str(quantity), f'\u20b9{unit_price:.2f}', f'\u20b9{item_total:.2f}'],
    ]
    
    item_table = Table(table_data, colWidths=[10*mm, 75*mm, 15*mm, 30*mm, 30*mm])
    item_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Data rows
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 3*mm))
    
    # ---- Totals ----
    totals_data = []
    totals_data.append(['', '', 'Subtotal:', f'\u20b9{item_total:.2f}'])
    totals_data.append(['', '', 'Shipping/GST:', f'\u20b9{shipping_gst:.2f}'])
    
    if advance_paid is not None:
        totals_data.append(['', '', 'Advance Paid:', f'\u20b9{float(advance_paid):.2f}'])
    if remaining_amount is not None:
        totals_data.append(['', '', 'Remaining:', f'\u20b9{float(remaining_amount):.2f}'])
    
    totals_data.append(['', '', 'GRAND TOTAL:', f'\u20b9{grand_total:.2f}'])
    
    totals_table = Table(totals_data, colWidths=[45*mm, 50*mm, 35*mm, 30*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, -1), (3, -1), 11),
        ('TEXTCOLOR', (2, -1), (3, -1), colors.HexColor('#28a745')),
        ('LINEABOVE', (2, -1), (3, -1), 1.5, colors.HexColor('#1a1a2e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 6*mm))
    
    # ---- Payment Status ----
    if advance_paid is not None:
        status_text = "ADVANCE PAYMENT RECEIVED"
        status_color = colors.HexColor('#ffc107')
    else:
        status_text = "ORDER CONFIRMED"
        status_color = colors.HexColor('#28a745')
    
    status_style = ParagraphStyle(
        'Status', parent=styles['Normal'],
        fontSize=14, fontName='Helvetica-Bold',
        textColor=status_color, alignment=TA_CENTER,
        spaceBefore=2*mm, spaceAfter=2*mm
    )
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    elements.append(Paragraph(f"\u2713 {status_text}", status_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    
    # ---- Footer ----
    elements.append(Spacer(1, 8*mm))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Thank you for choosing TSB Enterprises!", footer_style))
    elements.append(Paragraph("For queries, contact us at support@tsbenterprises.com", footer_style))
    elements.append(Paragraph(f"Generated on {now.strftime('%d %b %Y at %I:%M %p')}", footer_style))
    
    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    print(f"[BILL_GEN] PDF generated: {len(pdf_bytes)} bytes for {service.title}")
    logger.info(f"[BILL_GEN] PDF generated: {len(pdf_bytes)} bytes for {service.title}")
    
    return pdf_bytes


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
