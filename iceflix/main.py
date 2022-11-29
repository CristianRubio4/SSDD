# Elaboracion del proceso main
# Cristian Rubio Barato 3ºC

import logging
from random import choice
from uuid import uuid4
import Ice
Ice.loadSlice("ssdd-lab-template/iceflix/iceflix.ice")
import IceFlix  # pylint:disable=import-error


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Main()
        self.proxy = None
        self.adapter = None
        self.servicios_main = {}
        self.servicios_autenticador = {}
        self.proxies_autenticador = []
        self.servicios_catalogo = {}
        self.proxies_catalogo = []
        self.servicios_archivo = {}
        self.proxies_archivo = []
        self.uuid = str(uuid4())

    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        logging.info("Running Main application")
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("MainAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        return 0


class Main(IceFlix.Main):
    # Creacion de diccionarios y listas para los distintos servicios
    #  Usamos un uuid4 con el que implementamos identificadores unicos, con el uuid4 los generamos pero con una mayor diferenciacion

    def announce(self, id_servidor, servicio, current=None):  # pylint:disable=invalid-name, unused-argument
        # Si no encontramos el id en la lista de servicios_main lo añadimos

        if id_servidor not in self.servicios_main:
            self.servicios_main[id_servidor] = IceFlix.MainPrx.uncheckedCast(
                servicio)

        # Si no encontramos el id en la lista de autenticadores de servicios lo añadimos
        elif id_servidor not in self.servicios_autenticador:
            logging.info("Authenticator service")
            self.servicios_autenticador[id_servidor] = IceFlix.AuthenticatorPrx.uncheckedCast(
                servicio)
            self.proxies_autenticador.append(
                IceFlix.AuthenticatorPrx.uncheckedCast(servicio))

        elif id_servidor not in self.servicios_catalogo:
            logging.info("Catalog service")
            self.servicios_catalogo[id_servidor] = IceFlix.MediaCatalogPrx.uncheckedCast(
                servicio)
            self.proxies_catalogo.append(
                IceFlix.MediaCatalogPrx.uncheckedCast(servicio))

        elif id_servidor not in self.servicios_archivo:
            logging.info("File service")
            self.servicios_archivo[id_servidor] = IceFlix.FileServicePrx.uncheckedCast(
                servicio)
            self.proxies_archivo.append(
                IceFlix.FileServicePrx.uncheckedCast(servicio))

# REVISAR PORQUE NO ESTA BIEN CREO

    def get_authenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        service = self.proxies_autenticador
        authenticator_service = ""
        services = list(service.get('authentication service').values())
        if services == []:
            raise IceFlix.TemporaryUnavailable()
        # seleccionamos uno de los servicios al azar con la funcion choice
        authenticator_service = choice(services)
        return authenticator_service
