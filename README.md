# MinhaLoja

Loja de eletrônicos com PDV, controle de estoque, promoções e relatório de vendas.
Back-end em Flask + SQLite, front-end em HTML/CSS/JS puro.

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Abra http://localhost:5000

## Estrutura
- `app.py`: API (produtos, vendas, relatório) e banco SQLite
- `static/index.html`: página da loja
- `requirements.txt`: dependências

O banco `minhaloja.db` é criado e populado automaticamente na primeira execução.
