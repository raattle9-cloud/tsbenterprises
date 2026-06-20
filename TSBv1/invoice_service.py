"""
Invoice creation and multi-party WhatsApp delivery.

Entry point: create_and_notify() — call it from any payment handler.
"""
import logging
from datetime import datetime

logger = logging.getLogger("TSBv1")


def _make_invoice_number(payment_id) -> str:
    """INV-YYYYMM-<suffix> — payment_id may be int or MongoDB ObjectId."""
    import random
    try:
        suffix = f"{int(payment_id):06d}"
    except (TypeError, ValueError):
        # MongoDB ObjectId — use last 6 hex chars converted to int
        suffix = f"{int(str(payment_id)[-6:], 16) % 1000000:06d}"
    return f"INV-{datetime.now().strftime('%Y%m')}-{suffix}"


def create_invoice(*, order=None, advance_booking=None, payment, customer, service, amount, quantity=1):
    """
    Persist an Invoice record and return it, or None on failure.
    Exactly one of `order` or `advance_booking` should be provided.
    """
    from .models import Invoice
    import time as _time, random as _random
    try:
        invoice_no = _make_invoice_number(payment.id)
        _inv_id = int(_time.time() * 1000) % 2147483647 + _random.randint(1, 999)
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
      1. The customer (buyer)
      2. The service vendor
      3. The platform owner

    Uses template `purchase_receipt_3` plus a follow-up text with the direct link,
    so the recipient can tap through even if the template button URL is still the
    example placeholder in WhatsApp Business Manager.
    """
    from django.conf import settings
    from .whatsapp_service import send_purchase_receipt_template

    invoice_url = invoice.get_download_url()
    invoice_no = invoice.invoice_no
    results = {}

    def _notify(phone, name, role):
        if not phone:
            logger.warning(f"[INVOICE] No phone for {role} — skipping")
            return {"skipped": True, "reason": "no_phone"}
        try:
            result = send_purchase_receipt_template(
                to=phone,
                recipient_name=name,
                invoice_no=invoice_no,
                invoice_url=invoice_url,
            )
            logger.info(f"[INVOICE] Notified {role}: {name} ({phone})")
            return result
        except Exception as e:
            logger.error(f"[INVOICE] {role} notification failed: {e}", exc_info=True)
            return {"error": str(e)}

    results["customer"] = _notify(
        phone=invoice.customer.mobile,
        name=invoice.customer.name,
        role="customer",
    )
    results["vendor"] = _notify(
        phone=invoice.service.vendor_whatsapp,
        name=invoice.service.title,
        role="vendor",
    )
    results["owner"] = _notify(
        phone=getattr(settings, "PLATFORM_OWNER_PHONE", ""),
        name=getattr(settings, "PLATFORM_OWNER_NAME", "TSB Admin"),
        role="platform_owner",
    )

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
