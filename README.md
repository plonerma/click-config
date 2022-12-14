# Small wrapper around dataclass to enable use with click (as config)


## Example Usage

```
@config_class
class Config:
    """Some description.

    :param a: a_help_str
    """
    a: int
    b: str = "test"
    c: List[str] = field("-c", help="c_help_str", default=["z"])


@click.command()
@Config.click_options
def run(config):
    print("Config", config)


if __name__ == "__main__":
    run()
```

This script can be called from the command line. A configuration file can be
loaded via `--config <path>` and individual fields can be overwritten using
cli options such as `-a 5`.
