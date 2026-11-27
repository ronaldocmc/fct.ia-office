# FCT.IA Office

Escritório Virtual Inteligente — V0.1 Experimental.

Base: [Paperclip](https://github.com/paperclipai/paperclip), licença MIT. Preservar avisos de licença e autoria upstream. FCT.IA Core permanece independente. FCT.IA Brain será uma extensão/serviço futuro, não uma dependência inicial.

## Desenvolvimento

- Branch de desenvolvimento: develop/fctia-v0.1.
- Requisitos: requirements/REQUISITOS-FUNCIONAIS.md.
- Rastreabilidade: requirements/traceability.json.
- Segurança: requirements/REQUISITOS-NAO-FUNCIONAIS.md.
- Testes: tests/test_requirements.py (Python 3, biblioteca padrão).
- Executar da raiz: python3 -m unittest discover -s fctia/tests -v
- Cada mudança funcional deve referenciar RF/RNF, evidência de implementação e teste.
- Não marcar requisito como validado sem evidência reproduzível.
- Preservar upstream e preferir configuração ou plugins à alteração do núcleo.
- Usar somente dados fictícios até autorização institucional.

## Roadmap

| Versão | Escopo |
|---|---|
| V0.1 | Paperclip, organização, agentes, tarefas e segurança básica |
| V0.2 | Adaptador de execução, comunicação, skills e memória individual |
| V0.3 | Autonomia, aprovações e rotinas |
| V0.4 | Segundo Cérebro |
| V0.5 | Mapa visual |
| V0.6 | Integrações |
| V0.7 | Interface própria |
| V1.0 | Homologação |

A escolha do Hermes permanece sujeita a testes. Nenhuma implantação ou validação funcional é declarada concluída.
