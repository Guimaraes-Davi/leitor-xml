# Leitor XML Fiscal

## Contexto do projeto
Aplicação web em Python/Flask para leitura e interpretação de XMLs fiscais brasileiros (NFe, NFCe, CTe, MDFe).

## Objetivo da versão 1.0
- Upload de arquivo XML via interface web
- Identificação automática do tipo do documento
- Extração e exibição formatada dos dados de NFe

## Stack
- Python 3
- Flask (framework web)
- lxml ou xml.etree (parsing de XML)
- HTML/CSS (frontend simples)

## Estrutura esperada do projeto

leitor-xml/
├── app/
│   ├── init.py
│   ├── parser.py        # lógica de parsing do XML
│   └── routes.py        # rotas Flask
├── templates/
│   └── index.html
├── static/
├── run.py
└── requirements.txt

## Padrões a seguir
- Código comentado em português
- Funções pequenas com responsabilidade única
- Tratamento de erros em todas as operações de parsing
- Nunca salvar XMLs enviados — processar em memória e descartar

## Namespaces fiscais brasileiros conhecidos
- NFe: http://www.portalfiscal.inf.br/nfe
- CTe: http://www.portalfiscal.inf.br/cte
- MDFe: http://www.portalfiscal.inf.br/mdfe