from azure.communication.email import EmailClient
from fastapi import HTTPException
import os

connection_string = os.getenv("AZURE_EMAIL_CONNECTION_STRING")
# from_email = os.getenv("AZURE_COMMUNICATION_EMAIL_FROM")

email_client = EmailClient.from_connection_string(connection_string)


def send_email_with_attachment(
    partner, to_emails, cc_emails, subject, html, attachments
):

    recipients = {"to": [{"address": email} for email in to_emails]}
    if cc_emails:
        recipients["cc"] = [{"address": email} for email in cc_emails]

    message = {
        "senderAddress": "DoNotReply@playground.kraliknorbert.com",
        "recipients": recipients,
        "content": {
            "subject": subject,
            "plainText": f"{partner} részére elküldésre került {len(attachments)} db számla a csatolmányban.",
            "html": html,
        },
        "attachments": attachments,
    }

    try:
        print("EmailClient begin_send meghívása...")
        poller = email_client.begin_send(message)
        print("Várakozás a küldési eredményre (poller.result)...")
        result = poller.result()
        print(result)
        # status = result["status"]
        print(
            f"Küldés eredménye: status={getattr(result, 'status', None)}, id={getattr(result, 'id', None)}"
        )
        if result.get("status") == "Succeeded":
            print("Email sikeresen elküldve.")
            return {
                "message": "Email elküldve",
                "operation_id": result.get("id"),
                "status": result.get("status"),
            }
        else:
            print(
                f"Email küldés sikertelen! Status: {getattr(result, 'status', None)}, error: {getattr(result, 'error', None)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Email küldés sikertelen! Status: {getattr(result, 'status', None)}, error: {getattr(result, 'error', None)}",
            )
    except Exception as ex:
        print(f"Email küldési hiba (kivétel): {ex}")
        raise HTTPException(status_code=500, detail=f"Email küldési hiba: {ex}")
