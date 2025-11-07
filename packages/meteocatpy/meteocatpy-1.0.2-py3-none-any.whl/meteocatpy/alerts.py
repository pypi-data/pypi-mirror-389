import aiohttp
import logging
import re
from datetime import datetime
from .const import BASE_URL, ALERTS_URL
from .exceptions import (
    BadRequestError,
    ForbiddenError,
    TooManyRequestsError,
    InternalServerError,
    UnknownAPIError,
)

_LOGGER = logging.getLogger(__name__)

class MeteocatAlerts:
    """Clase para interactuar con los datos de estaciones de la API de Meteocat."""

    def __init__(self, api_key: str):
        """
        Inicializa la clase MeteocatAlerts.

        Args:
            api_key (str): Clave de API para autenticar las solicitudes.
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
        }
    
    @staticmethod
    def get_current_date():
        """
        Obtiene la fecha actual en formato numérico.

        Returns:
            tuple: Año (YYYY), mes (MM), día (DD) como enteros.
        """
        now = datetime.now()
        return now.year, now.month, now.day

    async def get_alerts(self):
        """
        Obtiene los datos meteorológicos de alertas desde la API de Meteocat.

        Args:
            any (str): Año de la consulta.
            mes (str): Mes de la consulta.
            dia (str): Día de la consulta.

        Returns:
            dict: Datos de alertas meteorológicas.
        """
        any, mes, dia = self.get_current_date()  # Calcula la fecha actual
        url = f"{BASE_URL}{ALERTS_URL}".format(
            any=any, mes=f"{mes:02d}", dia=f"{dia:02d}"
        )
    
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()

                    # Gestionar errores según el código de estado
                    if response.status == 400:
                        error_data = await response.json()
                        # Intentar extraer la última fecha válida del mensaje de error
                        if "message" in error_data:
                            match = re.search(r'entre (\d{2}-\d{2}-\d{4}) i', error_data["message"])
                            if match:
                                last_valid_date = match.group(1)  # Captura la última fecha válida
                                dia, mes, any = map(int, last_valid_date.split('-'))
                                # Intentar nuevamente con la última fecha válida
                                new_url = f"{BASE_URL}{ALERTS_URL}".format(
                                    any=any, mes=f"{mes:02d}", dia=f"{dia:02d}"
                                )
                                async with session.get(new_url, headers=self.headers) as new_response:
                                    if new_response.status == 200:
                                        return await new_response.json()
                                    raise UnknownAPIError(
                                        f"Failed with the valid date {last_valid_date}: {await new_response.text()}"
                                    )
                        raise BadRequestError(await response.json())
                    elif response.status == 403:
                        error_data = await response.json()
                        if error_data.get("message") == "Forbidden":
                            raise ForbiddenError(error_data)
                        elif error_data.get("message") == "Missing Authentication Token":
                            raise ForbiddenError(error_data)
                    elif response.status == 429:
                        raise TooManyRequestsError(await response.json())
                    elif response.status == 500:
                        raise InternalServerError(await response.json())
                    else:
                        raise UnknownAPIError(
                            f"Unexpected error {response.status}: {await response.text()}"
                        )

            except aiohttp.ClientError as e:
                raise UnknownAPIError(
                    message=f"Error al conectar con la API de Meteocat: {str(e)}",
                    status_code=0,
                )

            except Exception as ex:
                raise UnknownAPIError(
                    message=f"Error inesperado: {str(ex)}",
                    status_code=0,
                )
