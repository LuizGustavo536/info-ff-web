# Suporte para Vercel

Este projeto foi adaptado para rodar na Vercel usando Flask em função serverless.

## Estrutura importante

```txt
api/index.py        # entrada da Vercel
vercel.json         # configuração do deploy
requirements.txt    # bibliotecas Python
static/             # CSS/JS
templates/          # HTML
proto/              # arquivos protobuf
```

## Como hospedar

1. Envie todos os arquivos deste projeto para um repositório no GitHub.
2. Entre na Vercel e clique em **Add New Project**.
3. Selecione o repositório.
4. Em Framework Preset, deixe como **Other**.
5. Clique em **Deploy**.

## Rotas

```txt
/                  site principal
/get?uid=UID       buscar informações
/get?uid=UID&region=BR
/status            status dos tokens
/refresh           atualizar tokens
/test/BR           testar região
```

## Observação

A Vercel é serverless, então tarefas em segundo plano permanentes não funcionam bem. Por isso, os tokens são gerados quando a API recebe chamadas.
