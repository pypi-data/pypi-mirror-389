from correos_preregistro.requests.preregistro_envio import (
    RequestPreregistroEnvio,
    RequestPreregistroEnvioDatosDireccion,
    RequestPreregistroEnvioDatosSMS,
    RequestPreregistroEnvioDestinatario,
    RequestPreregistroEnvioEnvio,
    RequestPreregistroEnvioIdentificacion,
    RequestPreregistroEnvioRemitente,
)
from correos_preregistro.responses.preregistro_envio import ResponsePreregistroEnvio


class PreRegistrationShipment:
    @classmethod
    def create(cls, client, code, receiver, sender, package):
        xml_destinatario = cls._destinatario(receiver)
        xml_remitente = cls._remitente(sender)
        xml_envio = cls._envio(package)

        request = RequestPreregistroEnvio(
            codigo_etiquetador=code,
            destinatario=xml_destinatario,
            remitente=xml_remitente,
            envio=xml_envio,
        ).xml
        response = client.send_request(payload=request)
        return ResponsePreregistroEnvio(response)

    def _destinatario(receiver):
        if receiver.nif:
            xml_identificacion = RequestPreregistroEnvioIdentificacion(
                nombre=receiver.name,
                nif=receiver.nif,
            ).xml
        else:
            xml_identificacion = RequestPreregistroEnvioIdentificacion(
                nombre=receiver.name,
                apellidos=receiver.surname,
            ).xml
        xml_direccion = RequestPreregistroEnvioDatosDireccion(
            direccion=receiver.address,
            localidad=receiver.city,
            provincia=receiver.state,
        ).xml
        xml_datos_sms = RequestPreregistroEnvioDatosSMS(
            numero=receiver.sms_phone,
            idioma=1 if receiver.lang == "ES" else 2,
        ).xml
        return RequestPreregistroEnvioDestinatario(
            identificacion=xml_identificacion,
            direccion=xml_direccion,
            cp=receiver.zip,
            telefono=receiver.phone,
            email=receiver.email,
            datos_sms=xml_datos_sms,
        ).xml

    def _remitente(sender):
        xml_identificacion = RequestPreregistroEnvioIdentificacion(
            nombre=sender.name,
            nif=sender.nif,
        ).xml
        xml_direccion = RequestPreregistroEnvioDatosDireccion(
            direccion=sender.address,
            localidad=sender.city,
            provincia=sender.state,
        ).xml
        return RequestPreregistroEnvioRemitente(
            identificacion=xml_identificacion,
            direccion=xml_direccion,
            cp=sender.zip,
            telefono=sender.phone,
            email=sender.email,
        ).xml

    def _envio(package):
        return RequestPreregistroEnvioEnvio(
            cod_producto=package.product_code,
            modalidad_entrega=package.delivery_modality,
            tipo_franqueo=package.postage_type,
            tipo_peso=package.weight_type,
            peso=package.weight,
        ).xml
