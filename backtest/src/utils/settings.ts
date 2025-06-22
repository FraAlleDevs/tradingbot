import { config } from 'dotenv';

config();

function getEnvValue(name: string) {
  return process.env[name];
}

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

function parseDate(name: string) {
  const dateString = getEnvValue(name);

  if (!dateString || !dateRegex.test(dateString)) {
    throw new Error(`Incorrect env date format: ${name} = ${dateString}`);
  }

  return new Date(dateString);
}

function parseNumber(name: string) {
  const numberString = getEnvValue(name);

  const number = Number(numberString);

  if (isNaN(number)) {
    throw new Error(`Incorrect env number format: ${name} = ${numberString}`);
  }

  return number;
}

function parseBoolean(booleanString?: string) {
  return booleanString === 'true';
}

console.log('Reading env settings...');

const envVariables = {
  /** First day the algorithm will calculate */
  startDate: parseDate('START_DATE'),
  /** Last day the algorithm will calculate */
  endDate: parseDate('END_DATE'),
  /** Run or don't run the "hold" algorithm */
  shouldRunAlgorithmHold: parseBoolean('SHOULD_RUN_ALGORITHM_HOLD'),
  /** Run or don't run the "moving average" algorithm */
  shouldRunAlgorithmMovingAverage: parseBoolean(
    'SHOULD_RUN_ALGORITHM_MOVING_AVERAGE',
  ),
  /** Run or don't run the "moving average volume compensated" algorithm */
  shouldRunAlgorithmMovingAverageVolumeCompensated: parseBoolean(
    'SHOULD_RUN_ALGORITHM_MOVING_AVERAGE_VOLUME_COMPENSATED',
  ),
  /** Run or don't run the "mean reversion" algorithm */
  shouldRunAlgorithmMeanReversion: parseBoolean(
    'SHOULD_RUN_ALGORITHM_MEAN_REVERSION',
  ),
  /** Run or don't run the "mean reversion volume compensated" algorithm */
  shouldRunAlgorithmMeanReversionVolumeCompensated: parseBoolean(
    'SHOULD_RUN_ALGORITHM_MEAN_REVERSION_VOLUME_COMPENSATED',
  ),
  /** The days the long term average is calculated for, for the "moving average" algorithm */
  movingAveragelongTermDays: parseNumber('MOVING_AVERAGE_LONG_TERM_DAYS'),
  /** The days the short term average is calculated for, for the "moving average" algorithm */
  movingAverageShortTermDays: parseNumber('MOVING_AVERAGE_SHORT_TERM_DAYS'),
  /** The days the mean is calculated for, for the "mean reversion" algorithm */
  meanReversionScopeDays: parseNumber('MEAN_REVERSION_SCOPE_DAYS'),
  /** The maximum amount of dollar value the bot is allowed to trade every day */
  tradeDollarMaxAmount: parseNumber('TRADE_DOLLAR_MAX_AMOUNT'),
};

export const settings = {
  ...envVariables,
  /** Technical setting: this specifies for how many days before the start date and after the end date should we fetch the data */
  marginDays:
    Math.max(
      envVariables.movingAveragelongTermDays,
      envVariables.meanReversionScopeDays,
    ) * 1.5,
};

console.log('Settings read:');
console.log(settings);
console.log();
