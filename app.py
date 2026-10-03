from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_NAME = "fila.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            servico TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aguardando',
            criado_em TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def index():

    conn = get_db()

    clientes = conn.execute("""
        SELECT * FROM clientes
        WHERE status != 'Concluído'
        AND status != 'Cancelado'
        ORDER BY id ASC
    """).fetchall()

    historico = conn.execute("""
        SELECT * FROM clientes
        WHERE status IN ('Concluído', 'Cancelado')
        ORDER BY id DESC
        LIMIT 12
    """).fetchall()

    atual = conn.execute("""
        SELECT * FROM clientes
        WHERE status = 'Em Atendimento'
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()

    conn.close()

    aguardando = sum(
        1 for cliente in clientes
        if cliente["status"] == "Aguardando"
    )

    return render_template(
        "index.html",
        clientes=clientes,
        historico=historico,
        atual=atual,
        aguardando=aguardando
    )


@app.post("/cadastrar")
def cadastrar():

    nome = request.form.get("nome", "").strip()
    servico = request.form.get("servico", "").strip()

    if nome and servico:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO clientes
            (nome, servico, status, criado_em)
            VALUES (?, ?, 'Aguardando', ?)
            """,
            (
                nome,
                servico,
                datetime.now().strftime("%d/%m/%Y %H:%M")
            )
        )

        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.post("/chamar")
def chamar():

    conn = get_db()

    atual = conn.execute("""
        SELECT id
        FROM clientes
        WHERE status = 'Em Atendimento'
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()

    if atual:

        conn.execute(
            """
            UPDATE clientes
            SET status = 'Concluído'
            WHERE id = ?
            """,
            (atual["id"],)
        )

    proximo = conn.execute("""
        SELECT id
        FROM clientes
        WHERE status = 'Aguardando'
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()

    if proximo:

        conn.execute(
            """
            UPDATE clientes
            SET status = 'Em Atendimento'
            WHERE id = ?
            """,
            (proximo["id"],)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.post("/status/<int:cliente_id>")
def alterar_status(cliente_id):

    novo_status = request.form.get("status")

    permitidos = {
        "Aguardando",
        "Em Atendimento",
        "Concluído",
        "Cancelado"
    }

    if novo_status in permitidos:

        conn = get_db()

        conn.execute(
            """
            UPDATE clientes
            SET status = ?
            WHERE id = ?
            """,
            (novo_status, cliente_id)
        )

        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.post("/cancelar/<int:cliente_id>")
def cancelar(cliente_id):

    conn = get_db()

    conn.execute(
        """
        UPDATE clientes
        SET status = 'Cancelado'
        WHERE id = ?
        """,
        (cliente_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.post("/limpar")
def limpar():

    conn = get_db()

    conn.execute("DELETE FROM clientes")

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)