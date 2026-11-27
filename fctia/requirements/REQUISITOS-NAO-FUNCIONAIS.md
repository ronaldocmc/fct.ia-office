# Requisitos não funcionais — proposta inicial

Complementam RF01–RF87 sem alterar sua numeração. Critérios propostos, pendentes de homologação.

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RNF01 | Autenticação | Usuário não autenticado não acessa dados nem operações protegidas. |
| RNF02 | Autorização | Usuário e agente sem permissão recebem recusa na API; teste negativo por papel. |
| RNF03 | Isolamento | Dados pessoais, organizacionais e de outras instâncias não aparecem em consultas não autorizadas. |
| RNF04 | Segredos | Credenciais não são versionadas, expostas na interface nem registradas em logs; usar referências protegidas. |
| RNF05 | Privacidade | Dados fictícios na fase experimental; dados reais apenas após análise de finalidade, base legal e autorização. |
| RNF06 | Auditoria | Ação relevante registra ator, instante, objeto e resultado, sem expor segredos. |
| RNF07 | Supervisão | Ações externas ou de alto impacto bloqueadas até política e autorização adequadas; teste de recusa. |
| RNF08 | Persistência | Banco e conta dedicados; acesso sem privilégios administrativos; nenhum acesso ao banco Core. |
| RNF09 | Recuperação | Backup e restauração testados em ambiente isolado antes de uso real. |
| RNF10 | Custos | Limites de execução e orçamento definidos e testados antes de habilitar agentes autônomos. |
| RNF11 | Telemetria | Telemetria opcional externa desativada e configuração verificada. |
| RNF12 | Implantação | Acesso inicial privado e autenticado; sem exposição pública ou alteração de serviços existentes. |
| RNF13 | Reprodutibilidade | Registrar revisão upstream, versões, configuração sem segredos e instruções de instalação. |
| RNF14 | Compatibilidade | Executar testes de regressão upstream aplicáveis e registrar resultados. |
| RNF15 | Desempenho | Medir latência, concorrência, CPU, memória e custo; metas serão definidas após baseline. |

Todos os requisitos estão pendentes de teste. RNF01–RNF08, RNF10–RNF13 são condições para ampliar o ambiente experimental além do teste local isolado.
