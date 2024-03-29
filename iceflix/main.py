#!/usr/bin/env python3
"""Elaboracion del proceso main"""
# Cristian Rubio Barato 3ºC

import logging
import random
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
logging.basicConfig(level=logging.INFO)


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Main()
        self.servantannouncement = Announcement()
        self.proxy = None
        self.adapter = None
        self.uuid = uuid4()
        self.tiempo = 8

    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        logging.info("Running Main application")

        comm = self.communicator()
        self.adapter = comm.createObjectAdapterWithEndpoints(
            "MainAdapter", "tcp")
        proxy = self.adapter.addWithUUID(self.servant)
        proxyannounce = self.adapter.addWithUUID(self.servantannouncement)

        print(proxy, flush=True)

        topic_manager = IceStorm.TopicManagerPrx.checkedCast(  # pylint:disable=E1101
            self.communicator().propertyToProxy("IceStorm.TopicManager"))
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
        hilo_auth = threading.Thread(target=self.servant.hiloauth, daemon=True)
        hilo_auth.start()
        hilo_catalog = threading.Thread(
            target=self.servant.hilocatalog, daemon=True)
        hilo_catalog.start()
        hilo_file = threading.Thread(target=self.servant.hilofile, daemon=True)
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
            logging.info(
                '***Announcement authenticator comprobado correctamente con proxy: %s***\n', proxy)

        elif service_id in catalog_services or proxy.ice_isA("::IceFlix::MediaCatalog"):
            time_services[service_id] = time.time()
            catalog_services[service_id] = proxy
            logging.info(
                '***Announcement catalogo comprobado correctamente con proxy: %s***\n', proxy)

        elif service_id in file_services or proxy.ice_isA("::IceFlix::FileService"):
            time_services[service_id] = time.time()
            file_services[service_id] = proxy
            logging.info(
                '***Announcement file comprobado correctamente con proxy: %s***\n', proxy)

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
            logging.info(" Enviando announce...\n")
            publicador.announce(proxymain, str(idmain))
            time.sleep(tiempo)


class Main(IceFlix.Main):
    """_summary_
    En esta clase hacemos los metodos que nos exigen, entre ellos los getter de
    los distintos servicios y sus respectivos hilos.
    Args:
        IceFlix
    """

    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument R0201
        """_summary_
        Este código define un método "getAuthenticator" en la clase MainApp que obtiene
        un servicio de autenticación aleatorio del diccionario authenticator_services.
        """
        logging.info("****Obteniendo proxy authenticator****")
        auth = ""
        services = authenticator_services
        if not services:
            logging.warning("**No hay ningun authenticator disponible**\n")
            raise IceFlix.TemporaryUnavailable
        # Seleccionamos una referencia aleatoria del diccionario de servicios
        auth = random.choice(list(services.items()))[1]
        auth = MainApp.communicator().stringToProxy(str(auth))
        proxy = IceFlix.AuthenticatorPrx.checkedCast(auth)
        logging.info(
            '***Proxy authenticator recopilado correctamente: %s***\n', proxy)
        return proxy

    def getCatalog(self, current=None):  # pylint:disable=invalid-name, unused-argument R0201
        """
        Este código define un método "getCatalog" en la clase MainApp que obtiene
        un servicio de catalogo aleatorio del diccionario catalog_services.
        """
        logging.info("****Obteniendo proxy catalogo****")
        catalog = ""
        services = catalog_services
        if not services:
            logging.warning("**No hay ningun catalogo disponible**\n")
            raise IceFlix.TemporaryUnavailable
        catalog = random.choice(list(services.items()))[1]
        catalog = MainApp.communicator().stringToProxy(str(catalog))
        proxy = IceFlix.MediaCatalogPrx.checkedCast(catalog)
        logging.info(
            ' ***Proxy catalogo recopilado correctamente: %s***\n', proxy)
        return proxy

    def getFileService(self, current=None):  # pylint:disable=invalid-name, unused-argument R0201
        """
        Este código define un método "getFileService" en la clase MainApp que obtiene
        un servicio de file aleatorio del diccionario file_services.
        """
        logging.info(" ****Obteniendo proxy file****")
        archive = ""
        services = file_services
        if not services:
            logging.warning(" **No hay ningun file disponible**\n")
            raise IceFlix.TemporaryUnavailable
        archive = random.choice(list(services.items()))[1]
        archive = MainApp.communicator().stringToProxy(str(archive))
        proxy = IceFlix.FileServicePrx.checkedCast(archive)
        logging.info('***Proxy file recopilado correctamente: %s***\n', proxy)
        return proxy

    def hiloauth(self):  # pylint:disable=R0201
        """_summary_
        El hilo entra en un bucle infinito, y en cada iteración realiza lo siguiente:
        - Crea una copia del diccionario "time_services" y la almacena en
            "additional_services"
        - Itera sobre cada elemento del diccionario "additional_services", obteniendo el
            "service_id" de cada uno.
        - Obtiene el tiempo de servicio asociado al "service_id" en el diccionario "time_services"
            y lo almacena en "tiempo_service"
        - Si "tiempo_service" no es None, entonces comparar el tiempo actual con "tiempo_service"
            y si la diferencia es mayor a 10 segundos y el servicio authenticator tiene al menos
            un elemento, elimina ese elemento del diccionario "authenticator_services" y
            "time_services" y muestra un mensaje indicando que se ha eliminado el servicio.
        ESTE METODO SE HARA IGUAL EN EL RESTO DE HILOS, PERO CAMBIANDO LOS RESPECTIVOS DICCIONARIOS
         """
        # Hilo en el que comprobamos el servicio authenticator.
        while 1:
            additional_services = time_services.copy()
            for service_id in additional_services:
                # mira si eso te devuleve el tiempo del servicio creo que si
                tiempo_service = time_services.get(service_id)
                if tiempo_service is not None:
                    if time.time() - tiempo_service > 10 and service_id in authenticator_services:
                        authenticator_services.pop(service_id)
                        time_services.pop(service_id)
                        logging.info(
                           'Eliminado servicio authenticator, cuyo service_id es: %s\n', service_id)

    def hilocatalog(self):  # pylint:disable=R0201
        """Hilo en el que comprobamos el servicio catalogo."""
        while 1:
            additional_services = time_services.copy()
            for service_id in additional_services:
                tiempo_service = time_services.get(service_id)
                if tiempo_service is not None:
                    if time.time() - tiempo_service > 10 and service_id in catalog_services:
                        catalog_services.pop(service_id)
                        time_services.pop(service_id)
                        logging.info(
                            'Eliminado servicio catalogo, cuyo service_id es: %s\n', service_id)

    def hilofile(self):  # pylint:disable=R0201
        """Hilo en el que comprobamos el servicio file."""
        while 1:
            additional_services = time_services.copy()
            for service_id in additional_services:
                tiempo_service = time_services.get(service_id)
                if tiempo_service is not None:
                    if time.time() - tiempo_service > 10 and service_id in file_services:
                        file_services.pop(service_id)
                        time_services.pop(service_id)
                        logging.info(
                            'Eliminado servicio file, cuyo service_id es: %s\n', service_id)


if __name__ == '__main__':
    aplication = MainApp()
    sys.exit(aplication.main(sys.argv))
