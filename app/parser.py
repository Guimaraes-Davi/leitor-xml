from abc import ABC, abstractmethod
from lxml import etree


# Mapeamento de namespace URI → tipo do documento fiscal
TIPO_POR_NAMESPACE = {
    'http://www.portalfiscal.inf.br/nfe': 'NFe',
    'http://www.portalfiscal.inf.br/cte': 'CTe',
    'http://www.portalfiscal.inf.br/mdfe': 'MDFe',
}


_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


def detect_tipo_xml(raw_bytes: bytes) -> tuple:
    """Identifica o tipo do documento fiscal inspecionando o namespace do elemento raiz.

    Retorna uma tupla (tipo_str, root_element) para evitar parsear duas vezes.
    """
    root = etree.fromstring(raw_bytes, _SAFE_PARSER)
    for uri in root.nsmap.values():
        if uri in TIPO_POR_NAMESPACE:
            return TIPO_POR_NAMESPACE[uri], root
    raise ValueError(
        f"Namespace fiscal não reconhecido. Namespaces encontrados: {list(root.nsmap.values())}"
    )


# ---------------------------------------------------------------------------
# Classe base
# ---------------------------------------------------------------------------

class BaseParser(ABC):
    def __init__(self, root: etree._Element):
        self.root = root

    @abstractmethod
    def parse(self) -> dict:
        pass

    @abstractmethod
    def _extract_identificacao(self) -> dict:
        pass

    @abstractmethod
    def _extract_emitente(self) -> dict:
        pass

    @abstractmethod
    def _extract_destinatario(self) -> dict:
        pass

    @abstractmethod
    def _extract_itens(self) -> list:
        pass

    @abstractmethod
    def _extract_totais(self) -> dict:
        pass


# ---------------------------------------------------------------------------
# Parser de NFe (modelo 55) e NFCe (modelo 65)
# ---------------------------------------------------------------------------

class NFeParser(BaseParser):
    NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    def __init__(self, root: etree._Element):
        super().__init__(root)
        # infNFe existe dentro de nfeProc/NFe/infNFe ou diretamente em NFe/infNFe
        self.inf_nfe = root.xpath('//nfe:infNFe', namespaces=self.NS)[0]

    def parse(self) -> dict:
        return {
            **self._extract_identificacao(),
            'emitente': self._extract_emitente(),
            'destinatario': self._extract_destinatario(),
            'itens': self._extract_itens(),
            'totais': self._extract_totais(),
        }

    # --- Helpers internos ---

    def _x(self, element: etree._Element, xpath: str):
        """XPath relativo ao elemento dado com o namespace nfe já injetado.

        Retorna o primeiro resultado ou None.
        """
        result = element.xpath(xpath, namespaces=self.NS)
        return result[0] if result else None

    def _endereco(self, parent: etree._Element, tag_ender: str) -> dict:
        """Extrai campos de endereço de qualquer sub-elemento (enderEmit, enderDest)."""
        ender = self._x(parent, f'nfe:{tag_ender}')
        if ender is None:
            return {}
        x = lambda xp: self._x(ender, xp)
        return {
            'logradouro': x('nfe:xLgr/text()'),
            'numero': x('nfe:nro/text()'),
            'complemento': x('nfe:xCpl/text()'),
            'bairro': x('nfe:xBairro/text()'),
            'municipio': x('nfe:xMun/text()'),
            'uf': x('nfe:UF/text()'),
            'cep': x('nfe:CEP/text()'),
        }

    # --- Implementação dos métodos abstratos ---

    def _extract_identificacao(self) -> dict:
        ide = self._x(self.inf_nfe, 'nfe:ide')
        x = lambda xp: self._x(ide, xp)

        modelo = x('nfe:mod/text()')

        # O atributo Id do infNFe tem o formato "NFe" + 44 dígitos da chave de acesso
        id_attr = self.inf_nfe.get('Id', '')
        chave = id_attr[3:] if id_attr.startswith('NFe') else (
            self._x(self.root, '//nfe:chNFe/text()')
        )

        return {
            # modelo 55 = NFe, 65 = NFCe
            'tipo': 'NFCe' if modelo == '65' else 'NFe',
            'modelo': modelo,
            'chave': chave,
            'serie': x('nfe:serie/text()'),
            'numero': x('nfe:nNF/text()'),
            'data_emissao': x('nfe:dhEmi/text()'),
            'natureza_operacao': x('nfe:natOp/text()'),
            # 0 = entrada, 1 = saída
            'tipo_operacao': x('nfe:tpNF/text()'),
        }

    def _extract_emitente(self) -> dict:
        emit = self._x(self.inf_nfe, 'nfe:emit')
        if emit is None:
            return {}
        x = lambda xp: self._x(emit, xp)
        return {
            'cnpj': x('nfe:CNPJ/text()'),
            'nome': x('nfe:xNome/text()'),
            'nome_fantasia': x('nfe:xFant/text()'),
            'ie': x('nfe:IE/text()'),
            # CRT: 1=Simples Nacional, 2=Simples Nacional excesso, 3=Regime Normal
            'crt': x('nfe:CRT/text()'),
            'endereco': self._endereco(emit, 'enderEmit'),
        }

    def _extract_destinatario(self) -> dict:
        dest = self._x(self.inf_nfe, 'nfe:dest')
        if dest is None:
            return {}
        x = lambda xp: self._x(dest, xp)
        cnpj = x('nfe:CNPJ/text()')
        cpf = x('nfe:CPF/text()')
        return {
            'cnpj': cnpj,
            'cpf': cpf,
            'documento': cnpj or cpf,
            'tipo_documento': 'CNPJ' if cnpj else 'CPF',
            'nome': x('nfe:xNome/text()'),
            'ie': x('nfe:IE/text()'),
            'email': x('nfe:email/text()'),
            'endereco': self._endereco(dest, 'enderDest'),
        }

    def _extract_itens(self) -> list:
        itens = []
        for det in self.inf_nfe.xpath('nfe:det', namespaces=self.NS):
            prod = self._x(det, 'nfe:prod')
            if prod is None:
                continue
            x = lambda xp, _p=prod: self._x(_p, xp)
            itens.append({
                'numero_item': det.get('nItem'),
                'codigo': x('nfe:cProd/text()'),
                'ean': x('nfe:cEAN/text()'),
                'descricao': x('nfe:xProd/text()'),
                'ncm': x('nfe:NCM/text()'),
                'cfop': x('nfe:CFOP/text()'),
                'unidade_comercial': x('nfe:uCom/text()'),
                'quantidade': x('nfe:qCom/text()'),
                'valor_unitario': x('nfe:vUnCom/text()'),
                'valor_total_produto': x('nfe:vProd/text()'),
                'valor_desconto': x('nfe:vDesc/text()'),
                'valor_frete': x('nfe:vFrete/text()'),
                'valor_seguro': x('nfe:vSeg/text()'),
                'valor_outros': x('nfe:vOutro/text()'),
            })
        return itens

    def _extract_totais(self) -> dict:
        tot = self._x(self.inf_nfe, 'nfe:total/nfe:ICMSTot')
        if tot is None:
            return {}
        x = lambda xp: self._x(tot, xp)
        return {
            'valor_produtos': x('nfe:vProd/text()'),
            'valor_frete': x('nfe:vFrete/text()'),
            'valor_seguro': x('nfe:vSeg/text()'),
            'valor_desconto': x('nfe:vDesc/text()'),
            'valor_outros': x('nfe:vOutro/text()'),
            'valor_nf': x('nfe:vNF/text()'),
            'base_calculo_icms': x('nfe:vBC/text()'),
            'valor_icms': x('nfe:vICMS/text()'),
            'valor_ipi': x('nfe:vIPI/text()'),
            'valor_pis': x('nfe:vPIS/text()'),
            'valor_cofins': x('nfe:vCOFINS/text()'),
            'base_calculo_st': x('nfe:vBCST/text()'),
            'valor_st': x('nfe:vST/text()'),
            'valor_total_tributos': x('nfe:vTotTrib/text()'),
        }


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def parse_xml(raw_bytes: bytes) -> dict:
    """Detecta o tipo do XML fiscal e delega ao parser especializado correto."""
    tipo, root = detect_tipo_xml(raw_bytes)

    parsers = {
        'NFe': NFeParser,
        # 'CTe': CTeParser,   # a implementar
        # 'MDFe': MDFeParser, # a implementar
    }

    if tipo not in parsers:
        raise NotImplementedError(f"Parser para {tipo} ainda não implementado.")

    return parsers[tipo](root).parse()
