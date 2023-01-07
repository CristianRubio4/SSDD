#!/usr/bin/env python3
"""Elaboracion del proceso main"""
# Cristian Rubio Barato 3ºC

import sys
import threading
import time
import os
from uuid import uuid4
import IceStorm
import Ice
Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
import IceFlix  # pylint:disable=import-error C0413
authenticator_services = {}
catalog_services = {}
file_services = {}
time_services = {}


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Main()
        self.servantannouncement = Announcement()
        self.proxy = None
        self.adapter = None
        self.uuid = uuid4()
        self.tiempo = 10

    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        print("Running Main application")

        comm = self.communicator()
        self.adapter = comm.createObjectAdapterWithEndpoints(
            "MainAdapter", "tcp")
        proxy = self.adapter.addWithUUID(self.servant)
        proxyannounce = self.adapter.addWithUUID(self.servantannouncement)

        print(proxy, flush=True)

        topic_manager_str_prx = "IceStorm/TopicManager -t:tcp -h localhost -p 10000"
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(  # pylint:disable=E1101
            self.communicator().stringToProxy(topic_manager_str_prx),
        )

        if not topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        topic_name = "Announcements"
        try:
            topic = topic_manager.create(topic_name)
        except IceStorm.TopicExists:  # pylint:disable=E1101
            topic = topic_manager.retrieve(topic_name)

        publisher = topic.getPublisher()
        publisher = IceFlix.AnnouncementPrx.uncheckedCast(publisher)

        if not publisher:
            raise RuntimeError("Invalid publisher proxy")

        topic.subscribeAndGetPublisher({}, proxyannounce)

        # creacion de un hilo que invoca al metodo "mandar_announcement"
        hilo_announcement = threading.Thread(
            target=self.servantannouncement.mandar_announcement,
            args=(publisher, proxy, self.uuid, self.tiempo),
            daemon=True)
        hilo_announcement.start()

        self.adapter.activate()
        self.proxy = self.adapter.addWithUUID(self.servant)
        # creacion de hilos para que se ejecute de forma paralela y así poder
        # comprobar el announce.
        hilo_auth = threading.Thread(target=self.servant.hiloauth,daemon=True)
        hilo_auth.start()
        hilo_catalog = threading.Thread(target=self.servant.hilocatalog,daemon=True)
        hilo_catalog.start()
        hilo_file = threading.Thread(target=self.servant.hilofile,daemon=True)
        hilo_file.start()

        self.shutdownOnInterrupt()
        comm.waitForShutdown()
        topic.unsubscribe(proxyannounce)

        return 0


class Announcement(IceFlix.Announcement):
    """_summary_
    En esta clase, lo que tendremos ahora serán dos metodos, el announce que
    ya conociamos y un otro nuevo que servira para llamar al metodo announce cada 10 segundos
    Args:
        IceFlix
    """

    def announce(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument R0201
        """En este metodo, comprobaremos en primer lugar de que tipo es el servicio que estamos
        recibiendo, para posteriormente coger su tiempo y su proxy y guardarlos en sus respectivos
        diccionarios.

        Args:
            proxy: proxy del servicio que queremos anunciar
            service_id: el id del servicio que queremos anunciar
            current
        """
        if (service_id in authenticator_services or
                proxy.ice_isA("::IceFlix::Authenticator")):
            time_services[service_id] = time.time()
            authenticator_services[service_id] = proxy
            print("***Announcement authenticator comprobado correctamente***")

        elif service_id in catalog_services or proxy.ice_isA("::IceFlix::MediaCatalog"):
            time_services[service_id] = time.time()
            catalog_services[service_id] = proxy
            print("***Announcement catalogo comprobado correctamente***")

        elif service_id in file_services or proxy.ice_isA("::IceFlix::FileService"):
            time_services[service_id] = time.time()
            file_services[service_id] = proxy
            print("***Announcement fichero comprobado correctamente***")

    def mandar_announcement(self, publicador, proxymain, idmain, tiempo):  # pylint:disable=R0201
        """_summary_
        En este metodo, lo que haremos particularmente sera llamar al metodo announce
        cada 10 segundos.
        Args:
            publicador: publicador del programa
            proxymain: proxy del main
            idmain: identificador unico del main
            tiempo: intervalo en el que queremos llamar al metodo announce
        """
        while 1:
            print("\nEsperando servicio...")
            publicador.announce(proxymain, str(idmain))
            time.sleep(tiempo)


class Main(IceFlix.Main):
    """Desarrollo de los metodos necesarios para el servicio."""

    # En este metodo, lo que haremos sera crear una variable services la cual contienen
    # los servicios y proxies dependiendo de el tipo de servicio que busquemos, posteriormente,
    # cogemos el que esta en la posicion 0. Con stringToProxy, establecemos una comunicacion
    # con mainApp mediante el metodo communicator, pasandole el proxy obtenido.
    # con checked cast asumimos que el puntero es del tipo que indicamos.
    # En el primer caso seria de tipo AuthenticatorPrx

    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument R0201
        ''' Method to get one authentication service'''
        print("****Obteniendo proxy authenticator****")
        auth = ""
        services = authenticator_services
        if not services:
            raise IceFlix.TemporaryUnavailable
        # lo he convertido buscando en esta direccion:
        auth = list(services.items())[0][1]
        # https://thispointer.com/python-get-first-value-in-a-dictionary/
        auth = MainApp.communicator().stringToProxy(str(auth))
        proxy = IceFlix.AuthenticatorPrx.checkedCast(auth)
        print(f'***Proxy authenticator recopilado correctamente: {proxy}***')
        return proxy

    def getCatalog(self, current=None):  # pylint:disable=invalid-name, unused-argument R0201
        ''' Method to get one authentication service'''
        print("****Obteniendo proxy catalogo****")
        catalog = ""
        services = catalog_services
        if not services:
            raise IceFlix.TemporaryUnavailable
        catalog = list(services.items())[0][1]
        catalog = MainApp.communicator().stringToProxy(str(catalog))
        proxy = IceFlix.MediaCatalogPrx.checkedCast(catalog)
        print(f'***Proxy catalogo recopilado correctamente: {proxy}***')
        return proxy

    def getFileService(self, current=None):  # pylint:disable=invalid-name, unused-argument R0201
        ''' Method to get one authentication service'''
        print("****Obteniendo proxy file****")
        archive = ""
        services = file_services
        if not services:
            raise IceFlix.TemporaryUnavailable
        archive = list(services.items())[0][1]
        archive = MainApp.communicator().stringToProxy(str(archive))
        proxy = IceFlix.FileServicePrx.checkedCast(archive)
        print(f'***Proxy file recopilado correctamente: {proxy}***')
        return proxy

    # A continuacion, hacemos un metodo en el que comprobamos
    # que el servicio en el servicio recibido, no nos pasamos de
    # el tiempo que nos indican, en este caso 10 segundos, si nos
    # pasamos, eliminamos el servicio y el proxy.
    def hiloauth(self):  # pylint:disable=R0201
        """Hilo en el que comprobamos el servicio authenticator."""
        while 1:
            additional_services = time_services.copy()
            for service_id in additional_services:
                # mira si eso te devuleve el tiempo del servicio creo que si
                tiempo_service = time_services.get(service_id)
                if time.time() - tiempo_service > 10 and len(authenticator_services)!=0:
                    authenticator_services.pop(service_id)
                    time_services.pop(service_id)
                    print(
                        f'Eliminado servicio authenticator, cuyo service_id es: {service_id}\n')

    def hilocatalog(self):  # pylint:disable=R0201
        """Hilo en el que comprobamos el servicio catalogo."""
        while 1:
            additional_services = time_services.copy()
            for service_id in additional_services:
                tiempo_service = time_services.get(service_id)
                if time.time() - tiempo_service > 10 and len(catalog_services)!=0:
                    catalog_services.pop(service_id)
                    time_services.pop(service_id)
                    print(
                        f'Eliminado servicio catalogo, cuyo service_id es: {service_id}\n')

    def hilofile(self):  # pylint:disable=R0201
        """Hilo en el que comprobamos el servicio file."""
        while 1:
            additional_services = time_services.copy()
            for service_id in additional_services:
                tiempo_service = time_services.get(service_id)
                if time.time() - tiempo_service > 10 and len(file_services)!=0:
                    file_services.pop(service_id)    
                    time_services.pop(service_id)
                    print(
                        f'Eliminado servicio file, cuyo service_id es: {service_id}\n')


if __name__ == '__main__':
    aplication = MainApp()
    sys.exit(aplication.main(sys.argv))
