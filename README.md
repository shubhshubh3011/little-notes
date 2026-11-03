# Notes

A minimal Flask and MySQL notes app. Add notes with a title and content, view them newest first, and delete them. The app and MySQL run as separate Docker containers.
Use **Download PDF** to save a PDF of your notes to your device. MySQL's database files persist in `data/mysql` in the project folder. They are managed by MySQL; do not edit or move individual files there.

## Run with Docker

Build the app image:

```sh
docker build -t notes-app .
```

The image is the Flask app only. To run it with its MySQL database, use Docker Compose as shown below.

## Run with Docker Compose

```sh
docker compose up --build
```

Compose starts two containers: the Flask app and MySQL. Open [http://localhost:5000](http://localhost:5000). MySQL stores its data under `data/mysql` on your device, including after `docker compose down`.
The original SQLite database, `data/notes.db`, is retained as a backup; the running app uses MySQL in `data/mysql`.

The Compose file has development-only default database passwords. For local overrides, set `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` in the environment before starting Compose. Use strong secrets for any shared or deployed environment.

To keep a portable copy of your notes, download the PDF from the app before moving to another machine. To move the live database, use a MySQL backup and restore rather than copying the old SQLite `data/notes.db` file.

Stop the app with `Ctrl+C`, or run `docker compose down`.

## Stop a Docker container

```sh
docker compose down
```

## Push to Docker Hub

Sign in, tag the image with your Docker Hub username, and push it:

```sh
docker login
docker tag notes-app YOUR_DOCKERHUB_USERNAME/notes-app:latest
docker push YOUR_DOCKERHUB_USERNAME/notes-app:latest
```

On another machine, pull the published image:

```sh
docker pull YOUR_DOCKERHUB_USERNAME/notes-app:latest
```

Replace the `build: .` line for the `notes` service in `docker-compose.yml` with:

```yaml
image: YOUR_DOCKERHUB_USERNAME/notes-app:latest
```

Then run `docker compose up -d`. Each machine gets its own local MySQL data directory; use a database backup/restore to transfer notes between machines.
