"""
WhatsApp Business API integration for vendor notifications.
Adapted from the project's FastAPI WhatsApp microservice for Django (synchronous).
Uses the Meta Graph API to send text messages to vendors when purchases are made.
"""
import re
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"


def _get_whatsapp_config():
    """Get WhatsApp API configuration from Django settings."""
    token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    api_version = getattr(settings, 'WHATSAPP_API_VERSION', 'v22.0')
    return token, phone_id, api_version


def _validate_phone(number: str) -> str:
    """Validate and clean phone number to digits-only international format."""
    # Strip +, spaces, dashes
    cleaned = re.sub(r'[+\s\-()]', '', number)
    if not re.fullmatch(r'\d{10,15}', cleaned):
        raise ValueError(f"Invalid phone number format: {number}. Must be 10-15 digits, e.g. 919876543210")
    return cleaned


def send_whatsapp_text(to: str, body: str) -> dict:
    """
    Send a plain text WhatsApp message to the given phone number.
    
    Args:
        to: Recipient phone in international format (digits only, e.g. 919876543210)
        body: Message text (max 4096 chars)
    
    Returns:
        dict with API response on success, or error details on failure
    """
    token, phone_id, api_version = _get_whatsapp_config()
    
    print(f"[WHATSAPP_SVC] send_whatsapp_text called: to={to}")
    print(f"[WHATSAPP_SVC] Config: token={'SET (' + token[:10] + '...)' if token else 'EMPTY'}, phone_id={phone_id}, api_version={api_version}")
    
    if not token or not phone_id:
        msg = "WhatsApp credentials not configured — skipping notification"
        logger.warning(msg)
        print(f"[WHATSAPP_SVC] SKIP: {msg}")
        return {"skipped": True, "reason": "credentials_not_configured"}
    
    try:
        to = _validate_phone(to)
        print(f"[WHATSAPP_SVC] Phone validated: {to}")
    except ValueError as e:
        logger.error(f"WhatsApp phone validation failed: {e}")
        print(f"[WHATSAPP_SVC] PHONE VALIDATION ERROR: {e}")
        return {"skipped": True, "reason": str(e)}
    
    url = f"{GRAPH_API_BASE}/{api_version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": body[:4096],  # Meta's max text length
        },
    }
    
    print(f"[WHATSAPP_SVC] Sending to URL: {url}")
    print(f"[WHATSAPP_SVC] Message body (first 100 chars): {body[:100].encode('ascii', 'replace').decode()}...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"[WHATSAPP_SVC] Response status: {response.status_code}")
        print(f"[WHATSAPP_SVC] Response body: {response.text[:500]}")
        
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"raw": response.text}
            error_msg = error_data.get("error", {}).get("message", "Unknown API error")
            logger.error(f"WhatsApp API error ({response.status_code}): {error_msg}")
            print(f"[WHATSAPP_SVC] API ERROR ({response.status_code}): {error_msg}")
            return {"success": False, "status_code": response.status_code, "error": error_msg}
        
        result = response.json()
        logger.info(f"WhatsApp message sent successfully to {to}")
        print(f"[WHATSAPP_SVC] SUCCESS! Message sent to {to}")
        return {"success": True, "response": result}
        
    except requests.exceptions.Timeout:
        logger.error(f"WhatsApp API request timed out for {to}")
        print(f"[WHATSAPP_SVC] TIMEOUT for {to}")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API request failed: {e}")
        print(f"[WHATSAPP_SVC] REQUEST ERROR: {e}")
        return {"success": False, "error": str(e)}


def upload_whatsapp_media(file_bytes, filename, mime_type="application/pdf"):
    """
    Upload media to WhatsApp Business API.
    
    Returns: media_id string on success, None on failure
    """
    token, phone_id, api_version = _get_whatsapp_config()
    
    if not token or not phone_id:
        print("[WHATSAPP_SVC] SKIP upload: credentials not configured")
        return None
    
    url = f"{GRAPH_API_BASE}/{api_version}/{phone_id}/media"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    
    files = {
        'file': (filename, file_bytes, mime_type),
        'messaging_product': (None, 'whatsapp'),
        'type': (None, mime_type),
    }
    
    print(f"[WHATSAPP_SVC] Uploading media: {filename} ({len(file_bytes)} bytes)")
    
    try:
        response = requests.post(url, headers=headers, files=files, timeout=30)
        print(f"[WHATSAPP_SVC] Upload response status: {response.status_code}")
        print(f"[WHATSAPP_SVC] Upload response body: {response.text[:500]}")
        
        if response.status_code >= 400:
            error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else {"raw": response.text}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            logger.error(f"WhatsApp media upload failed ({response.status_code}): {error_msg}")
            print(f"[WHATSAPP_SVC] UPLOAD ERROR: {error_msg}")
            return None
        
        result = response.json()
        media_id = result.get("id")
        print(f"[WHATSAPP_SVC] Media uploaded successfully! media_id={media_id}")
        logger.info(f"WhatsApp media uploaded: {media_id}")
        return media_id
        
    except Exception as e:
        logger.error(f"WhatsApp media upload exception: {e}")
        print(f"[WHATSAPP_SVC] UPLOAD EXCEPTION: {e}")
        return None


def send_whatsapp_document(to, media_id, filename, caption=""):
    """
    Send a document message via WhatsApp using an uploaded media_id.
    """
    token, phone_id, api_version = _get_whatsapp_config()
    
    if not token or not phone_id:
        return {"skipped": True, "reason": "credentials_not_configured"}
    
    try:
        to = _validate_phone(to)
    except ValueError as e:
        return {"skipped": True, "reason": str(e)}
    
    url = f"{GRAPH_API_BASE}/{api_version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename,
        },
    }
    if caption:
        payload["document"]["caption"] = caption[:1024]
    
    print(f"[WHATSAPP_SVC] Sending document to {to}: {filename}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"[WHATSAPP_SVC] Document send status: {response.status_code}")
        print(f"[WHATSAPP_SVC] Document send response: {response.text[:500]}")
        
        if response.status_code >= 400:
            error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else {"raw": response.text}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            logger.error(f"WhatsApp document send failed ({response.status_code}): {error_msg}")
            print(f"[WHATSAPP_SVC] DOCUMENT SEND ERROR: {error_msg}")
            return {"success": False, "error": error_msg}
        
        result = response.json()
        print(f"[WHATSAPP_SVC] Document sent successfully to {to}")
        logger.info(f"WhatsApp document sent to {to}")
        return {"success": True, "response": result}
        
    except Exception as e:
        logger.error(f"WhatsApp document send failed: {e}")
        print(f"[WHATSAPP_SVC] DOCUMENT SEND EXCEPTION: {e}")
        return {"success": False, "error": str(e)}


def send_tsb_invoice_receipt_template(
    to: str,
    customer_name: str,
    service_name: str,
    invoice_no: str,
    date: str,
    total_amount: str,
    reference: str,
    invoice_token: str,
    pdf_media_id: str = None,
    pdf_filename: str = None,
) -> dict:
    """
    Send WhatsApp template `tsb_invoice_receipt` (English US) to a customer.

    Template structure:
        Header : Document (PDF) — attached if pdf_media_id is provided
        Body   : Hello {{1}}, ... Service: {{2}}, Invoice No: {{3}},
                 Date: {{4}}, Total Amount: Rs. {{5}}, Reference: {{6}}
        Button : "View Invoice" → https://tsbenterprises.onrender.com/invoices/{{1}}
                 (dynamic suffix = invoice_token + "/")
        Footer : TSB Enterprises - Book. Visit. Enjoy.
    """
    token, phone_id, api_version = _get_whatsapp_config()

    if not token or not phone_id:
        return {"skipped": True, "reason": "credentials_not_configured"}

    try:
        to_clean = _validate_phone(to)
    except ValueError as e:
        return {"skipped": True, "reason": str(e)}

    api_url = f"{GRAPH_API_BASE}/{api_version}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    components = []

    if pdf_media_id:
        components.append({
            "type": "header",
            "parameters": [{
                "type": "document",
                "document": {
                    "id": pdf_media_id,
                    "filename": pdf_filename or f"TSB_Invoice_{invoice_no}.pdf",
                },
            }],
        })

    components.append({
        "type": "body",
        "parameters": [
            {"type": "text", "text": str(customer_name)},
            {"type": "text", "text": str(service_name)},
            {"type": "text", "text": str(invoice_no)},
            {"type": "text", "text": str(date)},
            {"type": "text", "text": str(total_amount)},
            {"type": "text", "text": str(reference)},
        ],
    })

    components.append({
        "type": "button",
        "sub_type": "url",
        "index": "0",
        "parameters": [{"type": "text", "text": f"{invoice_token}/"}],
    })

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_clean,
        "type": "template",
        "template": {
            "name": "tsb_invoice_receipt",
            "language": {"code": "en_US"},
            "components": components,
        },
    }

    print(f"[WHATSAPP_SVC] Sending tsb_invoice_receipt template to {to_clean}")
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=20)
        print(f"[WHATSAPP_SVC] Template response {resp.status_code}: {resp.text[:400]}")
        if resp.status_code >= 400:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
            logger.error(f"WhatsApp tsb_invoice_receipt failed ({resp.status_code}): {err}")
            return {"success": False, "status_code": resp.status_code, "error": err}
        logger.info(f"WhatsApp tsb_invoice_receipt sent to {to_clean}")
        return {"success": True, "response": resp.json()}
    except Exception as e:
        logger.error(f"WhatsApp tsb_invoice_receipt request failed: {e}")
        return {"success": False, "error": str(e)}
def send_vendor_invoice_template(
    to: str,
    vendor_name: str,
    service_name: str,
    invoice_no: str,
    customer_name: str,
    quantity: str,
    total_amount: str,
    pdf_media_id: str = None,
) -> dict:
    """Vendor ke liye Template - 24hr Hi ki zarurat nahi"""
    token, phone_id, api_version = _get_whatsapp_config()
    if not token or not phone_id:
        return {"skipped": True, "reason": "credentials_not_configured"}
    try:
        to_clean = _validate_phone(to)
    except ValueError as e:
        return {"skipped": True, "reason": str(e)}

    api_url = f"{GRAPH_API_BASE}/{api_version}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    components = []
    if pdf_media_id:
        components.append({
            "type": "header",
            "parameters": [{"type": "document", "document": {"id": pdf_media_id}}],
        })
    
    components.append({
        "type": "body",
        "parameters": [
            {"type": "text", "text": str(vendor_name)},
            {"type": "text", "text": str(service_name)},
            {"type": "text", "text": str(invoice_no)},
            {"type": "text", "text": str(customer_name)},
            {"type": "text", "text": str(quantity)},
            {"type": "text", "text": str(total_amount)},
        ],
    })

    payload = {
        "messaging_product": "whatsapp",
        "to": to_clean,
        "type": "template",
        "template": {"name": "vendor_new_order_received", "language": {"code": "en_US"}, "components": components},
    }
    print(f"[WHATSAPP_SVC] Sending VENDOR template to {to_clean}")
    resp = requests.post(api_url, headers=headers, json=payload, timeout=20)
    print(f"[WHATSAPP_SVC] Vendor Template response {resp.status_code}: {resp.text[:500]}")
    if resp.status_code >= 400:
        return {"success": False, "error": resp.text[:500]}
    return {"success": True, "response": resp.json()}

def send_vendor_purchase_notification(service, customer_name, quantity, booking_code=None, 
                                       advance_paid=None, remaining_amount=None, booking_date=None,
                                       order_id=None, total_amount=None):
    """
    Send a purchase notification with PDF invoice to the vendor's WhatsApp number.
    
    Sends both a text summary AND a PDF invoice document.
    Falls back to text-only if PDF generation or upload fails.
    """
    vendor_number = getattr(service, 'vendor_whatsapp', '')
    if not vendor_number:
        print(f"[WHATSAPP_SVC] No vendor number for {service.title}")
        return None
    
    print(f"[WHATSAPP_SVC] === Sending vendor notification for {service.title} ===")
    
    # 1. Build text summary message
    lines = [
        "\U0001f514 *New Order Received!*",
        "",
        f"\U0001f4e6 *Service:* {service.title}",
        f"\U0001f464 *Customer:* {customer_name}",
        f"\U0001f4ca *Quantity:* {quantity}",
    ]
    
    if booking_code:
        lines.append(f"\U0001f3ab *Booking Code:* {booking_code}")
    if booking_date:
        lines.append(f"\U0001f4c5 *Date:* {booking_date}")
    if advance_paid is not None:
        lines.append(f"\U0001f4b0 *Advance Paid:* \u20b9{advance_paid}")
    if remaining_amount is not None:
        lines.append(f"\U0001f4b3 *Remaining:* \u20b9{remaining_amount}")
    if not booking_code and not advance_paid:
        try:
            total = float(service.discounted_price) * quantity
            lines.append(f"\U0001f4b0 *Total:* \u20b9{total}")
        except (TypeError, ValueError):
            pass
    
    lines.extend(["", "\U0001f4ce _Invoice PDF attached below_", "", "\u2014 TSB Enterprises"])
    message = "\n".join(lines)
    
    # 2. Send text summary first
    text_result = None
    try:
        text_result = send_whatsapp_text(vendor_number, message)
        print(f"[WHATSAPP_SVC] Text message result: {text_result}")
    except Exception as e:
        print(f"[WHATSAPP_SVC] Text message failed: {e}")
    
    # 3. Generate PDF invoice
    pdf_result = None
    try:
        from .bill_generator import generate_bill_pdf
        pdf_bytes = generate_bill_pdf(
            service=service,
            customer_name=customer_name,
            quantity=quantity,
            total_amount=total_amount,
            booking_code=booking_code,
            advance_paid=advance_paid,
            remaining_amount=remaining_amount,
            booking_date=booking_date,
            order_id=order_id,
        )
        print(f"[WHATSAPP_SVC] PDF generated: {len(pdf_bytes)} bytes")
        
        # 4. Upload PDF to WhatsApp
        from datetime import datetime
        filename = f"TSB_Invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        media_id = upload_whatsapp_media(pdf_bytes, filename)
        
        if media_id:
            # 5. Send document message
            caption = f"Invoice for {service.title} - {customer_name}"
            pdf_result = send_whatsapp_document(vendor_number, media_id, filename, caption)
            print(f"[WHATSAPP_SVC] PDF send result: {pdf_result}")
        else:
            print("[WHATSAPP_SVC] PDF upload failed, text-only notification sent")
            
    except Exception as e:
        logger.error(f"PDF generation/send failed: {e}")
        print(f"[WHATSAPP_SVC] PDF EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    return {
        "text_result": text_result,
        "pdf_result": pdf_result,
    }

