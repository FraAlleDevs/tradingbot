# Basic backtest for algorithms

### Source data

Copy the Bitcoin price data .csv file into `data/data.csv`.

### Requirements

To run this, you need to install Node (v16 preferably) and NPM (v8 preferably).

Then install all the dependencies:

```sh
npm ci
```

### Configuration

The initial file is `./src/index.ts`. Change the parameters in that file to configure the backtest to run.

### Run the backtest

Run the backtest with:

```sh
npm run app
```

This will output the results to the console.

For easier analysis, you can pipe this to a text file:

```sh
npm run app > results.txt
```
