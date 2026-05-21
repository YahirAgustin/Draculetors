# Módulo de Comunicación con WhatsApp (Twilio)

Este módulo está diseñado para conectar nuestra aplicación con la red de WhatsApp a través del servicio de **Twilio**. Su objetivo principal es permitir que la aplicación envíe notificaciones y mensajes automáticos de forma directa a los usuarios en sus chats de WhatsApp.

---

## ¿Qué es y para qué sirve?

Este componente actúa como el canal de comunicación móvil para nuestros agentes. Sirve para:
- **Enviar notificaciones automáticas:** Como confirmaciones de transacciones, alertas o respuestas directas generadas por agentes de IA.
- **Compartir archivos adjuntos:** Permite enviar documentos o imágenes (como facturas, tickets o reportes).
- **Iniciar conversaciones de manera oficial:** Utilizando plantillas pre-aprobadas para recordar citas, enviar códigos de verificación, etc.

---

## ¿Cómo funciona?

1. **Conexión con Twilio:** Nuestra aplicación envía una solicitud segura a Twilio indicando el número del destinatario y el mensaje a enviar.
2. **Entrega a WhatsApp:** Twilio recibe la solicitud y se encarga de enviarla y entregarla al usuario a través de la infraestructura oficial de WhatsApp.
3. **El Sandbox (Entorno de pruebas):** Durante la etapa de desarrollo, se utiliza un "Sandbox" (un entorno simulado y gratuito). Para que un usuario pueda recibir mensajes del Sandbox, primero debe dar su consentimiento enviando un mensaje de activación desde su propio WhatsApp.

---

## Configuración y Credenciales

Para que el módulo funcione correctamente, se deben añadir las credenciales de tu cuenta de Twilio en el archivo `.env` ubicado en la raíz del proyecto:

* **`TWILIO_ACCOUNT_SID`**: Es el identificador público único de tu cuenta en Twilio.
* **`TWILIO_AUTH_TOKEN`**: Es la contraseña o clave secreta de autenticación de tu cuenta.
* **`TWILIO_WHATSAPP_NUMBER`**: Es el número oficial de Twilio desde el que se enviarán los mensajes (durante las pruebas se utiliza el número sandbox por defecto: `whatsapp:+14155238886`).

Ejemplo de configuración en tu archivo `.env`:
```env
TWILIO_ACCOUNT_SID=tu_account_sid_de_twilio
TWILIO_AUTH_TOKEN=tu_auth_token_de_twilio
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

---

## ⚠️ Aspectos Importantes para el Equipo

* **Formato de números telefónicos en México:** Al enviar mensajes a números mexicanos, WhatsApp exige utilizar el prefijo `+521` (intercalando un `1` después del código de país `52`, ej: `+52 1 698 104 9748`). Si se envía al formato simple `+52698...`, el mensaje no se entregará.
* **Consentimiento previo en Sandbox:** Recuerda que para realizar cualquier prueba en desarrollo, el teléfono receptor debe enviar primero el mensaje de activación (ej: `join region-rear`) al número del Sandbox para poder recibir mensajes del sistema.
