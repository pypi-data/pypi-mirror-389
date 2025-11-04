# ruff: noqa: N802,N803,E501,SLF001,ARG002
"""Módulo de Data Management da API BDSCore."""
from __future__ import annotations

from typing import TYPE_CHECKING

from bdscore.validator import validate

if TYPE_CHECKING:
    from bdscore.enums import (
        EAttributeValueType,
        ECriticalLevel,
        ECurve,
        EDataQualityDataType,
        EDirection,
        EFactorCalculatorSymbol,
        EStatus,
        Lang,
        ResponseFormat,
    )
    from bdscore.result import BDSResult


class DataManagement:
    """Classe que encapsula os métodos de Data Management da API BDSCore."""

    def __init__(self, core) -> None:
        self._core = core

    @validate()
    def getBenchmarks(
        self,
        Symbols: str,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Fields: str | None = None,
        Interval: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Utilizado para encontrar benchmarks de renda fixa, variável, inflação e moeda, como: IBOVESPA, IPCA, Dólar.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields):
            Interval : str
                Define se retorno da API irá ser segregado em intervalos de tempo
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getBenchmarks(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., Interval=..., IgnDefault=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/public/Benchmarks', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/public/Benchmarks'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityBrokenRules(
        self,
        Classification: str | None = None,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Status: EStatus | str | None = None,
        OrderBy: str | None = None,
        Direction: EDirection | str | None = None,
        DataType: int | None = None,
        Data: int | None = None,
        Critical: ECriticalLevel | str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter Broken Rule.

            Parameters
            ----------
            Classification : str
                Id da regra quebrada.
            InitialDate : str
                Data inicial.
            FinalDate : str
                Data final.
            Status : str
                Status.
            OrderBy : str
                Campo para ordenação
            Direction : str
                Ordenação
            DataType : int
                Tipo de dado.
            Data : int
                Dado.
            Critical : str
                Nivel de criticidade.
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityBrokenRules(Classification=..., InitialDate=..., FinalDate=..., Status=..., OrderBy=..., Direction=..., DataType=..., Data=..., Critical=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/BrokenRule', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/BrokenRule'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCadasterAttributes(
        self,
        Id: str | None = None,
        FamilyId: str | None = None,
        CategoryId: str | None = None,
        StyleId: str | None = None,
        Type: str | None = None,
        SerieId: str | None = None,
        FilterId: str | None = None,
        ListId: str | None = None,
        IncludeCategories: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter cadastros.

            Parameters
            ----------
            Id : str
                Id do Cadastro
            FamilyId : str
                Id da Familia
            CategoryId : str
                Id da Categoria
            StyleId : str
                Id do Estilo
            Type : str
                Tipo do atributo que deseja procurar
            SerieId : str
                Id da série
            FilterId : str
                Id do filtro
            ListId : str
                Id da lista
            IncludeCategories : bool
                Se deseja incluir as categorias no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCadasterAttributes(Id=..., FamilyId=..., CategoryId=..., StyleId=..., Type=..., SerieId=..., FilterId=..., ListId=..., IncludeCategories=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Attribute/Cadaster', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Attribute/Cadaster'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getGroupCalculations(
        self,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter mapas de cálculos de um grupo.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getGroupCalculations()
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Calculate/List', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Calculate/List'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCurves(
        self,
        ReferenceDate: str | None = None,
        Name: str | None = None,
        Fields: str | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter curvas de cliente.

            Parameters
            ----------
            ReferenceDate : str
                Data de referência para a consulta (obrigatório)
                Ex: "2024-01-01", "D-1" (dia anterior), "last" (último disponível)
            Name : str
                Nome da curva específica (opcional)
                Ex: "SOFR_USD", "DI_BRL", "TREASURIES_USD"
            Fields : str
                Campos específicos a retornar (opcional)
                Ex: ":all" para todos os campos, ou campos específicos separados por vírgula
            Format : str
                Formato de retorno (opcional)
                Ex: "json", "xml", "csv"

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCurves(ReferenceDate=..., Name=..., Fields=..., Format=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Calculate/Curves', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Calculate/Curves'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFra(
        self,
        Curve: ECurve | str | None = None,
        ReferenceDate: str | None = None,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter a curva interpolada FRA.

            Parameters
            ----------
            Curve : str
                Nome da curva utilizada para o cálculo do FRA.
            ReferenceDate : str
                Data de referência.
            InitialDate : str
                Data inicial.
            FinalDate : str
                Data final.
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFra(Curve=..., ReferenceDate=..., InitialDate=..., FinalDate=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Calculate/Fra', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Calculate/Fra'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFactorCalculation(
        self,
        Symbol: EFactorCalculatorSymbol | str | None = None,
        ReferenceDate: str | None = None,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        SpreadValue: float | None = None,
        PercentValue: float | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter o cálculo do fator.

            Parameters
            ----------
            Symbol : str
                Símbolo
            ReferenceDate : str
                Data de referência.
            InitialDate : str
                Data inicial.
            FinalDate : str
                Data final.
            SpreadValue : float
                Valor do spread
            PercentValue : float
                Valor da porcentagem
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFactorCalculation(Symbol=..., ReferenceDate=..., InitialDate=..., FinalDate=..., SpreadValue=..., PercentValue=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Calculate/Factor', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Calculate/Factor'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCalendar(
        self,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter o calendário de divulgação.

            Parameters
            ----------
            InitialDate : str
                Data Inicial
            FinalDate : str
                Data Final
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCalendar(InitialDate=..., FinalDate=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Calendar', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Calendar'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCategories(
        self,
        Id: str | None = None,
        AttributeId: str | None = None,
        CadasterId: str | None = None,
        StyleId: str | None = None,
        FilterId: str | None = None,
        ListId: str | None = None,
        Type: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter categorias.

            Parameters
            ----------
            Id : str
                Id da Categoria
            AttributeId : str
                Id do Atributo
            CadasterId : str
                Id do Cadastro
            StyleId : str
                Id do Estilo
            FilterId : str
                Id do Filtro
            ListId : str
                Id da Lista
            Type : str
                Tipo da Categoria
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCategories(Id=..., AttributeId=..., CadasterId=..., StyleId=..., FilterId=..., ListId=..., Type=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Category', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Category'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCategoryTypes(
        self,
        Id: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter tipos de categorias.

            Parameters
            ----------
            Id : str
                Id do tipo de categoria
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCategoryTypes(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/CategoryType', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/CategoryType'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getClassification(
        self,
        Id: str | None = None,
        Name: str | None = None,
        FamilyId: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter classificação.

            Parameters
            ----------
            Id : str
                Id da Classificação
            Name : str
                Name da Classificação
            FamilyId : str
                Id da familia
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getClassification(Id=..., Name=..., FamilyId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Classification', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Classification'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getAttributesByFamily(
        self,
        Id: str | None = None,
        FamilyId: str | None = None,
        Type: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter atributos por família.

            Parameters
            ----------
            Id : str
                Id do Atributo
            FamilyId : str
                Informar a familia que deseja procurar
            Type : str
                Tipo do atributo que deseja procurar
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getAttributesByFamily(Id=..., FamilyId=..., Type=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Attribute/Family', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Attribute/Family'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCountries(
        self,
        Id: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os países.

            Parameters
            ----------
            Id : str
                Id do País
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCountries(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Country', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Country'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCounties(
        self,
        Id: str | None = None,
        StateId: str | None = None,
        CountryId: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os municípios.

            Parameters
            ----------
            Id : str
                Id do Municipio
            StateId : str
                Id do Estado
            CountryId : str
                Id do País
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getCounties(Id=..., StateId=..., CountryId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/County', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/County'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDashboardData(
        self,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os dados do dashboard.

            Parameters
            ----------
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDashboardData(Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Dashboard/Data', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Dashboard/Data'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedLists(
        self,
        Category: str | None = None,
        FeederId: int | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter listas de DataFeed.

            Parameters
            ----------
            Category : str
                Informar a categoria das listas que deseja procurar
            FeederId : int
                Informar o id do feeder
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedLists(Category=..., FeederId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/List', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/List'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleDataByDataType(
        self,
        DataType: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os dados de qualidade de dados por tipo de dado.

            Parameters
            ----------
            DataType : int
                Tipo de dado

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleDataByDataType(DataType=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/Data', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/Data'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityCategories(
        self,
        OrderBy: str | None = None,
        Direction: EDirection | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter categorias de qualidade de dados.

            Parameters
            ----------
            OrderBy : str
                Campo para ordenação
            Direction : str
                Ordenação
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityCategories(OrderBy=..., Direction=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Category', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Category'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedDemandingArea(
        self,
        Id: str | None = None,
        Name: str | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Parameters
            ----------
            Id : str
                Id a ser filtrado da área demandante
            Name : str
                Nome a ser filtrado da área demandante

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedDemandingArea(Id=..., Name=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/DemandingArea', status_code=200, call_duration=..., correlation_id=...)
        """  # noqa: D205
        url = f'{self._core.datamanagement_url}/DataFeed/DemandingArea'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getStatus(
        self,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para buscar o status de execução de um datafeed.

            Parameters
            ----------
            InitialDate : str
                Data inicial
            FinalDate : str
                Data final
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getStatus(InitialDate=..., FinalDate=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Datafeed/Execution/Status', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Datafeed/Execution/Status'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFamilies(
        self,
        FamilyId: str | None = None,
        Status: bool | None = None,
        FilterId: str | None = None,
        SourceId: str | None = None,
        AttributeId: str | None = None,
        NotebookId: str | None = None,
        CategoryId: str | None = None,
        CadasterId: str | None = None,
        TableId: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter famílias.

            Parameters
            ----------
            FamilyId : str
                Informar a familia que deseja procurar
            Status : bool
                Status da Familia
            FilterId : str
                Id do Filtro
            SourceId : str
                Id da Fonte
            AttributeId : str
                Id do Atributo
            NotebookId : str
                Id do Caderno
            CategoryId : str
                Id da Categoria
            CadasterId : str
                Id do Cadastro
            TableId : str
                Id da Tabela
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFamilies(FamilyId=..., Status=..., FilterId=..., SourceId=..., AttributeId=..., NotebookId=..., CategoryId=..., CadasterId=..., TableId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Family', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Family'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFilters(
        self,
        FilterId: str | None = None,
        FamilyId: str | None = None,
        ListId: str | None = None,
        CategoryId: str | None = None,
        IncludeList: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os Filters.

            Parameters
            ----------
            FilterId : str
                Informar o filtro que deseja procurar
            FamilyId : str
                Informar a familia que deseja procurar
            ListId : str
                Id da Lista
            CategoryId : str
                Id da Categoria
            IncludeList : str
                Inforamr se deseja a lista atrelada ao Filtro
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFilters(FilterId=..., FamilyId=..., ListId=..., CategoryId=..., IncludeList=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Filter', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Filter'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFilterRegistrationAsync(
        self,
        Id: str | None = None,
        CadasterId: str | None = None,
        MathematicalOperator: str | None = None,
        LogicalOperator: str | None = None,
        Value: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter registros de filtros.

            Parameters
            ----------
            Id : str
                Id do Filtro
            CadasterId : str
                Id do Cadastro
            MathematicalOperator : str
                Operador Matemático
            LogicalOperator : str
                Operador Lógico
            Value : str
                Valor
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFilterRegistrationAsync(Id=..., CadasterId=..., MathematicalOperator=..., LogicalOperator=..., Value=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/FilterRegistration', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/FilterRegistration'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getGen(
        self,
        Symbols: str,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Fields: str | None = None,
        Interval: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém informações de diversos instrumentos financeiros, tais como poupança, TR, volatilidade, inflação implícita, ETTJ, prefixados e outros. É possível obter taxas, valores e outras informações.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields):
            Interval : str
                Define se retorno da API irá ser segregado em intervalos de tempo
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getGen(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., Interval=..., IgnDefault=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/public/Gen', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/public/Gen'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getHolidays(
        self,
        Date: str | None = None,
        Type: str | None = None,
        Place: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os feriados.

            Parameters
            ----------
            Date : str
                Data do Feriado
            Type : str
                Tipo do Feriado
            Place : str
                Código do Local
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getHolidays(Date=..., Type=..., Place=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Holiday', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Holiday'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getInterfaces(
        self,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter uma lista de interfaces.

            Parameters
            ----------
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getInterfaces(Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Interface', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Interface'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFamilyInterfaces(
        self,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter uma lista de interfaces de família.

            Parameters
            ----------
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFamilyInterfaces(Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Interface/Family', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Interface/Family'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getLists(
        self,
        Id: str | None = None,
        FilterId: str | None = None,
        CategoryId: str | None = None,
        SerieId: str | None = None,
        Type: str | None = None,
        IncludeSeries: bool | None = None,
        IncludeCategories: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter listas.

            Parameters
            ----------
            Id : str
                Id da Lista
            FilterId : str
                Id do Filtro
            CategoryId : str
                Id da Categoria
            SerieId : str
                Id da Serie
            Type : str
                Informar o tipo de lista que deseja procurar
            IncludeSeries : bool
                Se deve incluir as series no retorno
            IncludeCategories : bool
                Se deve incluir as categorias no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getLists(Id=..., FilterId=..., CategoryId=..., SerieId=..., Type=..., IncludeSeries=..., IncludeCategories=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/List', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/List'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getListsByCategories(
        self,
        Category: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter listas por categorias.

            Parameters
            ----------
            Category : str
                Informar as listas das categorias que deseja procurar
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getListsByCategories(Category=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/List/Category', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/List/Category'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityMatrixRules(
        self,
        OrderBy: str | None = None,
        Direction: EDirection | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter as regras de qualidade de dados.

            Parameters
            ----------
            OrderBy : str
                Campo para ordenação
            Direction : str
                Ordenação

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityMatrixRules(OrderBy=..., Direction=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/MatrixRule', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/MatrixRule'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getNotebook(
        self,
        Id: str | None = None,
        FamilyId: str | None = None,
        IncludeFamilies: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para buscar cadernos.

            Parameters
            ----------
            Id : str
                Id do Caderno
            FamilyId : str
                Id da Familia
            IncludeFamilies : bool
                Se deve incluir as famílias no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getNotebook(Id=..., FamilyId=..., IncludeFamilies=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Notebook', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Notebook'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRules(
        self,
        CategoryId: str | None = None,
        DataType: EDataQualityDataType | str | None = None,
        Data: int | None = None,
        CriticalLevel: ECriticalLevel | str | None = None,
        OrderBy: str | None = None,
        Direction: EDirection | str | None = None,
        RuleTypeId: str | None = None,
        Active: bool | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para buscar regras de qualidade de dados.

            Parameters
            ----------
            CategoryId : str
                Id da categoria
            DataType : str
                Tipo de dado
            Data : int
                ObjectValue da regra
            CriticalLevel : str
                Nível de criticidade da regra
            OrderBy : str
                Campo para ordenação
            Direction : str
                Ordenação
            RuleTypeId : str
                Id do tipo de regra
            Active : bool
                Se a regra está ativa
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRules(CategoryId=..., DataType=..., Data=..., CriticalLevel=..., OrderBy=..., Direction=..., RuleTypeId=..., Active=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleTypesColumnsAndMappings(
        self,
        Id: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os tipos de regra de qualidade de dados com suas colunas e mapeamentos.

            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleTypesColumnsAndMappings(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/Type/ColumnsAndMappings', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/Type/ColumnsAndMappings'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleTypes(
        self,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os tipos de regra de qualidade de dados.

            Parameters
            ----------
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleTypes(Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/Type', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/Type'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSectors(
        self,
        Id: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter setores.

            Parameters
            ----------
            Id : str
                Id do Setor
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getSectors(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Sector', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Sector'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSerialAttributes(
        self,
        Id: str | None = None,
        FamilyId: str | None = None,
        CategoryId: str | None = None,
        StyleId: str | None = None,
        TableId: str | None = None,
        Type: str | None = None,
        SerieId: str | None = None,
        FilterId: str | None = None,
        ListId: str | None = None,
        IncludeFamilies: bool | None = None,
        IncludeCategories: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter atributos de valor.

            Parameters
            ----------
            Id : str
                Id do Atributo
            FamilyId : str
                Id da familia
            CategoryId : str
                Id da categoria
            StyleId : str
                Id do estilo
            TableId : str
                Id da tabela
            Type : str
                Tipo do atributo que deseja procurar
            SerieId : str
                Id da série
            FilterId : str
                Id do filtro
            ListId : str
                Id da lista
            IncludeFamilies : bool
                Se deve incluir as famílias no retorno
            IncludeCategories : bool
                Se deve incluir as categorias no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getSerialAttributes(Id=..., FamilyId=..., CategoryId=..., StyleId=..., TableId=..., Type=..., SerieId=..., FilterId=..., ListId=..., IncludeFamilies=..., IncludeCategories=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Attribute/Serial', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Attribute/Serial'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSeries(
        self,
        Search: str | None = None,
        Id: str | None = None,
        FamilyId: str | None = None,
        SerieName: str | None = None,
        FilterId: str | None = None,
        ListId: str | None = None,
        SourceId: str | None = None,
        IsActive: str | None = None,
        IncludeLists: bool | None = None,
        Paginate: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter séries.

            Parameters
            ----------
            Search : str
                Pesquisará pelo id e o nome da serie
            Id : str
                Id da Serie
            FamilyId : str
                Informar a familia que deseja procurar
            SerieName : str
                Informar a serie que deseja procurar
            FilterId : str
                Id do Filtro
            ListId : str
                Id da Lista
            SourceId : str
                Id da Fonte
            IsActive : str
                Informar se as series são ativas ou inativas que deseja procurar
            IncludeLists : bool
                Se deve incluir a lista no retorno
            Paginate : bool
                Se deve paginar o retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getSeries(Search=..., Id=..., FamilyId=..., SerieName=..., FilterId=..., ListId=..., SourceId=..., IsActive=..., IncludeLists=..., Paginate=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Serie', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Serie?paginate=true'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSource(
        self,
        SourceCode: str | None = None,
        IncludeFamilies: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter as fontes de dados que alimentam os métodos da API.

            Parameters
            ----------
            SourceCode : str
                Informar o(s) código(s) fonte que deseja procurar
            IncludeFamilies : bool
                Se deve incluir as famílias no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getSource(SourceCode=..., IncludeFamilies=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Source', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Source'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSourceByMethod(
        self,
        Methods: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para trazer a lista de Fontes relacionadas a determinado método da API.

            Parameters
            ----------
            Methods : str
                Informar o(s) método(s) que deseja procurar
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getSourceByMethod(Methods=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Source/method', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Source/method'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getStates(
        self,
        Id: str | None = None,
        CountryId: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os estados.

            Parameters
            ----------
            Id : str
                Id do Estado
            CountryId : str
                Id do Pais
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getStates(Id=..., CountryId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/State', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/State'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDashboardDataStatus(
        self,
        Page: int | None = None,
        Rows: int | None = None,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        SystemId: str | None = None,
        DataId: str | None = None,
        Status: str | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter o status do dashboard.

            Parameters
            ----------
            Page : int
                Página da requisição
            Rows : int
                Quantidade de linhas de dados
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas. Se informado, deve ser também informado o initialDate respectivo.
            SystemId : str
                Id do sistema a ser filtrado.
            DataId : str
                Id do dado a ser filtrado.
            Status : str
                Status do dado a ser filtrado.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDashboardDataStatus(Page=..., Rows=..., InitialDate=..., FinalDate=..., SystemId=..., DataId=..., Status=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Dashboard/Data/Status', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Dashboard/Data/Status'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDashboardStatus(
        self,
        Lang: Lang | str | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter o status do dashboard.

            Parameters
            ----------
            Lang : str
                Língua de resposta da API.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDashboardStatus(Lang=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Dashboard/Status', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Dashboard/Status'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getStyles(
        self,
        Id: str | None = None,
        Type: str | None = None,
        CategoryId: str | None = None,
        IncludeAttributes: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os estilos.

            Parameters
            ----------
            Id : str
                Id do Estilo
            Type : str
                Tipo do Estilo
            CategoryId : str
                Id da Categoria
            IncludeAttributes : bool
                Se deve incluir os atributos no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getStyles(Id=..., Type=..., CategoryId=..., IncludeAttributes=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Style', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Style'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getStyleTypes(
        self,
        Id: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os tipos de estilos.

            Parameters
            ----------
            Id : str
                Id do Tipo de Estilo
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getStyleTypes(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Style/Type', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Style/Type'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDashboardSystem(
        self,
        Id: str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os sistemas do dashboard.

            Parameters
            ----------
            Id : str
                Id do sistema
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDashboardSystem(Id=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Dashboard/System', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Dashboard/System'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedTables(
        self,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter as tabelas do datafeed.

            Parameters
            ----------
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedTables(Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Table', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/Table'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getTableAttributes(
        self,
        Id: str | None = None,
        FamilyId: str | None = None,
        IncludeSerialAttributes: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter atributos de tabela.

            Parameters
            ----------
            Id : str
                Id da Tabela
            FamilyId : str
                Id da Familia
            IncludeSerialAttributes : bool
                Se deve incluir os atributos de valor no retorno
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getTableAttributes(Id=..., FamilyId=..., IncludeSerialAttributes=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Attribute/Table', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Attribute/Table'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getThemes(
        self,
        Id: str | None = None,
        FamilyId: str | None = None,
        IncludeFamilyIds: bool | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os temas.

            Parameters
            ----------
            Id : str
                Id do Tema
            FamilyId : str
                Id da Família
            IncludeFamilyIds : bool
                Se deve incluir os Ids das famílias
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getThemes(Id=..., FamilyId=..., IncludeFamilyIds=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Theme', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Theme'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getValue(
        self,
        SerieId: str | None = None,
        AttributesId: str | None = None,
        CadastersId: str | None = None,
        InitialDate: str | None = None,
        FinalDate: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter valor.

            Parameters
            ----------
            SerieId : str
                Informar as series que deseja procurar
            AttributesId : str
                Informar as atributos que deseja procurar
            CadastersId : str
                Informar os cadastros que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas. Se informado, deve ser também informado o initialDate respectivo.
            Lang : str
                Língua de resposta da API.
            Page : int
                Página da requisição

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getValue(SerieId=..., AttributesId=..., CadastersId=..., InitialDate=..., FinalDate=..., Lang=..., Page=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Value', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Value'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getValues(
        self,
        FamilyId: str,
        InitialDate: str,
        SeriesId: str | None = None,
        Interval: str | None = None,
        AttributesId: str | None = None,
        CadastersId: str | None = None,
        FinalDate: str | None = None,
        IsActive: str | None = None,
        Filter: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Consulta valores de séries temporais de acordo com os parâmetros da API DataManagement.

            Parameters
            ----------
            FamilyId : str
                Código da família. Ex: "184". Use o método GET /family para obter valores.
            InitialDate : str
                Data inicial. Aceita datas no formato "YYYY-MM-DD" ou códigos: "PDU" (Primeiro Dia Útil), "UDU" (Último Dia Útil), "UDC" (Último Dia Corrido), "PDC" (Primeiro Dia Corrido), "C" (Dia Corrido), "D" (Dia Útil), "M" (Mês Útil), "S" (Semana Útil), "A" (Ano Útil).

                Pode ser combinado com períodos: "MES" (Mês), "BIM" (Bimestre), "TRI" (Trimestre), "QUA" (Quadrimestre), "SMT" (Semestre), "ANO" (Ano), "SEM" (Semana).

                Exemplos: "PDU_MES-1" (primeiro dia útil do mês anterior), "UDU_MES-2" (último dia útil de dois meses anteriores), "PDC_ANO-1" (primeiro dia corrido do ano anterior).
            SeriesId : str
                Lista de códigos das séries, separados por vírgula. Ex: "1,2,3". Use GET /serie.
            Interval : str
                Código do intervalo. Valores possíveis: 1: Diário | 2: Semanal | 3: Quinzenal | 4: Mensal | 5: Bimestral | 6: Trimestral | 7: Quadrimestral | 8: Semestral | 9: Anual | 15: Prévia | 20: Intraday | 21: LastDiário. Ex: "1".
            AttributesId : str
                Lista de códigos de atributos, separados por vírgula. Ex: "10,11". Use GET /attribute/serial.
            CadastersId : str
                Lista de códigos de cadastros, separados por vírgula. Ex: "5,6". Use GET /attribute/cadaster.
            FinalDate : str
                Data final. Aceita datas no formato "YYYY-MM-DD" ou códigos: "PDU" (Primeiro Dia Útil), "UDU" (Último Dia Útil), "UDC" (Último Dia Corrido), "PDC" (Primeiro Dia Corrido), "C" (Dia Corrido), "D" (Dia Útil), "M" (Mês Útil), "S" (Semana Útil), "A" (Ano Útil).

                Pode ser combinado com períodos: "MES" (Mês), "BIM" (Bimestre), "TRI" (Trimestre), "QUA" (Quadrimestre), "SMT" (Semestre), "ANO" (Ano), "SEM" (Semana).

                Exemplos: "PDU_MES-1" (primeiro dia útil do mês anterior), "UDU_MES-2" (último dia útil de dois meses anteriores), "PDC_ANO-1" (primeiro dia corrido do ano anterior).
            IsActive : str
                Se o valor deve ser ativo. Aceita: "true", "false", "1", "0", "yes", "no". Ex: "true".
            Filter : str
                Texto para filtro livre. Ex: "cnpj:***,***".
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getValues(FamilyId=..., InitialDate=..., SeriesId=..., Interval=..., AttributesId=..., CadastersId=..., FinalDate=..., IsActive=..., Filter=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Values', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Values'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getXml(
        self,
        Id: str | None = None,
        CategoryId: str | None = None,
        DemandingAreaId: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter xmls.

            Parameters
            ----------
            Id : str
                Id do XML
            CategoryId : str
                Categoria do XML
            DemandingAreaId : str
                Id da área demandante
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getXml(Id=..., CategoryId=..., DemandingAreaId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Xml', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Xml'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityBrokenRuleById(
        self,
        Id: str,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter Broken Rule por id.

            Parameters
            ----------
            Id : str
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityBrokenRuleById(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/BrokenRule/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/BrokenRule/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getConfiguration(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getConfiguration(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Configuration/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """  # noqa: D205
        url = f'{self._core.datamanagement_url}/DataFeed/Configuration/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDashboardDataBySystem(
        self,
        SystemId: int,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os dados do dashboard por sistema.

            Parameters
            ----------
            SystemId : int
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDashboardDataBySystem(SystemId=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Dashboard/Data/System/{SystemId}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Dashboard/Data/System/{SystemId}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedSeriesByList(
        self,
        Id: int,
        FeederId: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter séries por lista de um DataFeed.

            Parameters
            ----------
            Id : int
            FeederId : str
                Informar o id do alimentador que deseja procurar
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedSeriesByList(Id=..., FeederId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/List/{Id}/Serie', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/List/{Id}/Serie'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedSeriesForMappingByList(
        self,
        Id: int,
        FeederId: int | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter séries por lista de um DataFeed.

            Parameters
            ----------
            Id : int
            FeederId : int
                Informar o id do alimentador que deseja procurar
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedSeriesForMappingByList(Id=..., FeederId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/List/{Id}/Serie/Map', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/List/{Id}/Serie/Map'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedSeriesByFamily(
        self,
        CodFam: int,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter séries por família de um DataFeed.

            Parameters
            ----------
            CodFam : int
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedSeriesByFamily(CodFam=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Family/{CodFam}/Serie', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/Family/{CodFam}/Serie'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedListsCadaster(
        self,
        FeederId: int,
        ListId: int,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter cadastros do datafeed por listas e feederId.

            Parameters
            ----------
            FeederId : int
            ListId : int
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedListsCadaster(FeederId=..., ListId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Feeder/{FeederId}/List/{ListId}/Cadasters', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/Feeder/{FeederId}/List/{ListId}/Cadasters'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedFamiliesByList(
        self,
        Id: int,
        FeederId: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter famílias por lista de DataFeed.

            Parameters
            ----------
            Id : int
            FeederId : int
                Id do Feeder

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedFamiliesByList(Id=..., FeederId=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/List/{Id}/Family', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/List/{Id}/Family'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedFamilyByFeederId(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter famílias por atributo do Feeder.

            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedFamilyByFeederId(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Feeder/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/Feeder/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedAttributesByList(
        self,
        Id: int,
        FeederId: int | None = None,
        Type: EAttributeValueType | str | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter atributos de DataFeed por lista.

            Parameters
            ----------
            Id : int
            FeederId : int
                Id do Feeder
            Type : str
                Tipo do atributo

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedAttributesByList(Id=..., FeederId=..., Type=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/List/{Id}/Attribute', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/List/{Id}/Attribute'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedAttributesByTable(
        self,
        Id: int,
        FamilyId: str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter atributos de DataFeed por tabela.

            Parameters
            ----------
            Id : int
            FamilyId : str
                Id da família
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedAttributesByTable(Id=..., FamilyId=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Table/{Id}/Attribute/Serial', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/Table/{Id}/Attribute/Serial'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleSeriesByFamilyId(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter series de regras DataQuality a partir do id da família.

            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleSeriesByFamilyId(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/Family/{Id}/Serie', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/Family/{Id}/Serie'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityCategoryById(
        self,
        Id: str,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter uma categoria de qualidade de dados por ID.

            Parameters
            ----------
            Id : str

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityCategoryById(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Category/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Category/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityCategoryByRuleId(
        self,
        Id: str,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter uma categoria de qualidade de dados por ID da regra.

            Parameters
            ----------
            Id : str

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityCategoryByRuleId(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/{Id}/Category', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/{Id}/Category'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDemandingAreaReportById(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDemandingAreaReportById(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/DemandingArea/{Id}/report', status_code=200, call_duration=..., correlation_id=...)
        """  # noqa: D205
        url = f'{self._core.datamanagement_url}/DataFeed/DemandingArea/{Id}/report'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getLogs(
        self,
        Id: str,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para buscar os logs de execução de um datafeed.

            Parameters
            ----------
            Id : str
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getLogs(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Datafeed/Execution/Log/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Datafeed/Execution/Log/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def canExecute(
        self,
        Id: str,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para verificar se um datafeed pode ser executado.

            Parameters
            ----------
            Id : str
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.canExecute(Id=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Datafeed/Execution/CanExecute/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Datafeed/Execution/CanExecute/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getHolidaysRange(
        self,
        InitialDate: str,
        FinalDate: str,
        Type: str,
        Place: str,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter os feriados.

            Parameters
            ----------
            InitialDate : str
            FinalDate : str
            Type : str
            Place : str

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getHolidaysRange(InitialDate=..., FinalDate=..., Type=..., Place=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Holiday/{InitialDate}/{FinalDate}/{Type}/{Place}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Holiday/{InitialDate}/{FinalDate}/{Type}/{Place}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getInterfaceById(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter uma interface pelo ID.

            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getInterfaceById(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Interface/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Interface/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFamilyInterfaceById(
        self,
        Id: int,
        FamilyId: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter uma interface de família pelo ID.

            Parameters
            ----------
            Id : int
            FamilyId : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getFamilyInterfaceById(Id=..., FamilyId=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Interface/{Id}/Family/{FamilyId}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Interface/{Id}/Family/{FamilyId}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleById(
        self,
        Id: str,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para buscar regra de qualidade de dados por id.

            Parameters
            ----------
            Id : str

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleById(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleObjectsByRuleId(
        self,
        Id: str,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para buscar objetos de regra de qualidade de dados por id.

            Parameters
            ----------
            Id : str

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleObjectsByRuleId(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/{Id}/Objects', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/{Id}/Objects'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleTypeById(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter um tipo de regra de qualidade de dados por Id.

            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleTypeById(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/Type/{Id}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/Type/{Id}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleTypeColumns(
        self,
        Id: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter as colunas de um tipo de regra de qualidade de dados por ID.

            Parameters
            ----------
            Id : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleTypeColumns(Id=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/Type/{Id}/Columns', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/Type/{Id}/Columns'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataQualityRuleTypeByRuleIdAndTypeId(
        self,
        RuleId: str,
        RuleTypeId: int,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter um tipo de regra de qualidade de dados por ID da regra e Id do tipo.

            Parameters
            ----------
            RuleId : str
            RuleTypeId : int

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataQualityRuleTypeByRuleIdAndTypeId(RuleId=..., RuleTypeId=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataQuality/Rule/{RuleId}/Type/{RuleTypeId}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataQuality/Rule/{RuleId}/Type/{RuleTypeId}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getSeriesByFilter(
        self,
        FilterId: int,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter séries por filtro.

            Parameters
            ----------
            FilterId : int
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getSeriesByFilter(FilterId=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/Serie/Filter/{FilterId}', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/Serie/Filter/{FilterId}'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDataFeedTablesByFamily(
        self,
        Codfam: int,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter as tabelas do datafeed por família.

            Parameters
            ----------
            Codfam : int
            Lang : str
                Língua de resposta da API. Aceita: "en" (Inglês), "pt" (Português), "es" (Espanhol). Ex: "en".
            Page : int
                Página da requisição. Ex: 1.
            Rows : int
                Quantidade de linhas de dados. Ex: 1000. Máx: 5000.

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = data_management.getDataFeedTablesByFamily(Codfam=..., Lang=..., Page=..., Rows=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAMANAGEMENT_URL}/DataFeed/Family/{Codfam}/Table', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datamanagement_url}/DataFeed/Family/{Codfam}/Table'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )
