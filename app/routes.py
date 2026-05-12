from flask import Blueprint, render_template, request, jsonify
from app.parser import parse_xml

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/upload', methods=['POST'])
def upload():
    arquivo = request.files.get('arquivo')
    if not arquivo:
        return jsonify({'erro': 'Nenhum arquivo enviado.'}), 400

    try:
        dados = parse_xml(arquivo.read())
        return jsonify(dados)
    except NotImplementedError as e:
        return jsonify({'erro': str(e)}), 422
    except ValueError as e:
        return jsonify({'erro': str(e)}), 422
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar o XML: {str(e)}'}), 500
