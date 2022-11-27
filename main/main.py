#Elaboracion del proceso main 
#Cristian Rubio Barato 3ºC

import logging
import Ice
Ice.loadSlice("Iceflix.ice")
import IceFlix


class Main(IceFlix.Main):
    """Servant for the IceFlix.Main interface.

    Disclaimer: this is demo code, it lacks of most of the needed methods
    for this interface. Use it with caution
    """

    def getAuthenticator(self, current=None):  # pylint:disable=invalid-name, unused-argument
        service = 