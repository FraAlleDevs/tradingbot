# Basic backtest for algorithms

### Source data

To use a CSV, specify the file path in [./src/csv/csvParser.ts](./src/csv/csvParser.ts#L8).

To use a database, configure the [env](./.env) file with the following fields:

```
DB_USER=xxx
DB_PASSWORD=xxx
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bitcoin_db
```

### Requirements

To run this, you need to install Node and NPM (check the package.json file's [engines](./package.json#L7) field for the versions).

Then install all the dependencies:

```sh
npm ci
```

### Run the backtest

Before running the backtest, configure your [env](./.env) file with the settings for the backtest you want to run. Here's an example:

```
# First day the algorithm will calculate
START_DATE=2020-01-01
# Last day the algorithm will calculate
END_DATE=2020-01-02
# Run or don't run the "hold" algorithm
SHOULD_RUN_ALGORITHM_HOLD=true
# Run or don't run the "moving average" algorithm
SHOULD_RUN_ALGORITHM_MEAN_REVERSION=true
# Run or don't run the "moving average volume compensated" algorithm
SHOULD_RUN_ALGORITHM_MEAN_REVERSION_VOLUME_COMPENSATED=true
# Run or don't run the "mean reversion" algorithm
SHOULD_RUN_ALGORITHM_MOVING_AVERAGE=true
# Run or don't run the "mean reversion volume compensated" algorithm
SHOULD_RUN_ALGORITHM_MOVING_AVERAGE_VOLUME_COMPENSATED=true
# The days the long term average is calculated for, for the "moving average" algorithm
MOVING_AVERAGE_LONG_TERM_DAYS=0.1
# The days the short term average is calculated for, for the "moving average" algorithm
MOVING_AVERAGE_SHORT_TERM_DAYS=0.025
# The days the mean is calculated for, for the "mean reversion" algorithm
MEAN_REVERSION_SCOPE_DAYS=1
# The maximum amount of dollar value the bot is allowed to trade every day
TRADE_DOLLAR_MAX_AMOUNT=100000
```

The following command will run the file [./src/index.ts](./src/index.ts):

```sh
npm run app
```

This will output the results to the console.

For easier analysis, you can pipe this to a text file:

```sh
npm run app > results.txt
```
