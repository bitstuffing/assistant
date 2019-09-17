Esta es una iniciativa debido a que los desarrollos de Google-Assistant, como todas las cosas que libera Google, dejan de funcionar ya que al cabo de unos meses sus APIs gratuitas dejan de estar disponibles debido a que siempre sacan unas más nuevas

Este es un intento de reconstrucción de Google Assistant personalizado utilizando las librerías de Snowboy (https://github.com/Kitt-AI/snowboy) y Python Google-Assistant gRPC API (https://github.com/googlesamples/assistant-sdk-python/tree/master/google-assistant-sdk/googlesamples/assistant/grpc)

Para empezar tendrás que configurarte con tu cuenta de google unos credenciales para ser usados desde el Google-Assistant-SDK

En la configuración tienes que crear dos cosas:
- Un proyecto
- Un dispositivo (dentro del proyecto)

Una vez hecho eso tienes que dar permisos a tu aplicación para poder utilizar el Google-Assistant, la alerta aparecerá durante el proceso, así que estate atento.

Si necesitas personalizar el trigger que lanza la escucha deberás de prestar atención al siguiente extracto (snowboy testing online, aunque puedes generarlo desde local):

Hotword as a Service

Snowboy now offers Hotword as a Service through the https://snowboy.kitt.ai/api/v1/train/ endpoint. Check out the Full Documentation and example Python/Bash script (other language contributions are very welcome).

As a quick start, POST to https://snowboy.kitt.ai/api/v1/train:

{
    "name": "a word",
    "language": "en",
    "age_group": "10_19",
    "gender": "F",
    "microphone": "mic type",
    "token": "<your auth token>",
    "voice_samples": [
        {wave: "<base64 encoded wave data>"},
        {wave: "<base64 encoded wave data>"},
        {wave: "<base64 encoded wave data>"}
    ]
}

then you'll get a trained personal model in return!


Enjoy!
