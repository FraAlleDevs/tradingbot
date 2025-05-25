# Basic backtest for algorithms

### Source data

Specify the file path of your csv file in [./src/csvParser.ts](./src/csvParser.ts#L8).

### Requirements

To run this, you need to install Node and NPM (check the package.json file's [engines](./package.json#L7) field for the versions).

Then install all the dependencies:

```sh
npm ci
```

### Run the backtest

The following command will run the file [./src/index.ts](./src/index.ts):

```sh
npm run app
```

This will output the results to the console.

For easier analysis, you can pipe this to a text file:

```sh
npm run app > results.txt
```
