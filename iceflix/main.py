#!/usr/bin/env python3
# Elaboracion del proceso main
# Cristian Rubio Barato 3ºC

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import IceFlix  # pylint:disable=C0413 E0401
import logging
import sys
import time
import os
import Ice
Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))


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
        proxy = self.adapter.add(self.servant, comm.stringToIdentity("proxy"))
        print(proxy, flush=True)
        self.adapter.activate()
        self.proxy = self.adapter.addWithUUID(self.servant)
        self.shutdownOnInterrupt()
        comm.waitForShutdown()
        return 0


class Main(IceFlix.Main):
    # Creacion de diccionarios y listas para los distintos servicios
    def __init__(self):
        self.authenticator_services = {}
        self.authenticator_proxies = []
        self.catalog_services = {}
        self.catalog_proxies = []
        self.file_services = {}
        self.file_proxies = []
        self.time_services = []

    def newService(self, proxy, id_service, current):  # pylint:disable=invalid-name, unused-argument
        "Receive a proxy of a new service."
        # Si no encontramos el id del servicio en la lista de autenticadores de servicios lo
        # añadimos, además de el proxy. Eso lo haremos para tosos los servicios
        # (authenticator, catalogo y ficheros).
        if id_service not in self.authenticator_services:
            self.time_services[id_service] = time.time()
            logging.info("Authenticator service")
            self.authenticator_services[id_service] = IceFlix.AuthenticatorPrx.uncheckedCast(
                id_service)
            self.authenticator_proxies.append(
                IceFlix.AuthenticatorPrx.uncheckedCast(proxy))

        elif id_service not in self.catalog_services:
            self.time_services[id_service] = time.time()
            logging.info("Catalog service")
            self.catalog_services[id_service] = IceFlix.MediaCatalogPrx.uncheckedCast(
                id_service)
            self.catalog_proxies.append(
                IceFlix.MediaCatalogPrx.uncheckedCast(proxy))

        elif id_service not in self.file_services:
            self.time_services[id_service] = time.time()
            logging.info("File service")
            self.file_services[id_service] = IceFlix.FileServicePrx.uncheckedCast(
                id_service)
            self.file_proxies.append(
                IceFlix.FileServicePrx.uncheckedCast(proxy))

    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        service = self.authenticator_proxies
        services = list(service)
        if not services:
            raise IceFlix.TemporaryUnavailable()
        auth = services.pop(0)
        # seleccionamos uno de los servicios al azar con la funcion choice
        return auth

    def getCatalog(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        service = self.catalog_proxies
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
        archive = services.pop(0)
        return archive

    def announce(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Announcements handler."
        actual_time = time.time()
        reemplazo = actual_time - self.time_services[service_id]
        if reemplazo >= 30:
            self.time_services[service_id] = None
        else:
            reemplazo = 0

if __name__ == '__main__':
    aplication = MainApp()
    sys.exit(aplication.main(sys.argv))
