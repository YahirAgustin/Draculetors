from twilio.rest import Client
from config.config import settings

class TwilioService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        # El número de Twilio Sandbox por defecto es 'whatsapp:+14155238886'
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER or 'whatsapp:+14155238886'
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None

    def send_whatsapp_message(
        self, 
        to_number: str, 
        body: str = None, 
        media_url: str = None,
        content_sid: str = None,
        content_variables: str = None
    ) -> bool:
        """
        Envía un mensaje de WhatsApp utilizando Twilio.
        
        Args:
            to_number (str): Número del destinatario con formato internacional (ej. '+521234567890').
            body (str, opcional): Cuerpo del mensaje.
            media_url (str, opcional): URL de una imagen o documento para enviar como archivo adjunto.
            content_sid (str, opcional): El SID del contenido/plantilla (Content API).
            content_variables (str/dict, opcional): Variables en formato JSON string o diccionario para la plantilla.
            
        Returns:
            bool: True si el mensaje se envió exitosamente, False en caso contrario.
        """
        if not self.client:
            print("Error: Twilio Client no inicializado. Verifica tus credenciales (TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN).")
            return False

        # Asegurar el formato 'whatsapp:xxxx' para el destinatario
        to_number = to_number.strip()
        if not to_number.startswith('whatsapp:'):
            to_number = f"whatsapp:{to_number}"

        # Asegurar el formato 'whatsapp:xxxx' para el remitente
        from_number = self.from_number.strip()
        if not from_number.startswith('whatsapp:'):
            from_number = f"whatsapp:{from_number}"

        try:
            kwargs = {
                "from_": from_number,
                "to": to_number
            }
            
            if body:
                kwargs["body"] = body
            if media_url:
                kwargs["media_url"] = [media_url]
            if content_sid:
                kwargs["content_sid"] = content_sid
            if content_variables:
                # Si viene como dict, lo convertimos a string JSON
                import json
                if isinstance(content_variables, dict):
                    kwargs["content_variables"] = json.dumps(content_variables)
                else:
                    kwargs["content_variables"] = content_variables

            message = self.client.messages.create(**kwargs)
            print(f"Mensaje enviado exitosamente. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Error al enviar mensaje de WhatsApp: {e}")
            return False
