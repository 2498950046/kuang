# Docker deployment

This deployment is designed for your current server layout on `154.44.25.243`.

It only deploys:

- Frontend
- `backendAdmin`
- MySQL
- Neo4j
- Redis

It intentionally reuses your already running services on:

- `8080` -> `kuangshi-backend-backend`
- `8081` -> `java-ai-langchain4j-app`
- `18080` -> `ml-platform-frontend`

## 1. Prepare files on the server

Upload the repository to the server, for example:

```bash
mkdir -p /opt/kuang
cd /opt/kuang
```

Copy the server env template:

```bash
cp deploy/.env.server.example deploy/.env.server
```

Then edit `deploy/.env.server`:

- Set `SERVER_IP` if your public IP changes
- Change `MYSQL_ROOT_PASSWORD`
- Change `NEO4J_PASSWORD`
- Confirm all `VITE_*` URLs still point to `154.44.25.243`

## 2. Build images

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml build frontend backend-admin data-init
```

## 3. Start infrastructure first

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml up -d mysql neo4j redis
```

Check status:

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml ps
```

## 4. Initialize data first

This step is required before starting `backend-admin`.

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml --profile init run --rm data-init
```

What this does:

- imports `backend_all/backendAdmin/mineral_data_test/gemsBasicInfo.csv` into MySQL
- imports `backend_all/backendAdmin/mineral_data_test/mydb.baoshi.json` into MySQL
- imports `backend_all/backendAdmin/mineral_data_test/矿物基本信息.csv` into Neo4j

## 5. Start application services

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml up -d backend-admin frontend
```

## 6. Verify

Open these addresses:

- Frontend: `http://154.44.25.243`
- Admin backend: `http://154.44.25.243:5002`
- Neo4j Browser: `http://154.44.25.243:17474`

Default admin account created by `backendAdmin` on first request:

- username: `admin`
- password: `Admin@123456`

## 7. Common commands

View logs:

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml logs -f frontend
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml logs -f backend-admin
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml logs -f mysql
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml logs -f neo4j
```

Restart services:

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml restart frontend backend-admin
```

Stop services:

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml down
```

Stop and remove data volumes:

```bash
docker compose --env-file deploy/.env.server -f deploy/docker-compose.server.yml down -v
```

## Notes

- If port `80` is already occupied on the server, change `FRONTEND_PORT` in `deploy/.env.server`.
- If you later want to move everything behind a domain and reverse proxy, the current compose can stay unchanged.
- The frontend build now reads service addresses from Vite env variables, so changing IPs no longer requires editing Vue source files.
