SELECT 
  "execution_unix" AS "time", 
  CASE 
    WHEN signal = 'BUY' THEN price + 1000 * confidence
    WHEN signal = 'SELL' THEN price - 1000 * confidence
    ELSE price
  END AS "signal",
  price + 200 AS "buy",
  price - 200 AS "sell",
  price
FROM 
  bot_executions 
 WHERE 
  ($__from/1000) < "execution_unix" AND "execution_unix" < ($__to/1000)
  AND report_card_id = 5