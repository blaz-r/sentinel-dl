# Sentinel DL

### Env

```bash
conda create -n sentinel_env python=3.10
conda activate sentinel_env

pip install -r requirements
```

### SentinelHub config

In order to download data from SentinelHub, you need to setup the API credentials used with `sentinelhub` library.

Use the provided `sh_setup.py`, which saves this into `sentinelhub` library config file under `sentinel-dl` profile. For more information, refer to [configuration docs](https://sentinelhub-py.readthedocs.io/en/latest/configure.html).

Use the script with the following params:
```bash
python sh_setup.py --id <insert ClientID here> --secret <insert ClinetSecret here>
```

This config will be later used when you use the `eolearn` functionalities to download the data.

### Data downloading
