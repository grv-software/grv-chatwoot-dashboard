"""
db.py — Conexão com o PostgreSQL da Soma Imob.

Não é um dos 5 módulos pedidos, mas é a dependência mínima que
harness/context_builder.py, harness/logger.py e jobs/proactive_scanner.py
precisam pra rodar de verdade (e não ficar pseudo-código). Não é
acoplamento entre os módulos do arnês — é a mesma dependência de
infraestrutura que qualquer um deles teria com o driver do banco.

Credenciais vêm sempre de variável de ambiente — nunca hardcoded.
"""
import os
import psycopg2
import psycopg2.extras


def get_connection():
    """Abre uma nova conexão com o banco usando DATABASE_URL do ambiente."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL não configurada no ambiente. "
            "Copie .env.example para .env e preencha os valores."
        )
    return psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
