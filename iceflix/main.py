#!/usr/bin/env python3
"""Elaboracion del proceso main"""
# Cristian Rubio Barato 3ºC

import sys
import threading
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
        print("Running Main application")
        comm = self.communicator()
        self.adapter = comm.createObjectAdapterWithEndpoints(
            "MainAdapter", "tcp")
        proxy = self.adapter.addWithUUID(self.servant)
        print(proxy, flush=True)
        self.adapter.activate()
        self.proxy = self.adapter.addWithUUID(self.servant)
        # creacion de hilos para que se ejecute de forma paralela y así poder
        # comprobar el announce.
        hilo_auth = threading.Thread(target=self.servant.hiloauth())
        hilo_auth.start()
        hilo_catalog = threading.Thread(target=self.servant.hilocatalog())
        hilo_catalog.start()
        hilo_file = threading.Thread(target=self.servant.hilofile())
        hilo_file.start()
        self.shutdownOnInterrupt()
        comm.waitForShutdown()
        return 0


class Announcement(IceFlix.Announcement):
    # Si no encontramos el id del servicio en la lista de autenticadores de servicios lo
    # añadimos, además de el proxy. Eso lo haremos para tosos los servicios
    # (authenticator, catalogo y ficheros). Además, con la función ice_isA
    # lo que hacemos es comprobar el tipo de proxy, para que no se nos meta en
    # cualquiera https://doc.zeroc.com/ice/3.7/the-slice-language/operations-on-object
    def newService(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Receive a proxy of a new service."
        print("****Creando un nuevo servicio****")
        if self.compdup(service_id) is False:
            if (proxy.ice_isA("::IceFlix::Authenticator") and
                    service_id not in self.authenticator_services):
                self.time_services[service_id] = time.time()
                self.authenticator_services[service_id] = IceFlix.AuthenticatorPrx.uncheckedCast(
                    proxy)
                print(
                    f'***Servicio authenticator añadido correctamente con id: {service_id} ***')
            elif (proxy.ice_isA("::IceFlix::MediaCatalog") and
                    service_id not in self.catalog_services):
                self.time_services[service_id] = time.time()
                self.catalog_services[service_id] = IceFlix.MediaCatalogPrx.uncheckedCast(
                    proxy)
                print(
                    f'***Servicio catalogo añadido correctamente con id: {service_id} ***')

            elif proxy.ice_isA("::IceFlix::FileService") and service_id not in self.file_services:
                self.time_services[service_id] = time.time()
                self.file_services[service_id] = IceFlix.FileServicePrx.uncheckedCast(
                    proxy)
                print(
                    f'***Servicio file añadido correctamente con id: {service_id} ***')
                
    # En este metodo, lo que hacemos sera, en primer lugar, mirar el tiempo con el que entra al
    # announce para poder compararlo con el que tenemos de antes (cuando se crea el servicio)
    # posteriormente comprobamos si el tiempo es mayor que 30, miramos de que tipo es el servicio,
    # para eliminar su proxy y su service_id, si no es mayor que 30 actualizamos el contador a 0
    # para el siguiente servicio.
    def announce(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Announcements handler."
        print("****Comprobando announce****")
        if service_id in self.authenticator_services:
            self.time_services[service_id] = time.time()
            print("***Authenticator comprobado correctamente***")

        elif service_id in self.catalog_services:
            self.time_services[service_id] = time.time()
            print("***Catalogo comprobado correctamente***")

        elif service_id in self.file_services:
            self.time_services[service_id] = time.time()
            print("***Fichero comprobado correctamente***")

    # A continuacion, hacemos un metodo en el que comprobamos
    # que el servicio en el servicio recibido, no nos pasamos de
    # el tiempo que nos indican, en este caso 30 segundos, si nos
    # pasamos, eliminamos el servicio y el proxy.
    def hiloauth(self):
        """Hilo en el que comprobamos el servicio authenticator."""
        while 1:
            for service_id in self.authenticator_services:
                tiempo_service = self.time_services.get(service_id)
                if time.time() - tiempo_service > 30:
                    self.authenticator_services.pop(service_id)
                    print(
                        f'Eliminado servicio authenticator con service_id es: {service_id}')

    def hilocatalog(self):
        """Hilo en el que comprobamos el servicio catalogo."""
        while 1:
            for service_id in self.catalog_services and self.catalog_services != 0:
                tiempo_service = self.time_services.get(service_id)
                if time.time() - tiempo_service > 30:
                    self.catalog_services.pop(service_id)
                    print(
                        f'Eliminado servicio catalogo con service_id es: {service_id}')

    def hilofile(self):
        """Hilo en el que comprobamos el servicio file."""
        while 1:
            for service_id in self.file_services:
                tiempo_service = self.time_services.get(service_id)
                if time.time() - tiempo_service > 30:
                    self.file_services.pop(service_id)
                    print(
                        f'Eliminado servicio file con service_id es: {service_id}')

    # Con este metodo, compruebo si un id de un servicio esta en alguno de los diccionarios,
    # si es así, lo elimino.
    def compdup(self, service_id):
        """Comprobacion de servicios duplicados."""
        if service_id in self.authenticator_services:
            self.authenticator_services.pop(service_id)
            print(
                f'***Servicio authenticator con id: {service_id} eliminado.***')
            return True

        if service_id in self.catalog_services:
            self.catalog_services.pop(service_id)
            print(f'***Servicio catalogo con id: {service_id} eliminado.***')
            return True

        if service_id in self.file_services:
            self.file_services.pop(service_id)
            print(f'***Servicio file con id: {service_id} eliminado.***')
            return True

        return False


class Main(IceFlix.Main):
    """Desarrollo de los metodos necesarios para el servicio."""
    # Creacion de diccionarios(ya que se pueden meter valores de cualquier tipo)
    #  para los distintos servicios.

    def __init__(self):
        self.authenticator_services = {}
        self.catalog_services = {}
        self.file_services = {}
        self.time_services = {}

    # En este metodo, lo que haremos sera crear una variable services la cual contienen
    # los servicios y proxies dependiendo de el tipo de servicio que busquemos, posteriormente,
    # cogemos el que esta en la posicion 0. Con stringToProxy, establecemos una comunicacion
    # con mainApp mediante el metodo communicator, pasandole el proxy obtenido.
    # con checked cast asumimos que el puntero es del tipo que indicamos.
    # En el primer caso seria de tipo AuthenticatorPrx
    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        print("****Obteniendo proxy authenticator****")
        auth = ""
        services = self.authenticator_services
        if not services:
            raise IceFlix.TemporaryUnavailable()
        # lo he convertido buscando en esta direccion:
        auth = list(services.items())[0][1]
        # https://thispointer.com/python-get-first-value-in-a-dictionary/
        auth = MainApp.communicator().stringToProxy(str(auth))
        proxy = IceFlix.AuthenticatorPrx.checkedCast(auth)
        print("***Proxy authenticator recopilado correctamente***")
        return proxy

    def getCatalog(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        print("****Obteniendo proxy catalogo****")
        catalog = ""
        services = self.catalog_services
        if not services:
            raise IceFlix.TemporaryUnavailable()
        catalog = list(services.items())[0][1]
        catalog = MainApp.communicator().stringToProxy(catalog)
        proxy = IceFlix.AuthenticatorPrx.checkedCast(catalog)
        print("***Proxy catalogo recopilado correctamente***")
        return proxy

    def getFile(self, current=None):  # pylint:disable=invalid-name, unused-argument
        ''' Method to get one authentication service'''
        print("****Obteniendo proxy file****")
        archive = ""
        services = self.file_services
        if not services:
            raise IceFlix.TemporaryUnavailable()
        archive = list(services.items())[0][1]
        archive = MainApp.communicator().stringToProxy(archive)
        proxy = IceFlix.AuthenticatorPrx.checkedCast(archive)
        print("***Proxy file recopilado correctamente***")
        return proxy


if __name__ == '__main__':
    aplication = MainApp()
    sys.exit(aplication.main(sys.argv))
