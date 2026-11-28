# Persistência PostgreSQL do FCT.IA Office

## Estado
001_office.sql é a proposta inicial de schema PostgreSQL 17; ainda não executada no servidor. O runtime continua utilizando SQLite. Não aplicar no banco do Core ou com a credencial do Paperclip.

## Contrato de migração
- Usar banco experimental dedicado e papéis separados para migração e execução.
- Criar backup consistente do SQLite; importar para banco vazio em uma transação.
- Mapear office_tasks.snapshot para tasks: id, title, skill, payload, state, agent, result, review. Timestamps ausentes devem ser reconstruídos dos eventos ou registrados explicitamente como desconhecidos; não inventar datas históricas.
- Mapear office_events.event para events, preservando ordem por seq, timestamps, actor, action, state, task_id e evidências de review/result.
- Mapear knowledge preservando todos os campos e escopos.
- Validar contagens, UUIDs, referências, estados, equivalência JSON e conteúdo aprovado. Abortar toda a transação diante de divergência. Não apagar SQLite.
- O runtime PostgreSQL deve persistir estado e evento na mesma transação e tratar concorrência por bloqueio ou controle otimista. Não reutilizar cache em memória como fonte de verdade multiusuário.
- Escopos são classificação lógica, não autorização. Antes de dados reais, implementar identidade institucional, RBAC, isolamento por escopo e testes de acesso.
- pgvector é uma extensão posterior, com modelo e dimensão de embeddings definidos, sem substituir a busca textual e aprovação humana.
- A revisão em homologação permanece fixa; estas mudanças não a afetam.

## Critérios de aceite
Teste em PostgreSQL descartável; rollback integral em caso de falha; persistência após reinicialização; equivalência SQLite/PostgreSQL; aprovação de conhecimento por escopo; eventos imutáveis para papel de execução; nenhuma alteração no Core. Alembic e adaptador de execução ainda pendentes.
