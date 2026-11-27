# Implantação experimental V0.1

Status: proposta ainda não executada. Exige autorização institucional para uso de Docker e recursos do servidor. Não registrar runner self-hosted no fork público. Não usar dados reais, credenciais institucionais, socket Docker nos containers ou integrações de agentes nesta etapa.

## Diagnóstico no servidor
Em sessão SSH já autorizada, execute:

```bash
git clone --branch develop/fctia-v0.1 --single-branch https://github.com/ronaldocmc/fct.ia-office.git ~/fctia-office
cd ~/fctia-office
bash fctia/deploy/diagnose.sh
```

Se o diretório já existir, não sobrescreva: verifique sua origem e revisão. Não altere o Core. Confirme Docker Compose, acesso autorizado ao daemon, recursos livres e porta 3100 (ou outra livre). A ausência de listener não reserva a porta.

## Isolamento
O compose experimental adapta docker/docker-compose.yml do upstream: banco PostgreSQL próprio em volume Docker, sem porta publicada; aplicação somente em 127.0.0.1; autenticação privada; telemetria desativada. Nesta fase optou-se por banco isolado em container em vez do PostgreSQL compartilhado do host para evitar alterações nele. O usuário criado por POSTGRES_USER é administrador do banco experimental, não uma conta de privilégios mínimos; antes de uso institucional, separar usuário de administração/migração e aplicação e testar os privilégios. Não aprovar RNF08 enquanto isso não for verificado.

## Configuração após autorização e diagnóstico
Criar arquivo de ambiente fora do Git, com permissão 600. Valores hexadecimais aleatórios evitam problemas de codificação na URL PostgreSQL. Não imprimir nem compartilhar o conteúdo.

```bash
umask 077
mkdir -p "$HOME/.config/fctia-office"
envfile="$HOME/.config/fctia-office/office.env"
if [ ! -e "$envfile" ]; then
  (set -C; printf 'FCTIA_DB_PASSWORD=%s\nFCTIA_AUTH_SECRET=%s\nFCTIA_SIGNING_SECRET=%s\nFCTIA_PORT=3100\n' "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" > "$envfile")
fi
chmod 600 "$envfile"
docker compose --project-name fctia-office --env-file "$envfile" -f fctia/deploy/compose.yml config --quiet
```

Verifique a revisão Git, disponibilidade de recursos e autorização antes de construir a imagem (build upstream pode consumir recursos substanciais). Depois:

```bash
docker compose --project-name fctia-office --env-file "$envfile" -f fctia/deploy/compose.yml up -d --build
docker compose --project-name fctia-office --env-file "$envfile" -f fctia/deploy/compose.yml ps
```

Use túnel SSH autorizado, com porta local correspondente à configurada: ssh -N -L 3100:127.0.0.1:3100 USUARIO@ia.fct.unesp.br. Abra http://localhost:3100 e siga o bootstrap de administrador documentado pelo upstream. Não exponha via Nginx até validar autenticação, isolamento e política institucional.

## Parada
```bash
docker compose --project-name fctia-office --env-file "$envfile" -f fctia/deploy/compose.yml down
```
Não usar down -v: preserva os volumes. Testar backup e restauração antes de uso real. Nenhum agente autônomo habilitado até validação de segurança e orçamento.
