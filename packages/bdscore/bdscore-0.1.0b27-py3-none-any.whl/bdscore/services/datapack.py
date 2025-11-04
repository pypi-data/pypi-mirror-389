# ruff: noqa: N802,N803,E501,SLF001,ARG002
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import requests

from bdscore.result import BDSResult
from bdscore.validator import validate

if TYPE_CHECKING:
    from bdscore.enums import Lang, ResponseFormat


class DataPack:
    """Classe que encapsula os métodos de Data Pack da API BDSCore."""

    def __init__(self, core) -> None:
        self._core = core

    # Débito Técnico: Implementação manual do método getTradeInformation direto no UP2DATA. Deve-se implementar uma API BDS para este método futuramente.
    def getTradeInformation(self, Symbols: str = ':all', InstrumentType: str | None = None, ReferenceDate: str | None = None) -> BDSResult:
        """Busca e retorna informações de negociações de renda fixa (Negócio a Negócio) para o tipo de instrumento e data especificados.

        Este método retorna dados de negócio a negócio para o tipo de instrumento informado (CRA, CRI, DEB) e para a data de referência desejada.
        Permite aplicar filtros flexíveis sobre o array de objetos retornado, possibilitando a seleção por qualquer campo presente no JSON (ex: TckrSymb:25H2095950, ISIN:XYZ).
        Caso o parâmetro Symbols seja ":all" (padrão), todos os registros do arquivo serão retornados sem filtro.

        Parâmetros:
            Symbols (str, opcional): Filtro para os registros retornados.
                - Para filtrar por campo específico, utilize o formato "Campo:Valor" (ex: TckrSymb:25H2095950, ISIN:XYZ).
                - Se apenas o valor for informado (ex: "25H2095950"), o filtro será aplicado sobre o campo padrão 'TckrSymb'.
                - Se ":all" (padrão), retorna todos os registros do arquivo sem filtro.
            InstrumentType (str, obrigatório): Tipo do instrumento financeiro. Aceita apenas "CRA", "CRI" ou "DEB".
            ReferenceDate (str, opcional): Data de referência do arquivo.
                - Aceita formatos YYYYMMDD, YYYY-MM-DD ou dinâmico (ex: D-1, D+1, C-1).
                - Datas dinâmicas são resolvidas automaticamente via utilitário interno.

        Returns:
            BDSResult: Objeto contendo os dados filtrados do arquivo Trade_FixedIncome.
                - api_url (str): URL do arquivo JSON acessado no blob.
                - body (list): Lista de registros filtrados conforme os parâmetros.
                - headers (dict): Cabeçalhos HTTP da resposta do blob.
                - status_code (int): Código de status HTTP da requisição.
                - call_duration (float): Tempo de execução da chamada em segundos.
                - data: (object): Dados brutos retornados pela API.

        Raises:
            ValueError: Se InstrumentType não for um dos valores permitidos ou se api_key não estiver configurada.
            FileNotFoundError: Se nenhum arquivo correspondente for encontrado para o tipo e data informados.

        Exemplos de uso:
            # Retorna todos os registros de DEB para a data dinâmica D-1
            result = bdscore.datapack.getTradeInformation(Symbols=":all", InstrumentType="DEB", ReferenceDate="D-1")

            # Filtra registros por ticker específico
            result = bdscore.datapack.getTradeInformation(Symbols="TckrSymb:25H2095950", InstrumentType="CRA", ReferenceDate="20231020")

            # Filtra registros por ISIN
            result = datapack.getTradeInformation(Symbols="ISIN:BR1234567890", InstrumentType="CRI", ReferenceDate="2023-10-20")

        """
        if not InstrumentType or InstrumentType.upper() not in {'CRI', 'CRA', 'DEB'}:
            raise ValueError(
                f"O parâmetro 'InstrumentType' deve ser um dos valores permitidos: CRI, CRA ou DEB. Valor recebido: '{InstrumentType}'. "
                "Consulte a documentação do método getTradeInformation para detalhes.",
            )

        # Resolve ReferenceDate
        refdate = ReferenceDate
        if isinstance(refdate, str) and ('+' in refdate or '-' in refdate):
            from .common import Common
            common = Common(self._core)
            base_date = getattr(common._core, 'reference_date', None)
            if not base_date:
                import datetime
                base_date = datetime.date.today().strftime('%Y-%m-%d')
            result = common.decodeDynamicDate(ReferenceDate=base_date, DynamicDates=refdate).data.to_dict()
            refdate = result[0]['date'].replace('-', '')
        elif isinstance(refdate, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', refdate):
            refdate = refdate.replace('-', '')

        # Obtém SAS via API externa validando api_key
        sas_api_url = 'https://prod-88.eastus.logic.azure.com:443/workflows/ae939630c3b547eca6cd3c552962eaf7/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=tuNC_HFgksiyJp0bG1NPygC_X6y9suvIrd_QcLtUWfI'
        api_key = getattr(self._core, 'api_key', None)
        if not api_key:
            raise ValueError('api_key não encontrada no core')
        headers = {'BDSKey': api_key}
        sas_resp = requests.post(sas_api_url, headers=headers)
        sas_resp.raise_for_status()
        sas_dict = sas_resp.json()
        InstrumentType_lower = InstrumentType.lower()
        if InstrumentType_lower not in sas_dict:
            raise ValueError(f"Instrumento invalido:'{InstrumentType}' não encontrado na resposta da API.")
        sas_url = sas_dict[InstrumentType_lower]

        prefix = f'{refdate}/Trade_FixedIncome/{InstrumentType}/Trade_FixedIncome_TradeOTCFile_{InstrumentType}_{refdate}_'
        list_url = sas_url.split('?')[0] + f'?restype=container&comp=list&prefix={refdate}/Trade_FixedIncome/{InstrumentType}/'
        if '?' in sas_url:
            list_url += '&' + sas_url.split('?', 1)[1]
        resp = requests.get(list_url)
        resp.raise_for_status()
        tree = ET.fromstring(resp.text)
        blobs = [b.find('Name').text for b in tree.findall('.//Blob') if b.find('Name') is not None]
        files = [b for b in blobs if b.startswith(prefix) and b.endswith('.json')]
        if not files:
            raise FileNotFoundError(f'Nenhum arquivo encontrado para {InstrumentType} em {refdate}')

        def extract_counter(fname):
            try:
                return int(fname.split('_')[-1].replace('.json', ''))
            except Exception:
                return -1
        last_file = max(files, key=extract_counter)

        blob_url = sas_url.split('?')[0] + '/' + last_file
        if '?' in sas_url:
            blob_url += '?' + sas_url.split('?', 1)[1]
        start = time.time()
        file_resp = requests.get(blob_url)
        file_resp.raise_for_status()
        data = file_resp.json()
        duration = time.time() - start

        # Aplica filtro genérico se fornecido
        if Symbols == ':all':
            Symbols = None
        if Symbols and isinstance(data, list):
            if ':' in Symbols:
                field, value = Symbols.split(':', 1)
                data = [item for item in data if str(item.get(field)) == value]
            else:
                # Se não especificar campo, filtra por TckrSymb
                value = Symbols
                data = [item for item in data if str(item.get('TckrSymb')) == value]

        return BDSResult(
            api_url=blob_url,
            body=data,
            headers=dict(file_resp.headers),
            status_code=file_resp.status_code,
            call_duration=duration,
        )

    # ====================================
    # MÉTODOS DE MERCADO FINANCEIRO
    # ====================================

    @validate()
    def getFX(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém informações como compra, venda e variação percentual das moedas de cada país, como dólar americano, euro, real, yen e yuan renminbi, entre muitas outras.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFX(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFX', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFX'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getEquitiesB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de ações cotadas na B3, é possível encontrar dados cadastrais e de valor, tais como ticker, categoria do instrumento, nome da empresa, oscilação do dia, volume financeiro, preço de abertura, melhor oferta de venda e melhor oferta de compra, entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getEquitiesB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getEquitiesB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getEquitiesB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getBrazilianTreasury(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Obtém dados de títulos públicos brasileiros (Tesouro Nacional) para o período e filtros especificados.

            Retorna informações cadastrais e de valores dos títulos (títulos públicos brasileiros, LFT, LTN, NTN-B, NTN-C e NTN-F), com suporte a filtros por campo, data, e outros parâmetros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getBrazilianTreasury(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getBrazilianTreasury', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getBrazilianTreasury'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCommodities(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Obtém dados de commodities negociadas no mercado internacional, como Ouro New York.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCommodities(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCommodities', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCommodities'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getIndex(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém as principais informações dos índices do mercado, são eles IPCA, IRF-M, IMA-B, JGP, IDka, IDA e outras variações destes.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getIndex(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getIndex', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getIndex'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getIndexB3(
        self,
        Symbols: str,
        InitialDate: str,
        Interval: str | None = None,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém índices dos ativos negociados na B3, como IBOV, IBRA, IBXX, ICON, entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            Interval : str
                Define se retorno da API irá ser segregado em intervalos de tempo
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getIndexB3(Symbols=..., InitialDate=..., Interval=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getIndexB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getIndexB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getIndexPortfolioB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados como Ticker, preço e data do relatório de empresas e fundos imobiliários negociados na B3, entre elas estão APPLE, ALUPAR, FII ANCAR...

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getIndexPortfolioB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getIndexPortfolioB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getIndexPortfolioB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getIndexMonthly(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém índices divulgados mensalmente como IGP-M, IPCA entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getIndexMonthly(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getIndexMonthly', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getIndexMonthly'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    # ====================================
    # MÉTODOS DE DERIVATIVOS E FUTUROS
    # ====================================

    @validate()
    def getFuturesB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de Contratos Futuros da B3, tais como boi gordo, café arábica, etanol, dólar comercial, euro, índices, câmbio com diversas moedas entre outros. É possível encontrar atributos cadastrais, tais como nome do ativo, código CFI, tipo de mercado e outros, bem como é possível obter atributos de valor, como melhor oferta de compra, melhor oferta de venda, preço máximo, preço mínimo, último preço, quantidade negociada e outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFuturesB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFuturesB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFuturesB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFuturesCME(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de Futuros de CME.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFuturesCME(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFuturesCME', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFuturesCME'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCMEAgricFutures(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Obtém dados de futuros agrícolas negociados na CME.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCMEAgricFutures(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCMEAgricFutures', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCMEAgricFutures'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCMEFuturesCommodities(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Obtém dados de futuros de commodities negociados na CME.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCMEFuturesCommodities(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCMEFuturesCommodities', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCMEFuturesCommodities'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFuturesOptionsB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de Futuros de Opções, tais como boi gordo, café arábica, etanol, índice S&P 500, milho campinas, dólar e outros. É possível obter informações sobre estilo de opção, código do ativo, ticker, código CFI, preços, volume financeiro negociado, oscilação do dia, cotação de ajuste, preço de exercício, prêmio de referência e outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFuturesOptionsB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFuturesOptionsB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFuturesOptionsB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getOptionsOnEquitiesB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de opções de ações negociadas na B3. Dentre as informações disponíveis no método estão código da Opção, Ativo, data de expiração, lote, entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getOptionsOnEquitiesB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getOptionsOnEquitiesB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getOptionsOnEquitiesB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    # ====================================
    # MÉTODOS DE EVENTOS CORPORATIVOS
    # ====================================

    @validate()
    def getAdjQuoteHistory(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        NominalValue: bool | None = None,
        MissingValues: bool | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Retorna o histórico de cotações ajustadas a proventos, incluindo preços de abertura, fechamento, máximo, mínimo, volume negociado e fatores de ajuste aplicados devido a eventos corporativos como dividendos, splits, bonificações, etc.

            Parameters
            ----------
            Symbols : str
                Código do ativo (ex PETR4)
            InitialDate : str
                Data inicial no formato YYYY-MM-DD, ou datas dinâmicas como: D-1, C-1, PDU_MES-1, etc.
            FinalDate : str
                Data final no formato YYYY-MM-DD ou datas dinâmicas como: D-1, C-1, PDU_MES-1, etc. Se informado, deve ser também informado o initialDate respectivo.
            NominalValue : bool
                Mostrar os valores nominais. (padrão false)
            MissingValues : bool
                Valor atribuído quando não houver dado disponível (padrão false)
            Page : int
                Índice de início para paginação. Se não informado, será retornada a primeira página.
            Rows : int
                Número máximo de registros a retornar (máx 1000). Para formatos como Excel o número retornado será sempre 10000, independente do valor informado.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel). Se não informado, será retornado o formato Json.
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getAdjQuoteHistory(Symbols=..., InitialDate=..., FinalDate=..., NominalValue=..., MissingValues=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getAdjQuoteHistory', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getAdjQuoteHistory'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCorporateActions(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        EvtActnTpCd: str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Retorna informações detalhadas sobre eventos corporativos de ativos listados na bolsa.

            Tipos de eventos corporativos incluem distribuição de proventos (dividendos, JCP, bonificações),
            alterações no capital (splits, grupamentos, incorporações), direitos de subscrição e outros eventos
            que afetam o preço e quantidade de ações.

            Parameters
            ----------
            Symbols : str
                Código do ativo (ex PETR4)
            InitialDate : str
                Data inicial no formato YYYY-MM-DD, ou datas dinâmicas como: D-1, C-1, PDU_MES-1, etc.
            FinalDate : str
                Data final no formato YYYY-MM-DD ou datas dinâmicas como: D-1, C-1, PDU_MES-1, etc. Se informado, deve ser também informado o initialDate respectivo.
            EvtActnTpCd : str
                Código do tipo do Evento Corporativo. Valores Aceitos (1 ou mais códigos separados por vírgula):
                * `10` - DIVIDENDO

                * `11` - RESTITUIÇÃO DE CAPITAL

                * `12` - BONIFICAÇÃO EM DINHEIRO

                * `13` - JUROS SOBRE CAPITAL PRÓPRIO

                * `14` - RENDIMENTO

                * `16` - JUROS

                * `17` - AMORTIZAÇÃO

                * `18` - PREMIO

                * `19` - ATUALIZAÇÃO MONETÁRIA

                * `20` - BONIFICAÇÃO EM ATIVOS

                * `21` - RESTITUIÇÃO CAPITAL EM AÇÕES

                * `22` - RESTITUIÇÃO CAPITALCOM REDUÇÃO DO NÚMERO DE AÇÕES

                * `30` - DESDOBRAMENTO DE AÇÕES

                * `40` - GRUPAMENTO

                * `50` - SUBSCRIÇÃO

                * `51` - PRIORIDADE DE SUBSCRICAO

                * `52` - EXERCICIO DE SUBSCRICAO

                * `53` - SUBSCRICAO COM RENUNCIA DO DIREITO DE PREFERENCIA

                * `60` - INCORPORAÇÃO

                * `70` - FUSÃO

                * `71` - CANCELAMENTO DE FRAÇÕES

                * `72` - LEILÃO DE FRAÇÕES

                * `73` - DOAÇÃO DE FRAÇÕES

                * `74` - ADMINISTRAÇÃO DE FRAÇÕES

                * `75` - COMPRA DE FRAÇÕES

                * `76` - VENDA DE FRAÇÕES

                * `80` - CISÃO COM RED. DE CAPITAL

                * `81` - CISÃO COM RED. DE CAPITAL E QTDE

                * `90` - ATUALIZACAO

                * `91` - EVENTO COM MÚLTIPLOS REQUISITOS E RESULTADOS

                * `92` - RETRATAÇÃO

                * `93` - RESGATE PARCIAL RENDA FIXA

                * `94` - RESGATE RENDA FIXA

                * `95` - CONVERSÃO DE ATIVOS

                * `96` - DISSIDÊNCIA

                * `97` - RESGATE RENDA VARIÁVEL

                * `98` - RENDIMENTO LÍQUIDO

                * `99` - SOBRAS DE SUBSCRIÇÃO

                * `101` - HOMOLOGAÇÃO DE SUBSCRIÇÃO
            Page : int
                Índice de início para paginação. Se não informado, será retornada a primeira página.
            Rows : int
                Número máximo de registros a retornar (máx 1000). Para formatos como Excel o número retornado será sempre 10000, independente do valor informado.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel). Se não informado, será retornado o formato Json.
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCorporateActions(Symbols=..., InitialDate=..., FinalDate=..., EvtActnTpCd=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCorporateActions', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCorporateActions'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCurvesB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de curvas da B3, swap, informações como identificação proprietária do instrumento, número de registros, código da taxa, descrição da taxa, prazo em dias corridos, taxa teórica, características do vértice e outras.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCurvesB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCurvesB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCurvesB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getEconomicIndicatorsB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém os principais indicadores dos ativos negociados na B3. Entre eles estão máxima, mínima, média.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getEconomicIndicatorsB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getEconomicIndicatorsB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getEconomicIndicatorsB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getScheduleCriB3(
        self,
        Symbols: str,
        RefDate: str | None = None,
        IniActlEvtDt: str | None = None,
        FinalActlEvtDt: str | None = None,
        IniPmtDt: str | None = None,
        FinalPmtDt: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter fluxo de pagamentos de CRI da B3.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            RefDate : str
                Data referencial para extrações históricas. Se informado
            IniActlEvtDt : str
                Data Inicial para extrações históricas.
            FinalActlEvtDt : str
                Data Final para extrações históricas. Se informado, deve ser também informado o IniActlEvtDt e não deve ser

                informado o parâmetro refDate
            IniPmtDt : str
                Data Inicial para extrações históricas.
            FinalPmtDt : str
                Data Final para extrações históricas. Se informado, deve ser também informado o IniPmtDt e não deve ser informado o

                parâmetro refDate
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos

                separados por vírgula (usar :all para todos os fields):
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getScheduleCriB3(Symbols=..., RefDate=..., IniActlEvtDt=..., FinalActlEvtDt=..., IniPmtDt=..., FinalPmtDt=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getScheduleCriB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getScheduleCriB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getScheduleCraB3(
        self,
        Symbols: str,
        RefDate: str | None = None,
        IniActlEvtDt: str | None = None,
        FinalActlEvtDt: str | None = None,
        IniPmtDt: str | None = None,
        FinalPmtDt: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter fluxo de pagamentos de CRA da B3.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            RefDate : str
                Data referencial para extrações históricas. Se informado
            IniActlEvtDt : str
                Data Inicial para extrações históricas.
            FinalActlEvtDt : str
                Data Final para extrações históricas. Se informado, deve ser também informado o IniActlEvtDt e não deve ser

                informado o parâmetro refDate
            IniPmtDt : str
                Data Inicial para extrações históricas.
            FinalPmtDt : str
                Data Final para extrações históricas. Se informado, deve ser também informado o IniPmtDt e não deve ser informado o

                parâmetro refDate
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos

                separados por vírgula (usar :all para todos os fields):
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getScheduleCraB3(Symbols=..., RefDate=..., IniActlEvtDt=..., FinalActlEvtDt=..., IniPmtDt=..., FinalPmtDt=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getScheduleCraB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getScheduleCraB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCorpActB3(
        self,
        Symbols: str,
        RefDate: str,
        Fields: str | None = None,
        CorpActnTpCd: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método serve para mostrar dados de eventos corporativos B3 (forma alternativa corporativa).

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            RefDate : str
                Data referencial para extrações históricas. Se informado
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields):
            CorpActnTpCd : str
                Informar o(s) numero(s) do(s) evento(s) corporativo(s).
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCorpActB3(Symbols=..., RefDate=..., Fields=..., CorpActnTpCd=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCorpActB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCorpActB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getVolSB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém valores da volatilidade de Tickers da B3, como IBOV11, PETR4, Boi Gordo (em reais), entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getVolSB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getVolSB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getVolSB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getRegulatoryListed(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para consulta de informações regulatórias de ativos listados.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getRegulatoryListed(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getRegulatoryListed', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getRegulatoryListed'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getRegulatoryOTC(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para consulta de informações regulatórias de ativos de Balcão da B3.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getRegulatoryOTC(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getRegulatoryOTC', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getRegulatoryOTC'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFundsCVM175(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de fundos CVM (atualizados pela resolução Nº 175 da CVM), é possível obter informações cadastrais e de valor, tais como nome do fundo, cnpj do fundo, patrimônio líquido, tipo de fundo, categoria do fundo, classe do fundo, variações percentuais, valor em carteira, rentabilidade, gestor do fundo, administrador do fundo e status do fundo, entre outras.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFundsCVM175(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFundsCVM175', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFundsCVM175'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFundsAnbima175(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de fundos Anbima (atualizados pela resolução Nº 175 da CVM), é possível obter informações cadastrais e de valor, tais como nome do fundo, cnpj do fundo, patrimônio líquido, tipo de fundo, categoria do fundo, classe do fundo, variações percentuais, valor em carteira, rentabilidade, gestor do fundo, administrador do fundo e status do fundo, entre outras.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFundsAnbima175(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFundsAnbima175', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFundsAnbima175'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFunds(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de fundos CVM, é possível obter informações cadastrais e de valor, tais como nome do fundo, cnpj do fundo, patrimônio líquido, tipo de fundo, categoria do fundo, classe do fundo, variações percentuais, valor em carteira, rentabilidade, gestor do fundo, administrador do fundo e status do fundo, entre outras.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFunds(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFunds', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFunds'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getFundsAnbima(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de fundos Anbima, é possível obter informações cadastrais e de valor, tais como nome do fundo, cnpj do fundo, patrimônio líquido, tipo de fundo, categoria do fundo, classe do fundo, variações percentuais, valor em carteira, rentabilidade, gestor do fundo, administrador do fundo e status do fundo, entre outras.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getFundsAnbima(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getFundsAnbima', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getFundsAnbima'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCorpDebentures(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de debêntures. Informações cadastrais, tais como instituição depositária, agente fiduciário, emissor, banco mandatário, CNPJ, agência classificadora e outros; E também informações quantitativas, como valor nominal na emissão, quantidade emitida, valor de compra, valor máximo, valor mínimo, valor de venda, preço unitário, taxa indicativa e outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCorpDebentures(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCorpDebentures', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCorpDebentures'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCriCraAnbima(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para trazer dados de mercado secundário de CRI e CRA do Anbima-Feed.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCriCraAnbima(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCriCraAnbima', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCriCraAnbima'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getCriCraB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de CRI e CRA da B3, tais como empresa emissora, instituição depositária, agente fiduciário, pu de emissão, quantidade emitida, taxa de juros e outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getCriCraB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getCriCraB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getCriCraB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDebenturesB3(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados de debêntures da B3, é possível encontrar registros cadastrais, tais como mercadoria, ticker, ISIN, moeda de negociação, nome da companhia, data de vencimento do instrumento, taxa de juros, valor unitário do título, classificação de risco do ativo, banco mandatário, instituição depositária e outros; também é possível encontrar registros de valor, tais como preço de abertura do dia, preço máximo do dia, preço mínimo do dia, preço médio do dia, preço de fechamento, oscilação do dia, prazo de dias para liquidação e outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getDebenturesB3(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getDebenturesB3', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getDebenturesB3'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getDebenturesAnbima(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para trazer dados de debêntures do Anbima Feed.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getDebenturesAnbima(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getDebenturesAnbima', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getDebenturesAnbima'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getVna(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém os dados de Valor Nominal Atualizado (VNA) dos títulos públicos NTN-B, NTN-C e LFT.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getVna(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getVna', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getVna'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getInflation(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados como data de divulgação, variação percentual dos principais Índices de inflação. Tais como IGP-M, INPC, IPCA, entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getInflation(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getInflation', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getInflation'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getMacroEcon(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém os principais dados estatísticos como desvio padrão, minima, máxima, média das informações disponiveis no Boletim Focus, sendo eles: PIB, IPCA, IGP-M e outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getMacroEcon(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getMacroEcon', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getMacroEcon'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getMoneyMarkets(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados das taxas de juros como Selic, Meta-Selic, IRF-M, TJLP, entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getMoneyMarkets(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getMoneyMarkets', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getMoneyMarkets'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getMoneyMktMth(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém dados das taxas de juros mensais como UR INPC e UR IGPM.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getMoneyMktMth(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getMoneyMktMth', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getMoneyMktMth'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getRates(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Contém informações como número do índice, taxa, valor, variações percentuais de taxas CDI, TR, IGP-M, Poupança, entre outros.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getRates(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getRates', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getRates'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )

    @validate()
    def getRatesMonthly(
        self,
        Symbols: str,
        InitialDate: str,
        FinalDate: str | None = None,
        Fields: str | None = None,
        IgnDefault: str | None = None,
        Lang: Lang | str | None = None,
        Page: int | None = None,
        Rows: int | None = None,
        Format: ResponseFormat | str | None = None,
        IgnNull: str | None = None,
        **kwargs: dict,
    ) -> BDSResult:
        """
            Método para obter dados de taxas mensais.

            Parameters
            ----------
            Symbols : str
                Informar o que deseja procurar
            InitialDate : str
                Data Inicial para extrações históricas.
            FinalDate : str
                Data Final para extrações históricas.Se informado, deve ser também informado o initialDate respectivo.
            Fields : str
                Campos de retorno adicionais solicitados, utilizando os mnemônicos ou estilos cadastrados. Aceitando um ou N campos separados por vírgula (usar :all para todos os fields)
            IgnDefault : str
                Retorna somente os campos especificados em fields. Aceita 1, true, yes ou 0, false, no
            Lang : str
                Idioma da resposta da API. Aceita os valores: PT, EN, ES. Se não informado, será retornado o valor padrão de EN (Inglês).
            Page : int
                Página de retorno. Se não informado, será retornada a primeira página.
            Rows : int
                Quantidade de linhas por página. Se não informado, será retornado o valor padrão de 1000 linhas.
            Format : str
                Formato de serialização da resposta da API. (Json, Xml, Csv, Excel)
            IgnNull : str
                Se deve retornar valores nulos ou não

            Returns
            -------
            BDSResult: Resposta da API

            Examples
            --------
            Uso básico:

            >>> result = datapack.getRatesMonthly(Symbols=..., InitialDate=..., FinalDate=..., Fields=..., IgnDefault=..., Lang=..., Page=..., Rows=..., Format=..., Format=..., IgnNull=...)
            >>> print(result)
                BDSResult(api_url='{BDS_DATAPACK_URL}/getRatesMonthly', status_code=200, call_duration=..., correlation_id=...)
        """
        url = f'{self._core.datapack_url}/getRatesMonthly'

        return self._core._BDSCore__request(
            method='get',
            url=url,
            params=kwargs['params'],
        )
