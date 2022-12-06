# Elaboracion del proceso main
# Cristian Rubio Barato 3ºC

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import logging
import Ice
Ice.loadSlice("iceflix.ice")
import IceFlix  # pylint:disable=C0413 E0401


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Main()
        self.proxy = None
        self.adapter = None

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
    def __init__(self):
        self.servicios_autenticador = {}
        self.proxies_autenticador = []
        self.servicios_catalogo = {}
        self.proxies_catalogo = []
        self.servicios_archivo = {}
        self.file_proxies = []

    def newService(self, proxy, id_service, current):  # pylint:disable=invalid-name, unused-argument
        "Receive a proxy of a new service."
        # Si no encontramos el id del servicio en la lista de autenticadores de servicios lo
        # añadimos, además de el proxy. Eso lo haremos para tosos los servicios
        # (authenticator, catalogo y ficheros).

        if id_service not in self.servicios_autenticador:
            logging.info("Authenticator service")
            self.servicios_autenticador[id_service] = IceFlix.AuthenticatorPrx.uncheckedCast(
                id_service)
            self.proxies_autenticador.append(
                IceFlix.AuthenticatorPrx.uncheckedCast(id_service))

        elif id_service not in self.servicios_catalogo:
            logging.info("Catalog service")
            self.servicios_catalogo[id_service] = IceFlix.MediaCatalogPrx.uncheckedCast(
                id_service)
            self.proxies_catalogo.append(
                IceFlix.MediaCatalogPrx.uncheckedCast(id_service))

        elif id_service not in self.servicios_archivo:
            logging.info("File service")
            self.servicios_archivo[id_service] = IceFlix.FileServicePrx.uncheckedCast(
                id_service)
            self.file_proxies.append(
                IceFlix.FileServicePrx.uncheckedCast(id_service))

    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        service = self.proxies_autenticador
        services = list(service)
        if not services:
            raise IceFlix.TemporaryUnavailable()
        auth = services.pop(0)
        # seleccionamos uno de los servicios al azar con la funcion choice
        return auth

    def getCatalog(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        service = self.proxies_catalogo
        services = list(service)
        if not services:
            raise IceFlix.TemporaryUnavailable()
        catalog = services.pop(0)
        return catalog

    def getFile(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        service = self.file_proxies
        services = list(service)
        if not services:
            raise IceFlix.TemporaryUnavailable()
        file = services.pop(0)
        return file

    def announce(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Announcements handler."
        
        return
