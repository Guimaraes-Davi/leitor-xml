# Leitor XML Fiscal

Aplicação web para leitura e interpretação de documentos fiscais brasileiros (NFe, CTe, MDFe, etc).

## Acesse online
https://leitor-xml.onrender.com/

## Versão 1.0
- Upload de XML
- Identificação automática do tipo (baseado em namespace)
- Extração e exibição de dados de NFe

## Como usar
```bash
pip install -r requirements.txt
python run.py
```

## Arquitetura
Veja `CLAUDE.md` para decisões técnicas e padrões.

## Stack
- Flask
- lxml
- HTML/CSS (dark mode)

## Autor
Davi Guimarães