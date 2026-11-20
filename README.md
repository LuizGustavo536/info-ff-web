# ⚡ LUIZxFFINFO — Site de Informações do Free Fire (OB55)

Um site moderno, rápido e completo para consulta de perfis e estatísticas de jogadores de Free Fire, atualizado e compatível com a versão **OB55**.

---

## 📁 Estrutura de Arquivos

```
Site-info/
├── main.py                     ← Servidor Flask principal (Python)
├── app.py                      ← Entrypoint alternativo de execução
├── api/
│   └── index.py                ← Entrada serverless para deploy na Vercel
├── vercel.json                 ← Configuração de rotas da Vercel
├── requirements.txt            ← Dependências do Python
├── uidpass.json                ← (Opcional/Privado) Pool local de contas para rotação
├── proto/                      ← Arquivos Protobuf compilados (OB55)
│   ├── AccountPersonalShow_pb2.py
│   ├── main_pb2.py
│   └── FreeFire_pb2.py
├── templates/
│   └── index.html              ← Página web principal (HTML)
└── static/
    ├── css/style.css           ← Folhas de estilo e temas
    └── js/script.js            ← Lógica do frontend e catálogo de habilidades
```

---

## ⚙️ Instalação e Execução Local

### 1. Requisitos
- Python 3.8 ou superior instalado.

### 2. Instalar Dependências:
```bash
pip install -r requirements.txt
```

### 3. Iniciar o Servidor:
```bash
python main.py
```

### 4. Acessar no Navegador:
Abra seu navegador e acesse:
```
http://localhost:5000
```

---

## 🚀 Deploy na Vercel

O projeto possui suporte nativo a funções Serverless da Vercel:
1. Conecte o repositório à sua conta na **Vercel**.
2. O arquivo [`vercel.json`](file:///vercel.json) e [`api/index.py`](file:///api/index.py) já estão pré-configurados.
3. Clique em **Deploy**.

---

## 🌐 Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `GET /` | HTTP | Página principal do site com interface interativa |
| `GET /get?uid={UID}` | HTTP | Consulta informações do jogador com busca automática de região |
| `GET /get?uid={UID}&region={REGIAO}` | HTTP | Consulta forçando uma região específica (`BR`, `US`, `IND`, `ME`, `BD`, etc.) |
| `GET /status` | HTTP | Exibe o status e tempo de expiração dos tokens por região |
| `GET /refresh` | HTTP | Força a renovação dos tokens |
| `GET /test/{REGIAO}` | HTTP | Testa a geração de token para a região informada |

---

## 🖼️ Exibição de Recursos e Imagens

- **Roupas Equipadas (`EquippedOutfit`):** Exibição dinâmica das peças de roupa através do CDN oficial de ícones.
- **Skins de Armas Equipadas (`EquippedWeapon`):** Renderização visual das skins equipadas pelo jogador.
- **Habilidades (`EquippedSkills`):** Identificação e tradução automática das habilidades ativas e passivas dos personagens.
- **Descompressão Automática:** Tratamento transparente de payloads comprimidos em Gzip pelo servidor da Garena.
- **Rotação de Contas:** Mecanismo resiliente contra limites de taxa (HTTP 429) usando pool de contas rotativo.

---

## 👤 Créditos

- Projeto atualizado e desenvolvido por **Luiz Gustavo** ⚡
- Compatibilidade e suporte à versão **Free Fire OB55**
