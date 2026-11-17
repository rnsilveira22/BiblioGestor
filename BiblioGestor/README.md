# 📚 BiblioGestor — Sistema de Gestão de Biblioteca

Sistema leve e 100% offline para gerenciar o acervo e os empréstimos da biblioteca.
Desenvolvido em Python com Tkinter e SQLite, para **Casa Espírita Joana Lima**.

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Painel** | Resumo geral e empréstimos em aberto |
| **Livros** | Cadastro com busca por título, autor e categoria |
| **Leitores** | Cadastro de leitores com tipo, matrícula e contatos |
| **Dependentes** | Dependentes vinculados a associados |
| **Empréstimos** | Busca inteligente por livro e mutuário (associado/dependente), com autocomplete |
| **Devoluções** | Confirmação simples de devolução |
| **Relatórios** | Histórico, em aberto, livros mais emprestados |
| **Usuários** | Gestão de usuários e níveis de acesso (somente Administrador) |

Recursos adicionais:
- Busca sem diferenciar acentos e maiúsculas/minúsculas
- Listas em ordem alfabética e autocomplete nos empréstimos
- Prazo padrão de empréstimo de **14 dias**
- Edição da data prevista de devolução com calendário
- Botões habilitados apenas quando há seleção
- Backup automático do banco antes de cada atualização

---

## Instalação

### Requisitos
- Python 3.8+
- pip

### Dependências
```bash
pip install -r requirements.txt
```

Dependências instaladas: `pandas`, `openpyxl`, `bcrypt`, `Pillow`, `tkcalendar`
(`tkinter` e `sqlite3` já vêm com o Python).

### Executar
```bash
python biblioteca.py
```

No Windows, basta executar o `BiblioGestor.bat` (ou `instalar_e_abrir.bat`
na primeira instalação, que instala as dependências, cria o atalho na Área de
Trabalho e inicia o sistema).

---

## Usuários e Níveis de Acesso

Na primeira execução o sistema cria o usuário padrão:
- Usuário: `admin`
- Senha: `admin123`

Tipos de usuário:
- **Administrador** — acesso a todos os módulos, incluindo Usuários
- **Operador** — acesso somente a Empréstimos e Devoluções

Novos usuários são criados pelo menu **Usuários** (somente Administradores).

---

## Atualização do Sistema

A atualização é feita por um **atualizador externo** (não precisa de Git).

### Online (link por WhatsApp / e-mail)

1. Feche o BiblioGestor
2. Baixe e execute o arquivo `Atualizar_BiblioGestor.exe`
3. Se pedir, selecione a pasta onde o sistema está instalado
4. Aguarde a mensagem de sucesso e abra o sistema novamente

### Offline (pendrive)

Coloque no pendrive:
- `Atualizar_BiblioGestor.exe`
- pasta `pacote_atualizacao\` (com os arquivos novos)

Execute o atualizador e escolha a pasta de instalação.

**O banco de dados (`biblioteca.db`) nunca é sobrescrito.**  
Antes de cada atualização é gerado um backup em `database/`.

Instruções detalhadas: veja o arquivo `COMO_ATUALIZAR.txt`.

Para gerar o `.exe` do atualizador:
```bash
build_atualizador.bat
```

---

## Backup

Todos os dados ficam no arquivo `biblioteca.db`.
Antes de cada atualização é gerada uma cópia em `database/biblioteca_backup_*.db`.

Para backup manual, copie o `biblioteca.db` para um pen drive ou nuvem.

---

## Importar Livros da Planilha

1. Coloque a planilha `BIBLIOTECA_CATEGORIZADA.xlsx` na pasta do sistema
2. Execute:
```bash
python importar_livros.py
```

O script lê a aba **Acervo Completo** (colunas `ID`, `CATEGORIA`,
`TÍTULO DO LIVRO`, `AUTOR`, `PELO ESPÍRITO`, `TOTAL EXEMPLARES`), agrupa os
exemplares por livro e recria o acervo no banco.

---

## Testes

```bash
python tests/test_biblioteca.py
```

---

## Estrutura do Projeto

```
BiblioGestor/
├── biblioteca.py              # Arquivo principal (aplicação)
├── config.py                  # Configurações, cores e constantes
├── importar_livros.py         # Importação do acervo a partir do Excel
├── requirements.txt           # Dependências
├── atualizador.py             # Atualizador externo (online + offline)
├── Atualizar_BiblioGestor.bat # Launcher do atualizador
├── build_atualizador.bat      # Gera o .exe do atualizador
├── COMO_ATUALIZAR.txt         # Instruções para o cliente
├── tests/
│   └── test_biblioteca.py     # Testes unitários
├── BiblioGestor.bat           # Atalho de execução (Windows)
├── instalar_e_abrir.bat       # Instala dependências e inicia (Windows)
├── build_exe.bat              # Gera o executável do sistema (Windows)
├── build_macos.sh             # Gera o app (macOS)
├── biblioteca.db              # Banco de dados
└── database/                  # Backups automáticos do banco
```
