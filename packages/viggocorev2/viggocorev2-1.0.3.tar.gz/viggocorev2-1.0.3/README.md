# viggocorev2

O viggocorev2 é um framework open source para criação de API REST. Ele foi
criado para dar poder ao desenvolvedor, permitindo focar no desenvolvimento do
produto e das regras de negócio em vez de problemas de engenharia.

## Começe do básico

Vamos criar um projeto básico. Primeiro, crie um arquivo chamado 'app.py' com
o seguinte conteúdo:

```python
import viggocorev2

system = viggocorev2.System()
system.run()
```

Abra um terminal e rode os seguintes comandos:

```bash
$ pip install viggocorev2
$ python3 app.py
```

Sua API está rodando e pronta para ser consumida. Vamos testar com uma requisição:

```bash
$ curl -i http://127.0.0.1:5000/
HTTP/1.0 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 5
Server: Werkzeug/1.0.1 Python/3.7.3
Date: Thu, 15 Oct 2020 13:08:19 GMT

1.0.0%
```

Com a sua API criada, siga para nossa [documentação](https://viggocorev2.readthedocs.io/en/latest/) e aproveite o poder e a facilidade
do viggocorev2 no seu negócio ou na sua nova ideia.
