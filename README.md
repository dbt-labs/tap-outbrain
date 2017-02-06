# tap-outbrain

Author: Connor McArthur (connor@fishtownanalytics.com)

### Development

This repository contains two configuration files that need to be copied and filled out before running:

- `config.json.example`: copy to `config.json` in the repo root. Contains the `access_token`, which is the Outbrain access token / API key. Also contains the `account_id`, aka the Marketer ID (unique to each account) in Outbrain. Looks like `00f4b02153ee75f3c9dc4fc128ab041962`.

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

- Outbrain only allows 5 requests per minute to the performance reporting API, which makes this integration potentially slow.
- There's a 30 day expiration on every access token, meaning this integration has to refresh its own token. This is not yet implemented but could be done using the state file.


---

Copyright &copy; 2017 Stitch
