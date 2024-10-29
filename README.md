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

To download data for the entire Slovenian region, run `main.py`:

```bash
python main.py
```

#### Resolution (resolution), resolution (size) and resolution (bbox size).
Sounds as confusing as it is...

In EOlearn API, `resolution` refers to sentinel sampling resolution in meters (usually 10m). 
Size refers to resolution of patch in pixels. 
Then bbox also contains "edge size" in meters of earth covered.

It's important to be careful when setting these up.

Side note (or warning): `SentinelHubInputTask` can't take simultaneous `size` and `resolution`, 
so in order to get let's say region of 2560m with resolution of 10m we need bbox with 2560m side and pass resolution=10. 

The problem is if you want to have a region of 5120m with resolution of 20m and patch of 512x512pixels, 
because this will default to 256x256 (as that is the size if you sample 5120m with spatial resolution of 20m).

Now one can try this: specify 5120m sided bbox and set size to 512px (but you can't also specify resolution). 
This then yields 512x512 res just fine, but it doesn't say which sampling resolution it uses (probably 10). 


### Developing

Use ruff formater and Google docstring format for development.

To format run:
```bash
ruff format .
```