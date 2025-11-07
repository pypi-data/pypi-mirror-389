import aiohttp
import logging
from .const import (
    BASE_URL,
    UVI_DATA_URL
)
from .exceptions import (
    BadRequestError,
    ForbiddenError,
    TooManyRequestsError,
    InternalServerError,
    UnknownAPIError,
)

_LOGGER = logging.getLogger(__name__)

class MeteocatUviData:
    """Clase para interactuar con los datos del índice UVI de la API de Meteocat."""

    def __init__(self, api_key: str):
        """
        Inicializa la clase MeteocatUviData.

        Args:
            api_key (str): Clave de API para autenticar las solicitudes.
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
        }

    async def get_uvi_index(self, town_id: str):
        """
        Obtiene los datos del índice UVI para un municipio.

        Args:
            town_id (str): Código del municipio.

        Returns:
            dict: Datos del índice UVI del municipio.
        """
        if not town_id:
            raise ValueError("El parámetro 'town_id' no puede estar vacío.")

        url = f"{BASE_URL}{UVI_DATA_URL}".format(
            codi_municipi=town_id
        )
    
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()

                    # Gestionar errores según el código de estado
                    if response.status == 400:
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
