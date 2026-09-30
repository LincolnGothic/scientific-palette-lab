# Full web application from a private GitHub repository

GitHub stores the source; a Python web host runs the application and provides the clickable HTTPS URL. GitHub Pages cannot execute the existing Python collector, SQLite review store, extraction, and analysis API.

## Prepared Render configuration

The root `render.yaml` defines one Docker web service with a 1 GB persistent disk mounted at `/var/data`. It uses Render's smallest paid compute plan (`0.5c-512mb` in the current Blueprint reference). This is a **paid configuration**: review the compute, disk, bandwidth, and workspace charges displayed by Render before creating anything. A free service's filesystem is ephemeral; using it without another persistent store would lose collected data and reviews after restarts/deploys.

1. Sign in to an existing Render account. If you need a new account, complete its registration and terms yourself.
2. Connect GitHub and grant Render access specifically to `LincolnGothic/scientific-palette-lab`. Keep the repository private. Review the GitHub App permission request before granting access.
3. Create a Blueprint from this repository's `main` branch and review `render.yaml`.
4. Set the secret `PALETTE_WEB_PASSWORD` in Render to a unique password of at least 16 characters. Enter it directly in Render; never commit it or paste it into a chat. The default sign-in username is `researcher`; it can be changed through `PALETTE_WEB_USERNAME`.
5. Review Render's charges and complete the service creation yourself if acceptable. The Docker build installs NumPy/Pillow and starts the existing application. `PORT` and `RENDER_EXTERNAL_URL` are supplied by Render.
6. When deployment is healthy, open Render's actual generated HTTPS URL. The browser prompts for the workspace username/password. Check collection, uploads, review saving, palette rankings, exports, and 3–8 color recommendations, then verify data remains after a restart.

There is no live URL until a deployment succeeds. The prepared files do not activate a service, incur charges, or grant Render repository access.

## Access and storage model

This deployment is a **single shared research workspace**, protected by HTTP Basic authentication at the application's request boundary. The service's network address exists publicly; the application, API, assets, and exports require credentials. HTTPS is terminated by the host's reverse proxy. Do not expose the backend port directly outside that proxy. `/health` is unauthenticated and returns only `{"status":"ok"}`. Host/origin checks allow the configured external URL and loopback addresses; cross-origin writes remain blocked.

All signed-in users share the same corpus and can edit its reviews. This is suitable for a personal tool or a trusted small research group. It does not implement separate user accounts, account recovery, individual permissions, or isolated datasets. Do not share its password with an anonymous public audience. A public collaborative product needs those additions before release.

The deployed corpus starts empty: local journal figures and the local database remain excluded from Git and Docker. Collection or authorized image uploads populate the hosted disk. Store the entire data directory on the persistent disk, including SQLite/WAL files, assets, and source snapshots. Keep one instance; multiple instances cannot safely share this local storage layout. Back up the complete corpus outside the running service. In-memory collection jobs do not resume after a deploy; avoid deploying during collection and inspect collection history afterward.

## Configuration

| Variable | Meaning |
|---|---|
| `PALETTE_HOST` | Defaults to `127.0.0.1`; set to `0.0.0.0` behind the host's HTTPS proxy. |
| `PORT` | Server port; defaults locally to 8765. |
| `PALETTE_DATA_DIR` | Persistent corpus directory; `/var/data` in the Blueprint. |
| `PALETTE_EXTERNAL_URL` | Optional explicit HTTPS site URL for another provider or custom domain. Takes precedence over Render's URL. |
| `RENDER_EXTERNAL_URL` | Render's automatically supplied HTTPS URL. |
| `PALETTE_WEB_USERNAME` | Workspace username, default `researcher`. |
| `PALETTE_WEB_PASSWORD` | Secret shared workspace password. Required for a non-loopback listener, with an HTTPS external URL. |

Local usage remains `bash run.sh`. Hosted configuration refuses to start on a non-loopback interface without an HTTPS URL and a sufficiently long password. A Docker build excludes local data and secrets. This version is intended for a modest single-workspace deployment behind the provider proxy; large public workloads require a production application server, resource limits, and durable background workers.

## Official references

- [GitHub Pages is static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Render web services and private repository integration](https://render.com/docs/web-services)
- [Render persistent disks and their limits](https://render.com/docs/disks)
- [Render default environment variables](https://render.com/docs/environment-variables)
- [Render Blueprint fields and plan IDs](https://render.com/docs/blueprint-spec)
- [Render pricing: confirm the actual displayed cost before deploying](https://render.com/pricing)
