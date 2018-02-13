# tap-outbrain

Author: Connor McArthur (connor@fishtownanalytics.com)

### Development

This repository contains two configuration files that need to be copied and filled out before running:

- `config.json.example`: copy to `config.json` in the repo root. Contains:
  - `account_id`, aka the Marketer ID (unique to each account) in Outbrain. Looks like `00f4b02153ee75f3c9dc4fc128ab041962`.
  - `username`, the Outbrain username used to generate an Amplify API token.
  - `password`, the Outbrain password to go along with `username`.
  - `access_token`, an optional argument. If provided, this will be used as the access token, and a new one won't be generated.

- `persist.json.example`: copy to `persist.json` in the repo root. Contains the configuration for the Stitch persister.

Then, the streamer can be run (with persistence) with:

```bash
docker build -f Dockerfile .
docker run <image-id>
```

Or, for interactive development:

```bash
docker build -f Dockerfile .

# this automatically propagates changes into the container
docker -v "$(pwd)":/usr/src/tap-outbrain run <image-id>
```

### Gotchas

- Outbrain only allows two calls to the `/login` API per hour. This integration calls that API on every run to generate a new access token. This means that this integration cannot be run more frequently than twice per hour. The access token could be stored in the state file with a timestamp, but at present secure state file storage is not implemented.
- Campaign pagination is not implemented -- this integration pulls incomplete data if more than 100 campaigns exist.

---

Copyright &copy; 2017 Stitch
