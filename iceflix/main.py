#!/usr/bin/env python3
# Elaboracion del proceso main
# Cristian Rubio Barato 3ºC

import logging
import sys
import time
import os
import Ice
Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
import IceFlix  # pylint:disable=import-error


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

  # Si no encontramos el id del servicio en la lista de autenticadores de servicios lo
        # añadimos, además de el proxy. Eso lo haremos para tosos los servicios
        # (authenticator, catalogo y ficheros). Además, con la función ice_isA
        # lo que hacemos es comprobar el tipo de proxy, para que no se nos meta en
        # cualquiera https://doc.zeroc.com/ice/3.7/the-slice-language/operations-on-object
    def newService(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Receive a proxy of a new service."
        logging.info("****Creando un nuevo servicio****")
        if (proxy.ice_isA("::IceFlix::Authenticator") and
                service_id not in self.authenticator_services):
            self.time_services[service_id] = time.time()
            self.authenticator_proxies.append(
                IceFlix.AuthenticatorPrx.uncheckedCast(proxy))
            self.authenticator_services[service_id] = IceFlix.AuthenticatorPrx.uncheckedCast(
                service_id)

        elif proxy.ice_isA("::IceFlix::MediaCatalog") and service_id not in self.catalog_services:
            self.time_services[service_id] = time.time()
            self.catalog_proxies.append(
                IceFlix.MediaCatalogPrx.uncheckedCast(proxy))
            self.catalog_services[service_id] = IceFlix.MediaCatalogPrx.uncheckedCast(
                service_id)

        elif proxy.ice_isA("::IceFlix::FileService") and service_id not in self.file_services:
            self.time_services[service_id] = time.time()
            self.file_proxies.append(
                IceFlix.FileServicePrx.uncheckedCast(proxy))
            self.file_services[service_id] = IceFlix.FileServicePrx.uncheckedCast(
                service_id)

    # En este metodo, lo que haremos sera crear una variable services la cual contien
    # los proxies dependiendo de el tipo de servicio que busquemos, posteriormente,
    # cogemos el que esta en la posicion 0. Con stringToProxy, establecemos una comunicacion
    # con mainApp mediante el metodo communicator, pasandole el proxy obtenido.
    # con checked cast asumimos que el puntero es del tipo que indicamos.
    # En el primer caso seria de tipo AuthenticatorPrx
    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        logging.info("****Obteniendo proxy authenticator****")
        auth = ""
        services = self.authenticator_proxies
        if not services:
            raise IceFlix.TemporaryUnavailable()
        auth = services[0]
        auth = MainApp.communicator().stringToProxy(auth)
        proxy = IceFlix.AuthenticatorPrx.checkedCast(auth)
        return proxy

    def getCatalog(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        logging.info("****Obteniendo proxy catalogo****")
        catalog = ""
        services = self.catalog_proxies
        if not services:
            raise IceFlix.TemporaryUnavailable()
        catalog = services[0]
        catalog = MainApp.communicator().stringToProxy(catalog)
        proxy = IceFlix.AuthenticatorPrx.checkedCast(catalog)
        return proxy

    def getFile(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        logging.info("****Obteniendo proxy file****")
        archive = ""
        services = self.file_proxies
        if not services:
            raise IceFlix.TemporaryUnavailable()
        archive = services[0]
        archive = MainApp.communicator().stringToProxy(archive)
        proxy = IceFlix.AuthenticatorPrx.checkedCast(archive)
        return proxy

    # En este metodo, lo que hacemos sera, en primer lugar, mirar el tiempo con el que entra al
    # announce para poder compararlo con el que tenemos de antes (cuando se crea el servicio)
    # posteriormente comprobamos si el tiempo es mayor que 30, miramos de que tipo es el servicio,
    # para eliminar su proxy y su service_id, si no es mayor que 30 actualizamos el contador a 0
    # para el siguiente servicio.
    def announce(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Announcements handler."
        logging.info("****Comprobando announce****")
        actual_time = time.time()
        reemplazo = actual_time - self.time_services[service_id]
        if reemplazo > 30:

            if service_id in self.authenticator_services:
                self.authenticator_proxies.remove(proxy)
                self.authenticator_services.pop(service_id)

            elif service_id not in self.catalog_services:
                self.catalog_proxies.remove(proxy)
                self.catalog_services.pop(service_id)

            elif service_id not in self.file_services:
                self.file_proxies.remove(proxy)
                self.file_services.pop(service_id)
        else:
            reemplazo = 0


if __name__ == '__main__':
    aplication = MainApp()
    sys.exit(aplication.main(sys.argv))
