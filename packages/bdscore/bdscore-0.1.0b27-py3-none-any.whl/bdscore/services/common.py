# ruff: noqa: N802,N803,E501,SLF001,ARG002
"""Módulo dos métodos comuns da API BDSCore."""
from __future__ import annotations

from typing import TYPE_CHECKING

from bdscore.validator import validate

if TYPE_CHECKING:
    from bdscore.enums import Lang, ResponseFormat
    from bdscore.result import BDSResult


class Common:
    """Classe que encapsula os métodos comuns da API BDSCore."""

    def __init__(self, core) -> None:
        self._core = core

    # ====================================
    #         MÉTODOS DE DATAS
    # ====================================

    @validate()
    def addDays(
        self,
        ReferenceDate: str,
        Format: ResponseFormat | str | None = None,
        Source: str | None = None,
        Days: int | None = None,
        BusinessDay: str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Recebe uma data de referência, uma fonte e uma lista de datas dinâmicas, carrega a lista de feriados,e efetua um loop para cada item da lista de datas, e para cada um ele chama a função  *DecodeDate*.

            Parameters
            ----------
            ReferenceDate : str
                Data para a qual se deseja adicionar ou subtrair dias
            Format : str
                Formato em que a solicitação deve ser retornada
            Source : str
                Fonte da data. Se não informado, será utilizada a fonte ANBIMA
            Days : int
                Número de dias
            BusinessDay : str
                Lista de feriados. Se não informado, será utilizada o padrão de dias úteis (DU)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getAddDays(ReferenceDate=..., Format=..., Source=..., Days=..., BusinessDay=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getAddDays', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getAddDays'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def decodeDynamicDate(
        self,
        ReferenceDate: str,
        DynamicDates: str,
        Format: ResponseFormat | str | None = None,
        SourceName: str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Recebe uma data de referência, uma fonte e uma lista de datas dinâmicas, carrega a lista de feriados,e efetua um loop para cada item da lista de datas, e para cada um ele chama a função  *DecodeDate*.

            Parameters
            ----------
            ReferenceDate : str
                Data para a qual se deseja decodificar
            DynamicDates : str
                Data dinâmica para a qual se deseja decodificar
            Format : str
                Formato em que a solicitação deve ser retornada
            SourceName : str
                Fonte da data. Se não informado, será utilizada a fonte ANBIMA
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getDateDecode(ReferenceDate=..., DynamicDates=..., Format=..., SourceName=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getDateDecode', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getDateDecode'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def encodeDynamicDate(
        self,
        ReferenceDate: str,
        Format: ResponseFormat | str | None = None,
        ReferenceDateBase: str | None = None,
        SourceName: str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Recebe duas datas que foram citadas previamente, seguidos de o nome de uma fonte; Com base no ano da data de referencia (_referenceDate_) e nome da fonte escolhida, são calculados os feriados para determinada fonte e uma outra função *GetDynamicDates* é chamada.

            Parameters
            ----------
            ReferenceDate : str
                Data para a qual se deseja codificar
            Format : str
                Formato em que a solicitação deve ser retornada
            ReferenceDateBase : str
                Data base para realizar o cálculo. Se não informado, será retornada a data atual no Formato: yyyy-MM-dd
            SourceName : str
                Fonte da data. Se não informado, será utilizada a fonte ANBIMA
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getDateEncode(ReferenceDate=..., Format=..., ReferenceDateBase=..., SourceName=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getDateEncode', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getDateEncode'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def diffDates(
        self,
        ReferenceDate: str,
        ComparisonDate: str,
        Format: ResponseFormat | str | None = None,
        Source: str | None = None,
        BusinessDay: str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Calcular a diferença entre duas datas.

            Parameters
            ----------
            ReferenceDate : str
                Data para a qual se deseja calcular a diferença entre duas datas
            ComparisonDate : str
                Data para a qual se deseja comparar
            Format : str
                Formato em que a solicitação deve ser retornada
            Source : str
                Fonte da data. Se não informado, será utilizada a fonte ANBIMA
            BusinessDay : str
                Lista de feriados. Se não informado, será utilizada o padrão de dias úteis (DU)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getDifferenceBetweenTwoDays(ReferenceDate=..., ComparisonDate=..., Format=..., Source=..., BusinessDay=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getDifferenceBetweenTwoDays', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getDifferenceBetweenTwoDays'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    # ====================================
    #         MÉTODOS DE CAMPOS
    # ====================================

    @validate()
    def getFields(
        self,
        Field: str | None = None,
        Method: str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Lang: Lang | str | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter a descrição dos campos disponíveis na API.

            Parameters
            ----------
            Field : str
                Informar o(s) campo(s) que deseja procurar e retornara os métodos do mesmo
            Method : str
                Informar o(s) método(s) que deseja procurar os símbolos válidos
            Page : int
                Página da requisição
            Rows : int
                Quantidade de linhas de dados
            Lang : str
                Língua de resposta da API.
            Format : str
                Formato em que a solicitação deve ser retornada
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getFields(Field=..., Method=..., Page=..., Rows=..., Lang=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getFields', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getFields'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFieldsByMethod(
        self,
        Method: str | None = None,
        Lang: Lang | str | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter a descrição dos campos disponíveis na API.

            Parameters
            ----------
            Method : str
                Método que deseja procurar os campos disponíveis
            Lang : str
                Língua de resposta da API.
            Format : str
                Formato em que a solicitação deve ser retornada
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getFields(Method=..., Lang=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getFieldsByMethod', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getFieldsByMethod'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getStyles(
        self,
        Style: str | None = None,
        Method: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os estilos e seus campos disponíveis na API.

            Parameters
            ----------
            Style : str
                Informar o(s) estilo(s) que deseja procurar e retornara os campos do mesmo
            Method : str
                Informar o(s) método(s) que deseja procurar os símbolos válidos
            Lang : str
                Língua de resposta da API
            Page : int
                Página da requisição
            Rows : int
                Quantidade de linhas de dados
            Format : str
                Formato em que a solicitação deve ser retornada
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getStyles(Style=..., Method=..., Lang=..., Page=..., Rows=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getStyles', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getStyles'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSymbols(
        self,
        Symbol: str | None = None,
        Method: str | None = None,
        Type: int | None = None,
        SearchType: str | None = None,
        IsActive: str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Lang: Lang | str | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter símbolos agregadores/classificadores dos instrumentos que fazem parte de um método específico.

            Parameters
            ----------
            Symbol : str
                Informar o que deseja procurar
            Method : str
                Informar o(s) método(s) que deseja procurar os símbolos válidos
            Type : int
                Tipo de dados: símbolos Agredadores ou Series
            SearchType : str
                Determina o tipo de pesquisa:"Fuzzy" busca será parcial ou "Full" realiza uma pesquisa normal
            IsActive : str
                Se o valor deve ser ativo ou não
            Page : int
                Página da requisição
            Rows : int
                Quantidade de linhas de dados
            Lang : str
                Língua de resposta da API.
            Format : str
                Formato em que a solicitação deve ser retornada
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getSymbols(Symbol=..., Method=..., Type=..., SearchType=..., IsActive=..., Page=..., Rows=..., Lang=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getSymbols', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getSymbols'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSymbolsAllProperties(
        self,
        Symbol: str | None = None,
        Method: str | None = None,
        Type: int | None = None,
        SearchType: str | None = None,
        IsActive: str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Lang: Lang | str | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter o objeto completo do Simbolo, com todas informações relacionadas.

            Parameters
            ----------
            Symbol : str
                Informar o que deseja procurar
            Method : str
                Informar o(s) método(s) que deseja procurar os símbolos válidos
            Type : int
                Tipo de dados: símbolos Agredadores ou Series
            SearchType : str
                Determina o tipo de pesquisa:"Fuzzy" busca será parcial ou "Full" realiza uma pesquisa normal
            IsActive : str
                Se o valor deve ser ativo ou não
            Page : int
                Página da requisição
            Rows : int
                Quantidade de linhas de dados
            Lang : str
                Língua de resposta da API.
            Format : str
                Formato em que a solicitação deve ser retornada
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = common.getSymbolsAllProperties(Symbol=..., Method=..., Type=..., SearchType=..., IsActive=..., Page=..., Rows=..., Lang=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_COMMON_URL}/getSymbols/allProperties', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.common_url}/getSymbols/allProperties'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )
