"""
Invoice creation and multi-party WhatsApp delivery.

Entry point: create_and_notify() — call it from any payment handler.
"""
import logging
from datetime import datetime

logger = logging.getLogger("TSBv1")


def _make_invoice_number(inv_id) -> str:
    """INV-YYYYMM-<suffix> unique per invoice using the pre-generated invoice ID."""
    try:
        suffix = f"{int(inv_id) % 1000000:06d}"
    except (TypeError, ValueError):
        suffix = f"{int(str(inv_id)[-6:], 16) % 1000000:06d}"
    return f"INV-{datetime.now().strftime('%Y%m')}-{suffix}"


def create_invoice(*, order=None, advance_booking=None, payment, customer, service, amount, quantity=1):
    """
    Persist an Invoice record and return it, or None on failure.
    Exactly one of `order` or `advance_booking` should be provided.
    """
    from .models import Invoice
    import time as _time, random as _random
    try:
        _inv_id = int(_time.time() * 1000) % 2147483647 + _random.randint(1, 999)
        invoice_no = _make_invoice_number(_inv_id)
        invoice = Invoice(
            id=_inv_id,
            invoice_no=invoice_no,
            order=order,
            advance_booking=advance_booking,
            customer=customer,
            service=service,
            payment=payment,
            amount=float(amount),
            quantity=int(quantity),
        )
        invoice.save()
        invoice.id = _inv_id  # restore integer after djongo ObjectId override
        logger.info(f"[INVOICE] Created {invoice_no} (token={invoice.token})")
        return invoice
    except Exception as e:
        logger.error(f"[INVOICE] Creation failed: {e}", exc_info=True)
        return None


def send_invoice_notifications(invoice):
    """
    Send WhatsApp invoice notifications to all three parties:
      1. Customer  — booking confirmation + PDF bill + QR code (advance)
      2. Vendor    — new booking alert + PDF bill
      3. Admin     — order summary + PDF bill

    Each party gets a rich text message followed by the PDF as a document.
    For advance bookings the customer also receives the QR code as an image.
    """
    from django.conf import settings
    from .whatsapp_service import send_whatsapp_text, upload_whatsapp_media, send_whatsapp_document
    from .bill_generator import generate_invoice_pdf

    booking = invoice.advance_booking
    is_advance = booking is not None
    service = invoice.service
    customer = invoice.customer
    invoice_no = invoice.invoice_no
    invoice_url = invoice.get_download_url()

    # ── Collect booking details ─────────────────────────────────────────────
    total_amt = float(invoice.amount)
    qty = invoice.quantity
    booking_code = booking.booking_code if is_advance else None
    booking_date = str(booking.booking_date) if is_advance else None
    advance_paid = float(str(booking.advance_paid)) if is_advance else None
    remaining = float(str(booking.remaining_amount)) if is_advance else None

    # ── Generate PDF once ───────────────────────────────────────────────────
    pdf_bytes = None
    media_id = None
    pdf_filename = f"TSB_Invoice_{invoice_no}.pdf"
    try:
        pdf_bytes = generate_invoice_pdf(invoice)
        logger.info(f"[INVOICE] PDF generated: {len(pdf_bytes)} bytes")
        media_id = upload_whatsapp_media(pdf_bytes, pdf_filename)
        if media_id:
            logger.info(f"[INVOICE] PDF uploaded to WhatsApp: media_id={media_id}")
        else:
            logger.warning("[INVOICE] PDF upload failed — will send text only")
    except Exception as e:
        logger.error(f"[INVOICE] PDF generation error: {e}", exc_info=True)

    # ── Upload QR image for advance bookings ────────────────────────────────
    qr_media_id = None
    if is_advance and booking.qr_code_data:
        try:
            import base64
            qr_b64 = booking.qr_code_data
            # Fix potential missing padding
            qr_b64 += '=' * (4 - len(qr_b64) % 4)
            qr_bytes = base64.b64decode(qr_b64)
            qr_media_id = upload_whatsapp_media(qr_bytes, f"QR_{booking_code}.png", mime_type="image/png")
            if qr_media_id:
                logger.info(f"[INVOICE] QR uploaded: media_id={qr_media_id}")
        except Exception as e:
            logger.error(f"[INVOICE] QR upload error: {e}", exc_info=True)

    def _send_to(phone, text_msg, role):
        if not phone:
            logger.warning(f"[INVOICE] No phone for {role} — skipping")
            return {"skipped": True, "reason": "no_phone"}
        try:
            # Normalize 10-digit Indian numbers to international format
            import re as _re
            _digits = _re.sub(r'\D', '', str(phone))
            if len(_digits) == 10:
                phone = '91' + _digits
            r1 = send_whatsapp_text(phone, text_msg)
            r2 = None
            if media_id:
                r2 = send_whatsapp_document(
                    phone, media_id, pdf_filename,
                    caption=f"Invoice {invoice_no} — {service.title}"
                )
            logger.info(f"[INVOICE] Notified {role} ({phone}): text={r1.get('success')}, pdf={r2.get('success') if r2 else 'n/a'}")
            return {"text": r1, "pdf": r2}
        except Exception as e:
            logger.error(f"[INVOICE] {role} notification failed: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Customer message ────────────────────────────────────────────────────
    if is_advance:
        customer_msg = (
            f"🎉 *Booking Confirmed!*\n\n"
            f"📋 *Invoice:* {invoice_no}\n"
            f"🏨 *Service:* {service.title}\n"
            f"👤 *Name:* {customer.name}\n"
            f"🎫 *Tickets:* {qty}\n"
            f"📅 *Visit Date:* {booking_date}\n"
            f"💰 *Total Amount:* ₹{total_amt:.0f}\n"
            f"💳 *Advance Paid:* ₹{advance_paid:.0f}\n"
            f"💵 *Due at Entry:* ₹{remaining:.0f}\n"
            f"🎟️ *Booking Code:* {booking_code}\n\n"
            f"Your QR code is attached — show it at the entry gate.\n"
            f"📥 Download invoice: {invoice_url}\n\n"
            f"— TSB Enterprises"
        )
    else:
        customer_msg = (
            f"✅ *Order Confirmed!*\n\n"
            f"📋 *Invoice:* {invoice_no}\n"
            f"🏨 *Service:* {service.title}\n"
            f"👤 *Name:* {customer.name}\n"
            f"🛒 *Quantity:* {qty}\n"
            f"💰 *Amount Paid:* ₹{total_amt:.0f}\n\n"
            f"📥 Download invoice: {invoice_url}\n\n"
            f"Thank you for booking with TSB Enterprises!"
        )

    # ── Vendor message ──────────────────────────────────────────────────────
    if is_advance:
        vendor_msg = (
            f"🔔 *New Booking Received!*\n\n"
            f"📋 *Invoice:* {invoice_no}\n"
            f"🏨 *Service:* {service.title}\n"
            f"👤 *Customer:* {customer.name}\n"
            f"📱 *Contact:* {customer.mobile}\n"
            f"🎫 *Tickets:* {qty}\n"
            f"📅 *Visit Date:* {booking_date}\n"
            f"💳 *Advance Paid:* ₹{advance_paid:.0f}\n"
            f"💵 *Collect at Entry:* ₹{remaining:.0f}\n"
            f"🎟️ *Booking Code:* {booking_code}\n\n"
            f"Invoice attached below.\n— TSB Enterprises"
        )
    else:
        vendor_msg = (
            f"🔔 *New Order Received!*\n\n"
            f"📋 *Invoice:* {invoice_no}\n"
            f"🏨 *Service:* {service.title}\n"
            f"👤 *Customer:* {customer.name}\n"
            f"📱 *Contact:* {customer.mobile}\n"
            f"🛒 *Quantity:* {qty}\n"
            f"💰 *Amount:* ₹{total_amt:.0f}\n\n"
            f"Invoice attached below.\n— TSB Enterprises"
        )

    # ── Admin message ───────────────────────────────────────────────────────
    if is_advance:
        admin_msg = (
            f"📊 *TSB Admin — New Advance Booking*\n\n"
            f"📋 *Invoice:* {invoice_no}\n"
            f"🏨 *Service:* {service.title}\n"
            f"👤 *Customer:* {customer.name} ({customer.mobile})\n"
            f"🎫 *Tickets:* {qty}  |  📅 *Date:* {booking_date}\n"
            f"💳 *Advance:* ₹{advance_paid:.0f}  |  💵 *Remaining:* ₹{remaining:.0f}\n"
            f"🎟️ *Code:* {booking_code}\n\n"
            f"Invoice attached.\n— TSB System"
        )
    else:
        admin_msg = (
            f"📊 *TSB Admin — New Order*\n\n"
            f"📋 *Invoice:* {invoice_no}\n"
            f"🏨 *Service:* {service.title}\n"
            f"👤 *Customer:* {customer.name} ({customer.mobile})\n"
            f"🛒 *Qty:* {qty}  |  💰 *Amount:* ₹{total_amt:.0f}\n\n"
            f"Invoice attached.\n— TSB System"
        )

    results = {}
    results["customer"] = _send_to(customer.mobile, customer_msg, "customer")
    results["vendor"] = _send_to(service.vendor_whatsapp, vendor_msg, "vendor")
    results["owner"] = _send_to(
        getattr(settings, "PLATFORM_OWNER_PHONE", ""),
        admin_msg, "platform_owner"
    )

    # ── Send QR image to customer (advance bookings only) ───────────────────
    if is_advance and qr_media_id:
        try:
            from .whatsapp_service import _get_whatsapp_config, _validate_phone
            import requests as _req
            token, phone_id, api_version = _get_whatsapp_config()
            import re as _re2
            _cust_digits = _re2.sub(r'\D', '', str(customer.mobile))
            if len(_cust_digits) == 10:
                _cust_digits = '91' + _cust_digits
            to_clean = _validate_phone(_cust_digits)
            url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_clean,
                "type": "image",
                "image": {
                    "id": qr_media_id,
                    "caption": f"🎟️ Entry QR Code — {booking_code}\nShow this at the gate on {booking_date}"
                }
            }
            resp = _req.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload, timeout=20)
            logger.info(f"[INVOICE] QR image sent to customer: {resp.status_code}")
            results["qr_image"] = {"success": resp.status_code < 400}
        except Exception as e:
            logger.error(f"[INVOICE] QR image send failed: {e}", exc_info=True)

    return results


def create_and_notify(*, order=None, advance_booking=None, payment, customer, service, amount, quantity=1):
    """
    Create an Invoice record and send WhatsApp notifications to all three parties.
    Safe to call from payment handlers — all exceptions are caught internally.

    Returns the Invoice instance (or None if creation failed).
    """
    invoice = create_invoice(
        order=order,
        advance_booking=advance_booking,
        payment=payment,
        customer=customer,
        service=service,
        amount=amount,
        quantity=quantity,
    )
    if invoice:
        try:
            send_invoice_notifications(invoice)
        except Exception as e:
            logger.error(f"[INVOICE] Notification dispatch error: {e}", exc_info=True)
    return invoice
