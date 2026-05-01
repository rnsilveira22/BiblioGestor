# 📚 BiblioGestor — Sistema de Gestão de Biblioteca

Sistema simples, leve e 100% offline para gerenciar empréstimos de livros.
Desenvolvido em Python com Tkinter e SQLite.

---

## 🚀 Instalação no Windows (primeira vez)

1. Copie a pasta **BiblioGestor** para o local desejado (ex: `C:\BiblioGestor`)
2. Dê **dois cliques** no arquivo `instalar_e_abrir.bat`
3. O script irá:
   - Verificar se o Python está instalado (e instalar automaticamente se necessário)
   - Instalar as dependências (`pandas`, `openpyxl`)
   - Criar um **atalho na Área de Trabalho**
   - Abrir o sistema

**Nas próximas vezes:** use o atalho da Área de Trabalho ou o `BiblioGestor.bat`

---

## 📥 Importar livros da planilha Excel

1. Coloque a planilha `.xlsx` na mesma pasta do sistema
2. Abra o terminal na pasta e execute:
   ```
   python importar_livros.py
   ```
3. Os livros serão importados automaticamente com as categorias:
   - Espiritismo - Chico Xavier
   - Espiritismo - Divaldo Franco
   - Obras Diversas

---

## 📋 Funcionalidades

| Módulo | Funções |
|---|---|
| **🏠 Painel** | Resumo geral, alertas de atraso em destaque |
| **📖 Livros** | Cadastro com: Número, Título, Autor, Pelo Espírito, Categoria, Exemplares |
| **👤 Associados** | Cadastro de Associados, Professores, Funcionários e Visitantes |
| **🔄 Empréstimos** | Busca inteligente por livro e associado (autocomplete) |
| **↩️ Devoluções** | Confirmação de devolução com cálculo automático de multa |
| **📊 Relatórios** | Histórico, atrasados, multas pendentes, mais emprestados |

---

## ⚙️ Configurações

Edite as linhas iniciais do `biblioteca.py`:

```python
PRAZO_DIAS = 14     # dias padrão de empréstimo
MULTA_DIA  = 0.50   # R$ por dia de atraso
```

---

## 💾 Backup

Todos os dados ficam no arquivo `biblioteca.db`.
Para backup, copie este arquivo para um pen drive ou nuvem.

---

## 📁 Arquivos do sistema

| Arquivo | Descrição |
|---|---|
| `biblioteca.py` | Sistema principal |
| `importar_livros.py` | Importação da planilha Excel |
| `instalar_e_abrir.bat` | Instalador completo (primeira vez) |
| `BiblioGestor.bat` | Abre o sistema rapidamente |
| `biblioteca.db` | Banco de dados (criado automaticamente) |
