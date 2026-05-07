# BiblioGestor — Sistema de Gestão de Biblioteca

Sistema completo, leve e 100% offline para gerenciar empréstimos de livros.
Desenvolvido em Python com Tkinter e SQLite.

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Painel** | Resumo geral, empréstimos em aberto |
| **Livros** | Cadastro com busca por categoria e filtros |
| **Associados** | Cadastro de Associados, Professores, Funcionários e Visitantes |
| **Dependentes** | Dependentes vinculados a associados |
| **Empréstimos** | Busca inteligente por livro e mutuário (associado/dependente) |
| **Devoluções** | Confirmação simples de devolução |
| **Relatórios** | Histórico, em aberto, livros mais emprestados |

---

## Instalação

### Requisitos
- Python 3.8+
- pip

### Dependências
```bash
pip install -r requirements.txt
```

### Executar
```bash
python main.py
```

---

## Usuários (Gestores)

O sistema possui controle de acesso via login:
- Usuário padrão: `admin`
- Senha padrão: `admin123`

Para criar novos usuários, acesse o banco de dados SQLite.

---

## Estrutura do Projeto

```
BiblioGestor/
├── main.py                 # Arquivo principal
├── config.py               # Configurações e cores
├── database/
│   ├── __init__.py        # Conexão com banco
│   └── models.py          # Tabelas e migrações
├── ui/
│   ├── __init__.py
│   ├── utils.py           # Funções auxiliares de UI
│   └── frames/
│       ├── __init__.py
│       ├── login.py       # Tela de login
│       ├── painel.py      # Painel principal
│       ├── livros.py      # Gestão de livros
│       ├── associados.py  # Gestão de associados
│       ├── dependentes.py # Gestão de dependentes
│       ├── emprestimos.py # Empréstimos
│       ├── devolucoes.py  # Devoluções
│       └── relatorios.py  # Relatórios
├── assets/                # Imagens de fundo
├── importar_livros.py     # Importação Excel
├── requirements.txt       # Dependências
└── biblioteca.db          # Banco de dados
```

---

## Importar Livros da Planilha

1. Coloque a planilha `.xlsx` na pasta do sistema
2. Execute:
```bash
python importar_livros.py
```

Categorias importadas:
- Espiritismo - Chico Xavier
- Espiritismo - Divaldo Franco
- Obras Diversas

---

## Backup

Todos os dados ficam no arquivo `biblioteca.db`.
Para backup, copie este arquivo para um pen drive ou nuvem.
