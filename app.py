# -*- coding: utf-8 -*-
"""MinhaLoja - back-end (Flask + SQLite).
Rodar:  pip install -r requirements.txt  ->  python app.py  ->  http://localhost:5000
"""
import os
import sqlite3
from datetime import date

from flask import Flask, g, jsonify, request

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "minhaloja.db")
app = Flask(__name__, static_folder="static", static_url_path="")

# nome, categoria, preco, estoque, promo %, icone
PRODUTOS = [
    ("Notebook", "Informática", 3500.00, 12, 10, "💻"),
    ("Smartphone", "Informática", 2200.00, 18, 0, "📱"),
    ("Monitor 27'' 144Hz", "Informática", 1390.00, 9, 0, "🖥️"),
    ("SSD NVMe 1TB", "Informática", 459.00, 25, 0, "💾"),
    ("Roteador Wi-Fi 6", "Informática", 399.00, 14, 15, "📡"),
    ("Webcam Full HD", "Informática", 229.00, 3, 0, "📷"),
    ("Cafeteira", "Eletrodomésticos", 350.00, 7, 15, "☕"),
    ("Geladeira", "Eletrodomésticos", 2900.00, 4, 0, "🧊"),
    ("Smart TV 50''", "Eletrodomésticos", 2490.00, 6, 12, "📺"),
    ("Air Fryer 12L", "Eletrodomésticos", 429.00, 8, 18, "🍟"),
    ("Ventilador Turbo", "Eletrodomésticos", 239.00, 2, 0, "🌀"),
    ("Fone Bluetooth", "Áudio", 180.00, 30, 20, "🎧"),
    ("Headset 7.1", "Áudio", 289.00, 15, 0, "🎮"),
    ("Caixa de Som Bluetooth", "Áudio", 259.00, 16, 0, "🔊"),
    ("Mouse Gamer", "Acessórios", 180.00, 30, 0, "🖱️"),
    ("Teclado Mecânico", "Acessórios", 320.00, 22, 25, "⌨️"),
    ("Controle Sem Fio", "Acessórios", 349.00, 20, 10, "🕹️"),
    ("Smartwatch", "Acessórios", 599.00, 11, 30, "⌚"),
    ("Power Bank 20000mAh", "Acessórios", 149.00, 40, 0, "🔋"),
    ("Lâmpada Smart RGB", "Casa Inteligente", 49.90, 60, 0, "💡"),
]

# Histórico do script original: data, produto, quantidade, valor unitário
VENDAS = [
    ("2024-01-15", "Notebook", 1, 3500.00), ("2024-01-20", "Cafeteira", 2, 350.00),
    ("2024-01-30", "Fone Bluetooth", 4, 180.00), ("2024-02-05", "Smartphone", 1, 2200.00),
    ("2024-02-18", "Fone Bluetooth", 3, 180.00), ("2024-02-25", "Notebook", 2, 3500.00),
    ("2024-03-10", "Geladeira", 1, 2900.00), ("2024-03-22", "Fone Bluetooth", 5, 180.00),
    ("2024-03-28", "Cafeteira", 1, 350.00), ("2024-04-02", "Smartphone", 2, 2200.00),
    ("2024-04-19", "Geladeira", 1, 2900.00), ("2024-04-25", "Notebook", 1, 3500.00),
    ("2024-05-03", "Cafeteira", 3, 350.00), ("2024-05-15", "Smartphone", 2, 2200.00),
    ("2024-05-28", "Fone Bluetooth", 6, 180.00), ("2024-06-10", "Geladeira", 2, 2900.00),
    ("2024-06-20", "Notebook", 3, 3500.00), ("2024-06-30", "Smartphone", 1, 2200.00),
]


class Erro(Exception):
    def __init__(self, msg, status=400):
        self.msg, self.status = msg, status


@app.errorhandler(Erro)
def tratar_erro(e):
    return jsonify(erro=e.msg), e.status


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def fechar(_):
    con = g.pop("db", None)
    if con:
        con.close()


def iniciar_banco():
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL CHECK (preco > 0),
            estoque INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
            promo REAL NOT NULL DEFAULT 0 CHECK (promo BETWEEN 0 AND 100),
            icone TEXT NOT NULL DEFAULT '🔌'
        );
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            produto_id INTEGER,
            produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL
        );
    """)
    # só popula na primeira vez (o script original apagava as vendas a cada execução)
    if con.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO produtos (nome, categoria, preco, estoque, promo, icone) VALUES (?,?,?,?,?,?)",
            PRODUTOS)
        for data, nome, qtd, unit in VENDAS:
            pid, cat = con.execute("SELECT id, categoria FROM produtos WHERE nome=?", (nome,)).fetchone()
            con.execute(
                "INSERT INTO vendas (data, produto_id, produto, categoria, quantidade, valor_unitario) "
                "VALUES (?,?,?,?,?,?)", (data, pid, nome, cat, qtd, unit))
    con.commit()
    con.close()


def numero(v, minimo, maximo, tipo=float, campo="valor"):
    try:
        n = tipo(v)
    except (TypeError, ValueError):
        raise Erro(f"{campo} inválido")
    if not minimo <= n <= maximo:
        raise Erro(f"{campo} deve estar entre {minimo} e {maximo}")
    return n


def produto_json(p):
    d = dict(p)
    d["preco_final"] = round(p["preco"] * (1 - p["promo"] / 100), 2)
    return d


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/produtos")
def listar():
    rows = db().execute("SELECT * FROM produtos ORDER BY categoria, nome").fetchall()
    return jsonify([produto_json(p) for p in rows])


@app.post("/api/produtos")
def criar():
    d = request.get_json(silent=True) or {}
    nome = str(d.get("nome", "")).strip()
    categoria = str(d.get("categoria", "")).strip()
    if not nome or not categoria:
        raise Erro("Informe nome e categoria")
    preco = numero(d.get("preco"), 0.01, 1_000_000, float, "preço")
    estoque = numero(d.get("estoque", 0), 0, 100_000, int, "estoque")
    promo = numero(d.get("promo", 0), 0, 100, float, "promoção")
    icone = str(d.get("icone") or "🔌")[:4]
    try:
        with db() as con:
            con.execute(
                "INSERT INTO produtos (nome, categoria, preco, estoque, promo, icone) VALUES (?,?,?,?,?,?)",
                (nome, categoria, preco, estoque, promo, icone))
    except sqlite3.IntegrityError:
        raise Erro("Já existe um produto com esse nome", 409)
    return jsonify(ok=True), 201


@app.patch("/api/produtos/<int:pid>")
def atualizar(pid):
    d = request.get_json(silent=True) or {}
    campos = {}
    if "estoque" in d:
        campos["estoque"] = numero(d["estoque"], 0, 100_000, int, "estoque")
    if "promo" in d:
        campos["promo"] = numero(d["promo"], 0, 100, float, "promoção")
    if "preco" in d:
        campos["preco"] = numero(d["preco"], 0.01, 1_000_000, float, "preço")
    if not campos:
        raise Erro("Nada para atualizar")
    sql = "UPDATE produtos SET " + ", ".join(f"{c}=?" for c in campos) + " WHERE id=?"
    with db() as con:
        if con.execute(sql, (*campos.values(), pid)).rowcount == 0:
            raise Erro("Produto não encontrado", 404)
    return jsonify(ok=True)


@app.delete("/api/produtos/<int:pid>")
def remover(pid):
    with db() as con:
        if con.execute("DELETE FROM produtos WHERE id=?", (pid,)).rowcount == 0:
            raise Erro("Produto não encontrado", 404)
    return jsonify(ok=True)


@app.post("/api/vendas")
def vender():
    d = request.get_json(silent=True) or {}
    extra = numero(d.get("desconto", 0), 0, 100, float, "desconto")
    itens = {}
    for it in d.get("itens") or []:  # junta o mesmo produto repetido
        pid = numero(it.get("id"), 1, 10**9, int, "produto")
        itens[pid] = itens.get(pid, 0) + numero(it.get("qtd"), 1, 999, int, "quantidade")
    if not itens:
        raise Erro("Carrinho vazio")

    con = db()
    linhas, total = [], 0.0
    for pid, qtd in itens.items():
        p = con.execute("SELECT * FROM produtos WHERE id=?", (pid,)).fetchone()
        if not p:
            raise Erro("Produto não encontrado", 404)
        if p["estoque"] < qtd:
            raise Erro(f"Estoque insuficiente de {p['nome']}: restam {p['estoque']}", 409)
        unit = round(p["preco"] * (1 - p["promo"] / 100) * (1 - extra / 100), 2)
        linhas.append((p, qtd, unit))
        total += unit * qtd

    hoje = date.today().isoformat()
    with con:  # tudo ou nada
        for p, qtd, unit in linhas:
            con.execute(
                "INSERT INTO vendas (data, produto_id, produto, categoria, quantidade, valor_unitario) "
                "VALUES (?,?,?,?,?,?)", (hoje, p["id"], p["nome"], p["categoria"], qtd, unit))
            con.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (qtd, p["id"]))
    return jsonify(ok=True, total=round(total, 2)), 201


@app.get("/api/relatorio")
def relatorio():
    con = db()
    q = lambda sql: [dict(r) for r in con.execute(sql).fetchall()]
    kpi = dict(con.execute(
        "SELECT COALESCE(SUM(quantidade*valor_unitario),0) AS faturamento, "
        "COALESCE(SUM(quantidade),0) AS unidades, COUNT(*) AS vendas FROM vendas").fetchone())
    kpi["ticket"] = round(kpi["faturamento"] / kpi["vendas"], 2) if kpi["vendas"] else 0
    kpi["valor_estoque"] = con.execute("SELECT COALESCE(SUM(preco*estoque),0) FROM produtos").fetchone()[0]
    kpi["por_mes"] = q("SELECT substr(data,1,7) AS mes, SUM(quantidade*valor_unitario) AS total "
                       "FROM vendas GROUP BY mes ORDER BY mes")
    kpi["por_categoria"] = q("SELECT categoria, SUM(quantidade*valor_unitario) AS total "
                             "FROM vendas GROUP BY categoria ORDER BY total DESC")
    kpi["ranking"] = q("SELECT produto, SUM(quantidade) AS unidades, SUM(quantidade*valor_unitario) AS total "
                       "FROM vendas GROUP BY produto ORDER BY total DESC LIMIT 8")
    return jsonify(kpi)


iniciar_banco()

if __name__ == "__main__":
    app.run(debug=True)
