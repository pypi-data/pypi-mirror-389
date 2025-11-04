# ruff: noqa: N802,N803,E501,SLF001,ARG002
"""Módulo dos métodos comuns da API BDSCore."""
from __future__ import annotations

from typing import TYPE_CHECKING

from bdscore.validator import validate

if TYPE_CHECKING:
    from bdscore import BDSCore
    from bdscore.result import BDSResult


class Dataflex:
    """Classe que encapsula os métodos de Dataflex da API BDSCore."""

    def __init__(self, core: BDSCore) -> None:
        self._core = core

    @validate()
    def getMetadata(
        self,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os metadados das entidades do Dataflex.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = dataflex.getMetadata()
            >>> print(result)
                BDSResult(api_url='{BDS_DATAFLEX_URL}/odata/metadata', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.dataflex_url}/odata/$metadata'

        return self._core._BDSCore__request(
            method='get',
            url=url,
        )

    @validate()
    def getEntity(
        self,
        Entity: str,
        Filter: str | None = None,
        Select: str | None = None,
        Top: int | None = None,
        OrderBy: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter dados de uma entidade específica do Dataflex.

            Parameters
            ----------
            Filter : str
                Filtro OData para refinar os resultados.
            Select : str
                Campos a serem retornados na resposta.
            Top : int
                Número máximo de registros a serem retornados.
            OrderBy : str
                Campo pelo qual os resultados devem ser ordenados.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = dataflex.getEntity(Entity=..., Filter=..., Select=..., Top=..., OrderBy=..., **kwargs)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAFLEX_URL}/odata/{Entity}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.dataflex_url}/odata/{Entity}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )
