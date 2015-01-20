# neighborhood-yelper
Itty bitty little Python utility script that makes a request to the Yelp API search endpoint and produces a csv report.

## Getting Started
Clone this repository or download the Python script.  Run it in your command-line with options:

```
python get_business_data_by_neighborhood.py --term 'church' --location 'Woodstock, Portland, OR' --sort 0 --offset 0
```

The script will query the Yelp Search API for the provided term and location, along with the other parameters.  The script outputs the JSON returned from the API in the /json folder and creates a csv report with Python's pandas package in the /processed_data folder which can be imported into your spreadsheet program of choice.

The script returns a 400 error from the API if the query is not formed correctly, which is most likely to occur when a value is specified outside of what the API allows... like asking for radius_filter beyond 20000.

## Supported Parameters
The following parameters are supported:

|Shorthand | Long-hand | Description |
|----------|-----------|-------------|
|-q |--term          |Search term  |
|-l |--location      |Neighborhood, City, State |
|-r |--radius_filter |Allowed radius around neighborhood (meters) |
|-s |--sort          |Sort by Best Match, distance, highest rated (0, 1, 2) |
|-o |--offset        |Offset listed results |
