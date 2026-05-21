from langchain_core.tools import tool
from lib import TwilioService

@tool
def send_whatsapp_message(
    to_number: str, 
    body: str = None, 
    media_url: str = None,
    content_sid: str = None,
    content_variables: dict = None
) -> str:
    """
    Envía un mensaje de WhatsApp a un destinatario utilizando Twilio.
    
    Args:
        to_number (str): El número de teléfono destino en formato internacional (ej. '+5216981049748').
                         Para México, asegúrate de incluir el '1' después del código de país '52' (ej. '+521...').
        body (str, opcional): El contenido del mensaje de texto simple a enviar.
        media_url (str, opcional): URL de una imagen o documento (como PDF) para adjuntar al mensaje.
        content_sid (str, opcional): Identificador (SID) de la plantilla pre-aprobada si se usa Content API de Twilio.
        content_variables (dict, opcional): Diccionario con las variables de la plantilla (ej. {"1": "fecha", "2": "hora"}).
        
    Returns:
        str: Mensaje de confirmación de éxito o error al enviar.
    """
    try:
        service = TwilioService()
        success = service.send_whatsapp_message(
            to_number=to_number,
            body=body,
            media_url=media_url,
            content_sid=content_sid,
            content_variables=content_variables
        )
        if success:
            return f"Mensaje enviado con éxito a {to_number}."
        else:
            return f"Error: No se pudo enviar el mensaje a {to_number}. Verifica la configuración y que el número se haya unido al Sandbox."
    except Exception as e:
        return f"Error en la herramienta al enviar mensaje de WhatsApp: {str(e)}"
